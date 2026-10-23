"""Configuración de la aplicación.

Los valores sensibles se leen de variables de entorno (ver .env.example).
"""
import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "cambiar-en-produccion")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://root:root@localhost:3306/autos_colombia?charset=utf8mb4",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ITEMS_POR_PAGINA = 15


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test"
    WTF_CSRF_ENABLED = False
