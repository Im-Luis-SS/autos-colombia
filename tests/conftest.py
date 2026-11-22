import pytest

from app import create_app
from app.cli import cargar_datos_ejemplo
from app.config import TestConfig
from app.extensions import db


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        cargar_datos_ejemplo()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def operario(app):
    from app.models import UsuarioSistema

    return UsuarioSistema.query.filter_by(username="operario").first()


def iniciar_sesion(client, usuario="operario", clave="operario123"):
    return client.post("/login", data={"username": usuario, "password": clave}, follow_redirects=True)
