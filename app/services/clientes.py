"""Gestión de clientes, vehículos y mensualidades."""
import re
from datetime import date, timedelta

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app.errors import NoEncontradoError, ReglaNegocioError
from app.extensions import db
from app.models import (
    TIPOS_DOCUMENTO,
    TIPOS_VEHICULO,
    Cliente,
    Mensualidad,
    Movimiento,
    Vehiculo,
    ahora,
)
from app.services import PATRON_PLACA, normalizar_placa
from app.services.validaciones import (
    email_opcional,
    telefono_opcional,
    texto_opcional,
    texto_requerido,
)

DURACION_MENSUALIDAD_DIAS = 30  # incluye el día de inicio: fin = inicio + 29
PATRON_DOCUMENTO = re.compile(r"^[A-Za-z0-9]{5,20}$")


class ClienteService:
    # ------------------------------------------------------------ clientes
    @staticmethod
    def obtener(id_cliente) -> Cliente:
        cliente = db.session.get(Cliente, id_cliente)
        if cliente is None:
            raise NoEncontradoError("El cliente no existe.")
        return cliente

    @staticmethod
    def listar(q=None, pagina=1, por_pagina=15):
        consulta = Cliente.query
        q = (q or "").strip()
        if q:
            patron = f"%{q}%"
            condiciones = [
                Cliente.numero_documento.like(patron),
                Cliente.nombres.ilike(patron),
                Cliente.apellidos.ilike(patron),
            ]
            placa = normalizar_placa(q)
            if placa:
                condiciones.append(
                    Cliente.id_cliente.in_(
                        db.session.query(Vehiculo.id_cliente).filter(Vehiculo.placa.like(f"%{placa}%"))
                    )
                )
            consulta = consulta.filter(or_(*condiciones))
        return consulta.order_by(Cliente.apellidos, Cliente.nombres).paginate(
            page=pagina, per_page=por_pagina, error_out=False
        )

    @classmethod
    def crear(cls, tipo_documento, numero_documento, nombres, apellidos, telefono=None, email=None) -> Cliente:
        if tipo_documento not in TIPOS_DOCUMENTO:
            raise ReglaNegocioError("Seleccione un tipo de documento válido.")
        numero = (numero_documento or "").strip().replace(".", "").replace(" ", "")
        if not PATRON_DOCUMENTO.match(numero):
            raise ReglaNegocioError("El número de documento debe tener entre 5 y 20 letras o números.")
        nombres = texto_requerido(nombres, "Los nombres", 2, 100)
        apellidos = texto_requerido(apellidos, "Los apellidos", 2, 100)
        telefono = telefono_opcional(telefono)
        email = email_opcional(email)
        if Cliente.query.filter_by(tipo_documento=tipo_documento, numero_documento=numero).first():
            raise ReglaNegocioError(f"Ya existe un cliente con el documento {tipo_documento} {numero}.")

        cliente = Cliente(
            tipo_documento=tipo_documento, numero_documento=numero, nombres=nombres,
            apellidos=apellidos, telefono=telefono, email=email,
        )
        db.session.add(cliente)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ReglaNegocioError(f"Ya existe un cliente con el documento {tipo_documento} {numero}.")
        return cliente

    @classmethod
    def editar(cls, id_cliente, nombres, apellidos, telefono=None, email=None) -> Cliente:
        cliente = cls.obtener(id_cliente)
        cliente.nombres = texto_requerido(nombres, "Los nombres", 2, 100)
        cliente.apellidos = texto_requerido(apellidos, "Los apellidos", 2, 100)
        cliente.telefono = telefono_opcional(telefono)
        cliente.email = email_opcional(email)
        db.session.commit()
        return cliente

    # ------------------------------------------------------------ vehículos
    @staticmethod
    def obtener_vehiculo(id_vehiculo) -> Vehiculo:
        vehiculo = db.session.get(Vehiculo, id_vehiculo)
        if vehiculo is None:
            raise NoEncontradoError("El vehículo no existe.")
        return vehiculo

    @classmethod
    def registrar_vehiculo(cls, id_cliente, placa, tipo, marca=None, color=None) -> Vehiculo:
        cliente = cls.obtener(id_cliente)
        placa = normalizar_placa(placa)
        if not PATRON_PLACA.match(placa):
            raise ReglaNegocioError(
                "La placa debe tener entre 5 y 7 caracteres alfanuméricos (ej. ABC123 o ABC12D)."
            )
        if tipo not in TIPOS_VEHICULO:
            raise ReglaNegocioError("Seleccione el tipo de vehículo (carro o moto).")
        marca = texto_opcional(marca, "La marca", 50)
        color = texto_opcional(color, "El color", 30)
        if Vehiculo.query.filter_by(placa=placa).first():
            raise ReglaNegocioError(f"La placa {placa} ya está registrada.")

        vehiculo = Vehiculo(placa=placa, tipo=tipo, marca=marca, color=color, cliente=cliente)
        db.session.add(vehiculo)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ReglaNegocioError(f"La placa {placa} ya está registrada.")
        return vehiculo

    @classmethod
    def editar_vehiculo(cls, id_vehiculo, tipo, marca=None, color=None) -> Vehiculo:
        vehiculo = cls.obtener_vehiculo(id_vehiculo)
        if tipo not in TIPOS_VEHICULO:
            raise ReglaNegocioError("Seleccione el tipo de vehículo (carro o moto).")
        if tipo != vehiculo.tipo and Movimiento.query.filter_by(
            id_vehiculo=vehiculo.id_vehiculo, fecha_hora_salida=None
        ).first():
            raise ReglaNegocioError(
                "No se puede cambiar el tipo de un vehículo que está dentro del parqueadero."
            )
        vehiculo.tipo = tipo
        vehiculo.marca = texto_opcional(marca, "La marca", 50)
        vehiculo.color = texto_opcional(color, "El color", 30)
        db.session.commit()
        return vehiculo

    # ------------------------------------------------------------ mensualidad
    @classmethod
    def preparar_mensualidad(cls, vehiculo: Vehiculo, hoy: date = None) -> Mensualidad:
        """Crea (sin confirmar) la mensualidad de 30 días desde hoy. Solo puede haber una vigente.

        La confirma quien la llama: el pago la guarda junto con su registro de pago.
        """
        hoy = hoy or ahora().date()

        # Las ACTIVAS ya caducadas pasan a VENCIDA para liberar el cupo de «una sola activa».
        for m in vehiculo.mensualidades:
            if m.estado == "ACTIVA" and m.fecha_fin < hoy:
                m.estado = "VENCIDA"
        db.session.flush()

        vigente = vehiculo.mensualidad_vigente(hoy)
        if vigente is not None:
            db.session.rollback()
            raise ReglaNegocioError(
                f"El vehículo {vehiculo.placa} ya tiene una mensualidad vigente hasta el "
                f"{vigente.fecha_fin:%d/%m/%Y}."
            )

        nueva = Mensualidad(
            fecha_inicio=hoy,
            fecha_fin=hoy + timedelta(days=DURACION_MENSUALIDAD_DIAS - 1),
            estado="ACTIVA",
            vehiculo=vehiculo,
        )
        db.session.add(nueva)
        return nueva

    @classmethod
    def activar_mensualidad(cls, id_vehiculo, hoy: date = None) -> Mensualidad:
        """Activa la mensualidad sin cobro. Uso interno y de pruebas: en la aplicación, la
        mensualidad solo se activa registrando su pago (PagoService.registrar)."""
        vehiculo = cls.obtener_vehiculo(id_vehiculo)
        nueva = cls.preparar_mensualidad(vehiculo, hoy)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ReglaNegocioError(
                f"El vehículo {vehiculo.placa} ya tiene una mensualidad activa."
            )
        return nueva
