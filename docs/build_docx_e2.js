// Genera docs/X.docx a partir de los diagramas, mockups y textos.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, ExternalHyperlink, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, AlignmentType,
  HeadingLevel, BorderStyle, WidthType, ShadingType, LevelFormat, Footer, PageNumber, PageBreak,
  VerticalAlign,
} = require("docx");

const ROOT = path.join(__dirname, "..");
const AZUL = "1F3A5F";
const GRIS = "5F6B7A";
const CONTENT_W = 9360; // 6.5" en DXA (carta, márgenes de 1")

// ---------- utilidades ----------
function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
let nFigura = 0;
let nTabla = 0;

function run(t, o = {}) { return new TextRun({ text: t, ...o }); }

// Texto con **negrita** inline
function rich(t, base = {}) {
  return t.split(/(\*\*[^*]+\*\*)/g).filter(Boolean).map((s) =>
    s.startsWith("**") ? run(s.slice(2, -2), { bold: true, ...base }) : run(s, base));
}
function p(t, o = {}) {
  return new Paragraph({
    spacing: { after: 120, line: 276 }, alignment: AlignmentType.JUSTIFIED, ...o.par,
    children: rich(t, o.run || {}),
  });
}
function h1(t, brk = true) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: brk, keepNext: true, children: [run(t)] });
}
function h2(t, brk = false) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, pageBreakBefore: brk, keepNext: true, children: [run(t)] });
}
function h3(t) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3, keepNext: true, children: [run(t)] });
}
function bullet(t) {
  return new Paragraph({ numbering: { reference: "vinetas", level: 0 }, spacing: { after: 60, line: 276 }, children: rich(t) });
}
function figura(file, caption, maxW = 624, maxH = 640) {
  const full = path.join(ROOT, file);
  const { w, h } = pngSize(full);
  const k = Math.min(maxW / w, maxH / h);
  nFigura += 1;
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(full), transformation: { width: Math.round(w * k), height: Math.round(h * k) },
        altText: { title: caption, description: caption, name: path.basename(file) } })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 200 },
      children: [run(`Figura ${nFigura}. ${caption}`, { italics: true, size: 18, color: GRIS })],
    }),
  ];
}

const borde = { style: BorderStyle.SINGLE, size: 4, color: "C5CFDC" };
const bordes = { top: borde, bottom: borde, left: borde, right: borde };

function celda(contenido, ancho, o = {}) {
  const parrafos = (Array.isArray(contenido) ? contenido : [contenido]).map((c) =>
    typeof c === "string"
      ? new Paragraph({ spacing: { after: 40, line: 252 }, alignment: AlignmentType.LEFT,
          children: rich(c, { size: o.size || 19, color: o.color, bold: o.bold }) })
      : c);
  return new TableCell({
    borders: bordes, width: { size: ancho, type: WidthType.DXA }, verticalAlign: VerticalAlign.TOP,
    shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 70, bottom: 70, left: 110, right: 110 }, children: parrafos,
  });
}
function tabla(caption, anchos, encabezados, filas, o = {}) {
  nTabla += 1;
  const total = anchos.reduce((a, b) => a + b, 0);
  const cab = new TableRow({
    tableHeader: true, cantSplit: true,
    children: encabezados.map((t, i) => celda(t, anchos[i], { fill: AZUL, color: "FFFFFF", bold: true })),
  });
  const cuerpo = filas.map((f, r) => new TableRow({
    cantSplit: true,
    children: f.map((t, i) => celda(t, anchos[i], { fill: r % 2 ? "F4F7FB" : undefined, bold: o.primeraNegrita && i === 0 })),
  }));
  return [
    new Paragraph({ keepNext: true, spacing: { before: 160, after: 80 },
      children: [run(`Tabla ${nTabla}. ${caption}`, { bold: true, size: 19, color: AZUL })] }),
    new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: anchos, rows: [cab, ...cuerpo] }),
    new Paragraph({ spacing: { after: 160 }, children: [] }),
  ];
}
// Ficha de dos columnas (etiqueta / contenido), usada en historias y casos de uso
function ficha(titulo, filas) {
  nTabla += 1;
  const a = [2000, 7360];
  const rows = filas.map(([k, v]) => new TableRow({
    cantSplit: true,
    children: [celda(k, a[0], { fill: AZUL_C(), bold: true, color: AZUL }), celda(v, a[1])],
  }));
  return [
    new Paragraph({ keepNext: true, spacing: { before: 160, after: 80 },
      children: [run(`Tabla ${nTabla}. ${titulo}`, { bold: true, size: 19, color: AZUL })] }),
    new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: a, rows }),
    new Paragraph({ spacing: { after: 160 }, children: [] }),
  ];
}
function AZUL_C() { return "E8EFF8"; }

function codigo(lineas) {
  const a = [9360];
  const rows = [new TableRow({ cantSplit: true, children: [new TableCell({
    borders: bordes, width: { size: a[0], type: WidthType.DXA },
    shading: { fill: "F3F4F6", type: ShadingType.CLEAR, color: "auto" },
    margins: { top: 100, bottom: 100, left: 160, right: 160 },
    children: lineas.map((l) => new Paragraph({ spacing: { after: 0, line: 240 },
      children: [run(l.replace(/ /g, " "), { font: "Courier New", size: 17 })] })),
  })] })];
  return [new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: a, rows }), new Paragraph({ spacing: { after: 160 }, children: [] })];
}
const resaltado = (t, o = {}) => run(t, { highlight: "yellow", ...o });

const REPO = "https://github.com/Im-Luis-SS/autos-colombia";

// ---------- PORTADA ----------
const centro = (t, o, sp) => new Paragraph({ spacing: sp, alignment: AlignmentType.CENTER, children: [run(t, o)] });
const portada = [
  new Paragraph({ spacing: { before: 1400, after: 0 }, alignment: AlignmentType.CENTER,
    children: [run("INSTITUCIÓN UNIVERSITARIA DIGITAL DE ANTIOQUIA", { bold: true, size: 24, color: GRIS })] }),
  new Paragraph({ spacing: { before: 60, after: 900 }, alignment: AlignmentType.CENTER,
    border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: "E8A317", space: 12 } },
    children: [run("Facultad de Ingeniería · Ingeniería de Software", { size: 22, color: GRIS })] }),
  centro("Sistema de información del parqueadero", { bold: true, size: 44, color: AZUL }, { after: 160 }),
  centro("“Autos Colombia”", { bold: true, size: 56, color: "E8A317" }, { after: 400 }),
  centro("Evidencia de aprendizaje EA2", { size: 28, color: AZUL, bold: true }, { after: 120 }),
  centro("Iteración 2: Gestión de usuarios y gestión de celdas", { size: 26, color: AZUL }, { after: 1500 }),
  centro("Presentado por:", { size: 22, color: GRIS }, { after: 80 }),
  centro("Luis Fernando Soto", { size: 28, bold: true }, { after: 300 }),
  centro("Asesor:", { size: 22, color: GRIS }, { after: 80 }),
  centro("Reinaldo Rojas", { size: 26, bold: true }, { after: 700 }),
  centro("San Pedro de Urabá, Antioquia · 14 de noviembre de 2026", { size: 22, color: GRIS }, {}),
];

// ---------- INTRODUCCIÓN ----------
const introduccion = [
  h1("1. Introducción", false),
  p("Este documento recoge la **segunda iteración** del sistema de información del parqueadero “Autos Colombia”. La primera iteración dejó funcionando el registro de entradas y salidas; esta segunda completa la parte administrativa que ese registro necesita para operar sola: quién usa el sistema (**gestión de usuarios**), a quién pertenecen los vehículos y cuándo vence su mensualidad (**clientes, vehículos y mensualidades**) y qué celdas existen y en qué estado están (**gestión de celdas**)."),
  p("Hasta ahora los clientes, vehículos, mensualidades y celdas solo existían porque se cargaban con un comando de datos de ejemplo. Con esta iteración el administrador puede crearlos y mantenerlos desde la propia aplicación, sin tocar la base de datos."),
  h3("Decisiones de negocio acordadas para esta iteración"),
  bullet("Cada vehículo tiene **una sola mensualidad** vigente a la vez, de **30 días** (el día de inicio cuenta como el primero)."),
  bullet("El parqueadero opera **24 horas, 7 días a la semana**; no hay horarios de apertura que validar."),
  bullet("Hay **80 celdas**: 70 para carro (C-01 a C-70) y 10 para moto (M-01 a M-10). Solo se atienden carros y motos."),
  bullet("Las celdas son **libres**: no hay una celda fija por cliente; el sistema asigna la primera libre del tipo del vehículo."),
  bullet("Hay dos roles: **Operario** (entradas, salidas y consultas) y **Administrador** (además gestiona usuarios, clientes, vehículos, mensualidades y celdas)."),
  h3("Cambios transversales respecto a la iteración 1"),
  bullet("**Seguridad:** todos los formularios de la aplicación llevan ahora una ficha anti-CSRF por sesión; un envío sin ella se rechaza (error 400). Se añadieron páginas de error 400 y 404 con mensajes claros."),
  bullet("**Base de datos:** la tabla mensualidad gana una columna generada y un índice único que impiden, desde el propio motor, tener dos mensualidades activas para un mismo vehículo."),
  bullet("**Menú:** los administradores ven los nuevos módulos Clientes, Celdas y Usuarios."),
  p("El documento se organiza así: la sección 2 presenta los ocho entregables de la iteración y la sección 3 expone las conclusiones. Las historias HU-01 a HU-06 y los requerimientos RF-01 a RF-12 corresponden a la iteración 1; aquí se continúa la numeración."),
];

// ---------- 2.1 RF / RNF ----------
const rf = [
  ["RF-13", "Consultar usuarios", "El administrador puede listar los usuarios del sistema y filtrarlos por nombre/usuario, rol y estado.", "Media"],
  ["RF-14", "Crear usuario", "El administrador puede crear un usuario con nombre, nombre de usuario único (sin distinguir mayúsculas), rol y contraseña con confirmación. La contraseña se guarda cifrada.", "Alta"],
  ["RF-15", "Editar usuario", "El administrador puede cambiar el nombre y el rol de un usuario. No puede quitar el rol de administrador al último administrador activo.", "Media"],
  ["RF-16", "Activar / desactivar usuario", "El administrador puede desactivar y reactivar usuarios; un usuario desactivado no puede iniciar sesión. No puede desactivarse a sí mismo ni al último administrador activo.", "Alta"],
  ["RF-17", "Restablecer contraseña", "El administrador puede asignar una nueva contraseña a cualquier usuario (mínimo 8 caracteres, con letras y números).", "Media"],
  ["RF-18", "Registrar cliente", "El administrador puede registrar un cliente con tipo y número de documento (único), nombres, apellidos y, opcionalmente, teléfono y correo.", "Alta"],
  ["RF-19", "Registrar vehículo", "El administrador puede asociar a un cliente un vehículo con placa única, tipo (carro o moto) y, opcionalmente, marca y color.", "Alta"],
  ["RF-20", "Consultar y editar clientes y vehículos", "El administrador puede buscar clientes por documento, nombre o placa, ver su detalle y editar sus datos de contacto y los datos del vehículo. No se cambia el tipo de un vehículo que está dentro.", "Media"],
  ["RF-21", "Activar mensualidad", "El administrador puede activar para un vehículo una mensualidad de 30 días desde hoy. Solo puede existir una mensualidad vigente por vehículo; las caducadas pasan a VENCIDA y permiten renovar.", "Alta"],
  ["RF-22", "Consultar celdas", "El administrador puede listar las celdas y filtrarlas por código, tipo y estado.", "Media"],
  ["RF-23", "Crear celda", "El administrador puede crear una celda con código único (máx. 10 caracteres) y tipo; nace en estado LIBRE.", "Media"],
  ["RF-24", "Editar celda", "El administrador puede cambiar el código y el tipo de una celda que no esté ocupada; el tipo no cambia si la celda ya tiene historial de movimientos.", "Media"],
  ["RF-25", "Mantenimiento de celdas", "El administrador puede poner una celda libre en MANTENIMIENTO y habilitarla de nuevo. Las celdas en mantenimiento no se asignan en las entradas. Una celda ocupada no cambia de estado.", "Alta"],
  ["RF-26", "Eliminar celda", "El administrador puede eliminar una celda solo si no está ocupada y no tiene movimientos históricos.", "Baja"],
  ["RF-27", "Acceso por rol", "Las pantallas de usuarios, clientes, vehículos y celdas solo están disponibles para el rol Administrador; los operarios son redirigidos al panel.", "Alta"],
];
const rnf = [
  ["RNF-09", "Seguridad (contraseñas)", "Las contraseñas deben tener entre 8 y 72 caracteres con letras y números y se almacenan con hash."],
  ["RNF-10", "Seguridad (CSRF)", "Toda petición POST debe traer la ficha anti-CSRF de la sesión; de lo contrario se rechaza con 400."],
  ["RNF-11", "Integridad", "La base de datos debe impedir dos mensualidades activas del mismo vehículo, códigos de celda repetidos, documentos de cliente repetidos y placas repetidas, aunque dos administradores actúen a la vez."],
  ["RNF-12", "Usabilidad", "Si un formulario falla, se muestra el motivo en español y se conservan los datos escritos. Las acciones destructivas (eliminar celda) piden confirmación."],
  ["RNF-13", "Disponibilidad", "El sistema debe poder operar las 24 horas del día, los 7 días de la semana (el parqueadero no cierra)."],
  ["RNF-14", "Mantenibilidad / calidad", "Las reglas de los nuevos módulos viven en servicios independientes de las rutas y están cubiertas por pruebas automáticas (46 pruebas nuevas; 76 en total)."],
];

// ---------- 2.3 Historias ----------
const hu = [
  ["HU-07", "Consultar usuarios", "administrador", "ver la lista de usuarios y filtrarla", "saber quién tiene acceso al sistema y con qué rol", ["La lista muestra nombre, usuario, rol y estado.", "Puedo filtrar por texto, rol y estado.", "Solo el administrador accede."], "Media", 3],
  ["HU-08", "Crear usuario", "administrador", "crear un usuario con rol y contraseña", "dar acceso a un nuevo operario o administrador", ["Nombre ≥ 3 caracteres; usuario de 3 a 30 caracteres (letras, números, punto o guion bajo).", "La contraseña pide 8+ caracteres con letras y números y confirmación igual.", "No se repite el usuario, aunque cambien las mayúsculas.", "Si hay error, se conserva lo escrito."], "Alta", 5],
  ["HU-09", "Editar usuario", "administrador", "cambiar el nombre y el rol de un usuario", "mantener actualizada la información y los permisos", ["Puedo cambiar nombre y rol.", "El nombre de usuario no se modifica.", "No puedo quitar el rol al último administrador activo."], "Media", 3],
  ["HU-10", "Activar o desactivar usuario", "administrador", "desactivar y reactivar usuarios", "bloquear el acceso de quien ya no trabaja en el parqueadero sin perder su historial", ["Un usuario desactivado no puede iniciar sesión.", "Puedo reactivarlo.", "No puedo desactivarme a mí mismo ni al último administrador activo."], "Alta", 3],
  ["HU-11", "Restablecer contraseña", "administrador", "asignar una nueva contraseña a un usuario", "recuperar el acceso de quien olvidó la suya", ["La nueva contraseña cumple la misma política de HU-08.", "La contraseña anterior deja de funcionar."], "Media", 2],
  ["HU-12", "Registrar cliente", "administrador", "registrar un cliente con sus datos", "poder asociarle vehículos y mensualidades", ["Tipo y número de documento obligatorios y únicos (5 a 20 caracteres).", "Nombres y apellidos obligatorios.", "Teléfono y correo opcionales pero válidos."], "Alta", 3],
  ["HU-13", "Registrar vehículo", "administrador", "agregar un vehículo a un cliente", "que el vehículo pueda entrar al parqueadero", ["La placa se normaliza a mayúsculas, 5 a 7 caracteres, y es única.", "El tipo es carro o moto.", "Marca y color son opcionales."], "Alta", 3],
  ["HU-14", "Consultar y editar clientes y vehículos", "administrador", "buscar clientes y corregir sus datos y los de sus vehículos", "mantener la información al día", ["Busco por documento, nombre o placa, con paginación.", "Edito contacto del cliente y marca, color y tipo del vehículo.", "No cambio el tipo de un vehículo que está dentro."], "Media", 3],
  ["HU-15", "Activar mensualidad de 30 días", "administrador", "activar la mensualidad de un vehículo", "que el vehículo pueda ingresar durante 30 días", ["Va de hoy hasta hoy + 29 días (30 días).", "Si ya hay una vigente, se rechaza y se informa hasta cuándo.", "Si la anterior caducó, se renueva y la vieja queda VENCIDA.", "Con la mensualidad activa, el vehículo puede registrar su entrada (iteración 1)."], "Alta", 5],
  ["HU-16", "Consultar celdas", "administrador", "ver todas las celdas con su tipo y estado", "controlar la capacidad del parqueadero", ["Se listan las 80 celdas.", "Filtro por código, tipo y estado."], "Media", 2],
  ["HU-17", "Crear celda", "administrador", "agregar una celda", "ampliar la capacidad del parqueadero", ["Código único de máximo 10 caracteres (letras, números, guiones).", "Tipo carro o moto; nace LIBRE."], "Media", 2],
  ["HU-18", "Editar celda", "administrador", "cambiar el código o el tipo de una celda", "corregir errores de registro", ["No se edita una celda ocupada.", "No cambia de tipo si ya tiene historial.", "El código nuevo no se repite."], "Media", 3],
  ["HU-19", "Mantenimiento de celdas", "administrador", "poner una celda en mantenimiento y habilitarla de nuevo", "evitar que se asigne una celda dañada o no disponible", ["Solo celdas libres pasan a mantenimiento.", "Una celda en mantenimiento no se asigna en las entradas.", "Al habilitarla vuelve a asignarse."], "Alta", 3],
  ["HU-20", "Eliminar celda sin historial", "administrador", "eliminar una celda creada por error", "no dejar celdas inútiles en el sistema", ["Solo si no está ocupada y no tiene movimientos.", "Pide confirmación.", "Si tiene historial, se sugiere ponerla en mantenimiento."], "Baja", 2],
];
const totalPts = hu.reduce((a, h) => a + h[7], 0);

const e21 = [
  h2("2.1 Requerimientos funcionales y no funcionales"),
  p("Se continúa la numeración de la iteración 1. Los requerimientos nuevos cubren los dos módulos pedidos (usuarios y celdas) y la gestión de clientes, vehículos y mensualidades, necesaria para que las entradas y salidas dejen de depender de datos de ejemplo."),
  h3("Requerimientos funcionales"),
  ...tabla("Requerimientos funcionales de la iteración 2", [900, 2100, 5460, 900], ["ID", "Nombre", "Descripción", "Prioridad"], rf, { primeraNegrita: true }),
  h3("Requerimientos no funcionales"),
  ...tabla("Requerimientos no funcionales de la iteración 2", [1000, 2100, 6260], ["ID", "Categoría", "Descripción / criterio"], rnf, { primeraNegrita: true }),
  h3("Reglas de negocio de la iteración"),
  bullet("Una sola mensualidad vigente por vehículo; dura 30 días contando el de inicio."),
  bullet("Siempre debe quedar al menos un administrador activo."),
  bullet("Una celda ocupada no se edita, no cambia de estado y no se elimina."),
  bullet("Una celda con historial de movimientos no se elimina ni cambia de tipo."),
];

// ---------- 2.2 Casos de uso ----------
const e22 = [
  h2("2.2 Diagramas de casos de uso", true),
  p("Se elaboraron dos diagramas: uno para usuarios, clientes y vehículos y otro para celdas. Todo lo nuevo lo realiza el Administrador; el Operario conserva las funciones de la iteración 1 y solo se relaciona con las celdas de forma indirecta (las celdas en mantenimiento no se le asignan al registrar una entrada). Los diagramas están elaborados con PlantUML."),
  ...figura("diagrams/e2/10_casos_uso_usuarios_clientes.png", "Casos de uso: usuarios, clientes y vehículos.", 600, 560),
  ...figura("diagrams/e2/11_casos_uso_celdas.png", "Casos de uso: celdas.", 600, 420),
  ...tabla("Permisos por rol", [3600, 2880, 2880], ["Función", "Operario", "Administrador"], [
    ["Registrar entrada y salida, ver panel y vehículos dentro", "Sí", "Sí"],
    ["Historial de movimientos", "No", "Sí"],
    ["Gestión de usuarios (HU-07 a HU-11)", "No", "Sí"],
    ["Gestión de clientes, vehículos y mensualidades (HU-12 a HU-15)", "No", "Sí"],
    ["Gestión de celdas (HU-16 a HU-20)", "No", "Sí"],
  ], { primeraNegrita: true }),
];

// ---------- 2.3 Historias ----------
const e23 = [
  h2("2.3 Historias de usuario", true),
  p("Se mantiene el formato «Como [rol] quiero [acción] para [beneficio]» con criterios de aceptación. Las estimaciones están en puntos de historia."),
  ...tabla("Historias de usuario HU-07 a HU-20", [800, 3200, 4260, 1100],
    ["ID", "Historia", "Criterios de aceptación", "Prioridad / puntos"],
    hu.map((h, i) => [`**${h[0]}**`,
      [`**${h[1]}.** Como ${h[2]}, quiero ${h[3]}, para ${h[4]}.`, `Mockup: ${["MK-07","MK-07","MK-08","MK-07","MK-09","MK-11","MK-13","MK-10 / MK-12","MK-12","MK-14","MK-15","MK-15","MK-14","MK-14"][i]}`],
      h[5].map((c, j) => `${j + 1}. ${c}`), `${h[6]} · ${h[7]} pts`])),
  p(`Total estimado de la iteración: **${totalPts} puntos de historia**.`),
];

// ---------- 2.4 Mockups ----------
const mk = [
  ["MK-07_usuarios.png", "MK-07 · Lista de usuarios (HU-07, HU-10)."],
  ["MK-08_usuario_nuevo.png", "MK-08 · Crear / editar usuario (HU-08, HU-09)."],
  ["MK-09_restablecer_clave.png", "MK-09 · Restablecer contraseña (HU-11)."],
  ["MK-10_clientes.png", "MK-10 · Lista de clientes (HU-14)."],
  ["MK-11_cliente_nuevo.png", "MK-11 · Registrar cliente (HU-12)."],
  ["MK-12_cliente_detalle.png", "MK-12 · Detalle del cliente, vehículos y mensualidad (HU-13, HU-15)."],
  ["MK-13_vehiculo_nuevo.png", "MK-13 · Registrar vehículo (HU-13)."],
  ["MK-14_celdas.png", "MK-14 · Lista de celdas (HU-16, HU-19, HU-20)."],
  ["MK-15_celda_nueva.png", "MK-15 · Crear / editar celda (HU-17, HU-18)."],
];
const e24 = [
  h2("2.4 Mockups", true),
  p("Se diseñaron nueve pantallas con la misma identidad visual de la iteración 1. En cada una se incluyen, junto al formulario, los mensajes de éxito y error previstos. Los mockups se generaron como imágenes con un script (mockups/generar_mockups_e2.py) en lugar de Figma; sirven de guía exacta (colores, tamaños y textos) para recrearlos allí si se requiere."),
  ...mk.flatMap(([f, t]) => figura(`mockups/${f}`, t, 600, 366)),
];

// ---------- 2.5 Secuencia ----------
const e25 = [
  h2("2.5 Diagramas de secuencia (iteraciones 1 y 2)", true),
  p("Se modelan los flujos principales de ambas iteraciones. En todos, la petición pasa por la ruta (que verifica sesión, rol y ficha CSRF), luego por el servicio (que aplica las reglas) y finalmente por la base de datos; los errores de negocio vuelven al usuario como mensajes."),
  h3("Iteración 1"),
  ...figura("diagrams/e2/12_secuencia_it1.png", "Secuencia: registrar entrada.", 600, 520),
  ...figura("diagrams/e2/13_secuencia_salida.png", "Secuencia: registrar salida.", 600, 460),
  h3("Iteración 2"),
  ...figura("diagrams/e2/14_secuencia_usuario.png", "Secuencia: crear usuario.", 600, 520),
  ...figura("diagrams/e2/15_secuencia_celda_mantenimiento.png", "Secuencia: poner una celda en mantenimiento.", 600, 460),
  ...figura("diagrams/e2/16_secuencia_mensualidad.png", "Secuencia: registrar vehículo y activar mensualidad.", 620, 560),
];

// ---------- 2.6 Componentes ----------
const e26 = [
  h2("2.6 Diagrama de componentes (iteraciones 1 y 2)", true),
  p("El diagrama muestra la arquitectura en capas con los componentes de ambas iteraciones; los marcados «it.2» son los nuevos. Cada módulo nuevo se sumó como una pareja ruta + servicio sin modificar la estructura existente, lo que confirma que la separación en capas de la iteración 1 permite crecer sin reescribir."),
  ...figura("diagrams/e2/17_componentes.png", "Diagrama de componentes de Autos Colombia.", 620, 420),
];

// ---------- 2.7 Plan de pruebas ----------
const cp = [
  ["CP-01", "HU-08", "Crear usuario «Ana.Perez» con clave «clave1234» y rol Operario.", "Se crea con usuario en minúsculas, activo; la clave queda cifrada y sirve para iniciar sesión."],
  ["CP-02", "HU-08", "Crear con: nombre vacío; usuario de 1 letra; clave corta; clave sin números; confirmación distinta; rol inválido.", "Cada caso se rechaza con su mensaje y no se crea nada."],
  ["CP-03", "HU-08", "Crear «ADMIN» cuando ya existe «admin».", "Rechaza por usuario repetido (sin distinguir mayúsculas)."],
  ["CP-04", "HU-09", "Cambiar nombre y rol del operario.", "Los cambios quedan guardados."],
  ["CP-05", "HU-09", "Pasar a Operario al único administrador activo.", "Rechaza: debe quedar un administrador."],
  ["CP-06", "HU-10", "Desactivar al operario e intentar iniciar sesión; reactivarlo y volver a intentar.", "Desactivado no entra; reactivado sí entra."],
  ["CP-07", "HU-10", "Administrador intenta desactivarse a sí mismo y desactivar al último administrador.", "Ambos se rechazan; sigue activo."],
  ["CP-08", "HU-11", "Restablecer clave a «nueva12345»; probar la anterior; probar clave «123».", "La nueva funciona, la anterior no; «123» se rechaza."],
  ["CP-09", "HU-07", "Listar usuarios filtrando por texto «oper», rol Administrador y estado inactivo.", "Devuelve solo los que coinciden en cada filtro."],
  ["CP-10", "HU-12", "Registrar cliente CC 1020304050, Juan Gómez, correo «Juan@Mail.com».", "Se crea; el correo queda en minúsculas."],
  ["CP-11", "HU-12", "Registrar con documento «12», nombres vacíos, correo sin @, teléfono «abc», tipo «XX».", "Cada caso se rechaza con su mensaje."],
  ["CP-12", "HU-12", "Registrar dos veces el mismo tipo y número de documento.", "El segundo se rechaza por duplicado."],
  ["CP-13", "HU-13", "Registrar vehículo « xyz-987 » tipo carro a un cliente.", "Se guarda como XYZ987 asociado al cliente."],
  ["CP-14", "HU-13", "Placa «A!», tipo «BUS» y placa ya registrada (abc123).", "Los tres se rechazan con su mensaje."],
  ["CP-15", "HU-14", "Editar contacto del cliente y marca/color del vehículo; cambiar el tipo con el vehículo dentro.", "Edición correcta; el cambio de tipo se rechaza."],
  ["CP-16", "HU-14", "Buscar por documento, apellido y placa parcial; buscar un texto inexistente.", "Encuentra al cliente en los tres casos; vacío en el inexistente."],
  ["CP-17", "HU-15", "Activar mensualidad el 14/11/2026.", "Queda ACTIVA del 14/11 al 13/12/2026 (30 días)."],
  ["CP-18", "HU-15", "Activar una segunda mensualidad con la primera vigente.", "Se rechaza; sigue habiendo una sola."],
  ["CP-19", "HU-15", "Activar cuando la anterior terminó hace 30 días.", "La vieja pasa a VENCIDA y se crea una nueva ACTIVA."],
  ["CP-20", "HU-15", "Insertar a la fuerza una segunda mensualidad ACTIVA saltándose el servicio.", "La base de datos la rechaza (índice único)."],
  ["CP-21", "HU-13 / HU-15", "Vehículo nuevo sin mensualidad intenta entrar; se activa la mensualidad y se reintenta.", "Primero se rechaza; luego entra a la celda C-01."],
  ["CP-22", "HU-17", "Crear celda «c-71» de carro.", "Queda C-71 LIBRE; el total pasa a 81."],
  ["CP-23", "HU-17", "Código vacío, con espacio, de 12 caracteres, tipo «BUS» y código repetido C-01.", "Cada caso se rechaza con su mensaje."],
  ["CP-24", "HU-18", "Renombrar una celda sin historial y cambiarle el tipo; usar un código existente.", "Edición correcta; el código repetido se rechaza."],
  ["CP-25", "HU-18 / 19 / 20", "Con ABC123 dentro, intentar editar, poner en mantenimiento y eliminar su celda.", "Los tres intentos se rechazan."],
  ["CP-26", "HU-19", "Poner C-01 en mantenimiento, registrar entrada, habilitarla y registrar otra.", "La primera entrada recibe C-02; tras habilitarla, la siguiente recibe C-01."],
  ["CP-27", "HU-20", "Eliminar una celda recién creada; eliminar una con historial.", "La nueva se elimina; la que tiene historial se rechaza."],
  ["CP-28", "HU-16", "Listar celdas y filtrar por tipo moto, estado ocupada y código «m-03».", "80 celdas; 10 de moto; 0 ocupadas; solo M-03."],
  ["CP-29", "RF-27", "Abrir las 6 pantallas administrativas sin sesión, como operario y como administrador.", "Sin sesión: login; operario: redirigido; administrador: acceso (200)."],
  ["CP-30", "General", "Abrir usuario, cliente, celda y vehículo inexistentes (id 9999).", "Responde 404, no error del servidor."],
  ["CP-31", "RNF-10", "Enviar login y eliminar celda sin ficha CSRF; luego iniciar sesión con la ficha.", "Sin ficha: 400; con ficha: entra."],
  ["CP-32", "Flujo completo", "Administrador crea cliente, vehículo, mensualidad (y repite) y celda; operario registra la entrada.", "Todo se confirma con mensajes; la segunda mensualidad se rechaza; la entrada se registra."],
  ["CP-33", "RNF-12", "Enviar el formulario de usuario con clave corta.", "400, mensaje de error y el nombre escrito se conserva."],
];
const e27 = [
  h2("2.7 Plan de pruebas resumido: usuarios y celdas", true),
  p("Se diseñaron 33 casos que cubren las historias HU-07 a HU-20, los requerimientos de seguridad y un flujo completo de extremo a extremo. Cada caso está automatizado en el archivo tests/test_iteracion2.py (los casos con varios datos de entrada se ejecutan como pruebas parametrizadas, lo que da 46 pruebas) y el ID del caso aparece en la descripción de cada prueba."),
  p("**Entorno de ejecución:** Python 3, pytest, base de datos SQLite en memoria (la misma capa de servicios y modelos que usa MySQL). **Criterio de aprobación:** el resultado obtenido coincide con el esperado. **Resultado global:** las 76 pruebas del proyecto (30 de la iteración 1 y 46 nuevas) se ejecutaron y aprobaron."),
  ...tabla("Casos de prueba de la iteración 2", [950, 1000, 3300, 3010, 1100],
    ["ID", "HU / RF", "Descripción y datos de prueba", "Resultado esperado", "Estado"],
    cp.map((c) => [`**${c[0]}**`, c[1], c[2], c[3], "Aprobada"])),
  p("Para repetirlas: `python -m pytest -v` desde la carpeta del proyecto."),
];

// ---------- 2.8 Código ----------
const e28 = [
  h2("2.8 Código fuente y repositorio", true),
  p("El código completo de las dos iteraciones está en GitHub:"),
  new Paragraph({ spacing: { after: 160 }, children: [new ExternalHyperlink({ link: REPO, children: [new TextRun({ text: REPO, style: "Hyperlink", color: "1155CC", underline: {} })] })] }),
  h3("Archivos nuevos o modificados en la iteración 2"),
  ...tabla("Estructura de lo agregado", [3700, 5660], ["Archivo", "Contenido"], [
    ["app/services/usuarios.py", "Reglas de usuarios: validación de contraseña, crear, editar, activar/desactivar, restablecer."],
    ["app/services/clientes.py", "Reglas de clientes, vehículos y mensualidad de 30 días."],
    ["app/services/celdas.py", "Reglas de celdas: crear, editar, mantenimiento, eliminar."],
    ["app/services/validaciones.py", "Validaciones de texto, correo y teléfono compartidas."],
    ["app/routes/usuarios.py, clientes.py, celdas.py", "Rutas (solo administrador) de cada módulo."],
    ["app/security.py, app/errors.py", "Protección CSRF y excepciones de negocio (incluye «no encontrado»)."],
    ["app/templates/*.html", "Plantillas nuevas: usuarios, clientes, vehículo, celdas y errores."],
    ["app/models/__init__.py, db/schema.sql", "Columna generada e índice único de mensualidad activa."],
    ["tests/test_iteracion2.py", "33 casos de prueba (46 pruebas)."],
    ["diagrams/e2/, mockups/", "Diagramas PlantUML y mockups de esta entrega."],
  ], { primeraNegrita: true }),
  h3("Cómo ejecutarlo"),
  bullet("Crear la base de datos ejecutando db/schema.sql en MySQL Workbench (el esquema cambió: incluye la restricción de mensualidad activa única)."),
  bullet("Cargar los datos de ejemplo con el comando de semilla del proyecto y arrancar la aplicación con Flask."),
  bullet("Ingresar como administrador para ver los menús Clientes, Celdas y Usuarios."),
];

const entregables = [
  h1("2. Entregables de la iteración 2"),
  p("A continuación se presentan los entregables de la iteración 2: Gestión de usuarios y gestión de celdas."),
  ...e21, ...e22, ...e23, ...e24, ...e25, ...e26, ...e27, ...e28,
];

// ---------- 3 Conclusiones ----------
const conclusiones = [
  h1("3. Conclusiones"),
  p("Con esta iteración el sistema “Autos Colombia” deja de depender de datos cargados a mano: el administrador puede dar de alta usuarios, clientes, vehículos, mensualidades y celdas desde la aplicación, y esos datos alimentan directamente el registro de entradas y salidas de la primera iteración."),
  bullet("**La arquitectura en capas funcionó:** cada módulo nuevo se agregó como un servicio y una ruta sin modificar los existentes, y las 30 pruebas de la iteración 1 siguieron aprobando."),
  bullet("**Las reglas críticas se defienden dos veces:** en el servicio (con mensajes claros) y en la base de datos (índices únicos), por ejemplo para impedir dos mensualidades activas de un mismo vehículo."),
  bullet("**Protecciones de consistencia:** nunca se queda el sistema sin administrador activo, no se tocan celdas ocupadas y no se borra lo que tiene historial."),
  bullet("**Seguridad reforzada:** control de acceso por rol en todas las pantallas administrativas y protección CSRF en todos los formularios."),
  bullet("**Pruebas:** 33 casos diseñados a partir de las historias, automatizados y aprobados (76 pruebas en total)."),
  h3("Limitaciones y siguientes pasos"),
  bullet("Los diagramas se hicieron en PlantUML y los mockups como imágenes generadas por código, no en StarUML ni Figma."),
  bullet("Las pruebas se ejecutaron sobre SQLite; conviene repetirlas contra MySQL al desplegar."),
  bullet("La **iteración 3 (pagos)** usará la mensualidad ya modelada para registrar y controlar los pagos y su estado."),
];

// ---------- DOCUMENTO ----------
const doc = new Document({
  creator: "Luis Fernando Soto",
  title: "Autos Colombia - EA2 Iteración 2: Gestión de usuarios y gestión de celdas",
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: AZUL }, paragraph: { spacing: { before: 240, after: 200 }, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: "E8A317", space: 4 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: AZUL }, paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: "Arial", color: "3A5578" }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [{ reference: "vinetas", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }] },
  sections: [
    { properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } }, children: portada },
    {
      properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1300, left: 1440 }, pageNumbers: { start: 1 } } },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: "C5CFDC", space: 6 } },
        children: [run("Autos Colombia · EA2 · Iteración 2   |   Página ", { size: 17, color: GRIS }),
          new TextRun({ children: [PageNumber.CURRENT], size: 17, color: GRIS })] })] }) },
      children: [...introduccion, ...entregables, ...conclusiones],
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(__dirname, "Soto_Luis_EA2.docx");
  fs.writeFileSync(out, buf);
  console.log("OK", out, buf.length, "bytes;", nFigura, "figuras;", nTabla, "tablas");
});
