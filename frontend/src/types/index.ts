// ============================================================================
// TYPES - ImportCost Pro
// ============================================================================

// Auth
export interface User {
  id: number;
  empresa_id: number;
  email: string;
  nombre: string;
  apellido: string;
  rol: 'admin' | 'usuario' | 'readonly';
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Common
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Proveedor
export interface Proveedor {
  id: number;
  ruc: string;
  razon_social: string;
  nombre_comercial?: string;
  pais?: string;
  pais_codigo?: string;
  moneda?: string;
  incoterm_default?: string;
  es_extranjero: boolean;
  email?: string;
  telefono?: string;
  contacto_nombre?: string;
  status: 'active' | 'inactive';
  total_ocs?: number;
  created_at: string;
}

export interface ProveedorForm {
  ruc: string;
  razon_social: string;
  nombre_comercial?: string;
  pais_id?: number;
  direccion?: string;
  email?: string;
  telefono?: string;
  contacto_nombre?: string;
  moneda_id?: number;
  incoterm_default?: string;
  es_extranjero?: boolean;
}

// Producto
export interface Producto {
  id: number;
  sku: string;
  nombre: string;
  descripcion?: string;
  codigo_hs?: string;
  unidad_medida: string;
  peso_kg?: number;
  volumen_m3?: number;
  categoria?: string;
  partida_descripcion?: string;
  tasa_ad_valorem?: number;
  proveedor_default?: string;
  color_ui: string;
  icono_ui: string;
  status: 'active' | 'inactive';
  stock_total?: number;
  created_at: string;
}

export interface ProductoForm {
  sku: string;
  nombre: string;
  descripcion?: string;
  codigo_hs?: string;
  categoria_id?: number;
  unidad_medida?: string;
  peso_kg?: number;
  volumen_m3?: number;
  proveedor_default_id?: number;
  color_ui?: string;
  icono_ui?: string;
}

// Almacen
export interface Almacen {
  id: number;
  codigo: string;
  nombre: string;
  responsable?: string;
  direccion?: string;
  notas?: string;
  status: 'active' | 'inactive';
  total_productos?: number;
  valor_total?: number;
}

// Orden de Compra
export interface OrdenCompra {
  id: number;
  numero_oc: string;
  fecha_orden: string;
  fecha_llegada_est?: string;
  incoterm: string;
  estado: string;
  total_fob: number;
  total_cif: number;
  total_costo_importacion: number;
  proveedor: string;
  proveedor_comercial?: string;
  pais_origen?: string;
  pais_codigo?: string;
  moneda: string;
  moneda_simbolo: string;
  tipo_cambio: number;
  estado_nombre: string;
  estado_color: string;
  estado_icono: string;
  total_items: number;
  total_cantidad: number;
  created_at: string;
}

export interface OCItem {
  id: number;
  producto_id: number;
  sku: string;
  producto_nombre: string;
  codigo_hs?: string;
  cantidad: number;
  precio_unitario: number;
  unidad_medida: string;
  valor_fob: number;
  peso_kg?: number;
  volumen_m3?: number;
  prorrateo_flete: number;
  prorrateo_seguro: number;
  prorrateo_tributos: number;
  prorrateo_gastos: number;
  costo_total: number;
  costo_unitario_landed: number;
}

export interface OrdenCompraForm {
  numero_oc: string;
  proveedor_id: number;
  fecha_orden: string;
  fecha_llegada_est?: string;
  incoterm: string;
  moneda_id: number;
  tipo_cambio: number;
  puerto_embarque?: string;
  puerto_destino?: string;
  agente_aduanero?: string;
  agente_carga?: string;
  notas?: string;
}

// Importacion
export interface Importacion {
  id: number;
  numero_importacion: string;
  descripcion: string;
  fecha_creacion: string;
  bl_number?: string;
  container_number?: string;
  via_transporte: string;
  fecha_embarque?: string;
  fecha_arribo_estimada?: string;
  fecha_arribo_real?: string;
  estado: string;
  total_fob_importacion: number;
  total_gastos_importacion: number;
  total_costo_importacion: number;
  agente_aduanero?: string;
  total_ocs: number;
  ocs_asociadas?: string;
  created_at: string;
}

// Dashboard
export interface DashboardMetricas {
  ocs_borrador: number;
  ocs_confirmadas: number;
  ocs_en_transito: number;
  ocs_en_aduana: number;
  ocs_prorrateadas: number;
  ocs_en_almacen: number;
  ocs_completadas: number;
  importaciones_activas: number;
  fob_mes_actual: number;
  costo_total_mes_actual: number;
  costo_total_mes_anterior: number;
  total_productos: number;
  total_proveedores: number;
  valor_inventario: number;
}

export interface PipelineItem {
  id: number;
  numero_oc: string;
  fecha_orden: string;
  proveedor: string;
  pais_codigo?: string;
  moneda_simbolo: string;
  total_fob: number;
  estado: string;
  estado_nombre: string;
  estado_color: string;
  estado_icono: string;
  estado_orden: number;
  items_count: number;
  dias_transcurridos: number;
}

// Pais y Moneda
export interface Pais {
  id: number;
  codigo: string;
  nombre: string;
  region?: string;
  tiene_tlc_peru: boolean;
}

export interface Moneda {
  id: number;
  codigo: string;
  nombre: string;
  simbolo: string;
}

// Estado de importacion
export interface EstadoImportacion {
  codigo: string;
  nombre: string;
  color_ui: string;
  icono_ui: string;
  orden: number;
}

// Gasto
export interface Gasto {
  id: number;
  tipo_gasto_codigo: string;
  tipo_gasto_nombre: string;
  color_ui: string;
  icono_ui: string;
  descripcion?: string;
  proveedor_nombre?: string;
  monto: number;
  monto_pen: number;
  tipo_cambio: number;
  moneda: string;
  moneda_simbolo: string;
  estado: string;
  prorrateado: boolean;
  created_at: string;
}

// DUA
export interface DUA {
  id: number;
  numero_dua: string;
  fecha_registro: string;
  fecha_levante?: string;
  agencia_aduanas?: string;
  valor_fob_usd: number;
  flete_usd: number;
  seguro_usd: number;
  valor_cif_usd: number;
  total_tributos: number;
  total_gastos_aduana: number;
  estado: string;
  numero_importacion: string;
  total_series: number;
}
