"""Mockups de la iteración 2 (usuarios, clientes/vehículos y celdas). Uso: python mockups/generar_mockups_e2.py"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from generar_mockups import *  # noqa

ITEMS = ["Panel", "Registrar entrada", "Registrar salida", "Vehículos dentro", "Clientes", "Celdas", "Usuarios", "Historial"]


class L2(Lienzo):
    def barra(self, activo, usuario="Administrador · Administrador"):
        self.rect(0, 34, W, 56, fill=AZUL)
        self.texto(24, 62, "Autos", 18, "white", True, "lm")
        self.texto(80, 62, "Colombia", 18, ACENTO, True, "lm")
        x = 190
        for it in ITEMS:
            w = len(it) * 6.6 + 20
            if it == activo:
                self.rect(x, 44, w, 36, fill="#3a5578", r=6)
            self.centrado(x, 44, w, 36, it, 12, "white" if it == activo else "#dbe6f5")
            x += w + 2
        self.texto(W - 118, 62, usuario, 11, "white", False, "rm")
        self.rect(W - 104, 48, 80, 28, line="#9fb2cc", r=6)
        self.centrado(W - 104, 48, 80, 28, "Salir", 12, "white")

    def pequeno(self, x, y, t, w=None, peligro=False, primario=False):
        w = w or len(t) * 7 + 22
        if peligro:
            self.rect(x, y, w, 26, fill=ROJO, r=5); self.centrado(x, y, w, 26, t, 11, "white", True)
        elif primario:
            self.rect(x, y, w, 26, fill=AZUL, r=5); self.centrado(x, y, w, 26, t, 11, "white", True)
        else:
            self.rect(x, y, w, 26, fill="white", line=AZUL, r=5); self.centrado(x, y, w, 26, t, 11, AZUL, True)
        return w + 8

    def tabla(self, x, y, w, cols, filas, alto=50, fn=None):
        self.rect(x, y, w, 42, fill=AZUL_C)
        for t, cx in cols:
            self.texto(cx, y + 21, t, 13, AZUL, True, "lm")
        for i, f in enumerate(filas):
            yy = y + 42 + i * alto
            self.d.line([x * S, (yy + alto) * S, (x + w) * S, (yy + alto) * S], fill=BORDE, width=S)
            fn(i, f, yy)


def encabezado(c, url, activo, titulo, sub, boton=None):
    c.navegador(url); c.barra(activo); c.titulo(titulo, sub)
    if boton:
        c.boton(1220 - len(boton) * 9 - 40, 108, len(boton) * 9 + 40, 40, boton)


def mk_usuarios():
    c = L2(); encabezado(c, "autoscolombia.local/usuarios", "Usuarios", "Usuarios del sistema", "Cuentas de operarios y administradores.", "+ Nuevo usuario")
    c.tarjeta(60, 175, 1160, 90)
    c.campo(84, 185, 380, "Nombre o usuario", "", h=38); c.campo(484, 185, 200, "Rol", "Todos", h=38); c.campo(704, 185, 200, "Estado", "Todos", h=38)
    c.boton(930, 207, 110, 38, "Buscar")
    c.tarjeta(60, 285, 1160, 270)
    cols = [("Nombre", 84), ("Usuario", 380), ("Rol", 520), ("Estado", 680), ("Acciones", 800)]
    filas = [("Administrador Autos Colombia", "admin", "Administrador", True), ("Carlos Operario", "operario", "Operario", True), ("Ana Pérez", "ana.perez", "Operario", False)]
    def fn(i, f, y):
        c.texto(84, y + 25, f[0], 13, TEXTO, False, "lm"); c.texto(380, y + 25, f[1], 13, TEXTO, False, "lm"); c.texto(520, y + 25, f[2], 13, TEXTO, False, "lm")
        c.chip(680, y + 14, "Activo" if f[3] else "Inactivo", VERDE_F if f[3] else GRIS_F, VERDE_T if f[3] else GRIS_T)
        x = 800; x += c.pequeno(x, y + 12, "Editar"); x += c.pequeno(x, y + 12, "Contraseña")
        c.pequeno(x, y + 12, "Desactivar" if f[3] else "Activar", peligro=f[3], primario=not f[3])
    c.tabla(60, 285, 1160, cols, filas, 52, fn)
    c.etiqueta_historia("HU-07 / HU-10", "Consultar y activar/desactivar"); c.guardar("MK-07_usuarios.png")


def form(c, y0, campos, boton="Guardar", w=540, alto=None):
    alto = alto or (len(campos) * 80 + 90)
    c.tarjeta(60, y0, w, alto)
    y = y0 + 20
    for et, val, ph in campos:
        c.campo(84, y, w - 48, et, val, placeholder=ph); y += 80
    c.boton(84, y + 4, 140, 44, boton); c.boton(238, y + 4, 110, 44, "Cancelar", fill="white", color=AZUL, line=AZUL)


def mk_usuario_form():
    c = L2(); encabezado(c, "autoscolombia.local/usuarios/nuevo", "Usuarios", "Nuevo usuario", "Todos los campos son obligatorios.")
    form(c, 180, [("Nombre completo", "Ana Pérez", False), ("Nombre de usuario", "ana.perez", False), ("Rol", "Operario", False),
                  ("Contraseña (mínimo 8, con letras y números)", "••••••••••", False), ("Confirmar contraseña", "••••••••••", False)])
    c.texto(640, 200, "Estados de la pantalla", 15, AZUL, True)
    for i, t in enumerate(["«La contraseña debe tener al menos 8 caracteres.»", "«Las contraseñas no coinciden.»", "«Ya existe un usuario con el nombre de usuario «ana.perez».»"]):
        c.rect(640, 230 + i * 80, 580, 60, fill=ROJO_F, line="#f0b3ad", r=8); c.texto(656, 260 + i * 80, "Error: " + t, 12, ROJO_T, False, "lm")
    c.rect(640, 470, 580, 60, fill=VERDE_F, line="#9ad4b1", r=8); c.texto(656, 500, "Éxito: «Usuario «ana.perez» creado.»", 12, VERDE_T, False, "lm")
    c.etiqueta_historia("HU-08 / HU-09", "Crear y editar usuario"); c.guardar("MK-08_usuario_nuevo.png")


def mk_clave():
    c = L2(); encabezado(c, "autoscolombia.local/usuarios/3/clave", "Usuarios", "Restablecer contraseña", "Usuario: ana.perez (Ana Pérez)")
    form(c, 180, [("Nueva contraseña (mínimo 8, con letras y números)", "••••••••••", False), ("Confirmar contraseña", "••••••••••", False)], "Restablecer", alto=290)
    c.rect(640, 200, 580, 60, fill=VERDE_F, line="#9ad4b1", r=8); c.texto(656, 230, "Éxito: «Contraseña de «ana.perez» restablecida.»", 12, VERDE_T, False, "lm")
    c.rect(640, 280, 580, 60, fill=ROJO_F, line="#f0b3ad", r=8); c.texto(656, 310, "Error: «La contraseña debe incluir letras y números.»", 12, ROJO_T, False, "lm")
    c.etiqueta_historia("HU-11", "Restablecer contraseña"); c.guardar("MK-09_restablecer_clave.png")


def mk_clientes():
    c = L2(); encabezado(c, "autoscolombia.local/clientes", "Clientes", "Clientes y vehículos", "Propietarios de los vehículos con mensualidad.", "+ Nuevo cliente")
    c.tarjeta(60, 175, 1160, 90); c.campo(84, 185, 600, "Documento, nombre o placa", "", h=38); c.boton(710, 207, 110, 38, "Buscar")
    c.tarjeta(60, 285, 1160, 330)
    cols = [("Documento", 84), ("Cliente", 260), ("Teléfono", 560), ("Vehículos", 720), ("", 1100)]
    filas = [("CC 1012345678", "Laura Gómez Rojas", "3001234567", ["ABC123"]), ("CC 1098765432", "Pedro Ruiz Mora", "3109876543", ["DEF456", "MNO12A"]),
             ("CE 884455", "Marta Salazar", "—", ["PQR34B"]), ("CC 70112233", "Jorge Cano", "3201112233", ["GHI789"])]
    def fn(i, f, y):
        for t, x in zip(f[:3], (84, 260, 560)): c.texto(x, y + 25, t, 13, TEXTO, False, "lm")
        x = 720
        for p in f[3]: c.placa(x, y + 14, p); x += len(p) * 10 + 28
        c.pequeno(1100, y + 12, "Ver")
    c.tabla(60, 285, 1160, cols, filas, 56, fn)
    c.texto(W / 2 + 30, 585, "Página 1 de 1", 12, GRIS, False, "mm")
    c.etiqueta_historia("HU-14", "Consultar clientes y vehículos"); c.guardar("MK-10_clientes.png")


def mk_cliente_form():
    c = L2(); encabezado(c, "autoscolombia.local/clientes/nuevo", "Clientes", "Nuevo cliente", "Después de guardar podrá agregar sus vehículos.")
    c.tarjeta(60, 180, 640, 440)
    c.campo(84, 200, 130, "Tipo", "CC"); c.campo(230, 200, 446, "Número de documento", "1012345678")
    c.campo(84, 280, 300, "Nombres", "Laura"); c.campo(400, 280, 276, "Apellidos", "Gómez Rojas")
    c.campo(84, 360, 300, "Teléfono (opcional)", "3001234567"); c.campo(400, 360, 276, "Correo (opcional)", "laura@correo.com")
    c.boton(84, 470, 140, 44, "Guardar"); c.boton(238, 470, 110, 44, "Cancelar", fill="white", color=AZUL, line=AZUL)
    for i, t in enumerate(["«Ya existe un cliente con ese documento.»", "«El correo electrónico no es válido.»"]):
        c.rect(740, 200 + i * 80, 480, 60, fill=ROJO_F, line="#f0b3ad", r=8); c.texto(756, 230 + i * 80, "Error: " + t.replace("(ejemplo: nombre@dominio.com)", ""), 11, ROJO_T, False, "lm")
    c.etiqueta_historia("HU-12", "Registrar cliente"); c.guardar("MK-11_cliente_nuevo.png")


def mk_detalle():
    c = L2(); encabezado(c, "autoscolombia.local/clientes/1", "Clientes", "Laura Gómez Rojas", "")
    c.boton(1060, 108, 160, 40, "Editar datos", fill="white", color=AZUL, line=AZUL)
    c.tarjeta(60, 165, 1160, 80); c.texto(84, 190, "Documento: CC 1012345678", 14); c.texto(84, 218, "Teléfono: 3001234567     Correo: laura@correo.com", 14)
    c.texto(60, 275, "Vehículos", 20, AZUL, True); c.boton(1000, 262, 220, 40, "+ Agregar vehículo")
    c.tarjeta(60, 315, 1160, 230)
    cols = [("Placa", 84), ("Tipo", 230), ("Marca / color", 340), ("Mensualidad", 560), ("Acciones", 880)]
    filas = [("ABC123", "Carro", "Mazda 3 / Rojo", True), ("XYZ987", "Moto", "Yamaha / Negro", False)]
    def fn(i, f, y):
        c.placa(84, y + 14, f[0]); c.texto(230, y + 25, f[1], 13, TEXTO, False, "lm"); c.texto(340, y + 25, f[2], 13, TEXTO, False, "lm")
        if f[3]: c.chip(560, y + 14, "Vigente hasta 04/12/2026", VERDE_F, VERDE_T)
        else: c.chip(560, y + 14, "Sin mensualidad", GRIS_F, GRIS_T)
        x = 880; x += c.pequeno(x, y + 12, "Editar")
        if not f[3]: c.pequeno(x, y + 12, "Activar mensualidad (30 días)", primario=True)
    c.tabla(60, 315, 1160, cols, filas, 60, fn)
    c.rect(60, 580, 700, 56, fill=VERDE_F, line="#9ad4b1", r=8)
    c.texto(76, 608, "Éxito: «Mensualidad activada para XYZ987: 14/11/2026 al 13/12/2026.»", 12, VERDE_T, False, "lm")
    c.rect(780, 580, 440, 56, fill=ROJO_F, line="#f0b3ad", r=8)
    c.texto(796, 608, "Error si ya hay una vigente (una sola por vehículo)", 12, ROJO_T, False, "lm")
    c.etiqueta_historia("HU-13 / HU-15", "Vehículos y mensualidad"); c.guardar("MK-12_cliente_detalle.png")


def mk_vehiculo():
    c = L2(); encabezado(c, "autoscolombia.local/clientes/1/vehiculos/nuevo", "Clientes", "Nuevo vehículo", "Cliente: Laura Gómez Rojas")
    form(c, 180, [("Placa", "XYZ987", False), ("Tipo de vehículo", "Moto", False), ("Marca (opcional)", "Yamaha", False), ("Color (opcional)", "Negro", False)])
    for i, t in enumerate(["«La placa XYZ987 ya está registrada.»", "«La placa debe tener entre 5 y 7 caracteres alfanuméricos.»", "«Seleccione el tipo de vehículo (carro o moto).»"]):
        c.rect(640, 200 + i * 80, 580, 60, fill=ROJO_F, line="#f0b3ad", r=8); c.texto(656, 230 + i * 80, "Error: " + t, 12, ROJO_T, False, "lm")
    c.etiqueta_historia("HU-13", "Registrar vehículo"); c.guardar("MK-13_vehiculo_nuevo.png")


def mk_celdas():
    c = L2(); encabezado(c, "autoscolombia.local/celdas", "Celdas", "Celdas del parqueadero", "Administración de las 80 celdas.", "+ Nueva celda")
    c.tarjeta(60, 175, 1160, 90)
    c.campo(84, 185, 300, "Código", "", h=38); c.campo(404, 185, 220, "Tipo", "Todos", h=38); c.campo(644, 185, 220, "Estado", "Todos", h=38); c.boton(890, 207, 110, 38, "Buscar")
    c.tarjeta(60, 285, 1160, 330)
    cols = [("Código", 84), ("Tipo", 260), ("Estado", 420), ("Acciones", 640)]
    filas = [("C-01", "Carro", "OCUPADA"), ("C-02", "Carro", "LIBRE"), ("C-11", "Carro", "MANTENIMIENTO"), ("M-01", "Moto", "LIBRE"), ("X-01", "Carro", "LIBRE")]
    est = {"LIBRE": (VERDE_F, VERDE_T, "Libre"), "OCUPADA": (ROJO_F, ROJO_T, "Ocupada"), "MANTENIMIENTO": (GRIS_F, GRIS_T, "Mantenimiento")}
    def fn(i, f, y):
        c.texto(84, y + 21, f[0], 13, TEXTO, True, "lm"); c.texto(260, y + 21, f[1], 13, TEXTO, False, "lm")
        fo, co, n = est[f[2]]; c.chip(420, y + 10, n, fo, co)
        if f[2] == "OCUPADA": c.texto(640, y + 21, "Vehículo dentro", 12, GRIS, False, "lm"); return
        x = 640; x += c.pequeno(x, y + 8, "Editar"); x += c.pequeno(x, y + 8, "Habilitar" if f[2] == "MANTENIMIENTO" else "Mantenimiento"); c.pequeno(x, y + 8, "Eliminar", peligro=True)
    c.tabla(60, 285, 1160, cols, filas, 44, fn)
    c.etiqueta_historia("HU-16 / HU-19 / HU-20", "Consultar y administrar celdas"); c.guardar("MK-14_celdas.png")


def mk_celda_form():
    c = L2(); encabezado(c, "autoscolombia.local/celdas/nueva", "Celdas", "Nueva celda", "El código debe ser único (ej. C-71, M-11).")
    form(c, 180, [("Código", "C-71", False), ("Tipo de celda", "Carro", False)], alto=290)
    for i, t in enumerate(["«Ya existe una celda con el código C-71.»", "«El código debe tener máximo 10 caracteres…»", "«La celda C-01 está ocupada: no se puede modificar…»"]):
        c.rect(640, 200 + i * 80, 580, 60, fill=ROJO_F, line="#f0b3ad", r=8); c.texto(656, 230 + i * 80, "Error: " + t, 12, ROJO_T, False, "lm")
    c.etiqueta_historia("HU-17 / HU-18", "Crear y editar celda"); c.guardar("MK-15_celda_nueva.png")


if __name__ == "__main__":
    for f in (mk_usuarios, mk_usuario_form, mk_clave, mk_clientes, mk_cliente_form, mk_detalle, mk_vehiculo, mk_celdas, mk_celda_form):
        f()
