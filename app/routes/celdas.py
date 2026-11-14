"""Gestión de celdas (solo administradores)."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.errors import NoEncontradoError, ReglaNegocioError
from app.models import ESTADOS_CELDA, TIPOS_VEHICULO
from app.security import admin_requerido
from app.services.celdas import CeldaService

celdas_bp = Blueprint("celdas", __name__, url_prefix="/celdas")


def _obtener(id_celda):
    try:
        return CeldaService.obtener(id_celda)
    except NoEncontradoError:
        abort(404)


@celdas_bp.route("")
@admin_requerido
def lista():
    q, tipo, estado = request.args.get("q", ""), request.args.get("tipo", ""), request.args.get("estado", "")
    return render_template(
        "celdas.html", celdas=CeldaService.listar(q, tipo, estado), q=q, tipo=tipo, estado=estado,
        tipos=TIPOS_VEHICULO, estados=ESTADOS_CELDA,
    )


@celdas_bp.route("/nueva", methods=["GET", "POST"])
@admin_requerido
def nueva():
    if request.method == "POST":
        try:
            c = CeldaService.crear(request.form.get("codigo"), request.form.get("tipo"))
        except ReglaNegocioError as error:
            flash(str(error), "danger")
            return render_template("celda_form.html", form=request.form, celda=None, tipos=TIPOS_VEHICULO), 400
        flash(f"Celda {c.codigo} creada.", "success")
        return redirect(url_for("celdas.lista"))
    return render_template("celda_form.html", form={}, celda=None, tipos=TIPOS_VEHICULO)


@celdas_bp.route("/<int:id_celda>/editar", methods=["GET", "POST"])
@admin_requerido
def editar(id_celda):
    celda = _obtener(id_celda)
    if request.method == "POST":
        try:
            CeldaService.editar(id_celda, request.form.get("codigo"), request.form.get("tipo"))
        except ReglaNegocioError as error:
            flash(str(error), "danger")
            return render_template("celda_form.html", form=request.form, celda=celda, tipos=TIPOS_VEHICULO), 400
        flash("Celda actualizada.", "success")
        return redirect(url_for("celdas.lista"))
    return render_template(
        "celda_form.html", form={"codigo": celda.codigo, "tipo": celda.tipo}, celda=celda, tipos=TIPOS_VEHICULO
    )


@celdas_bp.route("/<int:id_celda>/estado", methods=["POST"])
@admin_requerido
def estado(id_celda):
    _obtener(id_celda)
    nuevo = request.form.get("estado", "")
    try:
        c = CeldaService.cambiar_estado(id_celda, nuevo)
    except ReglaNegocioError as error:
        flash(str(error), "danger")
    else:
        flash(f"Celda {c.codigo} ahora está {c.estado.lower()}.", "success")
    return redirect(url_for("celdas.lista"))


@celdas_bp.route("/<int:id_celda>/eliminar", methods=["POST"])
@admin_requerido
def eliminar(id_celda):
    _obtener(id_celda)
    try:
        codigo = CeldaService.eliminar(id_celda)
    except ReglaNegocioError as error:
        flash(str(error), "danger")
    else:
        flash(f"Celda {codigo} eliminada.", "success")
    return redirect(url_for("celdas.lista"))
