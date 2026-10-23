"""Pruebas de las rutas HTTP (flujo completo de un operario)."""
from tests.conftest import iniciar_sesion


def test_rutas_protegidas_redirigen_a_login(client):
    for ruta in ("/", "/entrada", "/salida", "/dentro", "/historial"):
        r = client.get(ruta)
        assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_login_invalido(client):
    r = client.post("/login", data={"username": "operario", "password": "mala"})
    assert r.status_code == 200
    assert "Usuario o contraseña incorrectos" in r.get_data(as_text=True)


def test_flujo_entrada_y_salida(client):
    r = iniciar_sesion(client)
    assert "Panel de ocupación" in r.get_data(as_text=True)

    r = client.post("/entrada", data={"placa": "abc123", "observaciones": "ok"}, follow_redirects=True)
    html = r.get_data(as_text=True)
    assert "Entrada registrada: ABC123" in html and "C-01" in html

    r = client.get("/dentro")
    assert "ABC123" in r.get_data(as_text=True)

    r = client.post("/entrada", data={"placa": "ABC123"})
    assert r.status_code == 400
    assert "ya se encuentra dentro" in r.get_data(as_text=True)

    r = client.post("/salida", data={"placa": "ABC123"}, follow_redirects=True)
    assert "Salida registrada: ABC123" in r.get_data(as_text=True)

    r = client.post("/salida", data={"placa": "ABC123"})
    assert r.status_code == 400


def test_historial_solo_admin(client):
    iniciar_sesion(client)  # operario
    r = client.get("/historial", follow_redirects=True)
    assert "solo para administradores" in r.get_data(as_text=True)
    client.post("/logout")
    iniciar_sesion(client, "admin", "admin123")
    r = client.get("/historial")
    assert r.status_code == 200 and "Historial de movimientos" in r.get_data(as_text=True)


def test_logout(client):
    iniciar_sesion(client)
    client.post("/logout")
    assert client.get("/").status_code == 302
