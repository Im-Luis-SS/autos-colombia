"""Extensiones compartidas (evita importaciones circulares)."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
