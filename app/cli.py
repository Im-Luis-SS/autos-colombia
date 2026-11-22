"""Comandos de línea: crear tablas y cargar datos de ejemplo.

    flask --app run init-db
    flask --app run seed
"""
from datetime import date, datetime, time, timedelta

import click

from app.extensions import db
from app.models import Celda, Cliente, Mensualidad, Pago, Tarifa, UsuarioSistema, Vehiculo


CELDAS_CARRO = 70
CELDAS_MOTO = 10


TARIFAS_EJEMPLO = {"CARRO": 150_000, "MOTO": 70_000}


def cargar_datos_ejemplo():
    """Inserta usuarios, clientes, vehículos, mensualidades y celdas de demostración."""
    if UsuarioSistema.query.first():
        return False

    admin = UsuarioSistema(nombre="Administrador Autos Colombia", username="admin", rol="ADMINISTRADOR")
    admin.set_clave("admin123")
    operario = UsuarioSistema(nombre="Carlos Operario", username="operario", rol="OPERARIO")
    operario.set_clave("operario123")
    db.session.add_all([admin, operario])

    hoy = date.today()
    datos = [
        # (documento, nombres, apellidos, telefono, [(placa, tipo, marca, color, estado, inicio_dias, fin_dias)])
        ("1012345678", "Laura", "Gómez Rojas", "3001234567",
         [("ABC123", "CARRO", "Mazda 3", "Rojo", "ACTIVA", -10, 20)]),
        ("80123456", "Andrés", "Pérez Díaz", "3109876543",
         [("DEF456", "CARRO", "Renault Logan", "Gris", "ACTIVA", -5, 25),
          ("MNO12A", "MOTO", "Yamaha FZ", "Negro", "ACTIVA", -5, 25)]),
        ("52987654", "Marcela", "Torres Silva", "3205554433",
         [("GHI789", "CARRO", "Chevrolet Spark", "Blanco", "VENCIDA", -60, -30)]),
        ("1098765432", "Julián", "Ramírez Cruz", "3157778899",
         [("PQR34B", "MOTO", "Honda CB125", "Azul", "ACTIVA", -2, 28)]),
    ]
    n_pago = 0
    for tipo, valor in TARIFAS_EJEMPLO.items():
        db.session.add(Tarifa(tipo_vehiculo=tipo, valor=valor))
    for doc, nombres, apellidos, tel, vehiculos in datos:
        cliente = Cliente(
            tipo_documento="CC", numero_documento=doc, nombres=nombres,
            apellidos=apellidos, telefono=tel,
        )
        db.session.add(cliente)
        for placa, tipo, marca, color, estado, ini, fin in vehiculos:
            vehiculo = Vehiculo(placa=placa, tipo=tipo, marca=marca, color=color, cliente=cliente)
            mensualidad = Mensualidad(
                fecha_inicio=hoy + timedelta(days=ini),
                fecha_fin=hoy + timedelta(days=fin),
                estado=estado,
            )
            vehiculo.mensualidades.append(mensualidad)
            db.session.add(vehiculo)
            # Cada mensualidad de ejemplo ya tiene su pago (efectivo o transferencia).
            n_pago += 1
            transferencia = n_pago % 2 == 0
            db.session.add(
                Pago(
                    mensualidad=mensualidad,
                    valor=TARIFAS_EJEMPLO[tipo],
                    medio="TRANSFERENCIA" if transferencia else "EFECTIVO",
                    referencia=f"TRF-{1000 + n_pago}" if transferencia else None,
                    fecha_hora=datetime.combine(mensualidad.fecha_inicio, time(9, 0)),
                    estado="REGISTRADO",
                    usuario=admin,
                )
            )

    # 80 celdas: 70 para carros (C-01..C-70) y 10 para motos (M-01..M-10), todas libres.
    for i in range(1, CELDAS_CARRO + 1):
        db.session.add(Celda(codigo=f"C-{i:02d}", tipo="CARRO", estado="LIBRE"))
    for i in range(1, CELDAS_MOTO + 1):
        db.session.add(Celda(codigo=f"M-{i:02d}", tipo="MOTO", estado="LIBRE"))

    db.session.commit()
    return True


def registrar_comandos(app):
    @app.cli.command("init-db")
    def init_db():
        """Crea las tablas (si no existen)."""
        db.create_all()
        click.echo("Tablas creadas.")

    @app.cli.command("seed")
    def seed():
        """Carga datos de ejemplo (usuarios, vehículos, celdas)."""
        db.create_all()
        if cargar_datos_ejemplo():
            click.echo("Datos de ejemplo cargados. Usuarios: admin/admin123 y operario/operario123")
        else:
            click.echo("La base de datos ya tiene datos; no se cargó nada.")
