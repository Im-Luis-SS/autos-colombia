"""Capa de presentación: blueprints de Flask."""
from datetime import date

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from app.errors import ReglaNegocioError
from app.security import admin_requerido, login_requerido
from app.services import (
    AuthService,
    MovimientoService,
    OcupacionService,
    formatear_duracion,
)

auth_bp = Blueprint("auth", __name__)
movimientos_bp = Blueprint("movimientos", __name__)
consultas_bp = Blueprint("consultas", __name__)


# ------------------------------------------------------------------ Autenticación
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.get("usuario"):
        return redirect(url_for("consultas.panel"))
    if request.method == "POST":
        try:
            usuario = AuthService.autenticar(
                request.form.get("username"), request.form.get("password")
            )
        except ReglaNegocioError as error:
            flash(str(error), "danger")
        else:
            session.clear()
            session["id_usuario"] = usuario.id_usuario
            return redirect(url_for("consultas.panel"))
    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Sesión cerrada.", "success")
    return redirect(url_for("auth.login"))


# ------------------------------------------------------------------ Entrada / salida
@movimientos_bp.route("/entrada", methods=["GET", "POST"])
@login_requerido
def entrada():
    if request.method == "POST":
        placa = request.form.get("placa", "")
        try:
            mov = MovimientoService.registrar_entrada(
                placa,
                g.usuario,
                observaciones=request.form.get("observaciones"),
                celda_codigo=request.form.get("celda") or None,
            )
        except ReglaNegocioError as error:
            flash(str(error), "danger")
            return render_template("entrada.html", form=request.form), 400
        flash(
            f"Entrada registrada: {mov.vehiculo.placa} en la celda {mov.celda.codigo} "
            f"({mov.fecha_hora_entrada:%d/%m/%Y %H:%M}).",
            "success",
        )
        return redirect(url_for("movimientos.entrada"))
    return render_template("entrada.html", form={})


@movimientos_bp.route("/salida", methods=["GET", "POST"])
@login_requerido
def salida():
    if request.method == "POST":
        try:
            mov = MovimientoService.registrar_salida(
                request.form.get("placa", ""),
                g.usuario,
                observaciones=request.form.get("observaciones"),
            )
        except ReglaNegocioError as error:
            flash(str(error), "danger")
            return render_template("salida.html", form=request.form), 400
        flash(
            f"Salida registrada: {mov.vehiculo.placa} salió de la celda {mov.celda.codigo}. "
            f"Permanencia: {formatear_duracion(mov.duracion())}.",
            "success",
        )
        return redirect(url_for("movimientos.salida"))
    return render_template("salida.html", form={})


# ------------------------------------------------------------------ Consultas
@consultas_bp.route("/")
@login_requerido
def panel():
    return render_template(
        "panel.html",
        resumen=OcupacionService.resumen(),
        celdas=OcupacionService.celdas(),
    )


@consultas_bp.route("/dentro")
@login_requerido
def dentro():
    placa = request.args.get("placa", "")
    movimientos = MovimientoService.vehiculos_en_parqueadero(placa)
    return render_template("dentro.html", movimientos=movimientos, placa=placa)


def _fecha(valor):
    try:
        return date.fromisoformat(valor) if valor else None
    except ValueError:
        return None


@consultas_bp.route("/historial")
@admin_requerido
def historial():
    placa = request.args.get("placa", "")
    desde = _fecha(request.args.get("desde"))
    hasta = _fecha(request.args.get("hasta"))
    if desde and hasta and desde > hasta:
        flash("La fecha inicial no puede ser posterior a la final.", "warning")
        desde = hasta = None
    pagina = request.args.get("pagina", 1, type=int)
    resultado = MovimientoService.historial(placa, desde, hasta, pagina)
    return render_template(
        "historial.html",
        pagina=resultado,
        placa=placa,
        desde=desde.isoformat() if desde else "",
        hasta=hasta.isoformat() if hasta else "",
    )
