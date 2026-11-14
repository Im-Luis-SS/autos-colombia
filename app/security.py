"""Control de acceso basado en sesión y protección CSRF."""
import secrets
from functools import wraps

from flask import abort, current_app, flash, g, redirect, request, session, url_for

from app.extensions import db
from app.models import UsuarioSistema


def cargar_usuario_actual():
    id_usuario = session.get("id_usuario")
    g.usuario = db.session.get(UsuarioSistema, id_usuario) if id_usuario else None
    if g.usuario is not None and not g.usuario.activo:
        session.clear()
        g.usuario = None


def csrf_token() -> str:
    """Token por sesión; se incluye como campo oculto en cada formulario."""
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


def proteger_csrf():
    """Rechaza todo POST cuyo formulario no traiga el token de la sesión actual.

    Evita que otra página web haga actuar al usuario (por ejemplo, desactivar un usuario
    o borrar una celda) sin que se dé cuenta.
    """
    if not current_app.config.get("CSRF_ENABLED", True):
        return
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        esperado = session.get("csrf", "")
        enviado = request.form.get("csrf_token", "")
        if not esperado or not secrets.compare_digest(esperado.encode(), enviado.encode()):
            abort(400)


def login_requerido(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if g.get("usuario") is None:
            flash("Inicie sesión para continuar.", "warning")
            return redirect(url_for("auth.login"))
        return vista(*args, **kwargs)

    return envoltura


def admin_requerido(vista):
    @wraps(vista)
    @login_requerido
    def envoltura(*args, **kwargs):
        if not g.usuario.es_administrador():
            flash("Esta sección es solo para administradores.", "danger")
            return redirect(url_for("consultas.panel"))
        return vista(*args, **kwargs)

    return envoltura
