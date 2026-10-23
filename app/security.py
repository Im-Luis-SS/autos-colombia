"""Control de acceso basado en sesión."""
from functools import wraps

from flask import flash, g, redirect, session, url_for

from app.extensions import db
from app.models import UsuarioSistema


def cargar_usuario_actual():
    id_usuario = session.get("id_usuario")
    g.usuario = db.session.get(UsuarioSistema, id_usuario) if id_usuario else None
    if g.usuario is not None and not g.usuario.activo:
        session.clear()
        g.usuario = None


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
