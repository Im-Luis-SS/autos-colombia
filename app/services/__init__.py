"""Capa de negocio: todas las reglas del sistema viven aquí."""
import re
from datetime import date, datetime, time, timedelta

from sqlalchemy.exc import IntegrityError

from app.errors import ReglaNegocioError
from app.extensions import db
from app.models import (
    Celda,
    Mensualidad,
    Movimiento,
    UsuarioSistema,
    Vehiculo,
    ahora,
)

PATRON_PLACA = re.compile(r"^[A-Z0-9]{5,7}$")


def normalizar_placa(placa: str) -> str:
    return (placa or "").strip().upper().replace("-", "").replace(" ", "")


def formatear_duracion(delta: timedelta) -> str:
    minutos_totales = int(delta.total_seconds() // 60)
    dias, resto = divmod(minutos_totales, 1440)
    horas, minutos = divmod(resto, 60)
    partes = []
    if dias:
        partes.append(f"{dias} d")
    partes.append(f"{horas} h")
    partes.append(f"{minutos:02d} min")
    return " ".join(partes)


class AuthService:
    @staticmethod
    def autenticar(username: str, clave: str) -> UsuarioSistema:
        username = (username or "").strip()
        if not username or not clave:
            raise ReglaNegocioError("Ingrese usuario y contraseña.")
        usuario = UsuarioSistema.query.filter_by(username=username).first()
        if usuario is None or not usuario.activo or not usuario.verificar_clave(clave):
            # Mensaje genérico a propósito: no revela si el usuario existe.
            raise ReglaNegocioError("Usuario o contraseña incorrectos.")
        return usuario


class MovimientoService:
    # ---------- helpers privados ----------
    @staticmethod
    def _obtener_vehiculo(placa: str) -> Vehiculo:
        placa = normalizar_placa(placa)
        if not placa:
            raise ReglaNegocioError("Ingrese la placa del vehículo.")
        if not PATRON_PLACA.match(placa):
            raise ReglaNegocioError(
                "La placa debe tener entre 5 y 7 caracteres alfanuméricos (ej. ABC123 o ABC12D)."
            )
        vehiculo = Vehiculo.query.filter_by(placa=placa).first()
        if vehiculo is None:
            raise ReglaNegocioError(
                f"El vehículo con placa {placa} no está registrado. "
                "Solo pueden ingresar vehículos de clientes con mensualidad."
            )
        return vehiculo

    @staticmethod
    def _movimiento_abierto(vehiculo: Vehiculo):
        return Movimiento.query.filter_by(
            id_vehiculo=vehiculo.id_vehiculo, fecha_hora_salida=None
        ).first()

    @staticmethod
    def _validar_mensualidad(vehiculo: Vehiculo, hoy: date) -> Mensualidad:
        for m in vehiculo.mensualidades:
            if m.esta_vigente(hoy):
                return m
        raise ReglaNegocioError(
            f"El vehículo {vehiculo.placa} no tiene una mensualidad vigente. "
            "No se permite el ingreso."
        )

    @staticmethod
    def _asignar_celda(vehiculo: Vehiculo, codigo_preferido: str = None) -> Celda:
        if codigo_preferido:
            celda = Celda.query.filter_by(codigo=codigo_preferido.strip().upper()).first()
            if celda is None:
                raise ReglaNegocioError("La celda indicada no existe.")
            if celda.tipo != vehiculo.tipo:
                raise ReglaNegocioError(
                    f"La celda {celda.codigo} es para {celda.tipo.lower()}s y el vehículo es "
                    f"{vehiculo.tipo.lower()}."
                )
            if celda.estado != "LIBRE":
                raise ReglaNegocioError(f"La celda {celda.codigo} no está libre ({celda.estado.lower()}).")
            return celda
        celda = (
            Celda.query.filter_by(tipo=vehiculo.tipo, estado="LIBRE")
            .order_by(Celda.codigo)
            .first()
        )
        if celda is None:
            raise ReglaNegocioError(
                f"No hay celdas libres para {vehiculo.tipo.lower()}s en este momento."
            )
        return celda

    # ---------- casos de uso ----------
    @classmethod
    def registrar_entrada(cls, placa, operario, observaciones=None, celda_codigo=None) -> Movimiento:
        vehiculo = cls._obtener_vehiculo(placa)
        momento = ahora()
        cls._validar_mensualidad(vehiculo, momento.date())
        if cls._movimiento_abierto(vehiculo):
            raise ReglaNegocioError(f"El vehículo {vehiculo.placa} ya se encuentra dentro del parqueadero.")
        celda = cls._asignar_celda(vehiculo, celda_codigo)

        movimiento = Movimiento(
            vehiculo=vehiculo,
            celda=celda,
            usuario_entrada=operario,
            fecha_hora_entrada=momento,
            observaciones=(observaciones or "").strip()[:255] or None,
        )
        celda.ocupar()
        db.session.add(movimiento)
        try:
            db.session.commit()
        except IntegrityError:
            # Dos operarios intentaron ocupar lo mismo a la vez: la BD lo impide.
            db.session.rollback()
            raise ReglaNegocioError(
                "No se pudo registrar la entrada porque otro operario modificó la celda o el "
                "vehículo al mismo tiempo. Intente de nuevo."
            )
        return movimiento

    @classmethod
    def registrar_salida(cls, placa, operario, observaciones=None) -> Movimiento:
        vehiculo = cls._obtener_vehiculo(placa)
        movimiento = cls._movimiento_abierto(vehiculo)
        if movimiento is None:
            raise ReglaNegocioError(
                f"El vehículo {vehiculo.placa} no tiene una entrada registrada: no se puede registrar la salida."
            )
        movimiento.registrar_salida(operario, ahora())
        movimiento.celda.liberar()
        nota = (observaciones or "").strip()
        if nota:
            previa = movimiento.observaciones
            combinado = f"{previa} | Salida: {nota}" if previa else f"Salida: {nota}"
            movimiento.observaciones = combinado[:255]
        db.session.commit()
        return movimiento

    @staticmethod
    def vehiculos_en_parqueadero(filtro_placa=None):
        consulta = Movimiento.query.filter(Movimiento.fecha_hora_salida.is_(None))
        filtro = normalizar_placa(filtro_placa or "")
        if filtro:
            consulta = consulta.join(Vehiculo).filter(Vehiculo.placa.like(f"%{filtro}%"))
        return consulta.order_by(Movimiento.fecha_hora_entrada.desc()).all()

    @staticmethod
    def historial(placa=None, desde: date = None, hasta: date = None, pagina=1, por_pagina=15):
        consulta = Movimiento.query.join(Vehiculo)
        filtro = normalizar_placa(placa or "")
        if filtro:
            consulta = consulta.filter(Vehiculo.placa.like(f"%{filtro}%"))
        if desde:
            consulta = consulta.filter(Movimiento.fecha_hora_entrada >= datetime.combine(desde, time.min))
        if hasta:
            consulta = consulta.filter(
                Movimiento.fecha_hora_entrada <= datetime.combine(hasta, time.max)
            )
        return consulta.order_by(Movimiento.fecha_hora_entrada.desc()).paginate(
            page=pagina, per_page=por_pagina, error_out=False
        )


class OcupacionService:
    @staticmethod
    def celdas():
        return Celda.query.order_by(Celda.codigo).all()

    @classmethod
    def resumen(cls) -> dict:
        resumen = {}
        for tipo in ("CARRO", "MOTO"):
            celdas = Celda.query.filter_by(tipo=tipo).all()
            resumen[tipo] = {
                "total": len(celdas),
                "libres": sum(c.estado == "LIBRE" for c in celdas),
                "ocupadas": sum(c.estado == "OCUPADA" for c in celdas),
                "mantenimiento": sum(c.estado == "MANTENIMIENTO" for c in celdas),
            }
        todas = Celda.query.all()
        resumen["TOTAL"] = {
            "total": len(todas),
            "libres": sum(c.estado == "LIBRE" for c in todas),
            "ocupadas": sum(c.estado == "OCUPADA" for c in todas),
            "mantenimiento": sum(c.estado == "MANTENIMIENTO" for c in todas),
        }
        return resumen
