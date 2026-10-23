"""Excepciones de negocio."""


class ReglaNegocioError(Exception):
    """Se lanza cuando una operación viola una regla de negocio.

    El mensaje es apto para mostrarse al usuario final.
    """
