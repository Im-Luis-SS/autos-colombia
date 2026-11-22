"""Gestión de pagos de mensualidades y de las tarifas (solo administradores)."""
import re
from datetime import date, datetime, time

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from app.errors import NoEncontradoError, ReglaNegocioError
from app.extensions import db
from app.models import (
    ESTADOS_PAGO,
    MEDIOS_PAGO,
    TIPOS_VEHICULO,
    Cliente,
    Mensualidad,
    Pago,
    Tarifa,
    Vehiculo,
    ahora,
)
from app.services.clientes import ClienteService
from app.services.validaciones import texto_requerido

TARIFA_MINIMA = 10_000
TARIFA_MAXIMA = 5_000_000
PATRON_REFERENCIA = re.compile(r"^[A-Za-z0-9\-]{4,40}$")
MEDIOS_CON_REFERENCIA = ("TRANSFERENCIA", "TARJETA")


def formatear_pesos(valor) -> str:
    """150000 -> «$150.000» (separador de miles colombiano)."""
    return "$" + f"{int(valor):,}".replace(",", ".")


class TarifaService:
    @staticmethod
    def listar():
        return Tarifa.query.order_by(Tarifa.tipo_vehiculo).all()

    @staticmethod
    def obtener(tipo) -> Tarifa:
        tipo = (tipo or "").strip().upper()
        tarifa = Tarifa.query.filter_by(tipo_vehiculo=tipo).first() if tipo in TIPOS_VEHICULO else None
        if tarifa is None:
            raise NoEncontradoError("La tarifa no existe.")
        return tarifa

    @classmethod
    def actualizar(cls, tipo, valor) -> Tarifa:
        tarifa = cls.obtener(tipo)
        texto = (valor or "").replace("$", "").replace(".", "").replace(",", "").replace(" ", "")
        if not texto.isdigit():
            raise ReglaNegocioError(
                f"El valor debe ser un número entero de pesos, entre {formatear_pesos(TARIFA_MINIMA)} "
                f"y {formatear_pesos(TARIFA_MAXIMA)}."
            )
        numero = int(texto)
        if not TARIFA_MINIMA <= numero <= TARIFA_MAXIMA:
            raise ReglaNegocioError(
                f"El valor debe estar entre {formatear_pesos(TARIFA_MINIMA)} y {formatear_pesos(TARIFA_MAXIMA)}."
            )
        tarifa.valor = numero
        db.session.commit()
        return tarifa


class PagoService:
    @staticmethod
    def obtener(id_pago) -> Pago:
        pago = db.session.get(Pago, id_pago)
        if pago is None:
            raise NoEncontradoError("El pago no existe.")
        return pago

    @staticmethod
    def _validar_medio_y_referencia(medio, referencia):
        medio = (medio or "").strip().upper()
        if medio not in MEDIOS_PAGO:
            raise ReglaNegocioError("Seleccione un medio de pago válido (efectivo, transferencia o tarjeta).")
        if medio not in MEDIOS_CON_REFERENCIA:
            return medio, None  # en efectivo no se guarda referencia
        referencia = (referencia or "").strip()
        if not PATRON_REFERENCIA.match(referencia):
            raise ReglaNegocioError(
                "Para transferencia o tarjeta indique la referencia (número de transacción o de "
                "aprobación): de 4 a 40 letras, números o guiones."
            )
        return medio, referencia.upper()

    @classmethod
    def registrar(cls, id_vehiculo, medio, referencia, actor, hoy: date = None) -> Pago:
        """Cobra la mensualidad al valor de la tarifa vigente y la activa por 30 días.

        Pago y mensualidad se guardan juntos: si algo falla no queda ninguno de los dos.
        """
        vehiculo = ClienteService.obtener_vehiculo(id_vehiculo)
        medio, referencia = cls._validar_medio_y_referencia(medio, referencia)
        tarifa = TarifaService.obtener(vehiculo.tipo)
        mensualidad = ClienteService.preparar_mensualidad(vehiculo, hoy)  # rechaza si ya hay una vigente
        pago = Pago(
            mensualidad=mensualidad,
            valor=tarifa.valor,
            medio=medio,
            referencia=referencia,
            fecha_hora=ahora(),
            estado="REGISTRADO",
            usuario=actor,
        )
        db.session.add(pago)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ReglaNegocioError(
                f"El vehículo {vehiculo.placa} ya tiene una mensualidad activa: no se registró el pago."
            )
        return pago

    @classmethod
    def anular(cls, id_pago, motivo, actor, hoy: date = None) -> Pago:
        """Anula el pago y cancela su mensualidad. Solo mientras la mensualidad no haya vencido."""
        pago = cls.obtener(id_pago)
        hoy = hoy or ahora().date()
        if pago.esta_anulado():
            raise ReglaNegocioError(f"El pago {pago.numero} ya está anulado.")
        motivo = texto_requerido(motivo, "El motivo de la anulación", minimo=5, maximo=255)
        mensualidad = pago.mensualidad
        if mensualidad.estado != "ACTIVA" or mensualidad.fecha_fin < hoy:
            raise ReglaNegocioError(
                f"No se puede anular el pago {pago.numero}: su mensualidad ya venció y el servicio fue prestado."
            )
        pago.estado = "ANULADO"
        pago.motivo_anulacion = motivo
        pago.fecha_hora_anulacion = ahora()
        pago.usuario_anulo = actor
        mensualidad.estado = "CANCELADA"
        db.session.commit()
        return pago

    # ---------------------------------------------------------------- consultas
    @staticmethod
    def _consulta(q=None, medio=None, estado=None, desde: date = None, hasta: date = None):
        consulta = (
            Pago.query.join(Mensualidad, Pago.id_mensualidad == Mensualidad.id_mensualidad)
            .join(Vehiculo, Mensualidad.id_vehiculo == Vehiculo.id_vehiculo)
            .join(Cliente, Vehiculo.id_cliente == Cliente.id_cliente)
        )
        texto = (q or "").strip()
        if texto:
            patron = f"%{texto}%"
            consulta = consulta.filter(
                or_(
                    Vehiculo.placa.like(patron.upper().replace(" ", "")),
                    Cliente.numero_documento.like(patron),
                    Cliente.nombres.like(patron),
                    Cliente.apellidos.like(patron),
                )
            )
        if medio in MEDIOS_PAGO:
            consulta = consulta.filter(Pago.medio == medio)
        if estado in ESTADOS_PAGO:
            consulta = consulta.filter(Pago.estado == estado)
        if desde:
            consulta = consulta.filter(Pago.fecha_hora >= datetime.combine(desde, time.min))
        if hasta:
            consulta = consulta.filter(Pago.fecha_hora <= datetime.combine(hasta, time.max))
        return consulta

    @classmethod
    def listar(cls, q=None, medio=None, estado=None, desde=None, hasta=None, pagina=1, por_pagina=15):
        if desde and hasta and desde > hasta:
            raise ReglaNegocioError("La fecha inicial no puede ser posterior a la final.")
        return (
            cls._consulta(q, medio, estado, desde, hasta)
            .order_by(Pago.fecha_hora.desc(), Pago.id_pago.desc())
            .paginate(page=pagina, per_page=por_pagina, error_out=False)
        )

    @classmethod
    def total_recaudado(cls, q=None, medio=None, estado=None, desde=None, hasta=None) -> int:
        """Suma de los pagos REGISTRADOS (los anulados no cuentan) que cumplen el filtro."""
        consulta = cls._consulta(q, medio, estado, desde, hasta).filter(Pago.estado == "REGISTRADO")
        total = consulta.with_entities(func.coalesce(func.sum(Pago.valor), 0)).scalar()
        return int(total or 0)
