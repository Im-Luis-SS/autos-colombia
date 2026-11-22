"""Gestión de clientes, vehículos y mensualidades (solo administradores)."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.errors import NoEncontradoError, ReglaNegocioError
from app.models import TIPOS_DOCUMENTO, TIPOS_VEHICULO, ahora
from app.security import admin_requerido
from app.services.clientes import DURACION_MENSUALIDAD_DIAS, ClienteService

clientes_bp = Blueprint("clientes", __name__)


def _cliente(id_cliente):
    try:
        return ClienteService.obtener(id_cliente)
    except NoEncontradoError:
        abort(404)


def _vehiculo(id_vehiculo):
    try:
        return ClienteService.obtener_vehiculo(id_vehiculo)
    except NoEncontradoError:
        abort(404)


@clientes_bp.route("/clientes")
@admin_requerido
def lista():
    q = request.args.get("q", "")
    pagina = request.args.get("pagina", 1, type=int)
    return render_template("clientes.html", pagina=ClienteService.listar(q, pagina), q=q)


@clientes_bp.route("/clientes/nuevo", methods=["GET", "POST"])
@admin_requerido
def nuevo():
    if request.method == "POST":
        f = request.form
        try:
            c = ClienteService.crear(
                f.get("tipo_documento"), f.get("numero_documento"), f.get("nombres"),
                f.get("apellidos"), f.get("telefono"), f.get("email"),
            )
        except ReglaNegocioError as error:
            flash(str(error), "danger")
            return render_template("cliente_form.html", form=f, cliente=None, tipos_doc=TIPOS_DOCUMENTO), 400
        flash(f"Cliente {c.nombre_completo} registrado. Ahora puede agregarle un vehículo.", "success")
        return redirect(url_for("clientes.detalle", id_cliente=c.id_cliente))
    return render_template("cliente_form.html", form={}, cliente=None, tipos_doc=TIPOS_DOCUMENTO)


@clientes_bp.route("/clientes/<int:id_cliente>")
@admin_requerido
def detalle(id_cliente):
    cliente = _cliente(id_cliente)
    return render_template(
        "cliente_detalle.html", cliente=cliente, hoy=ahora().date(), dias=DURACION_MENSUALIDAD_DIAS
    )


@clientes_bp.route("/clientes/<int:id_cliente>/editar", methods=["GET", "POST"])
@admin_requerido
def editar(id_cliente):
    cliente = _cliente(id_cliente)
    if request.method == "POST":
        f = request.form
        try:
            ClienteService.editar(id_cliente, f.get("nombres"), f.get("apellidos"), f.get("telefono"), f.get("email"))
        except ReglaNegocioError as error:
            flash(str(error), "danger")
            return render_template("cliente_form.html", form=f, cliente=cliente, tipos_doc=TIPOS_DOCUMENTO), 400
        flash("Cliente actualizado.", "success")
        return redirect(url_for("clientes.detalle", id_cliente=id_cliente))
    form = {"nombres": cliente.nombres, "apellidos": cliente.apellidos,
            "telefono": cliente.telefono or "", "email": cliente.email or ""}
    return render_template("cliente_form.html", form=form, cliente=cliente, tipos_doc=TIPOS_DOCUMENTO)


@clientes_bp.route("/clientes/<int:id_cliente>/vehiculos/nuevo", methods=["GET", "POST"])
@admin_requerido
def vehiculo_nuevo(id_cliente):
    cliente = _cliente(id_cliente)
    if request.method == "POST":
        f = request.form
        try:
            v = ClienteService.registrar_vehiculo(id_cliente, f.get("placa"), f.get("tipo"), f.get("marca"), f.get("color"))
        except ReglaNegocioError as error:
            flash(str(error), "danger")
            return render_template("vehiculo_form.html", form=f, cliente=cliente, vehiculo=None, tipos=TIPOS_VEHICULO), 400
        flash(f"Vehículo {v.placa} registrado.", "success")
        return redirect(url_for("clientes.detalle", id_cliente=id_cliente))
    return render_template("vehiculo_form.html", form={}, cliente=cliente, vehiculo=None, tipos=TIPOS_VEHICULO)


@clientes_bp.route("/vehiculos/<int:id_vehiculo>/editar", methods=["GET", "POST"])
@admin_requerido
def vehiculo_editar(id_vehiculo):
    vehiculo = _vehiculo(id_vehiculo)
    cliente = vehiculo.cliente
    if request.method == "POST":
        f = request.form
        try:
            ClienteService.editar_vehiculo(id_vehiculo, f.get("tipo"), f.get("marca"), f.get("color"))
        except ReglaNegocioError as error:
            flash(str(error), "danger")
            return render_template("vehiculo_form.html", form=f, cliente=cliente, vehiculo=vehiculo, tipos=TIPOS_VEHICULO), 400
        flash("Vehículo actualizado.", "success")
        return redirect(url_for("clientes.detalle", id_cliente=cliente.id_cliente))
    form = {"placa": vehiculo.placa, "tipo": vehiculo.tipo, "marca": vehiculo.marca or "", "color": vehiculo.color or ""}
    return render_template("vehiculo_form.html", form=form, cliente=cliente, vehiculo=vehiculo, tipos=TIPOS_VEHICULO)
