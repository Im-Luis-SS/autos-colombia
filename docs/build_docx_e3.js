// Genera docs/X.docx a partir de los diagramas, mockups y textos.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, ExternalHyperlink, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, AlignmentType,
  HeadingLevel, BorderStyle, WidthType, ShadingType, LevelFormat, Footer, PageNumber, PageBreak,
  VerticalAlign, PageOrientation,
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
const VIDEO = process.env.VIDEO_URL || "";

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
  centro("Evidencia de aprendizaje EA3", { size: 28, color: AZUL, bold: true }, { after: 120 }),
  centro("Iteración 3: Gestión de pagos", { size: 26, color: AZUL }, { after: 1500 }),
  centro("Presentado por:", { size: 22, color: GRIS }, { after: 80 }),
  centro("Luis Fernando Soto", { size: 28, bold: true }, { after: 300 }),
  centro("Asesor:", { size: 22, color: GRIS }, { after: 80 }),
  centro("Reinaldo Rojas", { size: 26, bold: true }, { after: 700 }),
  centro("San Pedro de Urabá, Antioquia · 22 de noviembre de 2026", { size: 22, color: GRIS }, {}),
];

// ---------- INTRODUCCIÓN ----------
const introduccion = [
  h1("1. Introducción", false),
  p("Este documento recoge la **tercera y última iteración** del sistema de información del parqueadero “Autos Colombia”: la **gestión de pagos**. Las dos primeras iteraciones dejaron funcionando el registro de entradas y salidas (iteración 1) y la administración de usuarios, clientes, vehículos, mensualidades y celdas (iteración 2). Faltaba lo que da sentido al negocio: **cobrar la mensualidad** y llevar el control de lo recaudado."),
  h3("Decisiones de negocio de esta iteración"),
  bullet("Cada mensualidad se cobra al valor de una **tarifa por tipo de vehículo** (carro y moto), que el administrador puede modificar. La tarifa cambia solo los pagos futuros: cada pago guarda el valor que se cobró."),
  bullet("**Pagar activa la mensualidad:** al registrar el pago se activa automáticamente la mensualidad de 30 días. Por eso el botón «Activar mensualidad» de la iteración 2 se reemplaza por «Registrar pago»; ya no es posible tener una mensualidad sin su pago."),
  bullet("Los medios de pago son **efectivo, transferencia y tarjeta**. En transferencia y tarjeta se registra la referencia de la transacción; el sistema no se conecta a una pasarela de pagos."),
  bullet("Un pago puede **anularse** con un motivo, mientras la mensualidad no haya vencido. Al anular, la mensualidad se cancela y el vehículo deja de poder entrar."),
  bullet("Todo lo relacionado con dinero (tarifas, pagos, comprobantes y anulaciones) lo realiza únicamente el **Administrador**."),
  h3("Ajustes a los diagramas por la retroalimentación de la iteración 2"),
  bullet("**Activar mensualidad ya no incluye registrar el vehículo.** Son operaciones separadas: el vehículo existe antes de cobrar. Se corrigió el caso de uso y se separaron las secuencias."),
  bullet("**La exclusión de celdas en mantenimiento ahora es una regla de asignación** y se muestra dentro de la secuencia «Registrar entrada» (solo se asignan celdas LIBRES del tipo del vehículo), no como una nota suelta."),
  bullet("**Las secuencias se completaron:** hay un diagrama por operación (18 en total) que incluye el inicio de sesión, crear y editar usuarios, activar y desactivar cuentas, restablecer contraseñas y todas las operaciones de celdas, cada una con sus rechazos."),
  p("El documento se organiza así: la sección 2 presenta los entregables de la iteración y la sección 3 expone las conclusiones. La numeración continúa la de las iteraciones anteriores (RF-01 a RF-27 y HU-01 a HU-20 ya existen; aquí se agregan RF-28 a RF-38 y HU-21 a HU-26)."),
];

// ---------- 2.1 RF / RNF ----------
const rf = [
  ["RF-28", "Consultar tarifas", "El administrador puede ver la tarifa mensual de cada tipo de vehículo (carro y moto) en pesos.", "Media"],
  ["RF-29", "Actualizar tarifa", "El administrador puede cambiar el valor de una tarifa. Acepta enteros con puntos, comas o signo de pesos, entre $10.000 y $5.000.000. El cambio solo afecta los pagos futuros.", "Alta"],
  ["RF-30", "Registrar pago de mensualidad", "El administrador puede registrar el pago de la mensualidad de un vehículo. El sistema cobra la tarifa de su tipo y exige un medio de pago: efectivo, transferencia o tarjeta.", "Alta"],
  ["RF-31", "Referencia del pago", "En transferencia y tarjeta es obligatoria una referencia de 4 a 40 letras, números o guiones (se guarda en mayúsculas). En efectivo no se guarda referencia.", "Media"],
  ["RF-32", "Activar la mensualidad al pagar", "Al registrar el pago se activa la mensualidad de 30 días desde hoy; pago y mensualidad se guardan juntos o no se guarda ninguno. Si el vehículo ya tiene una mensualidad vigente se rechaza; si la anterior venció, se renueva.", "Alta"],
  ["RF-33", "Un pago por mensualidad", "Cada mensualidad tiene un solo pago, incluso si dos administradores intentan registrarlo a la vez.", "Alta"],
  ["RF-34", "Consultar pagos", "El administrador puede listar los pagos, del más reciente al más antiguo y paginados, y filtrarlos por placa, documento o apellido, medio, estado y rango de fechas.", "Media"],
  ["RF-35", "Total recaudado", "La lista de pagos muestra el total recaudado según los filtros aplicados. Los pagos anulados no se suman.", "Media"],
  ["RF-36", "Comprobante de pago", "Cada pago tiene un comprobante imprimible con número (P-000001), fecha y hora, cliente, vehículo, vigencia, medio, referencia, valor y usuario que lo registró.", "Media"],
  ["RF-37", "Anular pago", "El administrador puede anular un pago indicando un motivo (5 a 255 caracteres). El pago queda ANULADO con fecha, hora y usuario, y su mensualidad queda CANCELADA. No se anula un pago ya anulado ni uno cuya mensualidad ya venció.", "Alta"],
  ["RF-38", "Acceso por rol", "Las pantallas de pagos y tarifas solo están disponibles para el rol Administrador; los operarios son redirigidos al panel.", "Alta"],
];
const rnf = [
  ["RNF-15", "Integridad", "La base de datos debe impedir dos pagos para la misma mensualidad. Pago y mensualidad se confirman en una sola transacción."],
  ["RNF-16", "Trazabilidad", "Cada pago guarda el valor cobrado, el medio, la referencia, quién lo registró y, si se anula, el motivo, la fecha y quién lo anuló. Cambiar una tarifa no altera pagos anteriores."],
  ["RNF-17", "Usabilidad", "Los valores se muestran en pesos con separador de miles ($150.000). Si un formulario falla se explica el motivo y se conservan los datos escritos. El botón «Registrar pago» solo aparece en vehículos sin mensualidad vigente."],
  ["RNF-18", "Seguridad y calidad", "Toda petición POST de pagos y tarifas lleva la ficha anti-CSRF (RNF-10). Las reglas viven en servicios cubiertos por pruebas automáticas (49 pruebas nuevas; 125 en total)."],
];

// ---------- 2.3 Historias ----------
const hu = [
  ["HU-21", "Consultar tarifas", "administrador", "ver el valor mensual de cada tipo de vehículo", "saber cuánto se le cobra a cada cliente", ["Se listan carro y moto con su valor en pesos.", "Solo el administrador accede."], "Media", 2],
  ["HU-22", "Actualizar tarifa", "administrador", "cambiar el valor de la mensualidad de un tipo de vehículo", "ajustar los precios cuando el negocio lo decida", ["Acepto el valor con puntos, comas o signo de pesos.", "Debe estar entre $10.000 y $5.000.000; si no, se rechaza y la tarifa no cambia.", "Los pagos ya registrados conservan su valor."], "Alta", 3],
  ["HU-23", "Registrar pago y activar mensualidad", "administrador", "registrar el pago de la mensualidad de un vehículo", "que el vehículo pueda ingresar durante 30 días", ["Se cobra la tarifa de su tipo (carro o moto).", "Elijo efectivo, transferencia o tarjeta; en transferencia y tarjeta la referencia es obligatoria.", "Se activa la mensualidad de hoy a hoy + 29 días.", "Si ya hay una vigente, se rechaza y no se crea el pago.", "Si la anterior venció, se renueva."], "Alta", 5],
  ["HU-24", "Consultar pagos y total recaudado", "administrador", "ver los pagos y filtrarlos", "controlar lo que ha recaudado el parqueadero", ["Lista de más reciente a más antiguo, paginada.", "Filtro por placa, documento o apellido, medio, estado y fechas.", "Muestra el total recaudado sin contar los anulados.", "Si la fecha inicial es posterior a la final, se avisa."], "Media", 3],
  ["HU-25", "Ver e imprimir el comprobante", "administrador", "abrir el comprobante de un pago", "entregarle al cliente una constancia de lo que pagó", ["Muestra número, fecha, cliente, vehículo, vigencia, medio, valor y quién lo registró.", "Se puede imprimir sin los botones de la pantalla."], "Media", 2],
  ["HU-26", "Anular pago", "administrador", "anular un pago registrado por error", "corregir cobros equivocados sin borrar el historial", ["El motivo es obligatorio (5 a 255 caracteres).", "El pago queda ANULADO y la mensualidad CANCELADA.", "Con el pago anulado el vehículo no entra, pero se puede registrar un pago nuevo.", "No se anula un pago ya anulado ni uno cuya mensualidad ya venció."], "Alta", 3],
];
const totalPts = hu.reduce((a, h) => a + h[7], 0);

const e21 = [
  h2("2.1 Requerimientos funcionales y no funcionales"),
  p("Se continúa la numeración de las iteraciones anteriores. Estos requerimientos cubren la gestión de pagos pedida y su efecto sobre la mensualidad de la iteración 2: el requerimiento RF-32 **reemplaza** la activación manual de mensualidad (RF-21), que ahora ocurre únicamente al registrar el pago."),
  h3("Requerimientos funcionales"),
  ...tabla("Requerimientos funcionales de la iteración 3", [900, 2100, 5460, 900], ["ID", "Nombre", "Descripción", "Prioridad"], rf, { primeraNegrita: true }),
  h3("Requerimientos no funcionales"),
  ...tabla("Requerimientos no funcionales de la iteración 3", [1000, 2100, 6260], ["ID", "Categoría", "Descripción / criterio"], rnf, { primeraNegrita: true }),
  h3("Reglas de negocio de la iteración"),
  bullet("El valor que se cobra es la tarifa vigente del tipo de vehículo; queda guardado en el pago."),
  bullet("No existe mensualidad sin pago: la mensualidad se activa al pagar y se cancela al anular el pago."),
  bullet("Una sola mensualidad vigente por vehículo y un solo pago por mensualidad."),
  bullet("Un pago solo se anula mientras su mensualidad esté vigente: si ya venció, el servicio fue prestado."),
];

// ---------- 2.2 Casos de uso ----------
const e22 = [
  h2("2.2 Diagramas de casos de uso", true),
  p("El primer diagrama muestra los casos de uso de la gestión de pagos. El segundo es la visión general de las tres iteraciones, donde se ve cómo «Registrar pago» **incluye** activar la mensualidad y cómo la entrada de vehículos valida la mensualidad vigente y asigna una celda libre. Los diagramas se elaboraron en PlantUML."),
  ...figura("diagrams/e3/30_casos_uso_pagos.png", "Casos de uso: gestión de pagos.", 600, 560),
  ...figura("diagrams/e3/31_casos_uso_general.png", "Casos de uso: visión general de las tres iteraciones.", 600, 520),
  ...tabla("Permisos por rol", [3600, 2880, 2880], ["Función", "Operario", "Administrador"], [
    ["Registrar entrada y salida, ver panel y vehículos dentro", "Sí", "Sí"],
    ["Historial de movimientos", "No", "Sí"],
    ["Usuarios, clientes, vehículos y celdas (HU-07 a HU-20)", "No", "Sí"],
    ["Tarifas (HU-21 y HU-22)", "No", "Sí"],
    ["Registrar, consultar y anular pagos; comprobantes (HU-23 a HU-26)", "No", "Sí"],
  ], { primeraNegrita: true }),
];

// ---------- 2.3 Historias ----------
const e23 = [
  h2("2.3 Historias de usuario", true),
  p("Se mantiene el formato «Como [rol] quiero [acción] para [beneficio]» con criterios de aceptación. Las estimaciones están en puntos de historia."),
  ...tabla("Historias de usuario HU-21 a HU-26", [800, 3200, 4260, 1100],
    ["ID", "Historia", "Criterios de aceptación", "Prioridad / puntos"],
    hu.map((h, i) => [`**${h[0]}**`,
      [`**${h[1]}.** Como ${h[2]}, quiero ${h[3]}, para ${h[4]}.`, `Mockup: ${["MK-20","MK-21","MK-17 / MK-22","MK-16","MK-18","MK-19"][i]}`],
      h[5].map((c, j) => `${j + 1}. ${c}`), `${h[6]} · ${h[7]} pts`])),
  p(`Total estimado de la iteración: **${totalPts} puntos de historia**.`),
];

// ---------- 2.4 Mockups ----------
const mk = [
  ["MK-20_tarifas.png", "MK-20 · Tarifas de la mensualidad (HU-21)."],
  ["MK-21_tarifa_editar.png", "MK-21 · Editar tarifa (HU-22)."],
  ["MK-22_cliente_pago.png", "MK-22 · Detalle del cliente con el botón «Registrar pago» (HU-23)."],
  ["MK-17_pago_nuevo.png", "MK-17 · Registrar pago y activar mensualidad (HU-23)."],
  ["MK-16_pagos.png", "MK-16 · Lista de pagos con filtros y total recaudado (HU-24)."],
  ["MK-18_comprobante.png", "MK-18 · Comprobante de pago y anulación (HU-25, HU-26)."],
  ["MK-19_pago_anulado.png", "MK-19 · Pago anulado (HU-26)."],
];
const e24 = [
  h2("2.4 Mockups", true),
  p("Se diseñaron siete pantallas con la misma identidad visual de las iteraciones anteriores. Junto a cada formulario se incluyen los mensajes de éxito y error previstos. Los mockups se generaron como imágenes con un script (mockups/generar_mockups_e3.py) en lugar de Figma; sirven de guía exacta de colores, tamaños y textos, y las pantallas reales de la aplicación siguen el mismo diseño."),
  ...mk.flatMap(([f, t]) => figura(`mockups/${f}`, t, 600, 366)),
];

// ---------- 2.5 Secuencia ----------
const seq = [
  ["Acceso", "Iniciar sesión (usuario o contraseña incorrectos, usuario desactivado)", "Todas", "32_sec_login.png", "Secuencia: iniciar sesión."],
  ["Acceso", "Control de acceso por rol y ficha CSRF en las pantallas administrativas", "RF-27, RF-38", "33_sec_acceso.png", "Secuencia: control de acceso por rol."],
  ["It. 1", "Registrar entrada, con la regla de asignación de celda", "HU-01", "34_sec_entrada.png", "Secuencia: registrar entrada y asignar celda."],
  ["It. 1", "Registrar salida", "HU-02", "35_sec_salida.png", "Secuencia: registrar salida."],
  ["It. 2", "Crear usuario", "HU-08", "36_sec_usuario_crear.png", "Secuencia: crear usuario."],
  ["It. 2", "Editar usuario", "HU-09", "37_sec_usuario_editar.png", "Secuencia: editar usuario."],
  ["It. 2", "Activar o desactivar usuario", "HU-10", "38_sec_usuario_estado.png", "Secuencia: activar o desactivar usuario."],
  ["It. 2", "Restablecer contraseña", "HU-11", "39_sec_usuario_clave.png", "Secuencia: restablecer contraseña."],
  ["It. 2", "Registrar cliente", "HU-12", "40_sec_cliente.png", "Secuencia: registrar cliente."],
  ["It. 2", "Registrar vehículo (sin activar mensualidad)", "HU-13", "41_sec_vehiculo.png", "Secuencia: registrar vehículo."],
  ["It. 2", "Crear celda", "HU-17", "42_sec_celda_crear.png", "Secuencia: crear celda."],
  ["It. 2", "Editar celda", "HU-18", "43_sec_celda_editar.png", "Secuencia: editar celda."],
  ["It. 2", "Poner en mantenimiento / habilitar celda", "HU-19", "44_sec_celda_estado.png", "Secuencia: poner en mantenimiento o habilitar una celda."],
  ["It. 2", "Eliminar celda", "HU-20", "45_sec_celda_eliminar.png", "Secuencia: eliminar celda."],
  ["It. 3", "Actualizar tarifa", "HU-22", "46_sec_tarifa.png", "Secuencia: actualizar tarifa."],
  ["It. 3", "Registrar pago y activar mensualidad", "HU-23", "47_sec_pago_registrar.png", "Secuencia: registrar pago y activar mensualidad."],
  ["It. 3", "Anular pago", "HU-26", "48_sec_pago_anular.png", "Secuencia: anular pago."],
  ["It. 3", "Consultar pagos y ver comprobante", "HU-24, HU-25", "49_sec_pago_consultar.png", "Secuencia: consultar pagos y ver comprobante."],
];
const baseSeq = nFigura + 1;
const e25 = [
  h2("2.5 Diagramas de secuencia (iteraciones 1, 2 y 3)", true),
  p("Se actualizó el conjunto de secuencias para cubrir **las tres iteraciones**, con un diagrama por operación y sus **rechazos**. En todos, la petición pasa por la ruta (sesión, rol y ficha CSRF), el servicio (reglas) y la base de datos. Los archivos completos están en diagrams/e3."),
  ...tabla("Cobertura de los diagramas de secuencia", [1100, 7560, 2200, 2100], ["Iteración", "Operación", "Historia / RF", "Figura"],
    seq.map((s, i) => [s[0], s[1], s[2], `Figura ${baseSeq + i}`]), { primeraNegrita: true }),
  ...seq.flatMap((s, i) => [
    ...(i === 0 ? [h3("Acceso al sistema")] : []),
    ...(i === 2 ? [h3("Iteración 1: entrada y salida")] : []),
    ...(i === 4 ? [h3("Iteración 2: usuarios")] : []),
    ...(i === 8 ? [h3("Iteración 2: clientes y vehículos")] : []),
    ...(i === 10 ? [h3("Iteración 2: celdas")] : []),
    ...(i === 14 ? [h3("Iteración 3: pagos")] : []),
    ...figura(`diagrams/e3/${s[3]}`, s[4], 680, 470),
  ]),
];

// ---------- 2.6 Componentes ----------
const e26 = [
  h2("2.6 Diagrama de componentes (iteraciones 1, 2 y 3)", true),
  p("El diagrama muestra la arquitectura en capas con los componentes de las tres iteraciones, marcados con «it.1», «it.2» e «it.3». Pagos se sumó como dos parejas ruta + servicio (pagos y tarifas) sin modificar la estructura existente. Las flechas entre servicios muestran las dependencias de la iteración: el pago usa la tarifa del tipo de vehículo y le pide al servicio de clientes preparar la mensualidad, y la entrada de vehículos usa las celdas libres."),
  ...figura("diagrams/e3/50_componentes.png", "Diagrama de componentes de Autos Colombia (iteraciones 1, 2 y 3).", 620, 460),
];

// ---------- 2.7 Plan de pruebas ----------
const cp = [
  ["CP-34", "HU-21", "Abrir la lista de tarifas.", "Muestra Carro $150.000 y Moto $70.000."],
  ["CP-35", "HU-22", "Actualizar la tarifa del carro con «180000», «$ 180.000» y «1,200,000».", "Se guarda como número entero de pesos ($180.000, $180.000 y $1.200.000)."],
  ["CP-36", "HU-22", "Actualizar con valor vacío, «abc», «12.5x», «5000», «5.000.001», «-100» y «0».", "Cada caso se rechaza con su mensaje y la tarifa sigue en $150.000."],
  ["CP-37", "HU-22", "Editar la tarifa del tipo «BUS».", "Responde «no encontrado» (404)."],
  ["CP-38", "HU-22", "Registrar un pago y luego cambiar la tarifa.", "El pago ya registrado conserva el valor que se cobró."],
  ["CP-39", "HU-23", "Pagar en efectivo la mensualidad de un carro sin mensualidad.", "Cobra $150.000 y activa la mensualidad de 30 días desde hoy."],
  ["CP-40", "HU-23", "Pagar la mensualidad de una moto.", "Cobra la tarifa de moto ($70.000)."],
  ["CP-41", "HU-23", "Pagar por transferencia y por tarjeta con referencias en minúsculas.", "Se guarda la referencia en mayúsculas."],
  ["CP-42", "HU-23", "Pagar con medio inválido; transferencia sin referencia; referencia de 3 caracteres o con símbolos.", "Se rechaza con su mensaje y no se crea pago ni mensualidad."],
  ["CP-43", "HU-23", "Pagar en efectivo enviando una referencia.", "No se guarda la referencia."],
  ["CP-44", "HU-23", "Pagar un vehículo que ya tiene mensualidad vigente.", "Se rechaza y no se crea un segundo pago."],
  ["CP-45", "HU-23", "Pagar cuando la mensualidad anterior ya venció.", "Se crea una mensualidad nueva ACTIVA y la vieja pasa a VENCIDA."],
  ["CP-46", "HU-23", "Un vehículo sin mensualidad intenta entrar; se paga y se reintenta.", "Primero se rechaza; después del pago, entra."],
  ["CP-47", "HU-23", "Insertar a la fuerza un segundo pago para la misma mensualidad, saltándose el servicio.", "La base de datos lo rechaza (índice único)."],
  ["CP-48", "HU-23", "Pagar por un vehículo que no existe (id 9999).", "Responde 404."],
  ["CP-49", "HU-26", "Anular un pago indicando un motivo.", "Queda ANULADO con motivo, fecha y usuario; la mensualidad queda CANCELADA."],
  ["CP-50", "HU-26", "Con el pago anulado, intentar la entrada y luego registrar un pago nuevo.", "No entra; se puede pagar de nuevo."],
  ["CP-51", "HU-26", "Anular con motivo vacío, de pocos caracteres o de más de 255.", "Se rechaza y el pago sigue registrado."],
  ["CP-52", "HU-26", "Anular un pago ya anulado y uno que no existe.", "Se rechazan (el segundo con 404)."],
  ["CP-53", "HU-26", "Anular un pago cuya mensualidad ya venció.", "Se rechaza: el servicio ya fue prestado."],
  ["CP-54", "HU-24", "Abrir la lista de pagos con los datos de ejemplo.", "Muestra los 5 pagos, del más reciente al más antiguo."],
  ["CP-55", "HU-24", "Filtrar por placa, documento, apellido, medio, estado y rango de fechas.", "Cada filtro devuelve solo los pagos que coinciden."],
  ["CP-56", "HU-24", "Ver el total recaudado y anular un pago.", "El total suma solo los pagos REGISTRADOS y baja al anular."],
  ["CP-57", "HU-24", "Poner la fecha inicial posterior a la final.", "La pantalla avisa y no falla."],
  ["CP-58", "RF-38", "Abrir las pantallas de pagos y tarifas sin sesión, como operario y como administrador.", "Sin sesión: login; operario: redirigido al panel; administrador: acceso (200)."],
  ["CP-59", "General", "Abrir un pago y una tarifa que no existen.", "Responde 404, no un error del servidor."],
  ["CP-60", "RNF-10", "Registrar y anular un pago sin la ficha CSRF.", "Se rechaza con 400."],
  ["CP-61", "HU-23", "Abrir el detalle de un cliente con vehículos con y sin mensualidad.", "«Registrar pago» aparece solo en los vehículos sin mensualidad vigente."],
  ["CP-62", "RNF-17", "Enviar el formulario de pago por transferencia sin referencia.", "400, explica el error y conserva el medio elegido."],
  ["CP-63", "HU-25 / flujo", "Cambiar tarifa, pagar con tarjeta, abrir el comprobante, registrar la entrada, anular el pago e intentar entrar.", "Todo se confirma; tras anular, el vehículo ya no entra."],
  ["CP-64", "RNF-17", "Anular desde la pantalla con un motivo muy corto.", "400, explica el error y conserva lo escrito."],
];
const e27 = [
  h2("2.7 Plan de pruebas resumido: gestión de pagos", true),
  p("Se diseñaron 31 casos que cubren las historias HU-21 a HU-26, los requerimientos de seguridad y usabilidad, y un flujo completo de extremo a extremo. Cada caso está automatizado en el archivo tests/test_iteracion3.py (los casos con varios datos de entrada se ejecutan como varias pruebas) y el ID del caso aparece en la descripción de cada prueba. La numeración continúa la del plan de la iteración 2 (CP-01 a CP-33)."),
  p("**Entorno de ejecución:** Python 3, pytest y base de datos SQLite en memoria. **Criterio de aprobación:** el resultado obtenido coincide con el esperado. **Resultado global:** las 125 pruebas del proyecto (30 de la iteración 1, 46 de la 2 y 49 nuevas) se ejecutaron y aprobaron. Las 76 de las iteraciones 1 y 2 se ejecutaron además sobre MySQL 9.4."),
  ...tabla("Casos de prueba de la iteración 3", [950, 1000, 3300, 3010, 1100],
    ["ID", "HU / RF", "Descripción y datos de prueba", "Resultado esperado", "Estado"],
    cp.map((c) => [`**${c[0]}**`, c[1], c[2], c[3], "Aprobada"])),
  p("Para repetirlas: `python -m pytest -v` desde la carpeta del proyecto."),
];

// ---------- 2.8 Código ----------
const e28 = [
  h2("2.8 Código fuente y repositorio", true),
  p("El código completo de las tres iteraciones está en GitHub:"),
  new Paragraph({ spacing: { after: 160 }, children: [new ExternalHyperlink({ link: REPO, children: [new TextRun({ text: REPO, style: "Hyperlink", color: "1155CC", underline: {} })] })] }),
  h3("Archivos nuevos o modificados en la iteración 3"),
  ...tabla("Estructura de lo agregado", [3700, 5660], ["Archivo", "Contenido"], [
    ["app/services/pagos.py", "Reglas de tarifas y pagos: actualizar tarifa, registrar pago (activa la mensualidad), anular, consultar y total recaudado."],
    ["app/routes/pagos.py", "Rutas de pagos, comprobante y tarifas (solo administrador)."],
    ["app/services/clientes.py", "La mensualidad ahora se prepara desde el pago; se retira la activación manual."],
    ["app/models/__init__.py, db/schema.sql", "Tablas tarifa y pago, con índice único de un pago por mensualidad."],
    ["app/templates/pagos.html, pago_form.html, pago_detalle.html, tarifas.html, tarifa_form.html", "Pantallas de pagos, comprobante y tarifas; menú «Pagos»."],
    ["app/cli.py", "Datos de ejemplo: tarifas y un pago por cada mensualidad."],
    ["tests/test_iteracion3.py", "31 casos de prueba (49 pruebas)."],
    ["diagrams/e3/, mockups/", "Diagramas PlantUML y mockups de esta entrega."],
  ], { primeraNegrita: true }),
  h3("Cómo ejecutarlo"),
  bullet("Crear la base de datos ejecutando db/schema.sql en MySQL Workbench (el esquema cambió: incluye las tablas tarifa y pago)."),
  bullet("Cargar los datos de ejemplo con el comando de semilla del proyecto y arrancar la aplicación con Flask."),
  bullet("Ingresar como administrador para ver el menú Pagos con sus tarifas, pagos y comprobantes."),
];

// ---------- 2.9 Video ----------
const e29 = [
  h2("2.9 Video de demostración"),
  p("El video muestra el funcionamiento de las tres iteraciones: entradas y salidas, usuarios, clientes, vehículos, celdas y pagos, junto con la ejecución de las pruebas automáticas."),
  VIDEO
    ? new Paragraph({ spacing: { after: 160 }, children: [new ExternalHyperlink({ link: VIDEO, children: [new TextRun({ text: VIDEO, style: "Hyperlink", color: "1155CC", underline: {} })] })] })
    : new Paragraph({ spacing: { after: 160 }, children: [resaltado("[PEGAR AQUÍ EL ENLACE DEL VIDEO EN YOUTUBE]", { bold: true })] }),
];

const entregablesA = [
  h1("2. Entregables de la iteración 3"),
  p("A continuación se presentan los entregables de la iteración 3: Gestión de pagos."),
  ...e21, ...e22, ...e23, ...e24,
];
const entregablesC = [...e26, ...e27, ...e28, ...e29];

// ---------- 3 Conclusiones ----------
const conclusiones = [
  h1("3. Conclusiones"),
  p("Con esta iteración el sistema “Autos Colombia” queda completo para operar el parqueadero por mensualidad: registra entradas y salidas, administra usuarios, clientes, vehículos y celdas, y cobra y controla los pagos."),
  bullet("**El pago y la mensualidad quedaron unidos:** al cobrar se activa la mensualidad y al anular se cancela, de modo que ningún vehículo entra sin haber pagado. Las dos operaciones se guardan juntas o no se guarda ninguna."),
  bullet("**La arquitectura en capas volvió a funcionar:** pagos y tarifas se agregaron como servicios y rutas nuevos y las 76 pruebas anteriores siguieron aprobando; el proyecto suma 125 pruebas."),
  bullet("**Las reglas críticas se defienden dos veces:** en el servicio, con mensajes claros, y en la base de datos, con índices únicos (una mensualidad activa por vehículo y un pago por mensualidad)."),
  bullet("**Trazabilidad del dinero:** cada pago guarda lo que se cobró, quién lo registró y, si se anuló, por qué y quién lo hizo; cambiar una tarifa nunca altera lo ya cobrado."),
  bullet("**Aprendizaje del modelado:** la retroalimentación de la iteración 2 mostró que cada operación merece su propio diagrama con sus rechazos y que las reglas de negocio deben mostrarse donde ocurren. Se aplicó al conjunto completo de secuencias."),
  h3("Limitaciones y trabajo futuro"),
  bullet("Los diagramas se hicieron en PlantUML y los mockups como imágenes generadas por código, no en StarUML ni Figma."),
  bullet("Los pagos se registran manualmente: no hay conexión con una pasarela de pagos ni con facturación electrónica."),
  bullet("Posibles mejoras: recordatorios de mensualidades por vencer, reportes de ingresos por mes y permitir que el operario registre pagos."),
];


// ---------- DOCUMENTO ----------
function pie() {
  return new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
    border: { top: { style: BorderStyle.SINGLE, size: 4, color: "C5CFDC", space: 6 } },
    children: [run("Autos Colombia · EA3 · Iteración 3   |   Página ", { size: 17, color: GRIS }),
      new TextRun({ children: [PageNumber.CURRENT], size: 17, color: GRIS })] })] });
}
const doc = new Document({
  creator: "Luis Fernando Soto",
  title: "Autos Colombia - EA3 Iteración 3: Gestión de pagos",
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
    { properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1300, left: 1440 }, pageNumbers: { start: 1 } } },
      footers: { default: pie() }, children: [...introduccion, ...entregablesA] },
    { properties: { page: { size: { width: 12240, height: 15840, orientation: PageOrientation.LANDSCAPE }, margin: { top: 1000, right: 1000, bottom: 1000, left: 1000 } } },
      footers: { default: pie() }, children: e25 },
    { properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1300, left: 1440 } } },
      footers: { default: pie() }, children: [...entregablesC, ...conclusiones] },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(__dirname, "Soto_Luis_EA3.docx");
  fs.writeFileSync(out, buf);
  console.log("OK", out, buf.length, "bytes;", nFigura, "figuras;", nTabla, "tablas");
});
