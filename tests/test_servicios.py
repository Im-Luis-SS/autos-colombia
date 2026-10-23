"""Pruebas de las reglas de negocio de entrada y salida."""
import pytest
from sqlalchemy.exc import IntegrityError

from app.errors import ReglaNegocioError
from app.extensions import db
from app.models import Celda, Movimiento, Vehiculo, ahora
from app.services import (
    AuthService,
    MovimientoService,
    OcupacionService,
    normalizar_placa,
)


def test_normalizar_placa():
    assert normalizar_placa(" abc-123 ") == "ABC123"


def test_login_correcto_e_incorrecto(app):
    assert AuthService.autenticar("admin", "admin123").es_administrador()
    with pytest.raises(ReglaNegocioError):
        AuthService.autenticar("admin", "mala")
    with pytest.raises(ReglaNegocioError):
        AuthService.autenticar("noexiste", "x")


def test_entrada_asigna_celda_libre_del_tipo(app, operario):
    mov = MovimientoService.registrar_entrada("abc123", operario, "Sin novedad")
    assert mov.celda.tipo == "CARRO"
    assert mov.celda.estado == "OCUPADA"
    assert mov.celda.codigo == "C-01"  # primera libre por código
    assert mov.usuario_entrada.username == "operario"
    assert mov.observaciones == "Sin novedad"
    assert mov.esta_abierto()


def test_entrada_moto_usa_celda_de_moto(app, operario):
    mov = MovimientoService.registrar_entrada("MNO12A", operario)
    assert mov.celda.codigo.startswith("M-")


def test_entrada_duplicada_se_rechaza(app, operario):
    MovimientoService.registrar_entrada("ABC123", operario)
    with pytest.raises(ReglaNegocioError, match="ya se encuentra dentro"):
        MovimientoService.registrar_entrada("ABC123", operario)


def test_entrada_sin_mensualidad_vigente(app, operario):
    with pytest.raises(ReglaNegocioError, match="mensualidad vigente"):
        MovimientoService.registrar_entrada("GHI789", operario)  # mensualidad vencida


def test_entrada_vehiculo_no_registrado_o_placa_invalida(app, operario):
    with pytest.raises(ReglaNegocioError, match="no está registrado"):
        MovimientoService.registrar_entrada("ZZZ999", operario)
    with pytest.raises(ReglaNegocioError, match="entre 5 y 7"):
        MovimientoService.registrar_entrada("A!", operario)
    with pytest.raises(ReglaNegocioError, match="Ingrese la placa"):
        MovimientoService.registrar_entrada("  ", operario)


def test_entrada_con_celda_elegida(app, operario):
    mov = MovimientoService.registrar_entrada("ABC123", operario, celda_codigo="c-05")
    assert mov.celda.codigo == "C-05"


def test_celda_elegida_invalida(app, operario):
    with pytest.raises(ReglaNegocioError, match="no existe"):
        MovimientoService.registrar_entrada("ABC123", operario, celda_codigo="X-99")
    with pytest.raises(ReglaNegocioError, match="es para"):
        MovimientoService.registrar_entrada("ABC123", operario, celda_codigo="M-01")
    with pytest.raises(ReglaNegocioError, match="no está libre"):
        MovimientoService.registrar_entrada("ABC123", operario, celda_codigo="C-11")  # mantenimiento


def test_sin_celdas_libres(app, operario):
    Celda.query.filter_by(tipo="MOTO").update({"estado": "MANTENIMIENTO"})
    db.session.commit()
    with pytest.raises(ReglaNegocioError, match="No hay celdas libres"):
        MovimientoService.registrar_entrada("MNO12A", operario)


def test_salida_libera_celda_y_registra_datos(app, operario):
    entrada = MovimientoService.registrar_entrada("ABC123", operario, "Rayón puerta")
    celda = entrada.celda
    salida = MovimientoService.registrar_salida("ABC123", operario, "Todo bien")
    assert salida.fecha_hora_salida is not None
    assert salida.usuario_salida.username == "operario"
    assert celda.estado == "LIBRE"
    assert "Rayón puerta" in salida.observaciones and "Salida: Todo bien" in salida.observaciones
    assert not salida.esta_abierto()


def test_salida_sin_entrada_se_rechaza(app, operario):
    with pytest.raises(ReglaNegocioError, match="no tiene una entrada"):
        MovimientoService.registrar_salida("ABC123", operario)


def test_reingreso_tras_salida(app, operario):
    MovimientoService.registrar_entrada("ABC123", operario)
    MovimientoService.registrar_salida("ABC123", operario)
    MovimientoService.registrar_entrada("ABC123", operario)
    assert Movimiento.query.count() == 2


def test_consultas_dentro_e_historial(app, operario):
    MovimientoService.registrar_entrada("ABC123", operario)
    MovimientoService.registrar_entrada("DEF456", operario)
    MovimientoService.registrar_salida("ABC123", operario)
    dentro = MovimientoService.vehiculos_en_parqueadero()
    assert [m.vehiculo.placa for m in dentro] == ["DEF456"]
    assert MovimientoService.vehiculos_en_parqueadero("zzz") == []
    assert MovimientoService.historial().total == 2
    assert MovimientoService.historial(placa="abc").total == 1
    hoy = ahora().date()
    assert MovimientoService.historial(desde=hoy, hasta=hoy).total == 2


def test_resumen_ocupacion(app, operario):
    MovimientoService.registrar_entrada("ABC123", operario)
    r = OcupacionService.resumen()
    assert r["CARRO"]["ocupadas"] == 1
    assert r["CARRO"]["mantenimiento"] == 1
    assert r["TOTAL"]["total"] == 16
    assert r["MOTO"]["libres"] == 5


def test_bd_impide_dos_movimientos_abiertos_del_mismo_vehiculo(app, operario):
    """Defensa a nivel de base de datos (índices únicos sobre columnas generadas)."""
    MovimientoService.registrar_entrada("ABC123", operario)
    vehiculo = Vehiculo.query.filter_by(placa="ABC123").first()
    otra_celda = Celda.query.filter_by(codigo="C-09").first()
    db.session.add(
        Movimiento(
            id_vehiculo=vehiculo.id_vehiculo,
            id_celda=otra_celda.id_celda,
            id_usuario_entrada=operario.id_usuario,
            fecha_hora_entrada=ahora(),
        )
    )
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
