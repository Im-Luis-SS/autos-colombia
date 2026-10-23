"""Comandos de línea: crear tablas y cargar datos de ejemplo.

    flask --app run init-db
    flask --app run seed
"""
from datetime import date, timedelta

import click

from app.extensions import db
from app.models import Celda, Cliente, Mensualidad, UsuarioSistema, Vehiculo


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
    for doc, nombres, apellidos, tel, vehiculos in datos:
        cliente = Cliente(
            tipo_documento="CC", numero_documento=doc, nombres=nombres,
            apellidos=apellidos, telefono=tel,
        )
        db.session.add(cliente)
        for placa, tipo, marca, color, estado, ini, fin in vehiculos:
            vehiculo = Vehiculo(placa=placa, tipo=tipo, marca=marca, color=color, cliente=cliente)
            vehiculo.mensualidades.append(
                Mensualidad(
                    fecha_inicio=hoy + timedelta(days=ini),
                    fecha_fin=hoy + timedelta(days=fin),
                    estado=estado,
                )
            )
            db.session.add(vehiculo)

    for i in range(1, 11):
        db.session.add(Celda(codigo=f"C-{i:02d}", tipo="CARRO", estado="LIBRE"))
    for i in range(1, 6):
        db.session.add(Celda(codigo=f"M-{i:02d}", tipo="MOTO", estado="LIBRE"))
    db.session.add(Celda(codigo="C-11", tipo="CARRO", estado="MANTENIMIENTO"))

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
