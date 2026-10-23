// Genera docs/Soto_Fernando_EA1.docx a partir de los diagramas, mockups y textos.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, AlignmentType,
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

// ---------- PORTADA ----------
const portada = [
  new Paragraph({ spacing: { before: 1400, after: 0 }, alignment: AlignmentType.CENTER,
    children: [run("INSTITUCIÓN UNIVERSITARIA DIGITAL DE ANTIOQUIA", { bold: true, size: 24, color: GRIS })] }),
  new Paragraph({ spacing: { before: 60, after: 900 }, alignment: AlignmentType.CENTER,
    border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: "E8A317", space: 12 } },
    children: [run("Facultad de Ingeniería · Ingeniería de Software", { size: 22, color: GRIS })] }),
  new Paragraph({ spacing: { after: 160 }, alignment: AlignmentType.CENTER,
    children: [run("Sistema de información del parqueadero", { bold: true, size: 44, color: AZUL })] }),
  new Paragraph({ spacing: { after: 400 }, alignment: AlignmentType.CENTER,
    children: [run("“Autos Colombia”", { bold: true, size: 56, color: "E8A317" })] }),
  new Paragraph({ spacing: { after: 120 }, alignment: AlignmentType.CENTER,
    children: [run("Evidencia de aprendizaje EA1", { size: 28, color: AZUL, bold: true })] }),
  new Paragraph({ spacing: { after: 1500 }, alignment: AlignmentType.CENTER,
    children: [run("Iteración 1: Gestión de la entrada y salida de vehículos", { size: 26, color: AZUL })] }),
  new Paragraph({ spacing: { after: 80 }, alignment: AlignmentType.CENTER,
    children: [run("Presentado por:", { size: 22, color: GRIS })] }),
  new Paragraph({ spacing: { after: 300 }, alignment: AlignmentType.CENTER,
    children: [run("Fernando Soto", { size: 28, bold: true })] }),
  new Paragraph({ spacing: { after: 80 }, alignment: AlignmentType.CENTER,
    children: [run("Asesor:", { size: 22, color: GRIS })] }),
  new Paragraph({ spacing: { after: 700 }, alignment: AlignmentType.CENTER,
    children: [resaltado("[Nombre del asesor]", { size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [run("Bogotá, Colombia · 20 de octubre de 2026", { size: 22, color: GRIS })] }),
];

// ---------- INTRODUCCIÓN ----------
const introduccion = [
  h1("1. Introducción", false),
  p("El parqueadero “Autos Colombia” presta el servicio de estacionamiento por mensualidad y hoy necesita un sistema de información que ordene sus operaciones diarias: registrar las entradas y salidas de los vehículos, administrar usuarios y celdas, anotar las novedades que ocurran sobre un vehículo y gestionar los pagos. Llevar este control de forma manual genera errores, dificulta saber qué vehículos están dentro y no deja una huella confiable de quién hizo cada registro."),
  p("Este documento recoge la **primera iteración** del desarrollo, centrada en el requerimiento funcional de **gestión de la entrada y salida de vehículos**. Las otras dos áreas del alcance general (gestión de usuarios y celdas, y gestión de pagos) quedan para las siguientes iteraciones; aquí solo se modelan los elementos mínimos que necesitan para funcionar (clientes, vehículos, mensualidades y celdas)."),
  p("Siguiendo la ruta metodológica de la unidad de Ingeniería de Software, el trabajo recorre el ciclo completo de una iteración: se parte del análisis (requerimientos funcionales y no funcionales e historias de usuario), se continúa con el diseño (arquitectura, mockups, modelo de datos, casos de uso, clases y paquetes) y se termina con la construcción de un código fuente funcional, acompañado de pruebas automáticas."),
  p("El documento se organiza así: la sección 2 presenta los nueve entregables de la iteración; la sección 3 expone las conclusiones, incluyendo las decisiones de diseño más importantes y los pasos siguientes."),
  h3("Alcance de la iteración 1"),
  bullet("**Incluido:** inicio de sesión con roles, registro de entrada y de salida, validación de mensualidad vigente, asignación y liberación de celdas, consulta de vehículos dentro, consulta de ocupación e historial de movimientos."),
  bullet("**Fuera de alcance (próximas iteraciones):** altas, bajas y modificaciones de clientes, vehículos, usuarios y celdas; registro de novedades; cobro y control de pagos de mensualidades."),
];

// ---------- ENTREGABLES ----------
const rf = [
  ["RF-01", "Autenticar usuarios", "El sistema debe permitir iniciar sesión con usuario y contraseña y cerrar sesión. Solo usuarios activos pueden ingresar.", "Alta"],
  ["RF-02", "Control de acceso por rol", "El sistema debe distinguir los roles Operario y Administrador. El Operario registra entradas y salidas y consulta el panel y los vehículos dentro; el Administrador, además, consulta el historial.", "Alta"],
  ["RF-03", "Registrar entrada", "El sistema debe registrar la entrada de un vehículo a partir de su placa, guardando de forma automática la fecha y hora y el operario que la registra, con observaciones opcionales (máx. 255 caracteres).", "Alta"],
  ["RF-04", "Validar mensualidad vigente", "El sistema debe permitir el ingreso solo si el vehículo tiene una mensualidad en estado ACTIVA cuya vigencia cubra la fecha actual.", "Alta"],
  ["RF-05", "Validar vehículo y evitar duplicados", "El sistema debe verificar que la placa corresponda a un vehículo registrado y que no tenga ya una entrada sin salida.", "Alta"],
  ["RF-06", "Asignar celda", "El sistema debe asignar automáticamente la primera celda libre del mismo tipo del vehículo (carro o moto), o la celda que indique el operario si está libre y es compatible, y marcarla como OCUPADA.", "Alta"],
  ["RF-07", "Registrar salida", "El sistema debe registrar la salida de un vehículo a partir de su placa: guardar fecha y hora y operario, liberar la celda y mostrar el tiempo de permanencia.", "Alta"],
  ["RF-08", "Impedir salidas inconsistentes", "El sistema no debe permitir registrar la salida de un vehículo que no tenga una entrada abierta.", "Alta"],
  ["RF-09", "Consultar vehículos dentro", "El sistema debe listar los vehículos que están actualmente en el parqueadero (placa, tipo, cliente, celda, hora de entrada, tiempo dentro) y permitir buscar por placa.", "Media"],
  ["RF-10", "Consultar ocupación de celdas", "El sistema debe mostrar el estado de cada celda (libre, ocupada, mantenimiento) y un resumen de totales por tipo de vehículo.", "Media"],
  ["RF-11", "Consultar historial de movimientos", "El sistema debe permitir al Administrador consultar todos los movimientos, filtrar por placa y rango de fechas, y navegar por páginas.", "Media"],
  ["RF-12", "Mensajes al usuario", "El sistema debe informar con mensajes claros el resultado de cada operación y la causa de cualquier rechazo (por ejemplo: sin mensualidad, vehículo ya dentro, sin celdas libres).", "Media"],
];
const rnf = [
  ["RNF-01", "Rendimiento", "Registrar una entrada o una salida debe responder en menos de 2 segundos en condiciones normales de operación."],
  ["RNF-02", "Usabilidad", "Una entrada o una salida debe poder registrarse en un máximo de 3 acciones (escribir la placa, completar opcionales, confirmar). La interfaz estará en español y se adaptará a pantallas desde 360 px de ancho."],
  ["RNF-03", "Seguridad", "Las contraseñas se almacenan con hash (nunca en texto plano); todas las rutas, salvo el inicio de sesión, exigen sesión activa; el historial exige rol Administrador; el mensaje de error de acceso no revela si el usuario existe; las consultas usan un ORM (sin concatenar SQL) y las plantillas escapan el contenido."],
  ["RNF-04", "Integridad de datos", "Las operaciones de entrada y salida son transaccionales. La base de datos debe impedir por sí misma que un vehículo o una celda tengan dos movimientos abiertos al mismo tiempo, aun con operarios concurrentes."],
  ["RNF-05", "Disponibilidad", "El sistema debe estar disponible durante el horario de atención del parqueadero (meta: 99 % mensual)."],
  ["RNF-06", "Mantenibilidad", "Arquitectura en capas con las reglas de negocio aisladas en servicios, código siguiendo PEP 8 y pruebas automáticas de las reglas críticas."],
  ["RNF-07", "Portabilidad y compatibilidad", "Aplicación web compatible con las versiones recientes de Chrome, Edge y Firefox; ejecutable en Windows, Linux o macOS con Python 3.10+ y MySQL 8."],
  ["RNF-08", "Trazabilidad", "Cada movimiento debe conservar quién registró la entrada, quién registró la salida y en qué momento."],
];

const hu = [
  { id: "HU-01", t: "Iniciar sesión", rol: "operario del parqueadero", q: "iniciar sesión con mi usuario y contraseña", para: "acceder de forma segura a las funciones que me corresponden",
    ca: ["Dado que ingreso credenciales válidas, cuando presiono «Ingresar», entonces veo el panel del sistema.", "Dado que ingreso credenciales incorrectas, entonces veo «Usuario o contraseña incorrectos» sin saber cuál de los dos falló.", "Dado que no he iniciado sesión, cuando intento abrir cualquier otra página, entonces soy llevado al inicio de sesión.", "Dado que soy Operario, cuando intento abrir el historial, entonces el sistema me lo niega."],
    prio: "Alta", pts: "2", rfs: "RF-01, RF-02", mk: "MK-01" },
  { id: "HU-02", t: "Registrar entrada de un vehículo", rol: "operario del parqueadero", q: "registrar la entrada de un vehículo escribiendo su placa", para: "dejar constancia de que está en el parqueadero y saber en qué celda quedó",
    ca: ["Dado un vehículo con mensualidad vigente y celdas libres de su tipo, cuando registro la entrada, entonces se guarda la fecha y hora, mi usuario y la celda asignada, y esta pasa a OCUPADA.", "Dado un vehículo sin mensualidad vigente, entonces el sistema rechaza el ingreso e indica el motivo.", "Dado un vehículo que ya está dentro, entonces el sistema rechaza la entrada duplicada.", "Dado que no hay celdas libres de ese tipo, entonces el sistema lo informa y no registra nada.", "Dado que indico una celda, entonces el sistema solo la acepta si existe, está libre y es del tipo del vehículo.", "La placa se acepta en mayúsculas o minúsculas, con o sin guion (5 a 7 caracteres alfanuméricos)."],
    prio: "Alta", pts: "8", rfs: "RF-03, RF-04, RF-05, RF-06, RF-12", mk: "MK-03" },
  { id: "HU-03", t: "Registrar salida de un vehículo", rol: "operario del parqueadero", q: "registrar la salida de un vehículo escribiendo su placa", para: "cerrar su permanencia y dejar libre la celda para otro vehículo",
    ca: ["Dado un vehículo con entrada abierta, cuando registro la salida, entonces se guarda la fecha y hora y mi usuario, y la celda queda LIBRE.", "Tras la salida, el sistema muestra el tiempo de permanencia.", "Dado un vehículo sin entrada abierta, entonces el sistema rechaza la salida.", "Las observaciones de la salida se agregan a las de la entrada, sin perderlas."],
    prio: "Alta", pts: "5", rfs: "RF-07, RF-08, RF-12", mk: "MK-04" },
  { id: "HU-04", t: "Ver los vehículos dentro del parqueadero", rol: "operario del parqueadero", q: "ver la lista de vehículos que están dentro y buscar por placa", para: "ubicar rápidamente un vehículo y saber cuánto tiempo lleva estacionado",
    ca: ["La lista muestra solo vehículos con entrada sin salida, con placa, tipo, cliente, celda, hora de entrada y tiempo dentro.", "Al buscar por placa (completa o parcial) la lista se filtra.", "Si no hay resultados, se muestra un mensaje claro."],
    prio: "Media", pts: "3", rfs: "RF-09", mk: "MK-05" },
  { id: "HU-05", t: "Consultar el historial de movimientos", rol: "administrador", q: "consultar todos los movimientos filtrando por placa y fechas", para: "auditar la operación y resolver reclamos de los clientes",
    ca: ["El historial muestra placa, celda, entrada, salida, permanencia, operarios y observaciones, del más reciente al más antiguo.", "Puedo filtrar por placa y por rango de fechas; si la fecha inicial es posterior a la final, el sistema lo advierte.", "Los resultados se paginan de a 15.", "Un movimiento sin salida aparece marcado como «Dentro».", "Solo el Administrador puede acceder."],
    prio: "Media", pts: "5", rfs: "RF-11, RF-02, RF-08 (trazabilidad: RNF-08)", mk: "MK-06" },
  { id: "HU-06", t: "Ver la ocupación de las celdas", rol: "operario del parqueadero", q: "ver el estado de todas las celdas y un resumen de ocupación", para: "decidir si puedo recibir más vehículos sin revisar celda por celda",
    ca: ["Cada celda se muestra con su código y un color según su estado (libre, ocupada, mantenimiento).", "El resumen muestra ocupadas, libres y libres por tipo de vehículo.", "Los datos se actualizan al registrar una entrada o una salida."],
    prio: "Media", pts: "3", rfs: "RF-10", mk: "MK-02" },
];

const entregables = [
  h1("2. Entregables de la iteración 1"),
  p("A continuación se presentan los nueve entregables solicitados para la iteración 1: Gestión de la entrada y salida de vehículos."),

  // 2.1
  h2("2.1 Requerimientos funcionales y no funcionales"),
  p("Los requerimientos se obtuvieron del enunciado del parqueadero “Autos Colombia”: servicio por mensualidad, con control de entradas, salidas y celdas. Se delimitaron a lo que exige la gestión de entrada y salida; cada uno se identifica con un código para poder trazarlo hasta las historias de usuario, el modelo y el código."),
  h3("Requerimientos funcionales"),
  ...tabla("Requerimientos funcionales (RF)", [900, 2000, 5560, 900], ["ID", "Nombre", "Descripción", "Prioridad"], rf, { primeraNegrita: true }),
  h3("Requerimientos no funcionales"),
  ...tabla("Requerimientos no funcionales (RNF)", [1000, 1900, 6460], ["ID", "Categoría", "Descripción / criterio"], rnf, { primeraNegrita: true }),
  h3("Reglas de negocio identificadas"),
  bullet("Solo ingresan vehículos registrados con una mensualidad ACTIVA vigente en la fecha de ingreso."),
  bullet("Un vehículo no puede tener dos entradas abiertas; una celda no puede alojar dos vehículos a la vez."),
  bullet("Un carro solo usa celdas de carro y una moto solo celdas de moto; las celdas en mantenimiento no se asignan."),
  bullet("La salida solo existe si hay una entrada abierta; al registrarla, la celda vuelve a estar libre."),

  // 2.2
  h2("2.2 Historias de usuario", true),
  p("Cada historia sigue el formato «Como [rol] quiero [acción] para [beneficio]» e incluye criterios de aceptación en formato Dado–Cuando–Entonces. La estimación está en puntos de historia (escala Fibonacci) y se indica el mockup asociado."),
  ...hu.flatMap((h) => ficha(`${h.id} · ${h.t}`, [
    ["Historia", [`**Como** ${h.rol}, **quiero** ${h.q}, **para** ${h.para}.`]],
    ["Criterios de aceptación", h.ca.map((c, i) => `${i + 1}. ${c}`)],
    ["Prioridad / Puntos", `${h.prio} · ${h.pts} puntos`],
    ["Requerimientos", h.rfs],
    ["Mockup", h.mk],
  ])),
  p("Total estimado de la iteración: **26 puntos de historia**."),

  // 2.3
  h2("2.3 Arquitectura del sistema", true),
  p("Se eligió una **arquitectura en capas** desplegada como aplicación web, con el patrón MVC en la presentación:"),
  bullet("**Presentación:** navegador con HTML/CSS; en el servidor, rutas (blueprints de Flask) y plantillas Jinja2. Recibe las peticiones, delega y muestra el resultado."),
  bullet("**Negocio:** servicios (AuthService, MovimientoService, OcupacionService) que concentran todas las reglas. Las rutas nunca tocan la base de datos directamente."),
  bullet("**Acceso a datos:** modelos ORM (SQLAlchemy) que mapean las tablas de MySQL y se comunican mediante el conector PyMySQL."),
  p("Esta separación facilita las pruebas (los servicios se prueban sin navegador), permite cambiar la interfaz sin tocar las reglas y deja lista la estructura para sumar las próximas iteraciones (usuarios, celdas y pagos) como nuevos servicios y rutas."),
  ...figura("diagrams/01_arquitectura.png", "Arquitectura del sistema Autos Colombia (diagrama de componentes)."),
  ...tabla("Tecnologías utilizadas", [2400, 2400, 4560], ["Capa", "Tecnología", "Justificación"], [
    ["Cliente", "HTML5 + CSS3", "Interfaz ligera, sin instalación en los equipos del parqueadero."],
    ["Servidor", "Python 3 + Flask", "Framework sencillo y flexible; ideal para una aplicación de tamaño medio."],
    ["Persistencia", "SQLAlchemy + PyMySQL", "ORM que evita SQL manual y protege contra inyección SQL."],
    ["Base de datos", "MySQL 8 (InnoDB)", "Motor relacional con transacciones, llaves foráneas y columnas generadas."],
    ["Calidad", "pytest", "Pruebas automáticas de reglas de negocio y rutas."],
  ], { primeraNegrita: true }),

  // 2.4
  h2("2.4 Mockups de las historias de usuario", true),
  p("Se diseñó una pantalla por historia de usuario con la misma identidad visual (barra azul, acento dorado, estados con color verde/rojo/gris). Cada imagen indica en la esquina inferior la historia que representa; las pantallas de entrada y salida muestran además los mensajes de éxito y error previstos en los criterios de aceptación."),
  ...figura("mockups/MK-01_login.png", "MK-01 · Inicio de sesión (HU-01).", 600, 360),
  ...figura("mockups/MK-02_panel.png", "MK-02 · Panel de ocupación de celdas (HU-06).", 600, 360),
  ...figura("mockups/MK-03_entrada.png", "MK-03 · Registrar entrada de vehículo (HU-02).", 600, 360),
  ...figura("mockups/MK-04_salida.png", "MK-04 · Registrar salida de vehículo (HU-03).", 600, 360),
  ...figura("mockups/MK-05_vehiculos_dentro.png", "MK-05 · Vehículos dentro del parqueadero (HU-04).", 600, 360),
  ...figura("mockups/MK-06_historial.png", "MK-06 · Historial de movimientos (HU-05).", 600, 360),

  // 2.5
  h2("2.5 Modelo de datos: MER, modelo relacional y modelo físico", true),
  h3("Modelo entidad–relación (MER)"),
  p("El MER identifica seis entidades. Un **cliente** puede ser propietario de varios **vehículos**; cada vehículo puede tener varias **mensualidades** a lo largo del tiempo y generar muchos **movimientos** (cada visita al parqueadero). Cada movimiento usa una **celda** y es registrado por un **usuario del sistema** al entrar y, opcionalmente, por otro al salir."),
  ...figura("diagrams/05_mer.png", "Modelo entidad–relación (MER).", 600, 520),
  ...tabla("Cardinalidades del MER", [3000, 2000, 4360], ["Relación", "Cardinalidad", "Lectura"], [
    ["Cliente – Vehículo", "1 : N", "Un cliente puede tener varios vehículos; un vehículo pertenece a un solo cliente."],
    ["Vehículo – Mensualidad", "1 : N", "Un vehículo acumula mensualidades en el tiempo."],
    ["Vehículo – Movimiento", "1 : N", "Un vehículo genera muchos movimientos (visitas)."],
    ["Celda – Movimiento", "1 : N", "Una celda se usa en muchos movimientos, uno a la vez."],
    ["Usuario – Movimiento (entrada)", "1 : N", "Cada movimiento tiene un operario que registró la entrada."],
    ["Usuario – Movimiento (salida)", "0..1 : N", "El operario de salida existe solo cuando el movimiento se cierra."],
  ], { primeraNegrita: true }),
  h3("Modelo relacional (MR)", ),
  p("Al pasar el MER a tablas, cada relación 1:N se resuelve con una llave foránea en el lado «muchos». El modelo cumple la **tercera forma normal**: todos los atributos dependen de la llave primaria, sin dependencias transitivas (por ejemplo, los datos del cliente no se repiten en cada vehículo ni en cada movimiento)."),
  ...figura("diagrams/06_mr.png", "Modelo relacional (MR) con llaves primarias, foráneas y únicas.", 600, 520),
  ...tabla("Esquema relacional (PK = llave primaria; # = llave foránea)", [2300, 7060], ["Relación", "Atributos"], [
    ["usuario_sistema", "**PK** id_usuario, nombre, username (único), password_hash, rol, activo"],
    ["cliente", "**PK** id_cliente, tipo_documento, numero_documento, nombres, apellidos, telefono, email — único (tipo_documento, numero_documento)"],
    ["vehiculo", "**PK** id_vehiculo, placa (única), tipo, marca, color, #id_cliente → cliente"],
    ["mensualidad", "**PK** id_mensualidad, fecha_inicio, fecha_fin, estado, #id_vehiculo → vehiculo"],
    ["celda", "**PK** id_celda, codigo (único), tipo, estado"],
    ["movimiento", "**PK** id_movimiento, fecha_hora_entrada, fecha_hora_salida, observaciones, #id_vehiculo → vehiculo, #id_celda → celda, #id_usuario_entrada → usuario_sistema, #id_usuario_salida → usuario_sistema"],
  ], { primeraNegrita: true }),
  h3("Modelo físico (MySQL 8)"),
  p("El modelo físico define tipos de dato, restricciones y llaves para MySQL con motor InnoDB. Las columnas de dominio cerrado (rol, tipo de vehículo, estado de celda y de mensualidad) usan ENUM, y se agregaron restricciones CHECK para impedir fechas incoherentes."),
  p("**Decisión de diseño destacada:** en la tabla movimiento se crearon dos *columnas generadas* (vehiculo_abierto y celda_abierta) que valen NULL cuando el movimiento ya tiene salida. Con un índice UNIQUE sobre cada una, MySQL garantiza por sí mismo que no pueda existir más de un movimiento abierto por vehículo ni por celda; así, aun si dos operarios actúan a la vez, la base de datos rechaza la inconsistencia. El script completo está en el repositorio (db/schema.sql) y puede ejecutarse directamente en MySQL Workbench."),
  ...figura("diagrams/07_fisico.png", "Modelo físico en MySQL 8.", 600, 560),

  // 2.6
  h2("2.6 Diagrama de casos de uso", true),
  p("El sistema tiene dos actores: el **Operario**, que atiende la entrada y salida de vehículos, y el **Administrador**, que hereda todo lo del Operario y además consulta el historial completo. Los casos de uso «Validar mensualidad vigente» y «Asignar celda libre» se incluyen siempre en el registro de entrada, y «Liberar celda» en el de salida."),
  ...figura("diagrams/02_casos_uso.png", "Diagrama de casos de uso de la gestión de entrada y salida.", 600, 480),
  ...ficha("Especificación del caso de uso CU-02: Registrar entrada de vehículo", [
    ["Actor", "Operario (y Administrador por herencia)"],
    ["Precondiciones", "El actor tiene sesión iniciada. El vehículo está registrado en el sistema."],
    ["Flujo principal", ["1. El actor abre «Registrar entrada» y escribe la placa (y, opcionalmente, una celda y observaciones).", "2. El sistema normaliza la placa y valida su formato.", "3. El sistema valida que el vehículo exista, que tenga mensualidad vigente y que no esté ya dentro.", "4. El sistema asigna la celda libre del tipo del vehículo (o valida la elegida).", "5. El sistema guarda el movimiento con fecha, hora y operario, y marca la celda como ocupada.", "6. El sistema confirma: placa, celda y hora de entrada."]],
    ["Flujos alternos", ["3a. Vehículo no registrado, sin mensualidad vigente o ya dentro: el sistema rechaza e indica el motivo.", "4a. No hay celda libre, la celda elegida no existe, no es del tipo o no está libre: el sistema rechaza e indica el motivo.", "5a. Conflicto de concurrencia detectado por la base de datos: el sistema deshace la operación y pide reintentar."]],
    ["Postcondiciones", "Existe un movimiento abierto para el vehículo y su celda queda en estado OCUPADA."],
  ]),
  ...ficha("Especificación del caso de uso CU-03: Registrar salida de vehículo", [
    ["Actor", "Operario (y Administrador por herencia)"],
    ["Precondiciones", "El actor tiene sesión iniciada. El vehículo tiene un movimiento abierto."],
    ["Flujo principal", ["1. El actor abre «Registrar salida» y escribe la placa (y, opcionalmente, observaciones).", "2. El sistema busca el movimiento abierto del vehículo.", "3. El sistema guarda fecha, hora y operario de salida y libera la celda.", "4. El sistema confirma la salida y muestra el tiempo de permanencia."]],
    ["Flujos alternos", ["2a. El vehículo no existe o no tiene entrada abierta: el sistema rechaza e indica el motivo."]],
    ["Postcondiciones", "El movimiento queda cerrado y la celda en estado LIBRE."],
  ]),

  // 2.7
  h2("2.7 Diagrama de clases", true),
  p("El diagrama de clases se presenta en dos partes: (a) el **dominio** (las seis entidades con sus enumeraciones y los métodos propios de cada una, como Celda.ocupar() o Mensualidad.estaVigente()) y (b) los **servicios** que orquestan las reglas. Las asociaciones y multiplicidades coinciden con el modelo de datos, de modo que el paso de la clase a la tabla es directo."),
  ...figura("diagrams/03a_clases_dominio.png", "Diagrama de clases (a): dominio.", 560, 560),
  ...figura("diagrams/03b_clases_servicios.png", "Diagrama de clases (b): servicios de negocio.", 624, 300),

  // 2.8
  h2("2.8 Diagrama de paquetes", true),
  p("El código se organiza en paquetes con una única dirección de dependencia: las rutas usan servicios, los servicios usan modelos y todos comparten el paquete core (configuración, extensiones y errores de negocio). El paquete tests depende de los demás, pero ninguno depende de él, y db contiene el script SQL equivalente a los modelos."),
  ...figura("diagrams/04_paquetes.png", "Diagrama de paquetes del sistema.", 600, 560),

  // 2.9
  h2("2.9 Código fuente", true),
  p("El sistema quedó implementado como una aplicación web en Python (Flask) con base de datos MySQL. Cubre las seis historias de usuario de la iteración y corre localmente con los pasos del README del repositorio."),
  new Paragraph({ spacing: { after: 120 }, children: [run("Repositorio en GitHub: ", { bold: true }), resaltado("https://github.com/<usuario>/autos-colombia")] }),
  ...tabla("Estructura del proyecto", [2900, 6460], ["Ruta", "Contenido"], [
    ["app/models/", "Entidades: UsuarioSistema, Cliente, Vehiculo, Mensualidad, Celda, Movimiento."],
    ["app/services/", "Reglas de negocio: AuthService, MovimientoService, OcupacionService."],
    ["app/routes/", "Rutas Flask: autenticación, entrada/salida y consultas."],
    ["app/templates/, app/static/", "Vistas Jinja2 y hoja de estilos."],
    ["db/schema.sql", "Modelo físico para MySQL 8."],
    ["tests/", "21 pruebas automáticas (servicios y rutas)."],
    ["diagrams/, mockups/", "Fuentes PlantUML de los diagramas y generador de mockups."],
    ["run.py, requirements.txt, README.md", "Punto de entrada, dependencias e instrucciones de ejecución."],
  ], { primeraNegrita: true }),
  h3("Cómo ejecutarlo"),
  ...codigo([
    "pip install -r requirements.txt",
    "# ejecutar db/schema.sql en MySQL Workbench",
    "export DATABASE_URL=\"mysql+pymysql://root:CLAVE@localhost:3306/autos_colombia\"",
    "flask --app run seed      # datos de ejemplo",
    "python run.py             # http://127.0.0.1:5000",
  ]),
  p("Usuarios de ejemplo: **admin / admin123** (Administrador) y **operario / operario123** (Operario). Placas de ejemplo: ABC123 y DEF456 (carros), MNO12A y PQR34B (motos), y GHI789, que tiene la mensualidad vencida y sirve para comprobar el rechazo."),
  h3("Fragmento representativo: registro de entrada"),
  p("El servicio concentra las reglas en el orden en que deben validarse (versión resumida):"),
  ...codigo([
    "vehiculo = cls._obtener_vehiculo(placa)          # existe y placa válida",
    "momento = ahora()",
    "cls._validar_mensualidad(vehiculo, momento.date())",
    "if cls._movimiento_abierto(vehiculo):            # no duplicar",
    "    raise ReglaNegocioError(\"... ya se encuentra dentro ...\")",
    "celda = cls._asignar_celda(vehiculo, celda_codigo)",
    "movimiento = Movimiento(vehiculo=vehiculo, celda=celda,",
    "                        usuario_entrada=operario,",
    "                        fecha_hora_entrada=momento)",
    "celda.ocupar()",
    "db.session.add(movimiento)",
    "db.session.commit()   # la BD rechaza dobles movimientos abiertos",
  ]),
  h3("Pruebas"),
  p("Las reglas se verifican con **21 pruebas automáticas** (pytest) que cubren: entrada correcta y asignación de celda por tipo, rechazo por falta de mensualidad, placa inválida o no registrada, entrada duplicada, falta de celdas, celda elegida inválida, salida correcta y salida sin entrada, reingreso, consultas, ocupación, control de acceso por rol y el rechazo, a nivel de base de datos, de dos movimientos abiertos del mismo vehículo. Todas las pruebas pasan. Además, se comprobó manualmente el flujo completo sobre el servidor en ejecución (inicio de sesión, entrada, listado de vehículos dentro y salida)."),
];

// ---------- CONCLUSIONES ----------
const conclusiones = [
  h1("3. Conclusiones"),
  p("La primera iteración del sistema de “Autos Colombia” permitió llevar el requerimiento de **gestión de entrada y salida de vehículos** desde el análisis hasta un producto que funciona. Se definieron 12 requerimientos funcionales y 8 no funcionales, se convirtieron en 6 historias de usuario con criterios de aceptación verificables y se mantuvo la trazabilidad entre requerimiento, historia, mockup, modelo y código."),
  p("El trabajo de modelado mostró el valor de diseñar antes de programar. Definir el MER y el modelo relacional con claridad hizo que las clases, las tablas y el código coincidieran sin retrabajo, y la arquitectura en capas dejó las reglas del negocio en un solo lugar, lo que las hace fáciles de probar y de ampliar. Una decisión importante fue trasladar la regla «un vehículo o una celda no pueden tener dos movimientos abiertos» también a la base de datos (columnas generadas con índices únicos), de modo que la consistencia no dependa únicamente de que el programa se comporte bien."),
  p("Como aprendizaje, el alcance de la iteración exigió decidir qué dejar fuera: la administración de clientes, vehículos, usuarios y celdas, el registro de novedades y los pagos se pospusieron, y por eso los datos de apoyo se cargan con un script de ejemplo. Acotar así el trabajo permitió entregar algo completo y probado en lugar de varias piezas a medias."),
  p("Como siguientes pasos, la **iteración 2** abordará la gestión de usuarios y de celdas (altas, modificaciones y bajas) y el registro de novedades sobre un vehículo, y la **iteración 3** la gestión de pagos de las mensualidades, que además alimentará la validación de vigencia que hoy se apoya en el estado de la mensualidad. La estructura actual de servicios, rutas y modelos está pensada para recibir esas funciones sin reorganizar lo ya construido."),
];

// ---------- DOCUMENTO ----------
const doc = new Document({
  creator: "Fernando Soto",
  title: "Autos Colombia - EA1 Iteración 1: Gestión de entrada y salida de vehículos",
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
    {
      properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
      children: portada,
    },
    {
      properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1300, left: 1440 },
        pageNumbers: { start: 1 } } },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: "C5CFDC", space: 6 } },
        children: [run("Autos Colombia · EA1 · Iteración 1   |   Página ", { size: 17, color: GRIS }),
          new TextRun({ children: [PageNumber.CURRENT], size: 17, color: GRIS })] })] }) },
      children: [...introduccion, ...entregables, ...conclusiones],
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(__dirname, "Soto_Fernando_EA1.docx");
  fs.writeFileSync(out, buf);
  console.log("OK", out, buf.length, "bytes;", nFigura, "figuras;", nTabla, "tablas");
});
