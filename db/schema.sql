-- =====================================================================
--  Parqueadero "Autos Colombia" - Iteraciones 1 a 3: entrada/salida, usuarios/celdas y pagos
--  Modelo físico para MySQL 8.0+ (InnoDB, utf8mb4)
--  Uso en MySQL Workbench: File > Open SQL Script > ejecutar todo (rayo).
--  Para ver el diagrama EER: Database > Reverse Engineer...
-- =====================================================================

DROP DATABASE IF EXISTS autos_colombia;
CREATE DATABASE autos_colombia
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
USE autos_colombia;

-- ---------------------------------------------------------------------
-- Usuarios del sistema (quienes operan el software)
-- ---------------------------------------------------------------------
CREATE TABLE usuario_sistema (
  id_usuario     INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nombre         VARCHAR(100) NOT NULL,
  username       VARCHAR(50)  NOT NULL,
  password_hash  VARCHAR(255) NOT NULL,
  rol            ENUM('OPERARIO','ADMINISTRADOR') NOT NULL,
  activo         TINYINT(1)   NOT NULL DEFAULT 1,
  PRIMARY KEY (id_usuario),
  UNIQUE KEY uq_usuario_username (username)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Clientes (propietarios con mensualidad)
-- ---------------------------------------------------------------------
CREATE TABLE cliente (
  id_cliente        INT UNSIGNED NOT NULL AUTO_INCREMENT,
  tipo_documento    ENUM('CC','CE','NIT','PAS') NOT NULL,
  numero_documento  VARCHAR(20)  NOT NULL,
  nombres           VARCHAR(100) NOT NULL,
  apellidos         VARCHAR(100) NOT NULL,
  telefono          VARCHAR(20)  NULL,
  email             VARCHAR(120) NULL,
  PRIMARY KEY (id_cliente),
  UNIQUE KEY uq_cliente_documento (tipo_documento, numero_documento)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Vehículos
-- ---------------------------------------------------------------------
CREATE TABLE vehiculo (
  id_vehiculo  INT UNSIGNED NOT NULL AUTO_INCREMENT,
  placa        VARCHAR(10)  NOT NULL,
  tipo         ENUM('CARRO','MOTO') NOT NULL,
  marca        VARCHAR(50)  NULL,
  color        VARCHAR(30)  NULL,
  id_cliente   INT UNSIGNED NOT NULL,
  PRIMARY KEY (id_vehiculo),
  UNIQUE KEY uq_vehiculo_placa (placa),
  KEY ix_vehiculo_cliente (id_cliente),
  CONSTRAINT fk_vehiculo_cliente FOREIGN KEY (id_cliente)
    REFERENCES cliente (id_cliente) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Mensualidades (cada una se activa al registrar su pago; ver tabla pago)
-- ---------------------------------------------------------------------
CREATE TABLE mensualidad (
  id_mensualidad  INT UNSIGNED NOT NULL AUTO_INCREMENT,
  fecha_inicio    DATE NOT NULL,
  fecha_fin       DATE NOT NULL,
  estado          ENUM('ACTIVA','VENCIDA','CANCELADA') NOT NULL,
  id_vehiculo     INT UNSIGNED NOT NULL,
  -- Vale id_vehiculo si la mensualidad está ACTIVA y NULL si no: con el UNIQUE,
  -- la BD impide dos mensualidades activas para el mismo vehículo.
  mensualidad_activa INT UNSIGNED GENERATED ALWAYS AS (IF(estado = 'ACTIVA', id_vehiculo, NULL)) VIRTUAL,
  PRIMARY KEY (id_mensualidad),
  UNIQUE KEY uq_mensualidad_activa (mensualidad_activa),
  KEY ix_mensualidad_vehiculo (id_vehiculo, estado),
  CONSTRAINT ck_mensualidad_fechas CHECK (fecha_fin >= fecha_inicio),
  CONSTRAINT fk_mensualidad_vehiculo FOREIGN KEY (id_vehiculo)
    REFERENCES vehiculo (id_vehiculo) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Celdas
-- ---------------------------------------------------------------------
CREATE TABLE celda (
  id_celda  INT UNSIGNED NOT NULL AUTO_INCREMENT,
  codigo    VARCHAR(10) NOT NULL,
  tipo      ENUM('CARRO','MOTO') NOT NULL,
  estado    ENUM('LIBRE','OCUPADA','MANTENIMIENTO') NOT NULL DEFAULT 'LIBRE',
  PRIMARY KEY (id_celda),
  UNIQUE KEY uq_celda_codigo (codigo),
  KEY ix_celda_tipo_estado (tipo, estado)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Movimientos (entrada y salida de cada visita)
--   vehiculo_abierto / celda_abierta: columnas generadas que valen NULL
--   cuando el movimiento ya tiene salida. Sus índices UNIQUE garantizan
--   que un vehículo o una celda no tengan dos movimientos abiertos a la
--   vez (MySQL permite varios NULL en un índice UNIQUE).
-- ---------------------------------------------------------------------
CREATE TABLE movimiento (
  id_movimiento       BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  fecha_hora_entrada  DATETIME NOT NULL,
  fecha_hora_salida   DATETIME NULL,
  observaciones_entrada VARCHAR(255) NULL,
  observaciones_salida  VARCHAR(255) NULL,
  id_vehiculo         INT UNSIGNED NOT NULL,
  id_celda            INT UNSIGNED NOT NULL,
  id_usuario_entrada  INT UNSIGNED NOT NULL,
  id_usuario_salida   INT UNSIGNED NULL,
  vehiculo_abierto    INT UNSIGNED
      GENERATED ALWAYS AS (IF(fecha_hora_salida IS NULL, id_vehiculo, NULL)) VIRTUAL,
  celda_abierta       INT UNSIGNED
      GENERATED ALWAYS AS (IF(fecha_hora_salida IS NULL, id_celda, NULL)) VIRTUAL,
  PRIMARY KEY (id_movimiento),
  UNIQUE KEY uq_movimiento_vehiculo_abierto (vehiculo_abierto),
  UNIQUE KEY uq_movimiento_celda_abierta (celda_abierta),
  KEY ix_movimiento_entrada (fecha_hora_entrada),
  KEY ix_movimiento_vehiculo (id_vehiculo),
  KEY ix_movimiento_celda (id_celda),
  CONSTRAINT ck_movimiento_fechas
    CHECK (fecha_hora_salida IS NULL OR fecha_hora_salida >= fecha_hora_entrada),
  CONSTRAINT fk_mov_vehiculo FOREIGN KEY (id_vehiculo)
    REFERENCES vehiculo (id_vehiculo) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_mov_celda FOREIGN KEY (id_celda)
    REFERENCES celda (id_celda) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_mov_usuario_entrada FOREIGN KEY (id_usuario_entrada)
    REFERENCES usuario_sistema (id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_mov_usuario_salida FOREIGN KEY (id_usuario_salida)
    REFERENCES usuario_sistema (id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Tarifas (iteración 3): valor de la mensualidad por tipo de vehículo, en pesos
-- ---------------------------------------------------------------------
CREATE TABLE tarifa (
  id_tarifa      INT UNSIGNED NOT NULL AUTO_INCREMENT,
  tipo_vehiculo  ENUM('CARRO','MOTO') NOT NULL,
  valor          INT UNSIGNED NOT NULL,
  PRIMARY KEY (id_tarifa),
  UNIQUE KEY uq_tarifa_tipo (tipo_vehiculo),
  CONSTRAINT ck_tarifa_valor CHECK (valor > 0)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Pagos (iteración 3): un pago por mensualidad. Guarda el valor cobrado en
-- ese momento (no cambia si luego se edita la tarifa). Al anular un pago, su
-- mensualidad pasa a CANCELADA.
-- ---------------------------------------------------------------------
CREATE TABLE pago (
  id_pago               INT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_mensualidad        INT UNSIGNED NOT NULL,
  valor                 INT UNSIGNED NOT NULL,
  medio                 ENUM('EFECTIVO','TRANSFERENCIA','TARJETA') NOT NULL,
  referencia            VARCHAR(40) NULL,
  fecha_hora            DATETIME NOT NULL,
  estado                ENUM('REGISTRADO','ANULADO') NOT NULL DEFAULT 'REGISTRADO',
  motivo_anulacion      VARCHAR(255) NULL,
  fecha_hora_anulacion  DATETIME NULL,
  id_usuario            INT UNSIGNED NOT NULL,
  id_usuario_anulo      INT UNSIGNED NULL,
  PRIMARY KEY (id_pago),
  UNIQUE KEY uq_pago_mensualidad (id_mensualidad),
  KEY ix_pago_fecha (fecha_hora),
  CONSTRAINT ck_pago_valor CHECK (valor > 0),
  CONSTRAINT ck_pago_anulacion CHECK (
    (estado = 'REGISTRADO' AND motivo_anulacion IS NULL)
    OR (estado = 'ANULADO' AND motivo_anulacion IS NOT NULL)
  ),
  CONSTRAINT fk_pago_mensualidad FOREIGN KEY (id_mensualidad)
    REFERENCES mensualidad (id_mensualidad) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_pago_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuario_sistema (id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_pago_usuario_anulo FOREIGN KEY (id_usuario_anulo)
    REFERENCES usuario_sistema (id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;
