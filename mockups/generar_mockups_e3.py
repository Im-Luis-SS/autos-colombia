"""Mockups de la iteración 3 (tarifas y pagos). Uso: python mockups/generar_mockups_e3.py"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import generar_mockups_e2 as e2
from generar_mockups_e2 import L2, encabezado, form
from generar_mockups import *  # noqa

e2.ITEMS = ["Panel", "Registrar entrada", "Registrar salida", "Vehículos dentro", "Clientes", "Pagos", "Celdas", "Usuarios", "Historial"]


def aviso(c, x, y, w, texto, ok=True, tam=12):
    c.rect(x, y, w, 56, fill=VERDE_F if ok else ROJO_F, line="#9ad4b1" if ok else "#f0b3ad", r=8)
    c.texto(x + 16, y + 28, texto, tam, VERDE_T if ok else ROJO_T, False, "lm")


def mk_pagos():
    c = L2(); encabezado(c, "autoscolombia.local/pagos", "Pagos", "Pagos de mensualidades", "Para registrar un pago, abra el cliente y use «Registrar pago».", "Ver tarifas")
    c.tarjeta(60, 175, 1160, 90)
    c.campo(84, 185, 230, "Cliente o placa", "", h=38); c.campo(330, 185, 150, "Desde", "", h=38); c.campo(496, 185, 150, "Hasta", "", h=38)
    c.campo(662, 185, 170, "Medio", "Todos", h=38); c.campo(848, 185, 170, "Estado", "Todos", h=38); c.boton(1040, 207, 150, 38, "Filtrar")
    c.tarjeta(60, 280, 1160, 64)
    c.texto(84, 312, "Total recaudado con este filtro (sin pagos anulados)", 14, TEXTO, False, "lm"); c.texto(1196, 312, "$590.000", 24, AZUL, True, "rm")
    c.tarjeta(60, 360, 1160, 290)
    cols = [("N.º", 84), ("Fecha", 190), ("Cliente", 340), ("Placa", 560), ("Medio", 690), ("Valor", 820), ("Estado", 920), ("", 1060)]
    filas = [("P-000005", "20/11/2026 09:00", "Julián Ramírez Cruz", "PQR34B", "Efectivo", "$70.000", "Registrado"),
             ("P-000003", "17/11/2026 09:00", "Andrés Pérez Díaz", "MNO12A", "Efectivo", "$70.000", "Registrado"),
             ("P-000002", "17/11/2026 09:00", "Andrés Pérez Díaz", "DEF456", "Transferencia", "$150.000", "Registrado"),
             ("P-000001", "12/11/2026 09:00", "Laura Gómez Rojas", "ABC123", "Efectivo", "$150.000", "Anulado")]
    def fn(i, f, y):
        for t, x in zip((f[0], f[1], f[2]), (84, 190, 340)): c.texto(x, y + 24, t, 12, TEXTO, f[0] == t, "lm")
        c.placa(560, y + 12, f[3]); c.texto(690, y + 24, f[4], 12, TEXTO, False, "lm"); c.texto(820, y + 24, f[5], 12, TEXTO, False, "lm")
        an = f[6] == "Anulado"; c.chip(920, y + 12, f[6], GRIS_F if an else VERDE_F, GRIS_T if an else VERDE_T)
        c.pequeno(1060, y + 11, "Comprobante")
    c.tabla(60, 360, 1160, cols, filas, 50, fn)
    c.texto(W / 2 + 30, 625, "Página 1 de 1 · 4 pagos", 12, GRIS, False, "mm")
    c.etiqueta_historia("HU-24", "Consultar pagos"); c.guardar("MK-16_pagos.png")


def mk_pago_form():
    c = L2(); encabezado(c, "autoscolombia.local/pagos/nuevo?vehiculo=7", "Pagos", "Registrar pago de mensualidad", "Al registrar el pago, la mensualidad del vehículo se activa por 30 días.")
    c.tarjeta(60, 180, 540, 190)
    c.texto(84, 205, "Cliente: Pedro Ruiz (CC 1055667788)", 14); c.texto(84, 235, "Vehículo:", 14, TEXTO, True); c.placa(160, 224, "XYZ987"); c.texto(262, 235, "Carro", 14)
    c.texto(84, 268, "Periodo: 22/11/2026 al 21/12/2026", 14); c.texto(84, 310, "Valor a cobrar: $150.000", 19, AZUL, True)
    c.tarjeta(60, 390, 540, 250)
    c.campo(84, 410, 492, "Medio de pago", "Transferencia"); c.campo(84, 490, 492, "Referencia (transferencia o tarjeta)", "TRF-7788")
    c.boton(84, 574, 230, 44, "Registrar pago y activar"); c.boton(328, 574, 110, 44, "Cancelar", fill="white", color=AZUL, line=AZUL)
    c.texto(640, 195, "Estados de la pantalla", 15, AZUL, True)
    aviso(c, 640, 220, 580, "Éxito: «Pago P-000006 registrado. Mensualidad de XYZ987 activa…»")
    aviso(c, 640, 296, 580, "Error: «El vehículo XYZ987 ya tiene una mensualidad vigente hasta el 21/12/2026.»", False, 11)
    aviso(c, 640, 372, 580, "Error: «Para transferencia o tarjeta indique la referencia…»", False, 11)
    aviso(c, 640, 448, 580, "Error: «Seleccione un medio de pago válido…»", False, 11)
    c.texto(640, 540, "El valor sale de la tarifa del tipo de vehículo; no se digita.", 12, GRIS)
    c.etiqueta_historia("HU-23", "Registrar pago y activar mensualidad"); c.guardar("MK-17_pago_nuevo.png")


def comprobante(c, anulado):
    c.tarjeta(60, 175, 640, 400 if not anulado else 440)
    c.texto(84, 205, "Autos Colombia", 16, TEXTO, True); c.texto(84, 228, "Parqueadero por mensualidad", 11, GRIS)
    c.texto(676, 205, "P-000006", 20, AZUL, True, "ra")
    c.chip(590, 232, "Anulado" if anulado else "Registrado", GRIS_F if anulado else VERDE_F, GRIS_T if anulado else VERDE_T)
    c.rect(84, 262, 592, 2, fill=ACENTO)
    filas = [("Fecha y hora", "22/11/2026 10:24"), ("Cliente", "Pedro Ruiz (CC 1055667788)"), ("Vehículo", None), ("Mensualidad", "22/11/2026 al 21/12/2026 (" + ("Cancelada" if anulado else "Activa") + ")"),
             ("Medio de pago", "Transferencia · Ref. TRF-7788"), ("Valor", "$150.000"), ("Registrado por", "Administrador Autos Colombia")]
    y = 285
    for k, v in filas:
        c.texto(84, y + 12, k, 13, TEXTO, True, "lm")
        if v is None: c.placa(240, y, "XYZ987"); c.texto(342, y + 12, "Carro", 13, TEXTO, False, "lm")
        else: c.texto(240, y + 12, v, 17 if k == "Valor" else 13, AZUL if k == "Valor" else TEXTO, k == "Valor", "lm")
        y += 40
    if anulado:
        c.texto(84, y + 12, "Anulado", 13, ROJO_T, True, "lm"); c.texto(240, y + 12, "22/11/2026 10:31 por Administrador Autos Colombia", 12, ROJO_T, False, "lm")
        c.texto(240, y + 34, "Motivo: Cobro duplicado", 12, ROJO_T, True, "lm")
    c.boton(930, 108, 130, 40, "Imprimir", fill="white", color=AZUL, line=AZUL); c.boton(1074, 108, 146, 40, "Volver a pagos", fill="white", color=AZUL, line=AZUL)


def mk_comprobante():
    c = L2(); encabezado(c, "autoscolombia.local/pagos/6", "Pagos", "Comprobante de pago", "")
    comprobante(c, False)
    c.tarjeta(740, 175, 480, 230)
    c.texto(764, 205, "Anular este pago", 17, TEXTO, True); c.campo(764, 230, 432, "Motivo de la anulación", "", placeholder=True, h=60)
    c.boton(764, 330, 140, 44, "Anular pago", fill=ROJO)
    c.texto(740, 440, "El comprobante se puede imprimir; al imprimir se ocultan el menú y los botones.", 12, GRIS)
    c.etiqueta_historia("HU-25", "Ver e imprimir comprobante"); c.guardar("MK-18_comprobante.png")


def mk_anulado():
    c = L2(); encabezado(c, "autoscolombia.local/pagos/6", "Pagos", "Comprobante de pago", "")
    comprobante(c, True)
    c.texto(740, 195, "Estados de la pantalla", 15, AZUL, True)
    aviso(c, 740, 220, 480, "Éxito: «Pago P-000006 anulado. La mensualidad quedó cancelada.»", True, 11)
    aviso(c, 740, 296, 480, "Error: «El motivo de la anulación debe tener al menos 5 caracteres.»", False, 11)
    aviso(c, 740, 372, 480, "Error: «No se puede anular el pago P-000001: su mensualidad ya venció…»", False, 11)
    aviso(c, 740, 448, 480, "Error: «El pago P-000006 ya está anulado.»", False, 11)
    c.etiqueta_historia("HU-26", "Anular pago"); c.guardar("MK-19_pago_anulado.png")


def mk_tarifas():
    c = L2(); encabezado(c, "autoscolombia.local/tarifas", "Pagos", "Tarifas de la mensualidad", "Valor de una mensualidad de 30 días según el tipo de vehículo.", "Volver a pagos")
    c.tarjeta(60, 175, 1160, 190)
    cols = [("Tipo de vehículo", 84), ("Valor mensual", 420), ("Acciones", 760)]
    filas = [("Carro", "$150.000"), ("Moto", "$70.000")]
    def fn(i, f, y):
        c.texto(84, y + 30, f[0], 14, TEXTO, True, "lm"); c.texto(420, y + 30, f[1], 14, TEXTO, False, "lm"); c.pequeno(760, y + 17, "Editar")
    c.tabla(60, 175, 1160, cols, filas, 60, fn)
    c.texto(60, 395, "Cambiar la tarifa no modifica los pagos ya registrados: cada pago guarda el valor que se cobró.", 12, GRIS)
    c.etiqueta_historia("HU-21", "Consultar tarifas"); c.guardar("MK-20_tarifas.png")


def mk_tarifa_form():
    c = L2(); encabezado(c, "autoscolombia.local/tarifas/CARRO/editar", "Pagos", "Editar tarifa de carros", "Aplica a los pagos que se registren desde ahora.")
    form(c, 180, [("Valor de la mensualidad (pesos)", "180.000", False)], alto=220)
    for i, t in enumerate(["«El valor debe ser un número entero de pesos…»", "«El valor debe estar entre $10.000 y $5.000.000.»"]):
        aviso(c, 640, 200 + i * 80, 580, "Error: " + t, False)
    aviso(c, 640, 380, 580, "Éxito: «Tarifa de carros actualizada.»")
    c.etiqueta_historia("HU-22", "Editar tarifa"); c.guardar("MK-21_tarifa_editar.png")


def mk_detalle():
    c = L2(); encabezado(c, "autoscolombia.local/clientes/8", "Clientes", "Pedro Ruiz", "")
    c.boton(1060, 108, 160, 40, "Editar datos", fill="white", color=AZUL, line=AZUL)
    c.tarjeta(60, 165, 1160, 80); c.texto(84, 190, "Documento: CC 1055667788", 14); c.texto(84, 218, "Teléfono: —     Correo: —", 14)
    c.texto(60, 275, "Vehículos", 20, AZUL, True); c.boton(1000, 262, 220, 40, "+ Agregar vehículo")
    c.tarjeta(60, 315, 1160, 230)
    cols = [("Placa", 84), ("Tipo", 230), ("Marca / color", 340), ("Mensualidad", 560), ("Acciones", 860)]
    filas = [("XYZ987", "Carro", "Kia / Rojo", False), ("QWE123", "Moto", "Yamaha / Negro", True)]
    def fn(i, f, y):
        c.placa(84, y + 14, f[0]); c.texto(230, y + 25, f[1], 13, TEXTO, False, "lm"); c.texto(340, y + 25, f[2], 13, TEXTO, False, "lm")
        if f[3]: c.chip(560, y + 14, "Vigente hasta 21/12/2026", VERDE_F, VERDE_T)
        else: c.chip(560, y + 14, "Sin mensualidad", GRIS_F, GRIS_T)
        x = 860; x += c.pequeno(x, y + 12, "Editar")
        if not f[3]: c.pequeno(x, y + 12, "Registrar pago (30 días)", primario=True)
    c.tabla(60, 315, 1160, cols, filas, 60, fn)
    c.texto(60, 580, "Desde la iteración 3 la mensualidad ya no se activa sola: se activa al registrar su pago.", 12, GRIS)
    c.etiqueta_historia("HU-23", "Punto de entrada al pago"); c.guardar("MK-22_cliente_pago.png")


if __name__ == "__main__":
    for f in (mk_pagos, mk_pago_form, mk_comprobante, mk_anulado, mk_tarifas, mk_tarifa_form, mk_detalle):
        f()
