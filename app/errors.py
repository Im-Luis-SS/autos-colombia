"""Excepciones de negocio."""


class ReglaNegocioError(Exception):
    """Se lanza cuando una operación viola una regla de negocio.

    El mensaje es apto para mostrarse al usuario final.
    """


class NoEncontradoError(ReglaNegocioError):
    """El registro pedido (usuario, cliente, celda...) no existe."""
