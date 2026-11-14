"""Gestión de usuarios del sistema (operarios y administradores)."""
import re

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from app.errors import NoEncontradoError, ReglaNegocioError
from app.extensions import db
from app.models import ROLES, UsuarioSistema
from app.services.validaciones import texto_requerido

PATRON_USERNAME = re.compile(r"^[a-z0-9_.]{3,30}$")
MIN_CLAVE = 8
MAX_CLAVE = 72


def validar_clave(clave, confirmacion=None) -> str:
    clave = clave or ""
    if confirmacion is not None and clave != confirmacion:
        raise ReglaNegocioError("Las contraseñas no coinciden.")
    if len(clave) < MIN_CLAVE:
        raise ReglaNegocioError(f"La contraseña debe tener al menos {MIN_CLAVE} caracteres.")
    if len(clave) > MAX_CLAVE:
        raise ReglaNegocioError(f"La contraseña no puede superar {MAX_CLAVE} caracteres.")
    if not (re.search(r"[A-Za-z]", clave) and re.search(r"\d", clave)):
        raise ReglaNegocioError("La contraseña debe incluir letras y números.")
    return clave


class UsuarioService:
    @staticmethod
    def obtener(id_usuario) -> UsuarioSistema:
        usuario = db.session.get(UsuarioSistema, id_usuario)
        if usuario is None:
            raise NoEncontradoError("El usuario no existe.")
        return usuario

    @staticmethod
    def listar(q=None, rol=None, estado=None):
        consulta = UsuarioSistema.query
        q = (q or "").strip()
        if q:
            patron = f"%{q}%"
            consulta = consulta.filter(
                or_(UsuarioSistema.nombre.ilike(patron), UsuarioSistema.username.ilike(patron))
            )
        if rol in ROLES:
            consulta = consulta.filter(UsuarioSistema.rol == rol)
        if estado == "activo":
            consulta = consulta.filter(UsuarioSistema.activo.is_(True))
        elif estado == "inactivo":
            consulta = consulta.filter(UsuarioSistema.activo.is_(False))
        return consulta.order_by(UsuarioSistema.nombre).all()

    @staticmethod
    def _administradores_activos() -> int:
        return UsuarioSistema.query.filter_by(rol="ADMINISTRADOR", activo=True).count()

    @classmethod
    def crear(cls, nombre, username, clave, confirmacion, rol) -> UsuarioSistema:
        nombre = texto_requerido(nombre, "El nombre", 3, 100)
        username = (username or "").strip().lower()
        if not PATRON_USERNAME.match(username):
            raise ReglaNegocioError(
                "El usuario debe tener entre 3 y 30 caracteres: letras sin tilde, números, punto o guion bajo."
            )
        if rol not in ROLES:
            raise ReglaNegocioError("Seleccione un rol válido.")
        validar_clave(clave, confirmacion)
        if UsuarioSistema.query.filter(func.lower(UsuarioSistema.username) == username).first():
            raise ReglaNegocioError(f"Ya existe un usuario con el nombre de usuario «{username}».")

        usuario = UsuarioSistema(nombre=nombre, username=username, rol=rol, activo=True)
        usuario.set_clave(clave)
        db.session.add(usuario)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ReglaNegocioError(f"Ya existe un usuario con el nombre de usuario «{username}».")
        return usuario

    @classmethod
    def editar(cls, id_usuario, nombre, rol) -> UsuarioSistema:
        usuario = cls.obtener(id_usuario)
        nombre = texto_requerido(nombre, "El nombre", 3, 100)
        if rol not in ROLES:
            raise ReglaNegocioError("Seleccione un rol válido.")
        if (
            usuario.rol == "ADMINISTRADOR"
            and rol != "ADMINISTRADOR"
            and usuario.activo
            and cls._administradores_activos() <= 1
        ):
            raise ReglaNegocioError(
                "No se puede quitar el rol de administrador al último administrador activo."
            )
        usuario.nombre = nombre
        usuario.rol = rol
        db.session.commit()
        return usuario

    @classmethod
    def cambiar_estado(cls, id_usuario, activo: bool, actor) -> UsuarioSistema:
        usuario = cls.obtener(id_usuario)
        if not activo:
            if actor is not None and usuario.id_usuario == actor.id_usuario:
                raise ReglaNegocioError("No puede desactivar su propio usuario.")
            if (
                usuario.rol == "ADMINISTRADOR"
                and usuario.activo
                and cls._administradores_activos() <= 1
            ):
                raise ReglaNegocioError("No se puede desactivar al último administrador activo.")
        usuario.activo = activo
        db.session.commit()
        return usuario

    @classmethod
    def restablecer_clave(cls, id_usuario, clave, confirmacion) -> UsuarioSistema:
        usuario = cls.obtener(id_usuario)
        validar_clave(clave, confirmacion)
        usuario.set_clave(clave)
        db.session.commit()
        return usuario
