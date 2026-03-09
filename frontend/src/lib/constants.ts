export const STATUS_COLORS: Record<string, string> = {
  borrador: "bg-gray-100 text-gray-700 border-gray-300",
  confirmada: "bg-blue-100 text-blue-700 border-blue-300",
  en_produccion: "bg-yellow-100 text-yellow-700 border-yellow-300",
  en_transito: "bg-purple-100 text-purple-700 border-purple-300",
  en_aduana: "bg-orange-100 text-orange-700 border-orange-300",
  nacionalizada: "bg-teal-100 text-teal-700 border-teal-300",
  en_almacen: "bg-green-100 text-green-700 border-green-300",
  completada: "bg-emerald-100 text-emerald-700 border-emerald-300",
  cancelada: "bg-red-100 text-red-700 border-red-300",
};

export const STATUS_LABELS: Record<string, string> = {
  borrador: "Borrador",
  confirmada: "Confirmada",
  en_produccion: "En Producción",
  en_transito: "En Tránsito",
  en_aduana: "En Aduana",
  nacionalizada: "Nacionalizada",
  en_almacen: "En Almacén",
  completada: "Completada",
  cancelada: "Cancelada",
};

export const STATUS_BORDER_COLORS: Record<string, string> = {
  borrador: "border-t-gray-400",
  confirmada: "border-t-blue-500",
  en_produccion: "border-t-yellow-500",
  en_transito: "border-t-purple-500",
  en_aduana: "border-t-orange-500",
  nacionalizada: "border-t-teal-500",
  en_almacen: "border-t-green-500",
};

export const PIPELINE_STATUSES = [
  "borrador",
  "confirmada",
  "en_produccion",
  "en_transito",
  "en_aduana",
  "nacionalizada",
  "en_almacen",
] as const;

export const INCOTERMS = [
  "EXW",
  "FCA",
  "FAS",
  "FOB",
  "CFR",
  "CIF",
  "CPT",
  "CIP",
  "DAP",
  "DPU",
  "DDP",
] as const;

export const MONEDAS = [
  { value: "USD", label: "USD - Dólar Americano" },
  { value: "EUR", label: "EUR - Euro" },
  { value: "CNY", label: "CNY - Yuan Chino" },
  { value: "PEN", label: "PEN - Sol Peruano" },
] as const;

export const UNIDADES_MEDIDA = [
  { value: "UND", label: "Unidad" },
  { value: "KG", label: "Kilogramo" },
  { value: "MT", label: "Metro" },
  { value: "LT", label: "Litro" },
  { value: "CJ", label: "Caja" },
  { value: "PL", label: "Pallet" },
  { value: "RL", label: "Rollo" },
  { value: "JG", label: "Juego" },
] as const;

export const VIA_TRANSPORTE = [
  { value: "maritimo", label: "Marítimo" },
  { value: "aereo", label: "Aéreo" },
  { value: "terrestre", label: "Terrestre" },
  { value: "multimodal", label: "Multimodal" },
] as const;

export const VIA_TRANSPORTE_COLORS: Record<string, string> = {
  maritimo: "bg-blue-100 text-blue-700",
  aereo: "bg-sky-100 text-sky-700",
  terrestre: "bg-amber-100 text-amber-700",
  multimodal: "bg-violet-100 text-violet-700",
};

export const GASTO_ESTADOS = [
  { value: "pendiente", label: "Pendiente" },
  { value: "aprobado", label: "Aprobado" },
  { value: "pagado", label: "Pagado" },
] as const;

export const GASTO_STATUS_COLORS: Record<string, string> = {
  pendiente: "bg-yellow-100 text-yellow-700",
  aprobado: "bg-blue-100 text-blue-700",
  pagado: "bg-green-100 text-green-700",
};

export const GASTO_STATUS_LABELS: Record<string, string> = {
  pendiente: "Pendiente",
  aprobado: "Aprobado",
  pagado: "Pagado",
};

export const IMPORTACION_ESTADOS = [
  { value: "planificada", label: "Planificada" },
  { value: "en_transito", label: "En Tránsito" },
  { value: "en_aduana", label: "En Aduana" },
  { value: "nacionalizada", label: "Nacionalizada" },
  { value: "en_almacen", label: "En Almacén" },
  { value: "completada", label: "Completada" },
  { value: "cancelada", label: "Cancelada" },
] as const;

export const DUA_ESTADOS = [
  { value: "registrada", label: "Registrada" },
  { value: "en_proceso", label: "En Proceso" },
  { value: "levantada", label: "Levantada" },
  { value: "cancelada", label: "Cancelada" },
] as const;

export const DUA_STATUS_COLORS: Record<string, string> = {
  registrada: "bg-blue-100 text-blue-700",
  en_proceso: "bg-yellow-100 text-yellow-700",
  levantada: "bg-green-100 text-green-700",
  cancelada: "bg-red-100 text-red-700",
};

export const TIPO_DOCUMENTO_TRANSPORTE = [
  { value: "bill_of_lading", label: "Bill of Lading (BL)" },
  { value: "air_waybill", label: "Air Waybill (AWB)" },
  { value: "carta_porte", label: "Carta Porte" },
  { value: "otro", label: "Otro" },
] as const;

export const FACTURA_ESTADOS = [
  { value: "pendiente", label: "Pendiente" },
  { value: "validada", label: "Validada" },
  { value: "pagada", label: "Pagada" },
  { value: "cancelada", label: "Cancelada" },
] as const;

export const FACTURA_STATUS_COLORS: Record<string, string> = {
  pendiente: "bg-yellow-100 text-yellow-700",
  validada: "bg-blue-100 text-blue-700",
  pagada: "bg-green-100 text-green-700",
  cancelada: "bg-red-100 text-red-700",
};

export const METODOS_PRORRATEO = [
  { value: "valor_fob", label: "Por Valor FOB" },
  { value: "peso", label: "Por Peso" },
  { value: "volumen", label: "Por Volumen" },
  { value: "cantidad", label: "Por Cantidad" },
] as const;

export const PRORRATEO_STATUS_COLORS: Record<string, string> = {
  borrador: "bg-gray-100 text-gray-700",
  calculado: "bg-yellow-100 text-yellow-700",
  aplicado: "bg-green-100 text-green-700",
};

export const PRORRATEO_STATUS_LABELS: Record<string, string> = {
  borrador: "Borrador",
  calculado: "Calculado",
  aplicado: "Aplicado",
};

export const TIPO_MOVIMIENTO_COLORS: Record<string, string> = {
  ingreso: "bg-green-100 text-green-700",
  transferencia: "bg-blue-100 text-blue-700",
  ajuste: "bg-yellow-100 text-yellow-700",
  salida: "bg-red-100 text-red-700",
};

export const TIPO_MOVIMIENTO_LABELS: Record<string, string> = {
  ingreso: "Ingreso",
  transferencia: "Transferencia",
  ajuste: "Ajuste",
  salida: "Salida",
};

export const MOVIMIENTO_ESTADOS = [
  { value: "borrador", label: "Borrador" },
  { value: "confirmado", label: "Confirmado" },
  { value: "completado", label: "Completado" },
  { value: "cancelado", label: "Cancelado" },
] as const;

export const MOVIMIENTO_STATUS_COLORS: Record<string, string> = {
  borrador: "bg-gray-100 text-gray-700",
  confirmado: "bg-blue-100 text-blue-700",
  completado: "bg-green-100 text-green-700",
  cancelado: "bg-red-100 text-red-700",
};

// ============================================================================
// VALES (Sprint 5)
// ============================================================================

export const VALE_ESTADOS = [
  { value: "borrador", label: "Borrador" },
  { value: "completado", label: "Completado" },
  { value: "cancelado", label: "Cancelado" },
] as const;

export const VALE_STATUS_COLORS: Record<string, string> = {
  borrador: "bg-gray-100 text-gray-700",
  completado: "bg-green-100 text-green-700",
  cancelado: "bg-red-100 text-red-700",
};

export const VALE_TIPO_COLORS: Record<string, string> = {
  ingreso: "bg-emerald-100 text-emerald-700",
  salida: "bg-rose-100 text-rose-700",
};

export const VALE_TIPO_LABELS: Record<string, string> = {
  ingreso: "Ingreso",
  salida: "Salida",
};

// --- Sprint 7: Alertas Stock ---
export const ALERTA_NIVEL_COLORS: Record<string, string> = {
  critico: "bg-red-100 text-red-700 border-red-300",
  bajo: "bg-amber-100 text-amber-700 border-amber-300",
  normal: "bg-green-100 text-green-700 border-green-300",
};

export const ALERTA_NIVEL_LABELS: Record<string, string> = {
  critico: "Critico",
  bajo: "Bajo",
  normal: "Normal",
};

export const MONEDAS_VALORIZADO = [
  { value: "PEN", label: "Soles (PEN)" },
  { value: "USD", label: "Dolares (USD)" },
];

// --- Sprint 6: Requerimientos ---
export const REQ_ESTADOS = [
  { value: "abierto", label: "Abierto" },
  { value: "firmado", label: "Firmado" },
  { value: "derivado", label: "Derivado" },
  { value: "cerrado", label: "Cerrado" },
];

export const REQ_STATUS_COLORS: Record<string, string> = {
  abierto: "bg-blue-100 text-blue-700 border-blue-300",
  firmado: "bg-amber-100 text-amber-700 border-amber-300",
  derivado: "bg-purple-100 text-purple-700 border-purple-300",
  cerrado: "bg-green-100 text-green-700 border-green-300",
};

export const REQ_PRIORIDADES = [
  { value: "alta", label: "Alta" },
  { value: "media", label: "Media" },
  { value: "baja", label: "Baja" },
];

export const REQ_PRIORIDAD_COLORS: Record<string, string> = {
  alta: "bg-red-100 text-red-700 border-red-300",
  media: "bg-amber-100 text-amber-700 border-amber-300",
  baja: "bg-green-100 text-green-700 border-green-300",
};

// --- Sprint 8: Toma de Inventario ---
export const TOMA_ESTADOS = [
  { value: "pendiente", label: "Pendiente" },
  { value: "en_proceso", label: "En Proceso" },
  { value: "completado", label: "Completado" },
  { value: "regularizado", label: "Regularizado" },
];

export const TOMA_STATUS_COLORS: Record<string, string> = {
  pendiente: "bg-gray-100 text-gray-700 border-gray-300",
  en_proceso: "bg-blue-100 text-blue-700 border-blue-300",
  completado: "bg-amber-100 text-amber-700 border-amber-300",
  regularizado: "bg-green-100 text-green-700 border-green-300",
};

// --- Sprint 9: Reportes Avanzados ---
export const ROTACION_COLORS: Record<string, string> = {
  alta: "bg-green-100 text-green-700",
  media: "bg-blue-100 text-blue-700",
  lenta: "bg-amber-100 text-amber-700",
  sin_movimiento: "bg-red-100 text-red-700",
  sin_stock: "bg-gray-100 text-gray-500",
};

export const ROTACION_LABELS: Record<string, string> = {
  alta: "Alta",
  media: "Media",
  lenta: "Lenta",
  sin_movimiento: "Sin Movimiento",
  sin_stock: "Sin Stock",
};

export const URGENCIA_COLORS: Record<string, string> = {
  atrasada: "bg-red-100 text-red-700 border-red-300",
  proxima: "bg-amber-100 text-amber-700 border-amber-300",
  en_plazo: "bg-green-100 text-green-700 border-green-300",
};

export const URGENCIA_LABELS: Record<string, string> = {
  atrasada: "Atrasada",
  proxima: "Proxima",
  en_plazo: "En Plazo",
};

export const MESES_NOMBRES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

// --- Sprint 10: Administracion ---
export const USER_ROLES = [
  { value: "admin", label: "Administrador" },
  { value: "usuario", label: "Usuario" },
  { value: "readonly", label: "Solo Lectura" },
];

export const USER_ROL_COLORS: Record<string, string> = {
  admin: "bg-purple-100 text-purple-700 border-purple-300",
  usuario: "bg-blue-100 text-blue-700 border-blue-300",
  readonly: "bg-gray-100 text-gray-600 border-gray-300",
};

export const USER_STATUS = [
  { value: "active", label: "Activo" },
  { value: "inactive", label: "Inactivo" },
  { value: "blocked", label: "Bloqueado" },
];

export const USER_STATUS_COLORS: Record<string, string> = {
  active: "bg-green-100 text-green-700",
  inactive: "bg-gray-100 text-gray-500",
  blocked: "bg-red-100 text-red-700",
};

export const CONFIG_SECCIONES_LABELS: Record<string, string> = {
  general: "General",
  inventario: "Inventario",
  compras: "Compras",
  documentos: "Documentos",
};

export const CONFIG_SECCIONES_ICONS: Record<string, string> = {
  general: "Building2",
  inventario: "Boxes",
  compras: "ShoppingCart",
  documentos: "FileText",
};
