"""Fábrica de la aplicación Flask - Parqueadero Autos Colombia."""
from flask import Flask, render_template

from app.config import Config
from app.extensions import db
from app.services import formatear_duracion


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from app import models  # noqa: F401  (registra las tablas)
    from app.routes import auth_bp, consultas_bp, movimientos_bp
    from app.routes.celdas import celdas_bp
    from app.routes.clientes import clientes_bp
    from app.routes.usuarios import usuarios_bp
    from app.security import cargar_usuario_actual, csrf_token, proteger_csrf

    app.register_blueprint(auth_bp)
    app.register_blueprint(movimientos_bp)
    app.register_blueprint(consultas_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(celdas_bp)
    app.before_request(cargar_usuario_actual)
    app.before_request(proteger_csrf)

    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.errorhandler(400)
    def _400(_e):
        return render_template(
            "error.html", codigo=400,
            mensaje="La solicitud no es válida o la sesión expiró. Recargue la página e intente de nuevo.",
        ), 400

    @app.errorhandler(404)
    def _404(_e):
        return render_template("error.html", codigo=404, mensaje="La página o el registro que busca no existe."), 404

    app.jinja_env.filters["duracion"] = formatear_duracion

    from app.cli import registrar_comandos

    registrar_comandos(app)
    return app
