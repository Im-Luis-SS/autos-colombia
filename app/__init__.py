"""Fábrica de la aplicación Flask - Parqueadero Autos Colombia."""
from flask import Flask

from app.config import Config
from app.extensions import db
from app.services import formatear_duracion


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from app import models  # noqa: F401  (registra las tablas)
    from app.routes import auth_bp, consultas_bp, movimientos_bp
    from app.security import cargar_usuario_actual

    app.register_blueprint(auth_bp)
    app.register_blueprint(movimientos_bp)
    app.register_blueprint(consultas_bp)
    app.before_request(cargar_usuario_actual)

    app.jinja_env.filters["duracion"] = formatear_duracion

    from app.cli import registrar_comandos

    registrar_comandos(app)
    return app
