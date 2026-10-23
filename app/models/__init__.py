"""Modelos de dominio (capa de acceso a datos)."""
from datetime import date, datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


def ahora() -> datetime:
    """Fecha y hora actual (función aparte para poder simularla en pruebas)."""
    return datetime.now().replace(microsecond=0)


# Valores permitidos (se guardan como ENUM en MySQL).
ROLES = ("OPERARIO", "ADMINISTRADOR")
TIPOS_VEHICULO = ("CARRO", "MOTO")
ESTADOS_CELDA = ("LIBRE", "OCUPADA", "MANTENIMIENTO")
ESTADOS_MENSUALIDAD = ("ACTIVA", "VENCIDA", "CANCELADA")
TIPOS_DOCUMENTO = ("CC", "CE", "NIT", "PAS")


class UsuarioSistema(db.Model):
    __tablename__ = "usuario_sistema"

    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.Enum(*ROLES, name="rol"), nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)

    def set_clave(self, clave: str) -> None:
        self.password_hash = generate_password_hash(clave)

    def verificar_clave(self, clave: str) -> bool:
        return check_password_hash(self.password_hash, clave)

    def es_administrador(self) -> bool:
        return self.rol == "ADMINISTRADOR"


class Cliente(db.Model):
    __tablename__ = "cliente"
    __table_args__ = (
        db.UniqueConstraint("tipo_documento", "numero_documento", name="uq_cliente_documento"),
    )

    id_cliente = db.Column(db.Integer, primary_key=True)
    tipo_documento = db.Column(db.Enum(*TIPOS_DOCUMENTO, name="tipo_documento"), nullable=False)
    numero_documento = db.Column(db.String(20), nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(120))

    vehiculos = db.relationship("Vehiculo", back_populates="cliente")

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}"


class Vehiculo(db.Model):
    __tablename__ = "vehiculo"

    id_vehiculo = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(10), nullable=False, unique=True)
    tipo = db.Column(db.Enum(*TIPOS_VEHICULO, name="tipo_vehiculo"), nullable=False)
    marca = db.Column(db.String(50))
    color = db.Column(db.String(30))
    id_cliente = db.Column(db.Integer, db.ForeignKey("cliente.id_cliente"), nullable=False)

    cliente = db.relationship("Cliente", back_populates="vehiculos")
    mensualidades = db.relationship("Mensualidad", back_populates="vehiculo")
    movimientos = db.relationship("Movimiento", back_populates="vehiculo")


class Mensualidad(db.Model):
    __tablename__ = "mensualidad"

    id_mensualidad = db.Column(db.Integer, primary_key=True)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    estado = db.Column(db.Enum(*ESTADOS_MENSUALIDAD, name="estado_mensualidad"), nullable=False)
    id_vehiculo = db.Column(db.Integer, db.ForeignKey("vehiculo.id_vehiculo"), nullable=False)

    vehiculo = db.relationship("Vehiculo", back_populates="mensualidades")

    def esta_vigente(self, fecha: date) -> bool:
        return self.estado == "ACTIVA" and self.fecha_inicio <= fecha <= self.fecha_fin


class Celda(db.Model):
    __tablename__ = "celda"

    id_celda = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), nullable=False, unique=True)
    tipo = db.Column(db.Enum(*TIPOS_VEHICULO, name="tipo_celda"), nullable=False)
    estado = db.Column(db.Enum(*ESTADOS_CELDA, name="estado_celda"), nullable=False, default="LIBRE")

    movimientos = db.relationship("Movimiento", back_populates="celda")

    def ocupar(self) -> None:
        self.estado = "OCUPADA"

    def liberar(self) -> None:
        self.estado = "LIBRE"


class Movimiento(db.Model):
    """Una visita del vehículo: entrada y (cuando ocurre) salida."""

    __tablename__ = "movimiento"

    id_movimiento = db.Column(db.Integer, primary_key=True)
    fecha_hora_entrada = db.Column(db.DateTime, nullable=False)
    fecha_hora_salida = db.Column(db.DateTime)
    observaciones = db.Column(db.String(255))
    id_vehiculo = db.Column(db.Integer, db.ForeignKey("vehiculo.id_vehiculo"), nullable=False)
    id_celda = db.Column(db.Integer, db.ForeignKey("celda.id_celda"), nullable=False)
    id_usuario_entrada = db.Column(
        db.Integer, db.ForeignKey("usuario_sistema.id_usuario"), nullable=False
    )
    id_usuario_salida = db.Column(db.Integer, db.ForeignKey("usuario_sistema.id_usuario"))

    # Columnas generadas: valen NULL cuando el movimiento ya se cerró.
    # Con un índice UNIQUE garantizan, desde la BD, que un vehículo o una celda
    # no tengan dos movimientos abiertos a la vez.
    vehiculo_abierto = db.Column(
        db.Integer,
        db.Computed("CASE WHEN fecha_hora_salida IS NULL THEN id_vehiculo END"),
    )
    celda_abierta = db.Column(
        db.Integer,
        db.Computed("CASE WHEN fecha_hora_salida IS NULL THEN id_celda END"),
    )

    __table_args__ = (
        db.Index("uq_movimiento_vehiculo_abierto", "vehiculo_abierto", unique=True),
        db.Index("uq_movimiento_celda_abierta", "celda_abierta", unique=True),
        db.Index("ix_movimiento_entrada", "fecha_hora_entrada"),
    )

    vehiculo = db.relationship("Vehiculo", back_populates="movimientos")
    celda = db.relationship("Celda", back_populates="movimientos")
    usuario_entrada = db.relationship("UsuarioSistema", foreign_keys=[id_usuario_entrada])
    usuario_salida = db.relationship("UsuarioSistema", foreign_keys=[id_usuario_salida])

    def esta_abierto(self) -> bool:
        return self.fecha_hora_salida is None

    def registrar_salida(self, operario: UsuarioSistema, fecha_hora: datetime) -> None:
        self.fecha_hora_salida = fecha_hora
        self.usuario_salida = operario

    def duracion(self):
        fin = self.fecha_hora_salida or ahora()
        return fin - self.fecha_hora_entrada
