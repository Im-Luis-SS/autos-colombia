"""Gestión de celdas del parqueadero."""
import re

from sqlalchemy.exc import IntegrityError

from app.errors import NoEncontradoError, ReglaNegocioError
from app.extensions import db
from app.models import ESTADOS_CELDA, TIPOS_VEHICULO, Celda, Movimiento

PATRON_CODIGO = re.compile(r"^[A-Z0-9]+(-[A-Z0-9]+)*$")
ESTADOS_ASIGNABLES = ("LIBRE", "MANTENIMIENTO")  # OCUPADA solo la maneja el sistema


def _validar_codigo(codigo) -> str:
    codigo = (codigo or "").strip().upper()
    if not codigo or len(codigo) > 10 or not PATRON_CODIGO.match(codigo):
        raise ReglaNegocioError(
            "El código debe tener máximo 10 caracteres: letras, números y guiones (ej. C-71)."
        )
    return codigo


def _tiene_historial(celda: Celda) -> bool:
    return Movimiento.query.filter_by(id_celda=celda.id_celda).first() is not None


class CeldaService:
    @staticmethod
    def obtener(id_celda) -> Celda:
        celda = db.session.get(Celda, id_celda)
        if celda is None:
            raise NoEncontradoError("La celda no existe.")
        return celda

    @staticmethod
    def listar(q=None, tipo=None, estado=None):
        consulta = Celda.query
        q = (q or "").strip().upper()
        if q:
            consulta = consulta.filter(Celda.codigo.like(f"%{q}%"))
        if tipo in TIPOS_VEHICULO:
            consulta = consulta.filter(Celda.tipo == tipo)
        if estado in ESTADOS_CELDA:
            consulta = consulta.filter(Celda.estado == estado)
        return consulta.order_by(Celda.tipo, Celda.codigo).all()

    @classmethod
    def crear(cls, codigo, tipo) -> Celda:
        codigo = _validar_codigo(codigo)
        if tipo not in TIPOS_VEHICULO:
            raise ReglaNegocioError("Seleccione el tipo de celda (carro o moto).")
        if Celda.query.filter_by(codigo=codigo).first():
            raise ReglaNegocioError(f"Ya existe una celda con el código {codigo}.")
        celda = Celda(codigo=codigo, tipo=tipo, estado="LIBRE")
        db.session.add(celda)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ReglaNegocioError(f"Ya existe una celda con el código {codigo}.")
        return celda

    @classmethod
    def editar(cls, id_celda, codigo, tipo) -> Celda:
        celda = cls.obtener(id_celda)
        if celda.estado == "OCUPADA":
            raise ReglaNegocioError(
                f"La celda {celda.codigo} está ocupada: no se puede modificar hasta que el vehículo salga."
            )
        codigo = _validar_codigo(codigo)
        if tipo not in TIPOS_VEHICULO:
            raise ReglaNegocioError("Seleccione el tipo de celda (carro o moto).")
        repetida = Celda.query.filter(Celda.codigo == codigo, Celda.id_celda != celda.id_celda).first()
        if repetida:
            raise ReglaNegocioError(f"Ya existe una celda con el código {codigo}.")
        if tipo != celda.tipo and _tiene_historial(celda):
            raise ReglaNegocioError(
                "No se puede cambiar el tipo de una celda que ya tiene historial de movimientos."
            )
        celda.codigo = codigo
        celda.tipo = tipo
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ReglaNegocioError(f"Ya existe una celda con el código {codigo}.")
        return celda

    @classmethod
    def cambiar_estado(cls, id_celda, nuevo_estado) -> Celda:
        celda = cls.obtener(id_celda)
        if nuevo_estado not in ESTADOS_ASIGNABLES:
            raise ReglaNegocioError("Solo se puede dejar una celda libre o en mantenimiento.")
        if celda.estado == "OCUPADA":
            raise ReglaNegocioError(
                f"La celda {celda.codigo} tiene un vehículo dentro: no se puede cambiar su estado."
            )
        if celda.estado == nuevo_estado:
            raise ReglaNegocioError(f"La celda {celda.codigo} ya está en estado {nuevo_estado.lower()}.")
        celda.estado = nuevo_estado
        db.session.commit()
        return celda

    @classmethod
    def eliminar(cls, id_celda) -> str:
        celda = cls.obtener(id_celda)
        if celda.estado == "OCUPADA":
            raise ReglaNegocioError(f"La celda {celda.codigo} está ocupada: no se puede eliminar.")
        if _tiene_historial(celda):
            raise ReglaNegocioError(
                f"La celda {celda.codigo} tiene historial de movimientos y no se puede eliminar. "
                "Póngala en mantenimiento para dejar de usarla."
            )
        codigo = celda.codigo
        db.session.delete(celda)
        db.session.commit()
        return codigo
