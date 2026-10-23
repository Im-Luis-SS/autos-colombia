# Autos Colombia – Sistema de información del parqueadero

**Iteración 1: Gestión de la entrada y salida de vehículos.**
Aplicación web hecha con Python 3, Flask y MySQL.

## Qué hace esta iteración

- Inicio de sesión con roles (Operario / Administrador).
- Registro de **entrada**: valida placa, mensualidad vigente y que el vehículo no esté ya dentro; asigna celda libre del tipo correcto (automática o elegida).
- Registro de **salida**: cierra el movimiento abierto y libera la celda.
- Panel de ocupación de celdas, listado de vehículos dentro e historial de movimientos con filtros (solo Administrador).

> Los clientes, vehículos y mensualidades llegan por datos de ejemplo (`flask seed`). Su gestión completa (CRUD) y los pagos corresponden a las siguientes iteraciones.

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
Las pruebas usan SQLite en memoria, no necesitan MySQL.

## Publicar en GitHub

```bash
git init
git add .
git commit -m "Iteración 1: gestión de entrada y salida de vehículos"
git branch -M main
git remote add origin https://github.com/<su-usuario>/autos-colombia.git
git push -u origin main
```
