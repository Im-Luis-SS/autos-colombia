"""Validaciones de texto reutilizadas por los servicios."""
import re

from app.errors import ReglaNegocioError

PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PATRON_TELEFONO = re.compile(r"^\+?\d{7,15}$")


def texto_requerido(valor, etiqueta: str, minimo: int = 1, maximo: int = 100) -> str:
    texto = " ".join((valor or "").split())  # quita espacios sobrantes
    if len(texto) < minimo or not texto:
        if minimo <= 1:
            raise ReglaNegocioError(f"{etiqueta} es obligatorio.")
        raise ReglaNegocioError(f"{etiqueta} debe tener al menos {minimo} caracteres.")
    if len(texto) > maximo:
        raise ReglaNegocioError(f"{etiqueta} no puede superar {maximo} caracteres.")
    return texto


def texto_opcional(valor, etiqueta: str, maximo: int):
    texto = " ".join((valor or "").split())
    if not texto:
        return None
    if len(texto) > maximo:
        raise ReglaNegocioError(f"{etiqueta} no puede superar {maximo} caracteres.")
    return texto


def email_opcional(valor):
    email = texto_opcional(valor, "El correo", 120)
    if email and not PATRON_EMAIL.match(email):
        raise ReglaNegocioError("El correo electrónico no es válido (ejemplo: nombre@dominio.com).")
    return email.lower() if email else None


def telefono_opcional(valor):
    telefono = (valor or "").replace(" ", "").replace("-", "")
    if not telefono:
        return None
    if not PATRON_TELEFONO.match(telefono):
        raise ReglaNegocioError("El teléfono debe tener entre 7 y 15 dígitos (puede iniciar con +).")
    return telefono
