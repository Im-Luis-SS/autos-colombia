"""Genera los mockups (wireframes de alta fidelidad) de las historias de usuario.

Uso:  python mockups/generar_mockups.py
Salida: mockups/MK-01_login.png ... MK-06_historial.png
Nota: el entregable pide Figma; estas imágenes sirven de guía exacta para
recrear cada pantalla allí (colores, tamaños y textos están definidos aquí).
"""
import os
from PIL import Image, ImageDraw, ImageFont

S = 2  # factor de escala (imágenes nítidas)
W, H = 1280, 780
AZUL, AZUL_C, ACENTO = "#1f3a5f", "#e8eff8", "#e8a317"
VERDE_F, VERDE_B, VERDE_T = "#e6f5ec", "#7cc79a", "#145c34"
ROJO, ROJO_F, ROJO_B, ROJO_T = "#c0392b", "#fdeceb", "#e59a92", "#8c231a"
GRIS_F, GRIS_B, GRIS_T = "#eceff3", "#b8c0cc", "#4b5563"
GRIS, BORDE, FONDO, TEXTO = "#5f6b7a", "#d5dce6", "#f5f7fa", "#1c2733"

FR = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FB = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
_cache = {}


def fuente(tam, negrita=False):
    k = (tam, negrita)
    if k not in _cache:
        _cache[k] = ImageFont.truetype(FB if negrita else FR, int(tam * S))
    return _cache[k]


class Lienzo:
    def __init__(self):
        self.img = Image.new("RGB", (W * S, H * S), FONDO)
        self.d = ImageDraw.Draw(self.img)

    # primitivas (coordenadas lógicas, se escalan aquí)
    def rect(self, x, y, w, h, fill=None, line=None, r=0, lw=1):
        box = [x * S, y * S, (x + w) * S, (y + h) * S]
        if r:
            self.d.rounded_rectangle(box, r * S, fill=fill, outline=line, width=lw * S)
        else:
            self.d.rectangle(box, fill=fill, outline=line, width=lw * S)

    def texto(self, x, y, t, tam=14, color=TEXTO, negrita=False, ancla="la"):
        self.d.text((x * S, y * S), t, font=fuente(tam, negrita), fill=color, anchor=ancla)

    def centrado(self, x, y, w, h, t, tam=14, color=TEXTO, negrita=False):
        self.d.text(((x + w / 2) * S, (y + h / 2) * S), t, font=fuente(tam, negrita), fill=color, anchor="mm")

    def boton(self, x, y, w, h, t, fill=AZUL, color="white", line=None):
        self.rect(x, y, w, h, fill=fill, line=line, r=6, lw=1)
        self.centrado(x, y, w, h, t, 14, color, True)

    def campo(self, x, y, w, etiqueta, valor="", h=40, placeholder=False, alto_extra=0):
        self.texto(x, y, etiqueta, 13, TEXTO, True)
        self.rect(x, y + 22, w, h + alto_extra, fill="white", line="#b9c4d3", r=6)
        self.texto(x + 12, y + 22 + (h + alto_extra) / 2, valor, 14, "#9aa5b4" if placeholder else TEXTO, False, "lm")

    def placa(self, x, y, t):
        w = len(t) * 10 + 18
        self.rect(x, y, w, 22, fill="#ffd34d", line="#222", r=4, lw=2)
        self.centrado(x, y, w, 22, t, 12, "#111", True)

    def chip(self, x, y, t, fondo, color):
        w = len(t) * 7 + 22
        self.rect(x, y, w, 22, fill=fondo, r=11)
        self.centrado(x, y, w, 22, t, 11, color, True)

    def navegador(self, url):
        self.rect(0, 0, W, 34, fill="#dde3ec")
        for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
            self.d.ellipse([(16 + i * 20) * S, 12 * S, (28 + i * 20) * S, 24 * S], fill=c)
        self.rect(100, 6, 640, 22, fill="white", r=11)
        self.texto(116, 17, url, 12, GRIS, False, "lm")

    def barra(self, activo, admin=True, usuario="Carlos Operario · Operario"):
        self.rect(0, 34, W, 56, fill=AZUL)
        self.texto(24, 62, "Autos", 18, "white", True, "lm")
        self.texto(80, 62, "Colombia", 18, ACENTO, True, "lm")
        items = ["Panel", "Registrar entrada", "Registrar salida", "Vehículos dentro"]
        if admin:
            items.append("Historial")
        x = 220
        for it in items:
            w = len(it) * 7.6 + 28
            if it == activo:
                self.rect(x, 44, w, 36, fill="#3a5578", r=6)
            self.centrado(x, 44, w, 36, it, 13, "white" if it == activo else "#dbe6f5")
            x += w + 4
        self.texto(W - 130, 62, usuario, 12, "white", False, "rm")
        self.rect(W - 112, 48, 88, 28, line="#9fb2cc", r=6)
        self.centrado(W - 112, 48, 88, 28, "Salir", 12, "white")

    def titulo(self, t, sub):
        self.texto(60, 112, t, 24, AZUL, True)
        self.texto(60, 148, sub, 14, GRIS)

    def tarjeta(self, x, y, w, h):
        self.rect(x, y, w, h, fill="white", line=BORDE, r=10)

    def etiqueta_historia(self, codigo, nombre):
        self.rect(W - 330, H - 44, 310, 30, fill="#fff6e0", line="#f0d28a", r=6)
        self.centrado(W - 330, H - 44, 310, 30, f"{codigo} · {nombre}", 12, "#7a5a00", True)

    def guardar(self, nombre):
        ruta = os.path.join(os.path.dirname(__file__), nombre)
        self.img.save(ruta)
        print("ok", nombre)


def mk_login():
    c = Lienzo()
    c.navegador("autoscolombia.local/login")
    c.texto(W / 2, 175, "Autos", 34, AZUL, True, "rm")
    c.texto(W / 2 + 4, 175, "Colombia", 34, ACENTO, True, "lm")
    c.texto(W / 2, 212, "Sistema de gestión del parqueadero", 15, GRIS, False, "mm")
    c.tarjeta(450, 250, 380, 330)
    c.campo(480, 275, 320, "Usuario", "operario")
    c.campo(480, 355, 320, "Contraseña", "••••••••••")
    c.boton(480, 450, 320, 44, "Ingresar")
    c.texto(W / 2, 530, "¿Problemas para ingresar? Contacte al administrador.", 12, GRIS, False, "mm")
    c.rect(450, 600, 380, 44, fill=ROJO_F, line=ROJO_B, r=8)
    c.texto(466, 622, "Estado de error: «Usuario o contraseña incorrectos.»", 12, ROJO_T, False, "lm")
    c.etiqueta_historia("HU-01", "Iniciar sesión")
    c.guardar("MK-01_login.png")


def mk_panel():
    c = Lienzo()
    c.navegador("autoscolombia.local/")
    c.barra("Panel")
    c.titulo("Panel de ocupación", "Estado actual de las celdas del parqueadero.")
    mets = [("5", "Ocupadas"), ("10", "Libres"), ("7 / 11", "Carros libres"), ("3 / 5", "Motos libres")]
    for i, (v, e) in enumerate(mets):
        x = 60 + i * 295
        c.rect(x, 185, 275, 88, fill="white", line=BORDE, r=10)
        c.texto(x + 18, 218, v, 30, AZUL, True, "lm")
        c.texto(x + 18, 254, e.upper(), 11, GRIS, True, "lm")
    c.tarjeta(60, 295, 1160, 300)
    estados = {"C-01": "O", "C-02": "O", "C-03": "O", "C-11": "M", "M-02": "O", "M-04": "O"}
    codigos = [f"C-{i:02d}" for i in range(1, 12)] + [f"M-{i:02d}" for i in range(1, 6)]
    for i, cod in enumerate(codigos):
        col, fila = i % 8, i // 8
        x, y = 84 + col * 140, 320 + fila * 80
        est = estados.get(cod, "L")
        f, b, t, n = {"L": (VERDE_F, VERDE_B, VERDE_T, "Libre"), "O": (ROJO_F, ROJO_B, ROJO_T, "Ocupada"),
                      "M": (GRIS_F, GRIS_B, GRIS_T, "Mantenimiento")}[est]
        c.rect(x, y, 120, 62, fill=f, line=b, r=8, lw=2)
        c.centrado(x, y + 6, 120, 30, cod, 15, t, True)
        c.centrado(x, y + 34, 120, 20, n, 11, t)
    c.boton(60, 620, 170, 42, "Registrar entrada")
    c.boton(244, 620, 170, 42, "Registrar salida", fill=ROJO)
    c.etiqueta_historia("HU-06", "Ver ocupación de celdas")
    c.guardar("MK-02_panel.png")


def mk_entrada():
    c = Lienzo()
    c.navegador("autoscolombia.local/entrada")
    c.barra("Registrar entrada")
    c.titulo("Registrar entrada de vehículo", "Se valida la mensualidad y se asigna una celda libre del tipo del vehículo.")
    c.tarjeta(60, 185, 540, 430)
    c.texto(84, 205, "Placa", 13, TEXTO, True)
    c.rect(84, 227, 492, 52, fill="white", line="#b9c4d3", r=6)
    c.centrado(84, 227, 492, 52, "A B C 1 2 3", 24, TEXTO, True)
    c.campo(84, 295, 492, "Celda (opcional)", "Vacío = asignación automática", placeholder=True)
    c.campo(84, 375, 492, "Observaciones (opcional)", "Ej. Raspón en puerta derecha", placeholder=True, alto_extra=50)
    c.boton(84, 535, 190, 44, "Registrar entrada")
    c.boton(288, 535, 110, 44, "Cancelar", fill="white", color=AZUL, line=AZUL)
    # estados
    c.texto(640, 205, "Estados de la pantalla", 15, AZUL, True)
    c.rect(640, 235, 580, 70, fill=VERDE_F, line="#9ad4b1", r=8)
    c.texto(656, 270, "Éxito: «Entrada registrada: ABC123 en la celda C-01 (20/10/2026 19:06).»", 12, VERDE_T, False, "lm")
    c.rect(640, 320, 580, 70, fill=ROJO_F, line="#f0b3ad", r=8)
    c.texto(656, 355, "Error: «El vehículo GHI789 no tiene una mensualidad vigente.»", 12, ROJO_T, False, "lm")
    c.rect(640, 405, 580, 70, fill=ROJO_F, line="#f0b3ad", r=8)
    c.texto(656, 440, "Error: «El vehículo ABC123 ya se encuentra dentro del parqueadero.»", 12, ROJO_T, False, "lm")
    c.rect(640, 490, 580, 70, fill="#fff6e0", line="#f0d28a", r=8)
    c.texto(656, 525, "Error: «No hay celdas libres para carros en este momento.»", 12, "#7a5a00", False, "lm")
    c.etiqueta_historia("HU-02", "Registrar entrada")
    c.guardar("MK-03_entrada.png")


def mk_salida():
    c = Lienzo()
    c.navegador("autoscolombia.local/salida")
    c.barra("Registrar salida")
    c.titulo("Registrar salida de vehículo", "Se cierra el movimiento abierto del vehículo y se libera su celda.")
    c.tarjeta(60, 185, 540, 400)
    c.texto(84, 205, "Placa", 13, TEXTO, True)
    c.rect(84, 227, 492, 52, fill="white", line="#b9c4d3", r=6)
    c.centrado(84, 227, 492, 52, "A B C 1 2 3", 24, TEXTO, True)
    c.campo(84, 295, 492, "Observaciones (opcional)", "Ej. Salida con acompañante", placeholder=True, alto_extra=50)
    c.boton(84, 440, 190, 44, "Registrar salida", fill=ROJO)
    c.boton(288, 440, 110, 44, "Cancelar", fill="white", color=AZUL, line=AZUL)
    c.texto(640, 205, "Estados de la pantalla", 15, AZUL, True)
    c.rect(640, 235, 580, 80, fill=VERDE_F, line="#9ad4b1", r=8)
    c.texto(656, 262, "Éxito: «Salida registrada: ABC123 salió de la celda C-01.", 12, VERDE_T, False, "lm")
    c.texto(656, 286, "Permanencia: 3 h 25 min.»", 12, VERDE_T, False, "lm")
    c.rect(640, 330, 580, 70, fill=ROJO_F, line="#f0b3ad", r=8)
    c.texto(656, 365, "Error: «El vehículo ABC123 no tiene una entrada registrada…»", 12, ROJO_T, False, "lm")
    c.etiqueta_historia("HU-03", "Registrar salida")
    c.guardar("MK-04_salida.png")


def mk_dentro():
    c = Lienzo()
    c.navegador("autoscolombia.local/dentro")
    c.barra("Vehículos dentro")
    c.titulo("Vehículos en el parqueadero", "Vehículos con entrada registrada y sin salida.")
    c.tarjeta(60, 185, 1160, 90)
    c.campo(84, 195, 700, "Buscar por placa", "ABC123", h=38)
    c.boton(810, 217, 110, 38, "Buscar")
    c.tarjeta(60, 295, 1160, 360)
    cols = [("Placa", 84), ("Tipo", 230), ("Cliente", 340), ("Celda", 600), ("Entrada", 720), ("Tiempo dentro", 960)]
    c.rect(60, 295, 1160, 42, fill=AZUL_C)
    for t, x in cols:
        c.texto(x, 316, t, 13, AZUL, True, "lm")
    filas = [("ABC123", "Carro", "Laura Gómez Rojas", "C-01", "20/10/2026 15:40", "3 h 25 min"),
             ("DEF456", "Carro", "Andrés Pérez Díaz", "C-02", "20/10/2026 16:05", "3 h 00 min"),
             ("MNO12A", "Moto", "Andrés Pérez Díaz", "M-02", "20/10/2026 17:30", "1 h 35 min"),
             ("PQR34B", "Moto", "Julián Ramírez Cruz", "M-04", "20/10/2026 18:10", "0 h 55 min")]
    for i, f in enumerate(filas):
        y = 337 + i * 52
        c.d.line([60 * S, (y + 52) * S, 1220 * S, (y + 52) * S], fill=BORDE, width=S)
        c.placa(84, y + 15, f[0])
        for (t, x), v in zip(cols[1:], f[1:]):
            c.texto(x, y + 26, v, 13, TEXTO, False, "lm")
    c.texto(84, 635, "Total: 4", 13, GRIS, False, "lm")
    c.etiqueta_historia("HU-04", "Ver vehículos en el parqueadero")
    c.guardar("MK-05_vehiculos_dentro.png")


def mk_historial():
    c = Lienzo()
    c.navegador("autoscolombia.local/historial")
    c.barra("Historial", usuario="Administrador · Administrador")
    c.titulo("Historial de movimientos", "Todas las entradas y salidas registradas (solo administradores).")
    c.tarjeta(60, 185, 1160, 90)
    c.campo(84, 195, 300, "Placa", "ABC123", h=38)
    c.campo(404, 195, 220, "Desde", "01/10/2026", h=38)
    c.campo(644, 195, 220, "Hasta", "20/10/2026", h=38)
    c.boton(890, 217, 110, 38, "Filtrar")
    c.tarjeta(60, 295, 1160, 360)
    cols = [("Placa", 80), ("Celda", 200), ("Entrada", 270), ("Salida", 420), ("Permanencia", 570),
            ("Operario (ent./sal.)", 700), ("Observaciones", 890)]
    c.rect(60, 295, 1160, 42, fill=AZUL_C)
    for t, x in cols:
        c.texto(x, 316, t, 13, AZUL, True, "lm")
    filas = [("ABC123", "C-01", "20/10 15:40", None, "3 h 25 min", "operario", "Rayón puerta"),
             ("DEF456", "C-02", "19/10 08:02", "19/10 17:45", "9 h 43 min", "operario / admin", "—"),
             ("ABC123", "C-03", "19/10 07:55", "19/10 18:10", "10 h 15 min", "admin / admin", "—"),
             ("MNO12A", "M-01", "18/10 09:10", "18/10 13:40", "4 h 30 min", "operario / operario", "—")]
    for i, f in enumerate(filas):
        y = 337 + i * 52
        c.d.line([60 * S, (y + 52) * S, 1220 * S, (y + 52) * S], fill=BORDE, width=S)
        c.placa(80, y + 15, f[0])
        for (t, x), v in list(zip(cols, f))[1:]:
            if t == "Salida" and v is None:
                c.chip(x, y + 15, "Dentro", "#fff6e0", "#7a5a00")
            else:
                c.texto(x, y + 26, v, 12, TEXTO, False, "lm")
    c.texto(W / 2 + 30, 628, "← Anterior      Página 1 de 3 · 41 registros      Siguiente →", 12, GRIS, False, "mm")
    c.etiqueta_historia("HU-05", "Consultar historial de movimientos")
    c.guardar("MK-06_historial.png")


if __name__ == "__main__":
    mk_login(); mk_panel(); mk_entrada(); mk_salida(); mk_dentro(); mk_historial()
