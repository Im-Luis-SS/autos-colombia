"""Gestión de pagos de mensualidades y de tarifas (solo administradores)."""
from datetime import date, timedelta

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.errors import NoEncontradoError, ReglaNegocioError
from app.models import ESTADOS_PAGO, MEDIOS_PAGO, ahora
from app.security import admin_requerido
from app.services.clientes import DURACION_MENSUALIDAD_DIAS, ClienteService
from app.services.pagos import MEDIOS_CON_REFERENCIA, PagoService, TarifaService

pagos_bp = Blueprint("pagos", __name__, url_prefix="/pagos")
tarifas_bp = Blueprint("tarifas", __name__, url_prefix="/tarifas")


def _fecha(valor):
    try:
        return date.fromisoformat(valor) if valor else None
    except ValueError:
        return None


def _pago(id_pago):
    try:
        return PagoService.obtener(id_pago)
    except NoEncontradoError:
        abort(404)


def _tarifa(tipo):
    try:
        return TarifaService.obtener(tipo)
    except NoEncontradoError:
        abort(404)


def _contexto_cobro(vehiculo):
    """Datos que muestra el formulario de pago: tarifa y periodo que se activará."""
    hoy = ahora().date()
    return {
        "vehiculo": vehiculo,
        "cliente": vehiculo.cliente,
        "tarifa": TarifaService.obtener(vehiculo.tipo),
        "medios": MEDIOS_PAGO,
        "con_referencia": MEDIOS_CON_REFERENCIA,
        "inicio": hoy,
        "fin": hoy + timedelta(days=DURACION_MENSUALIDAD_DIAS - 1),
    }


# ------------------------------------------------------------------ Pagos
@pagos_bp.route("")
@admin_requerido
def lista():
    q = request.args.get("q", "")
    medio = request.args.get("medio", "")
    estado = request.args.get("estado", "")
    desde = _fecha(request.args.get("desde"))
    hasta = _fecha(request.args.get("hasta"))
    pagina = request.args.get("pagina", 1, type=int)
    try:
        resultado = PagoService.listar(q, medio, estado, desde, hasta, pagina)
    except ReglaNegocioError as error:
        flash(str(error), "warning")
        desde = hasta = None
        resultado = PagoService.listar(q, medio, estado, None, None, pagina)
    total = PagoService.total_recaudado(q, medio, estado, desde, hasta)
    return render_template(
        "pagos.html",
        pagina=resultado,
        total=total,
        q=q,
        medio=medio,
        estado=estado,
        desde=desde.isoformat() if desde else "",
        hasta=hasta.isoformat() if hasta else "",
        medios=MEDIOS_PAGO,
        estados=ESTADOS_PAGO,
    )


@pagos_bp.route("/nuevo", methods=["GET", "POST"])
@admin_requerido
def nuevo():
    if request.method == "POST":
        id_vehiculo = request.form.get("id_vehiculo", type=int)
    else:
        id_vehiculo = request.args.get("vehiculo", type=int)
    if not id_vehiculo:
        flash("Elija el vehículo desde el detalle del cliente.", "warning")
        return redirect(url_for("clientes.lista"))
    try:
        vehiculo = ClienteService.obtener_vehiculo(id_vehiculo)
    except NoEncontradoError:
        abort(404)
    if request.method == "POST":
        f = request.form
        try:
            pago = PagoService.registrar(id_vehiculo, f.get("medio"), f.get("referencia"), g.usuario)
        except ReglaNegocioError as error:
            flash(str(error), "danger")
            return render_template("pago_form.html", form=f, **_contexto_cobro(vehiculo)), 400
        flash(
            f"Pago {pago.numero} registrado. Mensualidad de {vehiculo.placa} activa del "
            f"{pago.mensualidad.fecha_inicio:%d/%m/%Y} al {pago.mensualidad.fecha_fin:%d/%m/%Y}.",
            "success",
        )
        return redirect(url_for("pagos.detalle", id_pago=pago.id_pago))
    return render_template("pago_form.html", form={}, **_contexto_cobro(vehiculo))


@pagos_bp.route("/<int:id_pago>")
@admin_requerido
def detalle(id_pago):
    return render_template("pago_detalle.html", pago=_pago(id_pago))


@pagos_bp.route("/<int:id_pago>/anular", methods=["POST"])
@admin_requerido
def anular(id_pago):
    pago = _pago(id_pago)
    try:
        PagoService.anular(id_pago, request.form.get("motivo"), g.usuario)
    except ReglaNegocioError as error:
        flash(str(error), "danger")
        return render_template("pago_detalle.html", pago=pago, motivo=request.form.get("motivo", "")), 400
    flash(f"Pago {pago.numero} anulado. La mensualidad quedó cancelada.", "success")
    return redirect(url_for("pagos.detalle", id_pago=id_pago))


# ------------------------------------------------------------------ Tarifas
@tarifas_bp.route("")
@admin_requerido
def lista():
    return render_template("tarifas.html", tarifas=TarifaService.listar(), dias=DURACION_MENSUALIDAD_DIAS)


@tarifas_bp.route("/<tipo>/editar", methods=["GET", "POST"])
@admin_requerido
def editar(tipo):
    tarifa = _tarifa(tipo)
    if request.method == "POST":
        valor = request.form.get("valor", "")
        try:
            TarifaService.actualizar(tipo, valor)
        except ReglaNegocioError as error:
            flash(str(error), "danger")
            return render_template("tarifa_form.html", tarifa=tarifa, valor=valor), 400
        flash(f"Tarifa de {tarifa.tipo_vehiculo.lower()}s actualizada.", "success")
        return redirect(url_for("tarifas.lista"))
    return render_template("tarifa_form.html", tarifa=tarifa, valor=str(tarifa.valor))
