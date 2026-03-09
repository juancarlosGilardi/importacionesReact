export interface User {
  id: number;
  email: string;
  nombre: string;
  rol: string;
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Proveedor {
  id: number;
  ruc: string;
  razon_social: string;
  nombre_comercial?: string;
  pais: string;
  email?: string;
  telefono?: string;
  contacto?: string;
  moneda: string;
  incoterm_default?: string;
  es_extranjero: boolean;
  activo: boolean;
  ordenes_count?: number;
  created_at: string;
  updated_at: string;
}

export interface Producto {
  id: number;
  sku: string;
  nombre: string;
  descripcion?: string;
  codigo_hs?: string;
  categoria?: string;
  unidad_medida: string;
  peso_kg?: number;
  volumen_m3?: number;
  stock_actual: number;
  activo: boolean;
  created_at: string;
  updated_at: string;
}

export interface OrdenCompra {
  id: number;
  numero: string;
  numero_oc?: string;
  proveedor_id: number;
  proveedor?: Proveedor;
  proveedor_nombre?: string;
  proveedor_ruc?: string;
  fecha_orden: string;
  fecha_llegada_est?: string;
  moneda: string;
  moneda_id?: number;
  incoterm: string;
  total_fob: number;
  estado: string;
  notas?: string;
  created_at: string;
  updated_at: string;
}

export interface OrdenCompraItem {
  id: number;
  oc_id: number;
  producto_id: number;
  producto_nombre?: string;
  producto_sku?: string;
  cantidad: number;
  precio_unitario: number;
  unidad_medida: string;
  valor_fob: number;
  peso_kg?: number;
  volumen_m3?: number;
  prorrateo_flete?: number;
  prorrateo_seguro?: number;
  prorrateo_tributos?: number;
  prorrateo_gastos?: number;
  costo_total?: number;
  costo_unitario_landed?: number;
}

export interface OrdenCompraDetalle {
  cabecera: OrdenCompra & {
    proveedor_nombre?: string;
    proveedor_ruc?: string;
    moneda_codigo?: string;
    tipo_cambio?: number;
    puerto_embarque?: string;
    puerto_destino?: string;
    agente_aduanero?: string;
    agente_carga?: string;
    total_flete?: number;
    total_seguro?: number;
    total_cif?: number;
    total_costo_importacion?: number;
    fecha_llegada_est?: string;
  };
  items: OrdenCompraItem[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface DashboardMetrics {
  importaciones_activas: number;
  fob_mes_actual: number;
  costo_total_mes: number;
  total_productos: number;
}

export interface PipelineItem {
  id: number;
  numero: string;
  proveedor_nombre: string;
  total_fob: number;
  estado: string;
  dias_transcurridos: number;
}

export interface Pais {
  codigo: string;
  nombre: string;
}

export interface Importacion {
  id: number;
  numero_importacion: string;
  descripcion: string;
  via_transporte: string;
  bl_number?: string;
  container_number?: string;
  nombre_nave?: string;
  numero_viaje?: string;
  fecha_embarque?: string;
  fecha_arribo_estimada?: string;
  fecha_arribo_real?: string;
  fecha_desaduanaje?: string;
  agente_aduanero?: string;
  agente_carga?: string;
  estado: string;
  total_fob_importacion: number;
  total_gastos_importacion: number;
  total_costo_importacion: number;
  notas?: string;
  created_at: string;
  updated_at: string;
}

export interface Gasto {
  id: number;
  importacion_id?: number;
  oc_id?: number;
  tipo_gasto_codigo: string;
  tipo_gasto_nombre?: string;
  descripcion?: string;
  proveedor_ruc?: string;
  proveedor_nombre?: string;
  moneda_id: number;
  moneda_codigo?: string;
  monto: number;
  tipo_cambio: number;
  monto_pen: number;
  numero_comprobante?: string;
  fecha_gasto?: string;
  prorrateado: boolean;
  estado: string;
  notas?: string;
  created_at: string;
}

export interface TipoGasto {
  codigo: string;
  nombre: string;
  descripcion?: string;
  requiere_proveedor: boolean;
  afecta_cif: boolean;
}

export interface Moneda {
  id: number;
  codigo: string;
  nombre: string;
  simbolo: string;
}

export interface GastoResumen {
  tipo_gasto_codigo: string;
  tipo_gasto_nombre: string;
  total: number;
  cantidad: number;
}

export interface ImportacionDetail {
  cabecera: Importacion;
  ordenes: OrdenCompra[];
  duas: unknown[];
  gastos: Gasto[];
}

export interface Prorrateo {
  id: number;
  importacion_id: number;
  oc_id: number;
  fecha_prorrateo: string;
  metodo_prorrateo: string;
  total_fob: number;
  total_flete: number;
  total_seguro: number;
  total_tributos: number;
  total_gastos: number;
  total_cif: number;
  total_costo_importacion: number;
  estado: string;
  notas?: string;
  created_at: string;
}

export interface ProrrateoDetalle {
  id: number;
  prorrateo_id: number;
  oc_item_id: number;
  producto_id: number;
  producto_nombre: string;
  producto_sku: string;
  cantidad: number;
  valor_fob: number;
  porcentaje_participacion: number;
  prorrateo_flete: number;
  prorrateo_seguro: number;
  prorrateo_tributos: number;
  prorrateo_gastos: number;
  costo_total: number;
  costo_unitario: number;
  costo_unitario_landed: number;
}

export interface ProrrateoResult {
  cabecera: Prorrateo;
  detalle: ProrrateoDetalle[];
}

export interface FichaCosteo {
  cabecera: {
    oc_id: number;
    numero_oc: string;
    proveedor_nombre: string;
    proveedor_ruc: string;
    fecha_orden: string;
    moneda: string;
    incoterm: string;
    total_fob: number;
    total_flete: number;
    total_seguro: number;
    total_cif: number;
    total_tributos: number;
    total_gastos: number;
    total_costo_importacion: number;
  };
  items: ProrrateoDetalle[];
  gastos: Gasto[];
}

export interface DuaDocumento {
  id: number;
  importacion_id: number;
  numero_dua: string;
  fecha_registro: string;
  fecha_levante?: string;
  agencia_aduanas?: string;
  ruc_agente?: string;
  numero_operacion?: string;
  valor_fob_usd: number;
  flete_usd: number;
  seguro_usd: number;
  valor_cif_usd: number;
  tasa_ad_valorem: number;
  monto_ad_valorem: number;
  tasa_igv: number;
  monto_igv: number;
  tasa_ipm: number;
  monto_ipm: number;
  monto_isc: number;
  monto_antidumping: number;
  monto_percepcion: number;
  tasa_percepcion: number;
  gastos_despacho: number;
  honorarios_agente: number;
  almacenaje: number;
  otros_gastos_aduana: number;
  total_tributos: number;
  total_gastos_aduana: number;
  tipo_cambio: number;
  estado: string;
  notas?: string;
  importacion_numero?: string;
  created_at: string;
}

export interface DuaItem {
  id: number;
  dua_id: number;
  numero_serie: number;
  producto_id?: number;
  producto_nombre?: string;
  codigo_hs: string;
  descripcion?: string;
  cantidad: number;
  unidad_medida?: string;
  valor_fob_usd: number;
  peso_kg?: number;
  tasa_ad_valorem: number;
  monto_ad_valorem: number;
  monto_igv: number;
  monto_ipm: number;
  monto_isc: number;
}

export interface DocumentoTransporte {
  id: number;
  importacion_id: number;
  tipo_documento: string;
  numero_documento: string;
  transportista?: string;
  nombre_nave?: string;
  numero_viaje?: string;
  fecha_etd?: string;
  fecha_eta?: string;
  fecha_arribo_real?: string;
  total_bultos?: number;
  peso_bruto_kg?: number;
  volumen_m3?: number;
  tracking_url?: string;
  notas?: string;
  importacion_numero?: string;
  created_at: string;
}

export interface FacturaProveedor {
  id: number;
  numero_factura: string;
  oc_id?: number;
  proveedor_id: number;
  proveedor_nombre?: string;
  proveedor_ruc?: string;
  oc_numero?: string;
  fecha_factura: string;
  moneda_id: number;
  moneda_codigo?: string;
  tipo_cambio: number;
  subtotal: number;
  impuesto: number;
  total: number;
  estado: string;
  notas?: string;
  created_at: string;
}

export interface KardexEntry {
  fecha: string;
  tipo_movimiento: string;
  documento_referencia?: string;
  cantidad_entrada: number;
  costo_unitario_entrada: number;
  costo_total_entrada: number;
  cantidad_salida: number;
  costo_unitario_salida: number;
  costo_total_salida: number;
  saldo_cantidad: number;
  saldo_costo_unitario: number;
  saldo_costo_total: number;
}

export interface ReporteMensual {
  mes: number;
  mes_nombre?: string;
  importaciones: number;
  total_fob: number;
  total_gastos: number;
  total_costo: number;
  incremento_pct: number;
}

export interface ReporteProveedor {
  proveedor_id: number;
  proveedor_nombre: string;
  proveedor_ruc: string;
  total_ocs: number;
  total_fob: number;
  total_gastos: number;
  costo_promedio: number;
  porcentaje_total: number;
}

export interface ReporteProducto {
  fecha: string;
  oc_numero: string;
  importacion_numero?: string;
  cantidad: number;
  fob_unitario: number;
  landed_unitario: number;
  incremento_pct: number;
}

export interface Almacen {
  id: number;
  codigo: string;
  nombre: string;
  responsable?: string;
  direccion?: string;
  status: string;
  notas?: string;
}

export interface StockItem {
  producto_id: number;
  producto_nombre: string;
  producto_sku: string;
  almacen_id: number;
  almacen_nombre: string;
  lote?: string;
  cantidad: number;
  costo_unitario: number;
  valor_total: number;
}

export interface MovimientoAlmacen {
  id: number;
  numero_movimiento: string;
  tipo_movimiento: string;
  fecha_movimiento: string;
  almacen_id?: number;
  almacen_nombre?: string;
  almacen_destino_id?: number;
  almacen_destino_nombre?: string;
  oc_id?: number;
  oc_numero?: string;
  documento_referencia?: string;
  total_productos: number;
  valor_total: number;
  estado: string;
  notas?: string;
  created_at: string;
}

export interface MovimientoDetalle {
  id: number;
  movimiento_id: number;
  producto_id: number;
  producto_nombre?: string;
  producto_sku?: string;
  oc_item_id?: number;
  cantidad: number;
  costo_unitario: number;
  costo_total: number;
  lote?: string;
  fecha_vencimiento?: string;
  ubicacion?: string;
}

// ============================================================================
// VALES (Sprint 5)
// ============================================================================

export interface ConceptoAlmacen {
  id: number;
  codigo: string;
  nombre: string;
  tipo: "ingreso" | "salida";
  afecta_costo: boolean;
  activo: boolean;
  habilitado?: boolean;
}

export interface ValeIngreso {
  id: number;
  numero_movimiento: string;
  fecha_movimiento: string;
  almacen_id?: number;
  almacen_nombre?: string;
  almacen_codigo?: string;
  concepto_id?: number;
  concepto_nombre?: string;
  concepto_codigo?: string;
  proveedor_id?: number;
  proveedor_nombre?: string;
  documento_referencia?: string;
  total_productos: number;
  subtotal: number;
  igv: number;
  total: number;
  estado: string;
  notas?: string;
  created_at: string;
}

export interface ValeSalida {
  id: number;
  numero_movimiento: string;
  fecha_movimiento: string;
  almacen_id?: number;
  almacen_nombre?: string;
  almacen_codigo?: string;
  concepto_id?: number;
  concepto_nombre?: string;
  concepto_codigo?: string;
  centro_costo?: string;
  solicitante?: string;
  documento_referencia?: string;
  total_productos: number;
  subtotal: number;
  total: number;
  estado: string;
  notas?: string;
  created_at: string;
}

export interface ValeItem {
  id: number;
  producto_id: number;
  producto_nombre?: string;
  sku?: string;
  unidad_medida?: string;
  cantidad: number;
  costo_unitario: number;
  costo_total: number;
  lote?: string;
  fecha_vencimiento?: string;
  ubicacion?: string;
  stock_disponible?: number;
}

export interface ValeUnificado {
  id: number;
  numero_movimiento: string;
  tipo_movimiento: "ingreso" | "salida";
  fecha_movimiento: string;
  almacen_nombre?: string;
  almacen_codigo?: string;
  concepto_nombre?: string;
  proveedor_o_solicitante?: string;
  total_productos: number;
  subtotal: number;
  total: number;
  estado: string;
  created_at: string;
}

// --- Sprint 7: Stock Avanzado + Alertas + Valorizado ---

export interface StockResumen {
  total_productos: number;
  items_con_stock: number;
  valor_total_inventario: number;
  almacenes_activos: number;
  productos_con_stock: number;
  productos_sin_stock: number;
}

export interface StockPorAlmacen {
  almacen_id: number;
  almacen_codigo: string;
  almacen_nombre: string;
  responsable?: string;
  total_productos: number;
  total_cantidad: number;
  valor_total: number;
}

export interface AlertaStock {
  producto_id: number;
  sku: string;
  producto_nombre: string;
  unidad_medida?: string;
  categoria_nombre?: string;
  stock_minimo: number;
  punto_reposicion: number;
  stock_actual: number;
  valor_stock: number;
  nivel_alerta: "critico" | "bajo" | "normal";
  cantidad_reponer: number;
}

export interface AlertasResumen {
  total_alertas: number;
  alertas_criticas: number;
  alertas_bajas: number;
  valor_reposicion_estimado: number;
}

export interface InventarioValorizado {
  producto_id: number;
  sku: string;
  producto_nombre: string;
  unidad_medida?: string;
  categoria_nombre?: string;
  almacen_codigo: string;
  almacen_nombre: string;
  cantidad: number;
  costo_unitario_pen: number;
  valor_total_pen: number;
  costo_unitario_moneda: number;
  valor_total_moneda: number;
  moneda: string;
  lote?: string;
  fecha_ultimo_movimiento?: string;
}

export interface ValorizadoPorFamilia {
  categoria_id: number;
  categoria_nombre: string;
  total_productos: number;
  total_cantidad: number;
  valor_total_pen: number;
  valor_total_moneda: number;
  porcentaje: number;
  moneda: string;
  total_general_pen: number;
  total_general_moneda: number;
}

// --- Sprint 6: Requerimientos Internos ---

export interface Requerimiento {
  id: number;
  numero: string;
  fecha: string;
  solicitante: string;
  prioridad: "alta" | "media" | "baja";
  estado: "abierto" | "firmado" | "derivado" | "cerrado";
  centro_costo?: string;
  almacen_id?: number;
  almacen_nombre?: string;
  almacen_codigo?: string;
  proveedor_sugerido_id?: number;
  proveedor_nombre?: string;
  moneda_id?: number;
  tipo_cambio?: number;
  firmado_por?: string;
  fecha_firma?: string;
  total_items?: number;
  valor_total?: number;
  notas?: string;
  created_by?: number;
  created_at: string;
  updated_at: string;
}

export interface RequerimientoItem {
  id: number;
  producto_id: number;
  sku?: string;
  producto_nombre?: string;
  unidad_medida?: string;
  cantidad: number;
  precio_estimado: number;
  total: number;
  notas?: string;
}

// --- Sprint 8: Toma de Inventario Fisico ---

export interface TomaInventario {
  id: number;
  numero: string;
  almacen_id: number;
  almacen_codigo?: string;
  almacen_nombre?: string;
  fecha_inicio: string;
  fecha_fin?: string;
  responsable: string;
  estado: "pendiente" | "en_proceso" | "completado" | "regularizado";
  notas?: string;
  total_items?: number;
  items_contados?: number;
  items_con_diferencia?: number;
  created_by?: number;
  created_at: string;
  updated_at: string;
}

export interface TomaInventarioItem {
  id: number;
  producto_id: number;
  sku?: string;
  producto_nombre?: string;
  unidad_medida?: string;
  stock_sistema: number;
  stock_contado: number | null;
  diferencia: number;
  observacion?: string;
}

// --- Sprint 9: Reportes Avanzados ---

export interface ReporteInventarioResumen {
  total_productos: number;
  productos_con_stock: number;
  productos_sin_stock: number;
  almacenes_con_stock: number;
  valor_total_inventario: number;
  total_unidades: number;
}

export interface ReporteTopProducto {
  producto_id: number;
  sku: string;
  producto_nombre: string;
  unidad_medida?: string;
  categoria_nombre?: string;
  stock_total: number;
  costo_promedio: number;
  valor_total: number;
}

export interface ReporteFamilia {
  categoria_id: number;
  categoria_nombre: string;
  total_productos: number;
  total_cantidad: number;
  valor_total: number;
  porcentaje: number;
}

export interface ReporteMovimientosResumen {
  total_movimientos: number;
  total_ingresos: number;
  total_salidas: number;
  valor_ingresos: number;
  valor_salidas: number;
  balance_neto: number;
}

export interface ReporteMovimientoDetalle {
  id: number;
  numero_movimiento: string;
  tipo_movimiento: string;
  fecha_movimiento: string;
  almacen_codigo?: string;
  almacen_nombre?: string;
  concepto?: string;
  total_productos: number;
  valor_total: number;
  estado: string;
  notas?: string;
}

export interface ReporteRotacion {
  producto_id: number;
  sku: string;
  producto_nombre: string;
  unidad_medida?: string;
  categoria_nombre?: string;
  stock_actual: number;
  valor_stock: number;
  total_salidas: number;
  valor_salidas: number;
  total_ingresos: number;
  indice_rotacion: number;
  clasificacion: "alta" | "media" | "lenta" | "sin_movimiento" | "sin_stock";
}

export interface ReporteAlmacenOcupacion {
  almacen_id: number;
  almacen_codigo: string;
  almacen_nombre: string;
  responsable?: string;
  status: string;
  total_productos: number;
  total_unidades: number;
  valor_total: number;
  porcentaje_valor: number;
  movimientos_30d: number;
}

export interface ReporteAlmacenMesMov {
  anio: number;
  mes: number;
  ingresos_count: number;
  salidas_count: number;
  valor_ingresos: number;
  valor_salidas: number;
  balance: number;
}

export interface ReporteAlmacenTopProducto {
  producto_id: number;
  sku: string;
  producto_nombre: string;
  cantidad_ingresada: number;
  cantidad_salida: number;
  total_movimientos: number;
}

export interface ReporteAlmacenComparativo {
  almacen_id: number;
  almacen_codigo: string;
  almacen_nombre: string;
  productos_distintos: number;
  total_unidades: number;
  valor_inventario: number;
  ingresos_30d: number;
  salidas_30d: number;
  alertas_stock: number | null;
}

export interface ReporteComprasResumen {
  total_ordenes: number;
  total_fob: number;
  total_costo: number;
  promedio_fob: number;
  proveedores_distintos: number;
  dias_entrega_promedio: number;
}

export interface ReporteComprasEstado {
  estado: string;
  cantidad: number;
  total_fob: number;
  total_costo: number;
}

export interface ReporteComprasMes {
  mes: number;
  total_ordenes: number;
  total_fob: number;
  total_costo: number;
}

export interface ReporteComprasProveedor {
  proveedor_id: number;
  proveedor_nombre: string;
  proveedor_ruc: string;
  pais: string;
  total_ordenes: number;
  total_fob: number;
  total_costo: number;
  promedio_fob_orden: number;
  dias_entrega_promedio: number;
  ultima_orden: string;
  porcentaje_total: number;
}

export interface ReporteComprasPendiente {
  id: number;
  numero_oc: string;
  proveedor_nombre: string;
  proveedor_ruc: string;
  fecha_orden: string;
  fecha_llegada_est?: string;
  moneda: string;
  total_fob: number;
  total_cif: number;
  estado: string;
  dias_desde_orden: number;
  dias_atraso: number;
  urgencia: "atrasada" | "proxima" | "en_plazo";
  total_items: number;
  notas?: string;
}

// --- Sprint 10: Administracion ---

export interface UsuarioAdmin {
  id: number;
  email: string;
  nombre: string;
  apellido: string;
  rol: "admin" | "usuario" | "readonly";
  status: "active" | "inactive" | "blocked";
  almacen_default_id?: number;
  almacen_nombre?: string;
  almacen_codigo?: string;
  ultimo_login?: string;
  created_at: string;
  updated_at: string;
}

export interface ConfiguracionItem {
  id: number;
  seccion: string;
  clave: string;
  valor: string | null;
  tipo_dato: "string" | "number" | "boolean" | "json";
  descripcion?: string;
  updated_at: string;
}

export interface ConfiguracionSeccion {
  seccion: string;
  total_claves: number;
}
