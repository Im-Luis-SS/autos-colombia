"""Pruebas de concurrencia: varios operarios actuando a la vez.

Demuestran que la BASE DE DATOS (no solo el código) impide dejar dos movimientos
abiertos para el mismo vehículo o la misma celda.

Cómo se ejecutan
----------------
* Por defecto usan un archivo SQLite temporal (corren en cualquier computador).
* Para correrlas sobre MySQL (lo recomendado, es el motor real del proyecto):

    1) En MySQL Workbench:  CREATE DATABASE autos_colombia_test;
    2) En la terminal (Windows):
         set TEST_DATABASE_URL=mysql+pymysql://root:CLAVE@localhost:3306/autos_colombia_test?charset=utf8mb4
         python -m pytest tests/test_concurrencia.py -v

  Por seguridad la base debe llamarse *_test: la prueba borra y recrea sus tablas, y
  se niega a correr contra una base que no termine en "_test" (para no tocar autos_colombia).
"""
import os
import tempfile
import threading

import pytest
from sqlalchemy import func
from sqlalchemy.engine import make_url

from app import create_app
from app.cli import cargar_datos_ejemplo
from app.config import TestConfig
from app.errors import ReglaNegocioError
from app.extensions import db
from app.models import Celda, Movimiento, UsuarioSistema
from app.services import MovimientoService

HILOS = 8


@pytest.fixture()
def app_compartida():
    """App con una base que comparten todos los hilos (no en memoria)."""
    url = os.environ.get("TEST_DATABASE_URL")
    archivo = None
    if url:
        nombre = make_url(url).database or ""
        if not nombre.endswith("_test"):
            pytest.skip("TEST_DATABASE_URL debe apuntar a una base cuyo nombre termine en _test")
    else:
        descriptor, archivo = tempfile.mkstemp(suffix=".db")
        os.close(descriptor)
        url = f"sqlite:///{archivo}"

    class Config(TestConfig):
        SQLALCHEMY_DATABASE_URI = url

    app = create_app(Config)
    with app.app_context():
        db.drop_all()
        db.create_all()
        cargar_datos_ejemplo()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
    if archivo:
        os.remove(archivo)


def _ejecutar_en_paralelo(app, tareas):
    """Lanza cada tarea en su propio hilo, con su propia sesión, soltándolas a la vez."""
    barrera = threading.Barrier(len(tareas))
    resultados = [None] * len(tareas)

    def trabajo(i, tarea):
        with app.app_context():
            operario = UsuarioSistema.query.filter_by(username="operario").first()
            barrera.wait()
            try:
                resultados[i] = ("ok", tarea(operario))
            except ReglaNegocioError as error:
                resultados[i] = ("rechazado", str(error))
            except Exception as error:  # cualquier otra cosa sería un fallo real
                resultados[i] = ("error", repr(error))
            finally:
                db.session.remove()

    hilos = [threading.Thread(target=trabajo, args=(i, t)) for i, t in enumerate(tareas)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(timeout=60)
    return resultados


def _verificar_invariantes(app):
    """Regla de oro: nunca más de un movimiento abierto por vehículo ni por celda."""
    with app.app_context():
        por_vehiculo = (
            db.session.query(Movimiento.id_vehiculo, func.count())
            .filter(Movimiento.fecha_hora_salida.is_(None))
            .group_by(Movimiento.id_vehiculo)
            .all()
        )
        por_celda = (
            db.session.query(Movimiento.id_celda, func.count())
            .filter(Movimiento.fecha_hora_salida.is_(None))
            .group_by(Movimiento.id_celda)
            .all()
        )
        assert all(n == 1 for _, n in por_vehiculo), f"Vehículo con dos entradas abiertas: {por_vehiculo}"
        assert all(n == 1 for _, n in por_celda), f"Celda con dos vehículos: {por_celda}"
        ocupadas = Celda.query.filter_by(estado="OCUPADA").count()
        abiertos = Movimiento.query.filter(Movimiento.fecha_hora_salida.is_(None)).count()
        assert ocupadas == abiertos, "Celdas ocupadas y movimientos abiertos no coinciden"
        return abiertos


def test_mismo_vehiculo_entrando_a_la_vez_solo_una_vez(app_compartida):
    """8 operarios registran la entrada de ABC123 al mismo tiempo: solo uno lo logra."""
    tareas = [lambda op: MovimientoService.registrar_entrada("ABC123", op)] * HILOS
    resultados = _ejecutar_en_paralelo(app_compartida, tareas)

    estados = [r[0] for r in resultados]
    assert "error" not in estados, f"Errores inesperados: {[r for r in resultados if r[0] == 'error']}"
    assert estados.count("ok") == 1, f"Debía entrar exactamente una vez: {resultados}"
    assert estados.count("rechazado") == HILOS - 1
    assert _verificar_invariantes(app_compartida) == 1


def test_misma_celda_pedida_por_dos_vehiculos_a_la_vez(app_compartida):
    """Dos carros distintos piden la celda C-05 al mismo tiempo: la BD deja pasar solo a uno."""
    tareas = [
        lambda op: MovimientoService.registrar_entrada("ABC123", op, celda_codigo="C-05"),
        lambda op: MovimientoService.registrar_entrada("DEF456", op, celda_codigo="C-05"),
    ]
    resultados = _ejecutar_en_paralelo(app_compartida, tareas)

    estados = [r[0] for r in resultados]
    assert "error" not in estados, f"Errores inesperados: {resultados}"
    assert estados.count("ok") == 1, f"Solo uno debía quedarse con C-05: {resultados}"
    assert _verificar_invariantes(app_compartida) == 1


def test_asignacion_automatica_concurrente_no_repite_celda(app_compartida):
    """Dos carros entran a la vez con asignación automática: nunca comparten celda.

    Pueden elegir la misma celda libre; la BD rechaza a uno (que debe reintentar), por lo
    que habrá 1 o 2 entradas, pero jamás dos vehículos en la misma celda.
    """
    tareas = [
        lambda op: MovimientoService.registrar_entrada("ABC123", op),
        lambda op: MovimientoService.registrar_entrada("DEF456", op),
    ]
    resultados = _ejecutar_en_paralelo(app_compartida, tareas)

    estados = [r[0] for r in resultados]
    assert "error" not in estados, f"Errores inesperados: {resultados}"
    assert estados.count("ok") >= 1
    assert _verificar_invariantes(app_compartida) == estados.count("ok")


def test_misma_salida_concurrente_se_cierra_una_sola_vez(app_compartida):
    """Dos operarios registran la salida del mismo vehículo a la vez: la celda se libera una vez."""
    with app_compartida.app_context():
        operario = UsuarioSistema.query.filter_by(username="operario").first()
        MovimientoService.registrar_entrada("ABC123", operario, "entrada")
        db.session.remove()

    tareas = [lambda op: MovimientoService.registrar_salida("ABC123", op, "salida")] * 2
    resultados = _ejecutar_en_paralelo(app_compartida, tareas)

    estados = [r[0] for r in resultados]
    assert "error" not in estados, f"Errores inesperados: {resultados}"
    assert estados.count("ok") >= 1
    with app_compartida.app_context():
        mov = Movimiento.query.one()
        assert mov.fecha_hora_salida is not None
        assert mov.observaciones_entrada == "entrada"
        assert mov.observaciones_salida == "salida"
        assert Celda.query.filter_by(estado="OCUPADA").count() == 0
