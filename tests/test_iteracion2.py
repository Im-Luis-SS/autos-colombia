"""Pruebas de la iteración 2: usuarios, clientes/vehículos/mensualidad y celdas.

Cada prueba lleva el ID del caso del plan de pruebas (CP-xx) en su docstring.
"""
from datetime import date, timedelta

import pytest

from app.errors import NoEncontradoError, ReglaNegocioError
from app.extensions import db
from app.models import Celda, Mensualidad, UsuarioSistema
from app.services import MovimientoService
from app.services.celdas import CeldaService
from app.services.clientes import ClienteService
from app.services.usuarios import UsuarioService
from tests.conftest import iniciar_sesion


def admin():
    return UsuarioSistema.query.filter_by(username="admin").first()


# ============================================================ USUARIOS
def test_cp01_crear_usuario_valido(app):
    """CP-01 HU-08: crea un usuario válido; la clave queda cifrada y puede iniciar sesión."""
    u = UsuarioService.crear("Ana Pérez", "Ana.Perez", "clave1234", "clave1234", "OPERARIO")
    assert u.username == "ana.perez" and u.activo
    assert u.password_hash != "clave1234" and u.verificar_clave("clave1234")


@pytest.mark.parametrize(
    "nombre,username,clave,conf,rol,fragmento",
    [
        ("", "ana", "clave1234", "clave1234", "OPERARIO", "nombre"),
        ("Ana Pérez", "a", "clave1234", "clave1234", "OPERARIO", "usuario debe tener"),
        ("Ana Pérez", "ana", "corta1", "corta1", "OPERARIO", "al menos 8"),
        ("Ana Pérez", "ana", "sololetras", "sololetras", "OPERARIO", "letras y números"),
        ("Ana Pérez", "ana", "clave1234", "otraclave1", "OPERARIO", "no coinciden"),
        ("Ana Pérez", "ana", "clave1234", "clave1234", "ROOT", "rol"),
    ],
)
def test_cp02_crear_usuario_datos_invalidos(app, nombre, username, clave, conf, rol, fragmento):
    """CP-02 HU-08: rechaza nombre vacío, usuario corto, clave débil, confirmación distinta y rol inválido."""
    with pytest.raises(ReglaNegocioError, match=fragmento):
        UsuarioService.crear(nombre, username, clave, conf, rol)
    assert UsuarioSistema.query.filter_by(username=username.lower()).count() == 0


def test_cp03_usuario_duplicado_sin_importar_mayusculas(app):
    """CP-03 HU-08: no permite repetir el nombre de usuario (ADMIN = admin)."""
    with pytest.raises(ReglaNegocioError, match="Ya existe"):
        UsuarioService.crear("Otro Admin", "ADMIN", "clave1234", "clave1234", "OPERARIO")


def test_cp04_editar_usuario(app):
    """CP-04 HU-09: edita nombre y rol de un usuario."""
    op = UsuarioSistema.query.filter_by(username="operario").first()
    UsuarioService.editar(op.id_usuario, "Operario Nocturno", "ADMINISTRADOR")
    assert op.nombre == "Operario Nocturno" and op.rol == "ADMINISTRADOR"


def test_cp05_no_quitar_rol_al_ultimo_admin(app):
    """CP-05 HU-09: el único administrador activo no puede pasar a operario."""
    with pytest.raises(ReglaNegocioError, match="último administrador"):
        UsuarioService.editar(admin().id_usuario, "Administrador", "OPERARIO")


def test_cp06_desactivar_usuario_bloquea_su_acceso(client, app):
    """CP-06 HU-10: un usuario desactivado ya no puede iniciar sesión; al activarlo vuelve a entrar."""
    op = UsuarioSistema.query.filter_by(username="operario").first()
    UsuarioService.cambiar_estado(op.id_usuario, False, admin())
    r = client.post("/login", data={"username": "operario", "password": "operario123"})
    assert "Usuario o contraseña incorrectos" in r.get_data(as_text=True)
    UsuarioService.cambiar_estado(op.id_usuario, True, admin())
    assert "Panel de ocupación" in iniciar_sesion(client).get_data(as_text=True)


def test_cp07_no_desactivarse_ni_dejar_sin_admin(app):
    """CP-07 HU-10: no se puede desactivar a sí mismo ni al último administrador activo."""
    with pytest.raises(ReglaNegocioError, match="propio usuario"):
        UsuarioService.cambiar_estado(admin().id_usuario, False, admin())
    with pytest.raises(ReglaNegocioError, match="último administrador"):
        UsuarioService.cambiar_estado(admin().id_usuario, False, None)
    assert admin().activo


def test_cp08_restablecer_clave(client, app):
    """CP-08 HU-11: la clave nueva funciona y la anterior deja de servir."""
    op = UsuarioSistema.query.filter_by(username="operario").first()
    UsuarioService.restablecer_clave(op.id_usuario, "nueva12345", "nueva12345")
    assert op.verificar_clave("nueva12345") and not op.verificar_clave("operario123")
    with pytest.raises(ReglaNegocioError):
        UsuarioService.restablecer_clave(op.id_usuario, "123", "123")


def test_cp09_listar_y_filtrar_usuarios(app):
    """CP-09 HU-07: filtra por texto, rol y estado."""
    assert {u.username for u in UsuarioService.listar()} >= {"admin", "operario"}
    assert [u.username for u in UsuarioService.listar(q="oper")] == ["operario"]
    assert [u.username for u in UsuarioService.listar(rol="ADMINISTRADOR")] == ["admin"]
    assert UsuarioService.listar(estado="inactivo") == []


# ============================================================ CLIENTES Y VEHÍCULOS
def _cliente(**extra):
    datos = dict(tipo_documento="CC", numero_documento="1020304050", nombres="Juan",
                 apellidos="Gómez", telefono="3001234567", email="Juan@Mail.com")
    datos.update(extra)
    return ClienteService.crear(**datos)


def test_cp10_registrar_cliente(app):
    """CP-10 HU-12: registra un cliente con datos válidos (correo en minúsculas)."""
    c = _cliente()
    assert c.id_cliente and c.email == "juan@mail.com" and c.nombre_completo == "Juan Gómez"


@pytest.mark.parametrize(
    "extra,fragmento",
    [
        ({"numero_documento": "12"}, "documento"),
        ({"nombres": " "}, "nombres"),
        ({"email": "no-es-correo"}, "correo"),
        ({"telefono": "abc"}, "teléfono"),
        ({"tipo_documento": "XX"}, "tipo de documento"),
    ],
)
def test_cp11_cliente_datos_invalidos(app, extra, fragmento):
    """CP-11 HU-12: valida documento, nombres, correo, teléfono y tipo de documento."""
    with pytest.raises(ReglaNegocioError, match=fragmento):
        _cliente(**extra)


def test_cp12_cliente_documento_duplicado(app):
    """CP-12 HU-12: no se repite tipo + número de documento."""
    _cliente()
    with pytest.raises(ReglaNegocioError, match="Ya existe un cliente"):
        _cliente(nombres="Otro")


def test_cp13_registrar_vehiculo(app):
    """CP-13 HU-13: registra un vehículo; la placa se normaliza a mayúsculas."""
    c = _cliente()
    v = ClienteService.registrar_vehiculo(c.id_cliente, " xyz-987 ", "CARRO", "Mazda", "Rojo")
    assert v.placa == "XYZ987" and v.cliente is c


def test_cp14_vehiculo_placa_invalida_o_repetida(app):
    """CP-14 HU-13: rechaza placa inválida, tipo inválido y placa ya registrada (ABC123)."""
    c = _cliente()
    with pytest.raises(ReglaNegocioError, match="placa"):
        ClienteService.registrar_vehiculo(c.id_cliente, "A!", "CARRO")
    with pytest.raises(ReglaNegocioError, match="tipo de vehículo"):
        ClienteService.registrar_vehiculo(c.id_cliente, "XYZ987", "BUS")
    with pytest.raises(ReglaNegocioError, match="ya está registrada"):
        ClienteService.registrar_vehiculo(c.id_cliente, "abc123", "CARRO")


def test_cp15_editar_cliente_y_vehiculo(app):
    """CP-15 HU-14: edita datos de contacto y marca/color; no se puede cambiar de tipo estando dentro."""
    c = _cliente()
    v = ClienteService.registrar_vehiculo(c.id_cliente, "XYZ987", "CARRO")
    ClienteService.editar(c.id_cliente, "Juan Carlos", "Gómez", "", "")
    assert c.nombres == "Juan Carlos" and c.telefono is None
    ClienteService.editar_vehiculo(v.id_vehiculo, "CARRO", "Kia", "Azul")
    assert v.marca == "Kia"
    ClienteService.activar_mensualidad(v.id_vehiculo)
    MovimientoService.registrar_entrada("XYZ987", admin())
    with pytest.raises(ReglaNegocioError, match="dentro del parqueadero"):
        ClienteService.editar_vehiculo(v.id_vehiculo, "MOTO")


def test_cp16_buscar_clientes(app):
    """CP-16 HU-14: busca por documento, nombre y placa."""
    c = _cliente()
    ClienteService.registrar_vehiculo(c.id_cliente, "XYZ987", "CARRO")
    for texto in ("1020304050", "gómez", "xyz"):
        assert c in ClienteService.listar(texto).items
    assert ClienteService.listar("zzzzzz-no-existe").items == []


def test_cp17_activar_mensualidad_30_dias(app):
    """CP-17 HU-15: la mensualidad dura 30 días contando el de inicio."""
    c = _cliente()
    v = ClienteService.registrar_vehiculo(c.id_cliente, "XYZ987", "MOTO")
    m = ClienteService.activar_mensualidad(v.id_vehiculo, hoy=date(2026, 11, 14))
    assert m.estado == "ACTIVA"
    assert (m.fecha_inicio, m.fecha_fin) == (date(2026, 11, 14), date(2026, 12, 13))
    assert (m.fecha_fin - m.fecha_inicio).days + 1 == 30


def test_cp18_una_sola_mensualidad_vigente(app):
    """CP-18 HU-15: no se puede activar otra mensualidad mientras haya una vigente."""
    c = _cliente()
    v = ClienteService.registrar_vehiculo(c.id_cliente, "XYZ987", "CARRO")
    ClienteService.activar_mensualidad(v.id_vehiculo)
    with pytest.raises(ReglaNegocioError, match="ya tiene una mensualidad vigente"):
        ClienteService.activar_mensualidad(v.id_vehiculo)
    assert Mensualidad.query.filter_by(id_vehiculo=v.id_vehiculo).count() == 1


def test_cp19_renovar_mensualidad_vencida(app):
    """CP-19 HU-15: si la anterior ya caducó se puede renovar y la vieja queda VENCIDA."""
    c = _cliente()
    v = ClienteService.registrar_vehiculo(c.id_cliente, "XYZ987", "CARRO")
    vieja = ClienteService.activar_mensualidad(v.id_vehiculo, hoy=date.today() - timedelta(days=60))
    nueva = ClienteService.activar_mensualidad(v.id_vehiculo)
    assert vieja.estado == "VENCIDA" and nueva.estado == "ACTIVA"


def test_cp20_bd_impide_dos_mensualidades_activas(app):
    """CP-20 HU-15 (RNF integridad): aun saltándose el servicio, la BD rechaza dos ACTIVAS."""
    from sqlalchemy.exc import IntegrityError

    c = _cliente()
    v = ClienteService.registrar_vehiculo(c.id_cliente, "XYZ987", "CARRO")
    ClienteService.activar_mensualidad(v.id_vehiculo)
    db.session.add(Mensualidad(fecha_inicio=date.today(), fecha_fin=date.today(),
                               estado="ACTIVA", id_vehiculo=v.id_vehiculo))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_cp21_flujo_vehiculo_nuevo_mensualidad_y_entrada(app):
    """CP-21 HU-13/15: vehículo recién registrado sin mensualidad no entra; con mensualidad, sí."""
    c = _cliente()
    v = ClienteService.registrar_vehiculo(c.id_cliente, "XYZ987", "CARRO")
    with pytest.raises(ReglaNegocioError):
        MovimientoService.registrar_entrada("XYZ987", admin())
    ClienteService.activar_mensualidad(v.id_vehiculo)
    assert MovimientoService.registrar_entrada("XYZ987", admin()).celda.codigo == "C-01"


# ============================================================ CELDAS
def test_cp22_crear_celda(app):
    """CP-22 HU-17: crea una celda libre; el código se guarda en mayúsculas."""
    c = CeldaService.crear("c-71", "CARRO")
    assert c.codigo == "C-71" and c.estado == "LIBRE"
    assert Celda.query.count() == 81


@pytest.mark.parametrize("codigo,tipo,fragmento", [
    ("", "CARRO", "código"), ("C 71", "CARRO", "código"), ("C-1234567890", "CARRO", "código"),
    ("C-72", "BUS", "tipo de celda"), ("C-01", "CARRO", "Ya existe"),
])
def test_cp23_celda_datos_invalidos(app, codigo, tipo, fragmento):
    """CP-23 HU-17: rechaza código vacío/inválido/largo, tipo inválido y código repetido."""
    with pytest.raises(ReglaNegocioError, match=fragmento):
        CeldaService.crear(codigo, tipo)


def test_cp24_editar_celda_libre(app):
    """CP-24 HU-18: renombra una celda sin historial y le cambia el tipo."""
    c = CeldaService.crear("X-01", "CARRO")
    CeldaService.editar(c.id_celda, "x-02", "MOTO")
    assert (c.codigo, c.tipo) == ("X-02", "MOTO")
    with pytest.raises(ReglaNegocioError, match="Ya existe"):
        CeldaService.editar(c.id_celda, "C-01", "MOTO")


def test_cp25_celda_ocupada_no_se_toca(app):
    """CP-25 HU-18/19/20: una celda ocupada no se edita, no cambia de estado ni se elimina."""
    mov = MovimientoService.registrar_entrada("ABC123", admin())
    id_celda = mov.id_celda
    with pytest.raises(ReglaNegocioError, match="ocupada"):
        CeldaService.editar(id_celda, "Z-99", "CARRO")
    with pytest.raises(ReglaNegocioError, match="vehículo dentro"):
        CeldaService.cambiar_estado(id_celda, "MANTENIMIENTO")
    with pytest.raises(ReglaNegocioError, match="ocupada"):
        CeldaService.eliminar(id_celda)


def test_cp26_mantenimiento_excluye_la_celda_de_la_asignacion(app):
    """CP-26 HU-19: con C-01 en mantenimiento la entrada recibe C-02; al habilitarla vuelve a asignarse."""
    c1 = Celda.query.filter_by(codigo="C-01").first()
    CeldaService.cambiar_estado(c1.id_celda, "MANTENIMIENTO")
    assert MovimientoService.registrar_entrada("ABC123", admin()).celda.codigo == "C-02"
    with pytest.raises(ReglaNegocioError, match="ya está en estado"):
        CeldaService.cambiar_estado(c1.id_celda, "MANTENIMIENTO")
    CeldaService.cambiar_estado(c1.id_celda, "LIBRE")
    assert MovimientoService.registrar_entrada("DEF456", admin()).celda.codigo == "C-01"


def test_cp27_eliminar_celda_sin_historial(app):
    """CP-27 HU-20: elimina una celda sin movimientos; una con historial no se puede eliminar."""
    nueva = CeldaService.crear("X-01", "CARRO")
    assert CeldaService.eliminar(nueva.id_celda) == "X-01"
    with pytest.raises(NoEncontradoError):
        CeldaService.obtener(nueva.id_celda)
    mov = MovimientoService.registrar_entrada("ABC123", admin())
    MovimientoService.registrar_salida("ABC123", admin())
    with pytest.raises(ReglaNegocioError, match="historial"):
        CeldaService.eliminar(mov.id_celda)


def test_cp28_listar_y_filtrar_celdas(app):
    """CP-28 HU-16: lista las 80 celdas y filtra por tipo, estado y código."""
    assert len(CeldaService.listar()) == 80
    assert len(CeldaService.listar(tipo="MOTO")) == 10
    assert len(CeldaService.listar(estado="OCUPADA")) == 0
    assert [c.codigo for c in CeldaService.listar(q="m-03")] == ["M-03"]


# ============================================================ RUTAS: permisos, CSRF, flujo
RUTAS_ADMIN = ["/usuarios", "/usuarios/nuevo", "/clientes", "/clientes/nuevo", "/celdas", "/celdas/nueva"]


def test_cp29_rutas_solo_admin(client):
    """CP-29 RNF seguridad: sin sesión → login; operario → rechazado; administrador → acceso."""
    for ruta in RUTAS_ADMIN:
        r = client.get(ruta)
        assert r.status_code == 302 and "/login" in r.headers["Location"]
    iniciar_sesion(client)  # operario
    for ruta in RUTAS_ADMIN:
        r = client.get(ruta)
        assert r.status_code == 302 and "/login" not in r.headers["Location"]
    client.post("/logout")
    iniciar_sesion(client, "admin", "admin123")
    for ruta in RUTAS_ADMIN:
        assert client.get(ruta).status_code == 200


def test_cp30_registro_inexistente_da_404(client):
    """CP-30: abrir un registro que no existe muestra 404 y no un error del servidor."""
    iniciar_sesion(client, "admin", "admin123")
    for ruta in ("/usuarios/9999/editar", "/clientes/9999", "/celdas/9999/editar", "/vehiculos/9999/editar"):
        assert client.get(ruta).status_code == 404


def test_cp31_proteccion_csrf(app):
    """CP-31 RNF seguridad: un POST sin el token de la sesión se rechaza con 400; con el token pasa."""
    app.config["CSRF_ENABLED"] = True
    c = app.test_client()
    assert c.post("/login", data={"username": "admin", "password": "admin123"}).status_code == 400
    html = c.get("/login").get_data(as_text=True)
    token = html.split('name="csrf_token" value="')[1].split('"')[0]
    r = c.post("/login", data={"username": "admin", "password": "admin123", "csrf_token": token})
    assert r.status_code == 302
    assert c.post("/celdas/1/eliminar").status_code == 400  # sin token


def test_cp32_flujo_completo_por_pantallas(client):
    """CP-32 flujo E2E: admin crea cliente → vehículo → mensualidad → crea celda → operario registra entrada."""
    iniciar_sesion(client, "admin", "admin123")
    r = client.post("/clientes/nuevo", data={
        "tipo_documento": "CC", "numero_documento": "99887766", "nombres": "Rosa", "apellidos": "Díaz"},
        follow_redirects=True)
    assert "Cliente Rosa Díaz registrado" in r.get_data(as_text=True)
    from app.models import Cliente
    id_cliente = Cliente.query.filter_by(numero_documento="99887766").first().id_cliente
    r = client.post(f"/clientes/{id_cliente}/vehiculos/nuevo", data={"placa": "rst456", "tipo": "CARRO"},
                    follow_redirects=True)
    assert "Vehículo RST456 registrado" in r.get_data(as_text=True)
    from app.models import Vehiculo
    id_veh = Vehiculo.query.filter_by(placa="RST456").first().id_vehiculo
    # Desde la iteración 3 la mensualidad se activa registrando su pago.
    r = client.post("/pagos/nuevo", data={"id_vehiculo": id_veh, "medio": "EFECTIVO"}, follow_redirects=True)
    assert "Mensualidad de RST456 activa" in r.get_data(as_text=True)
    r = client.post("/pagos/nuevo", data={"id_vehiculo": id_veh, "medio": "EFECTIVO"})
    assert r.status_code == 400 and "ya tiene una mensualidad vigente" in r.get_data(as_text=True)
    r = client.post("/celdas/nueva", data={"codigo": "c-71", "tipo": "carro".upper()}, follow_redirects=True)
    assert "Celda C-71 creada" in r.get_data(as_text=True)
    client.post("/logout")
    iniciar_sesion(client)
    r = client.post("/entrada", data={"placa": "RST456"}, follow_redirects=True)
    assert "Entrada registrada: RST456" in r.get_data(as_text=True)


def test_cp33_formulario_con_error_conserva_datos(client):
    """CP-33 usabilidad: si el formulario falla, responde 400, muestra el motivo y no pierde lo escrito."""
    iniciar_sesion(client, "admin", "admin123")
    r = client.post("/usuarios/nuevo", data={"nombre": "Ana Pérez", "username": "ana", "rol": "OPERARIO",
                                              "clave": "corta", "confirmacion": "corta"})
    html = r.get_data(as_text=True)
    assert r.status_code == 400 and "al menos 8" in html and 'value="Ana Pérez"' in html
