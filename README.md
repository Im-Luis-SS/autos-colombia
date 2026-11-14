# Autos Colombia – Sistema de información del parqueadero

**Iteración 1: entrada y salida de vehículos. Iteración 2: gestión de usuarios, clientes/vehículos/mensualidad y celdas.**
Aplicación web hecha con Python 3, Flask y MySQL.

## Qué hace esta iteración

- Inicio de sesión con roles (Operario / Administrador).
- Registro de **entrada**: valida placa, mensualidad vigente y que el vehículo no esté ya dentro; asigna celda libre del tipo correcto (automática o elegida).
- Registro de **salida**: cierra el movimiento abierto y libera la celda.
- Panel de ocupación de celdas (80 celdas: 70 de carro C-01..C-70 y 10 de moto M-01..M-10), listado de vehículos dentro e historial de movimientos con filtros (solo Administrador).

## Qué agrega la iteración 2 (solo Administrador)

- **Usuarios:** crear, editar, activar/desactivar y restablecer contraseña (siempre queda un administrador activo).
- **Clientes y vehículos:** registrar, buscar y editar; **mensualidad única de 30 días** por vehículo.
- **Celdas:** crear, editar, poner en mantenimiento/habilitar y eliminar (si no tienen historial).
- Protección CSRF en todos los formularios.

> Los pagos corresponden a la siguiente iteración.

## Estructura

```
app/
  models/      entidades (SQLAlchemy)
  services/    reglas de negocio (AuthService, MovimientoService, OcupacionService)
  routes/      blueprints Flask (presentación)
  templates/   vistas Jinja2
  static/      CSS
db/schema.sql  modelo físico para MySQL
diagrams/      fuentes PlantUML (.puml) y sus imágenes
tests/         pruebas automáticas (pytest)
run.py         punto de entrada
```

## Puesta en marcha

1. Requisitos: Python 3.10+ y MySQL 8 (MySQL Workbench sirve para administrarlo).
2. Instalar dependencias:
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Crear la base de datos. Opción A (recomendada): abrir `db/schema.sql` en MySQL Workbench y ejecutarlo. Opción B: dejar que Flask cree las tablas con `flask --app run init-db` (después de crear el esquema vacío `autos_colombia`).
4. Configurar la conexión (ajuste usuario y clave):
   ```bash
   export DATABASE_URL="mysql+pymysql://root:SU_CLAVE@localhost:3306/autos_colombia?charset=utf8mb4"
   export SECRET_KEY="una-clave-larga"
   # Windows PowerShell: $env:DATABASE_URL="..."
   ```
5. Cargar datos de ejemplo y arrancar:
   ```bash
   flask --app run seed
   python run.py
   ```
6. Abrir http://127.0.0.1:5000

| Usuario | Contraseña | Rol |
|---|---|---|
| admin | admin123 | Administrador |
| operario | operario123 | Operario |

Placas de ejemplo: `ABC123`, `DEF456` (carros con mensualidad), `MNO12A`, `PQR34B` (motos), `GHI789` (mensualidad vencida → se rechaza).

## Pruebas

```bash
python -m pytest -q
```
Por defecto usan SQLite (en memoria y en un archivo temporal), así que no necesitan MySQL.
Para correr **todas** las pruebas sobre MySQL, defina `TEST_DATABASE_URL` (ver abajo) y ejecute `python -m pytest -q`.

### Pruebas de concurrencia sobre MySQL

`tests/test_concurrencia.py` lanza varios hilos a la vez (varios operarios) para comprobar que
nunca queden dos movimientos abiertos del mismo vehículo o de la misma celda. Para correrlas
sobre MySQL, el motor real del proyecto:

1. En MySQL Workbench crea una base de pruebas: `CREATE DATABASE autos_colombia_test;`
2. En la terminal (Windows):
   ```
   set TEST_DATABASE_URL=mysql+pymysql://root:CLAVE@localhost:3306/autos_colombia_test?charset=utf8mb4
   python -m pytest tests/test_concurrencia.py -v
   ```

La base debe terminar en `_test`: la prueba borra y recrea sus tablas y se niega a correr contra
otra (así nunca toca `autos_colombia`).
