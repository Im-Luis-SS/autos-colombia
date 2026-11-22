"""Pruebas de la iteración 3: tarifas, pagos de mensualidades, anulación y consulta.

Cada prueba lleva el ID del caso del plan de pruebas (CP-xx) en su docstring.
"""
from datetime import date, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.errors import NoEncontradoError, ReglaNegocioError
from app.extensions import db
from app.models import Cliente, Mensualidad, Pago, Tarifa, UsuarioSistema, Vehiculo
from app.services import MovimientoService
from app.services.clientes import ClienteService
from app.services.pagos import PagoService, TarifaService, formatear_pesos
from tests.conftest import iniciar_sesion


def admin():
    return UsuarioSistema.query.filter_by(username="admin").first()


def vehiculo_nuevo(placa="XYZ987", tipo="CARRO", documento="1055667788"):
    """Cliente y vehículo recién registrados, sin mensualidad."""
    cliente = ClienteService.crear("CC", documento, "Pedro", "Ruiz")
    return ClienteService.registrar_vehiculo(cliente.id_cliente, placa, tipo)


# ============================================================ TARIFAS
def test_cp34_consultar_tarifas(app, client):
    """CP-34 HU-21: la lista de tarifas muestra carro y moto con su valor en pesos."""
    tarifas = {t.tipo_vehiculo: t.valor for t in TarifaService.listar()}
    assert tarifas == {"CARRO": 150_000, "MOTO": 70_000}
    iniciar_sesion(client, "admin", "admin123")
    html = client.get("/tarifas").get_data(as_text=True)
    assert "$150.000" in html and "$70.000" in html


@pytest.mark.parametrize("texto,esperado", [("180000", 180_000), ("$ 180.000", 180_000), ("1,200,000", 1_200_000)])
def test_cp35_actualizar_tarifa(app, texto, esperado):
    """CP-35 HU-22: acepta el valor con puntos, comas o signo de pesos y lo guarda como número entero."""
    t = TarifaService.actualizar("carro", texto)
    assert t.valor == esperado == TarifaService.obtener("CARRO").valor


@pytest.mark.parametrize("texto", ["", "abc", "12.5x", "5000", "5.000.001", "-100", "0"])
def test_cp36_tarifa_invalida_se_rechaza(app, texto):
    """CP-36 HU-22: valores vacíos, no numéricos o fuera de rango se rechazan y la tarifa no cambia."""
    with pytest.raises(ReglaNegocioError, match="valor"):
        TarifaService.actualizar("CARRO", texto)
    assert TarifaService.obtener("CARRO").valor == 150_000


def test_cp37_tarifa_inexistente(app, client):
    """CP-37 HU-22: un tipo de vehículo que no existe da 'no encontrado' (404 en pantalla)."""
    with pytest.raises(NoEncontradoError):
        TarifaService.obtener("BUS")
    iniciar_sesion(client, "admin", "admin123")
    assert client.get("/tarifas/BUS/editar").status_code == 404


def test_cp38_cambiar_tarifa_no_altera_pagos_hechos(app):
    """CP-38 HU-22: un pago guarda el valor cobrado; cambiar la tarifa después no lo modifica."""
    v = vehiculo_nuevo()
    pago = PagoService.registrar(v.id_vehiculo, "EFECTIVO", None, admin())
    TarifaService.actualizar("CARRO", "200000")
    assert db.session.get(Pago, pago.id_pago).valor == 150_000
    v2 = vehiculo_nuevo("QWE123", "CARRO", "2000000001")
    assert PagoService.registrar(v2.id_vehiculo, "EFECTIVO", None, admin()).valor == 200_000


# ============================================================ REGISTRAR PAGO
def test_cp39_pago_en_efectivo_activa_mensualidad_30_dias(app):
    """CP-39 HU-23: el pago cobra la tarifa del carro y activa la mensualidad de 30 días desde hoy."""
    v = vehiculo_nuevo()
    hoy = date(2026, 11, 22)
    pago = PagoService.registrar(v.id_vehiculo, "efectivo", None, admin(), hoy=hoy)
    m = pago.mensualidad
    assert pago.valor == 150_000 and pago.estado == "REGISTRADO" and pago.medio == "EFECTIVO"
    assert pago.referencia is None and pago.numero.startswith("P-")
    assert (m.estado, m.fecha_inicio, m.fecha_fin) == ("ACTIVA", hoy, date(2026, 12, 21))
    assert (m.fecha_fin - m.fecha_inicio).days + 1 == 30 and m.vehiculo is v


def test_cp40_moto_paga_tarifa_de_moto(app):
    """CP-40 HU-23: una moto paga la tarifa de moto."""
    v = vehiculo_nuevo("ABC12D", "MOTO")
    assert PagoService.registrar(v.id_vehiculo, "EFECTIVO", None, admin()).valor == 70_000


@pytest.mark.parametrize("medio,ref,guardada", [("TRANSFERENCIA", "trf-0001", "TRF-0001"), ("tarjeta", "A1B2C3", "A1B2C3")])
def test_cp41_pago_con_referencia(app, medio, ref, guardada):
    """CP-41 HU-23: transferencia y tarjeta guardan la referencia (en mayúsculas)."""
    v = vehiculo_nuevo()
    pago = PagoService.registrar(v.id_vehiculo, medio, ref, admin())
    assert pago.medio == medio.upper() and pago.referencia == guardada


@pytest.mark.parametrize(
    "medio,ref,fragmento",
    [
        ("", None, "medio de pago"),
        ("BITCOIN", None, "medio de pago"),
        ("TRANSFERENCIA", "", "referencia"),
        ("TARJETA", "ab", "referencia"),
        ("TARJETA", "ab#$cd", "referencia"),
        ("TRANSFERENCIA", "x" * 41, "referencia"),
    ],
)
def test_cp42_pago_invalido_no_crea_nada(app, medio, ref, fragmento):
    """CP-42 HU-23: medio inválido o referencia faltante/inválida se rechaza sin crear pago ni mensualidad."""
    v = vehiculo_nuevo()
    pagos, mens = Pago.query.count(), Mensualidad.query.count()
    with pytest.raises(ReglaNegocioError, match=fragmento):
        PagoService.registrar(v.id_vehiculo, medio, ref, admin())
    assert (Pago.query.count(), Mensualidad.query.count()) == (pagos, mens)


def test_cp43_efectivo_ignora_la_referencia(app):
    """CP-43 HU-23: en efectivo no se guarda referencia aunque se envíe."""
    v = vehiculo_nuevo()
    assert PagoService.registrar(v.id_vehiculo, "EFECTIVO", "cualquier cosa", admin()).referencia is None


def test_cp44_no_se_paga_con_mensualidad_vigente(app):
    """CP-44 HU-23: si ya hay mensualidad vigente se rechaza y no se crea un segundo pago."""
    v = vehiculo_nuevo()
    PagoService.registrar(v.id_vehiculo, "EFECTIVO", None, admin())
    pagos = Pago.query.count()
    with pytest.raises(ReglaNegocioError, match="ya tiene una mensualidad vigente"):
        PagoService.registrar(v.id_vehiculo, "EFECTIVO", None, admin())
    assert Pago.query.count() == pagos
    assert Mensualidad.query.filter_by(id_vehiculo=v.id_vehiculo, estado="ACTIVA").count() == 1


def test_cp45_renovar_cuando_la_anterior_vencio(app):
    """CP-45 HU-23: con la mensualidad anterior vencida se puede pagar otra; la vieja pasa a VENCIDA."""
    v = vehiculo_nuevo()
    vieja = ClienteService.activar_mensualidad(v.id_vehiculo, hoy=date.today() - timedelta(days=60))
    pago = PagoService.registrar(v.id_vehiculo, "EFECTIVO", None, admin())
    assert vieja.estado == "VENCIDA" and pago.mensualidad.estado == "ACTIVA"


def test_cp46_sin_pago_no_entra_con_pago_si(app):
    """CP-46 HU-23: un vehículo sin mensualidad no entra; después de pagar, entra."""
    v = vehiculo_nuevo()
    with pytest.raises(ReglaNegocioError, match="mensualidad"):
        MovimientoService.registrar_entrada("XYZ987", admin())
    PagoService.registrar(v.id_vehiculo, "EFECTIVO", None, admin())
    assert MovimientoService.registrar_entrada("XYZ987", admin()).celda.codigo.startswith("C-")


def test_cp47_un_solo_pago_por_mensualidad_en_la_bd(app):
    """CP-47 HU-23: la base de datos impide dos pagos para la misma mensualidad (UNIQUE)."""
    v = vehiculo_nuevo()
    pago = PagoService.registrar(v.id_vehiculo, "EFECTIVO", None, admin())
    db.session.add(Pago(id_mensualidad=pago.id_mensualidad, valor=1000, medio="EFECTIVO",
                        fecha_hora=pago.fecha_hora, id_usuario=admin().id_usuario))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_cp48_vehiculo_inexistente(app, client):
    """CP-48 HU-23: pagar por un vehículo que no existe da 'no encontrado' (404 en pantalla)."""
    with pytest.raises(NoEncontradoError):
        PagoService.registrar(9999, "EFECTIVO", None, admin())
    iniciar_sesion(client, "admin", "admin123")
    assert client.get("/pagos/nuevo?vehiculo=9999").status_code == 404


# ============================================================ ANULAR PAGO
def test_cp49_anular_pago(app):
    """CP-49 HU-26: anular deja el pago ANULADO con motivo, fecha y usuario, y cancela la mensualidad."""
    v = vehiculo_nuevo()
    pago = PagoService.registrar(v.id_vehiculo, "EFECTIVO", None, admin())
    PagoService.anular(pago.id_pago, "  Pago registrado por error  ", admin())
    assert pago.estado == "ANULADO" and pago.motivo_anulacion == "Pago registrado por error"
    assert pago.fecha_hora_anulacion is not None and pago.usuario_anulo.username == "admin"
    assert pago.mensualidad.estado == "CANCELADA" and v.mensualidad_vigente(date.today()) is None


def test_cp50_tras_anular_no_entra_y_puede_pagar_de_nuevo(app):
    """CP-50 HU-26: con el pago anulado el vehículo no entra; se puede registrar un pago nuevo."""
    v = vehiculo_nuevo()
    pago = PagoService.registrar(v.id_vehiculo, "EFECTIVO", None, admin())
    PagoService.anular(pago.id_pago, "Error de digitación", admin())
    with pytest.raises(ReglaNegocioError, match="mensualidad"):
        MovimientoService.registrar_entrada("XYZ987", admin())
    nuevo = PagoService.registrar(v.id_vehiculo, "TARJETA", "AP-9001", admin())
    assert nuevo.id_pago != pago.id_pago and nuevo.mensualidad.estado == "ACTIVA"


@pytest.mark.parametrize("motivo,fragmento", [("", "motivo"), ("   ", "motivo"), ("abc", "al menos 5"), ("x" * 256, "255")])
def test_cp51_anular_exige_motivo(app, motivo, fragmento):
    """CP-51 HU-26: el motivo es obligatorio (5 a 255 caracteres); si falla, el pago sigue registrado."""
    v = vehiculo_nuevo()
    pago = PagoService.registrar(v.id_vehiculo, "EFECTIVO", None, admin())
    with pytest.raises(ReglaNegocioError, match=fragmento):
        PagoService.anular(pago.id_pago, motivo, admin())
    assert pago.estado == "REGISTRADO" and pago.mensualidad.estado == "ACTIVA"


def test_cp52_no_se_anula_dos_veces_ni_uno_inexistente(app):
    """CP-52 HU-26: un pago ya anulado o que no existe no se puede anular."""
    v = vehiculo_nuevo()
    pago = PagoService.registrar(v.id_vehiculo, "EFECTIVO", None, admin())
    PagoService.anular(pago.id_pago, "Error de digitación", admin())
    with pytest.raises(ReglaNegocioError, match="ya está anulado"):
        PagoService.anular(pago.id_pago, "Otro motivo cualquiera", admin())
    with pytest.raises(NoEncontradoError):
        PagoService.anular(9999, "Motivo válido", admin())


def test_cp53_no_se_anula_si_la_mensualidad_ya_vencio(app):
    """CP-53 HU-26: no se puede anular un pago cuya mensualidad ya venció (el servicio ya se prestó)."""
    pago = Pago.query.join(Mensualidad).join(Vehiculo).filter(Vehiculo.placa == "GHI789").first()
    with pytest.raises(ReglaNegocioError, match="ya venció"):
        PagoService.anular(pago.id_pago, "Motivo válido", admin())
    assert pago.estado == "REGISTRADO"


# ============================================================ CONSULTAR PAGOS
def test_cp54_listar_pagos_mas_recientes_primero(app):
    """CP-54 HU-24: lista los pagos de ejemplo (5), del más reciente al más antiguo."""
    pagina = PagoService.listar()
    fechas = [p.fecha_hora for p in pagina.items]
    assert pagina.total == 5 and fechas == sorted(fechas, reverse=True)


def test_cp55_filtros_de_pagos(app):
    """CP-55 HU-24: filtra por placa, documento, apellido, medio, estado y rango de fechas."""
    assert [p.mensualidad.vehiculo.placa for p in PagoService.listar(q="abc").items] == ["ABC123"]
    assert PagoService.listar(q="80123456").total == 2  # Andrés tiene carro y moto
    assert PagoService.listar(q="Torres").total == 1
    por_medio = PagoService.listar(medio="TRANSFERENCIA")
    assert por_medio.total > 0 and all(p.medio == "TRANSFERENCIA" for p in por_medio.items)
    assert PagoService.listar(estado="ANULADO").total == 0
    hoy = date.today()
    assert PagoService.listar(desde=hoy, hasta=hoy).total == 0  # los de ejemplo son de fechas pasadas
    assert PagoService.listar(desde=hoy - timedelta(days=400), hasta=hoy).total == 5
    assert PagoService.listar(q="inexistente").total == 0


def test_cp56_total_recaudado_no_cuenta_anulados(app):
    """CP-56 HU-24: el total suma solo los pagos REGISTRADOS; al anular uno, baja su valor."""
    antes = PagoService.total_recaudado()
    assert antes == sum(p.valor for p in Pago.query.all())
    v = vehiculo_nuevo()
    pago = PagoService.registrar(v.id_vehiculo, "EFECTIVO", None, admin())
    assert PagoService.total_recaudado() == antes + 150_000
    PagoService.anular(pago.id_pago, "Error de digitación", admin())
    assert PagoService.total_recaudado() == antes
    assert PagoService.total_recaudado(medio="EFECTIVO", q="XYZ987") == 0


def test_cp57_rango_de_fechas_invertido(app, client):
    """CP-57 HU-24: fecha inicial posterior a la final se rechaza; la pantalla avisa y no falla."""
    with pytest.raises(ReglaNegocioError, match="fecha inicial"):
        PagoService.listar(desde=date(2026, 12, 1), hasta=date(2026, 11, 1))
    iniciar_sesion(client, "admin", "admin123")
    r = client.get("/pagos?desde=2026-12-01&hasta=2026-11-01")
    assert r.status_code == 200 and "fecha inicial no puede ser posterior" in r.get_data(as_text=True)


def test_formato_de_pesos():
    assert formatear_pesos(150000) == "$150.000" and formatear_pesos(1200000) == "$1.200.000"


# ============================================================ PANTALLAS, PERMISOS Y SEGURIDAD
RUTAS_PAGOS = ["/pagos", "/pagos/nuevo?vehiculo=1", "/pagos/1", "/tarifas", "/tarifas/CARRO/editar"]


def test_cp58_permisos_de_pagos_y_tarifas(client):
    """CP-58 RF-38: sin sesión → login; operario → redirigido al panel; administrador → acceso."""
    for ruta in RUTAS_PAGOS:
        r = client.get(ruta)
        assert r.status_code == 302 and "/login" in r.headers["Location"]
    iniciar_sesion(client)  # operario
    for ruta in RUTAS_PAGOS:
        r = client.get(ruta)
        assert r.status_code == 302 and "/login" not in r.headers["Location"]
    assert client.post("/pagos/nuevo", data={"id_vehiculo": 1, "medio": "EFECTIVO"}).status_code == 302
    client.post("/logout")
    iniciar_sesion(client, "admin", "admin123")
    for ruta in RUTAS_PAGOS:
        assert client.get(ruta).status_code == 200


def test_cp59_registro_inexistente_da_404(client):
    """CP-59: pago o tarifa que no existen muestran 404 y no un error del servidor."""
    iniciar_sesion(client, "admin", "admin123")
    for ruta in ("/pagos/9999", "/tarifas/BUS/editar"):
        assert client.get(ruta).status_code == 404
    assert client.post("/pagos/9999/anular", data={"motivo": "Motivo válido"}).status_code == 404


def test_cp60_proteccion_csrf_en_pagos(app):
    """CP-60 RNF-10: registrar o anular un pago sin la ficha CSRF se rechaza con 400."""
    app.config["CSRF_ENABLED"] = True
    c = app.test_client()
    html = c.get("/login").get_data(as_text=True)
    token = html.split('name="csrf_token" value="')[1].split('"')[0]
    c.post("/login", data={"username": "admin", "password": "admin123", "csrf_token": token})
    assert c.post("/pagos/nuevo", data={"id_vehiculo": 1, "medio": "EFECTIVO"}).status_code == 400
    assert c.post("/pagos/1/anular", data={"motivo": "Motivo válido"}).status_code == 400
    assert Pago.query.count() == 5


def test_cp61_boton_de_pago_en_el_detalle_del_cliente(client):
    """CP-61 HU-23: «Registrar pago» aparece solo en los vehículos sin mensualidad vigente."""
    iniciar_sesion(client, "admin", "admin123")
    vehiculo_nuevo()
    id_cliente = Cliente.query.filter_by(numero_documento="1055667788").first().id_cliente
    html = client.get(f"/clientes/{id_cliente}").get_data(as_text=True)
    assert "Registrar pago" in html and "/pagos/nuevo?vehiculo=" in html
    v = Vehiculo.query.filter_by(placa="XYZ987").first()
    PagoService.registrar(v.id_vehiculo, "EFECTIVO", None, admin())
    assert "Registrar pago" not in client.get(f"/clientes/{id_cliente}").get_data(as_text=True)


def test_cp62_formulario_con_error_conserva_datos(client):
    """CP-62 usabilidad: si falta la referencia responde 400, muestra el motivo y conserva el medio elegido."""
    iniciar_sesion(client, "admin", "admin123")
    v = vehiculo_nuevo()
    r = client.post("/pagos/nuevo", data={"id_vehiculo": v.id_vehiculo, "medio": "TRANSFERENCIA", "referencia": ""})
    html = r.get_data(as_text=True)
    assert r.status_code == 400 and "indique la referencia" in html
    assert 'value="TRANSFERENCIA" selected' in html and "$150.000" in html
    assert Pago.query.count() == 5


def test_cp63_flujo_completo_por_pantallas(client):
    """CP-63 flujo E2E: tarifa → pago con tarjeta → comprobante → entrada → anulación → ya no entra."""
    iniciar_sesion(client, "admin", "admin123")
    client.post("/clientes/nuevo", data={"tipo_documento": "CC", "numero_documento": "99887766",
                                        "nombres": "Rosa", "apellidos": "Díaz"})
    id_cliente = Cliente.query.filter_by(numero_documento="99887766").first().id_cliente
    client.post(f"/clientes/{id_cliente}/vehiculos/nuevo", data={"placa": "rst456", "tipo": "CARRO"})
    id_veh = Vehiculo.query.filter_by(placa="RST456").first().id_vehiculo

    r = client.post("/tarifas/CARRO/editar", data={"valor": "180.000"}, follow_redirects=True)
    assert "Tarifa de carros actualizada" in r.get_data(as_text=True)

    r = client.post("/pagos/nuevo", data={"id_vehiculo": id_veh, "medio": "TARJETA", "referencia": "ap-5521"},
                    follow_redirects=True)
    html = r.get_data(as_text=True)
    assert "registrado. Mensualidad de RST456 activa" in html
    assert "$180.000" in html and "Tarjeta" in html and "AP-5521" in html and "Anular este pago" in html
    pago = Pago.query.order_by(Pago.id_pago.desc()).first()

    client.post("/logout")
    iniciar_sesion(client)
    assert "Entrada registrada: RST456" in client.post("/entrada", data={"placa": "RST456"}, follow_redirects=True).get_data(as_text=True)
    client.post("/salida", data={"placa": "RST456"})
    client.post("/logout")

    iniciar_sesion(client, "admin", "admin123")
    r = client.post(f"/pagos/{pago.id_pago}/anular", data={"motivo": "Cobro duplicado"}, follow_redirects=True)
    html = r.get_data(as_text=True)
    assert "anulado" in html.lower() and "Motivo:</strong> Cobro duplicado" in html and "Anular este pago" not in html
    lista = client.get("/pagos?estado=ANULADO").get_data(as_text=True)
    assert pago.numero in lista and "Anulado" in lista
    client.post("/logout")
    iniciar_sesion(client)
    r = client.post("/entrada", data={"placa": "RST456"})
    assert r.status_code == 400 and "mensualidad" in r.get_data(as_text=True)


def test_cp64_anular_desde_pantalla_con_error_conserva_motivo(client):
    """CP-64 usabilidad: un motivo muy corto responde 400, explica el error y conserva lo escrito."""
    iniciar_sesion(client, "admin", "admin123")
    pago = Pago.query.first()
    r = client.post(f"/pagos/{pago.id_pago}/anular", data={"motivo": "abc"})
    html = r.get_data(as_text=True)
    assert r.status_code == 400 and "al menos 5" in html and ">abc</textarea>" in html
