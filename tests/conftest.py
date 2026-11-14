import os

import pytest
from sqlalchemy.engine import make_url

from app import create_app
from app.cli import cargar_datos_ejemplo
from app.config import TestConfig
from app.extensions import db


@pytest.fixture()
def app():
    """App de pruebas. Con TEST_DATABASE_URL (base *_test) corre sobre MySQL; si no, SQLite."""
    config = TestConfig
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        if not (make_url(url).database or "").endswith("_test"):
            pytest.skip("TEST_DATABASE_URL debe apuntar a una base cuyo nombre termine en _test")

        class config(TestConfig):  # noqa: N801
            SQLALCHEMY_DATABASE_URI = url

    app = create_app(config)
    with app.app_context():
        if url:
            db.drop_all()
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
