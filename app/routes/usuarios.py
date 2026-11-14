"""Gestión de usuarios del sistema (solo administradores)."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.errors import NoEncontradoError, ReglaNegocioError
from app.models import ROLES
from app.security import admin_requerido
from app.services.usuarios import UsuarioService

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


def _obtener(id_usuario):
    try:
        return UsuarioService.obtener(id_usuario)
    except NoEncontradoError:
        abort(404)


@usuarios_bp.route("")
@admin_requerido
def lista():
    q, rol, estado = request.args.get("q", ""), request.args.get("rol", ""), request.args.get("estado", "")
    return render_template(
        "usuarios.html", usuarios=UsuarioService.listar(q, rol, estado), q=q, rol=rol, estado=estado, roles=ROLES
    )


@usuarios_bp.route("/nuevo", methods=["GET", "POST"])
@admin_requerido
def nuevo():
    if request.method == "POST":
        f = request.form
        try:
            u = UsuarioService.crear(
                f.get("nombre"), f.get("username"), f.get("clave"), f.get("confirmacion"), f.get("rol")
            )
        except ReglaNegocioError as error:
            flash(str(error), "danger")
            return render_template("usuario_form.html", form=f, usuario=None, roles=ROLES), 400
        flash(f"Usuario «{u.username}» creado.", "success")
        return redirect(url_for("usuarios.lista"))
    return render_template("usuario_form.html", form={}, usuario=None, roles=ROLES)


@usuarios_bp.route("/<int:id_usuario>/editar", methods=["GET", "POST"])
@admin_requerido
def editar(id_usuario):
    usuario = _obtener(id_usuario)
    if request.method == "POST":
        f = request.form
        try:
            UsuarioService.editar(id_usuario, f.get("nombre"), f.get("rol"))
        except ReglaNegocioError as error:
            flash(str(error), "danger")
            return render_template("usuario_form.html", form=f, usuario=usuario, roles=ROLES), 400
        flash("Usuario actualizado.", "success")
        return redirect(url_for("usuarios.lista"))
    return render_template(
        "usuario_form.html", form={"nombre": usuario.nombre, "rol": usuario.rol}, usuario=usuario, roles=ROLES
    )


@usuarios_bp.route("/<int:id_usuario>/estado", methods=["POST"])
@admin_requerido
def estado(id_usuario):
    _obtener(id_usuario)
    activar = request.form.get("activo") == "1"
    try:
        u = UsuarioService.cambiar_estado(id_usuario, activar, g.usuario)
    except ReglaNegocioError as error:
        flash(str(error), "danger")
    else:
        flash(f"Usuario «{u.username}» {'activado' if activar else 'desactivado'}.", "success")
    return redirect(url_for("usuarios.lista"))


@usuarios_bp.route("/<int:id_usuario>/clave", methods=["GET", "POST"])
@admin_requerido
def clave(id_usuario):
    usuario = _obtener(id_usuario)
    if request.method == "POST":
        try:
            UsuarioService.restablecer_clave(id_usuario, request.form.get("clave"), request.form.get("confirmacion"))
        except ReglaNegocioError as error:
            flash(str(error), "danger")
            return render_template("usuario_clave.html", usuario=usuario), 400
        flash(f"Contraseña de «{usuario.username}» restablecida.", "success")
        return redirect(url_for("usuarios.lista"))
    return render_template("usuario_clave.html", usuario=usuario)
