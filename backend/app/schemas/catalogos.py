from pydantic import BaseModel
from decimal import Decimal


# --- PROVEEDORES ---
class ProveedorCreate(BaseModel):
    ruc: str | None = None
    razon_social: str
    nombre_comercial: str | None = None
    pais_id: int | None = None
    direccion: str | None = None
    email: str | None = None
    telefono: str | None = None
    contacto_nombre: str | None = None
    moneda_id: int | None = None
    incoterm_default: str | None = "FOB"
    es_extranjero: int | None = 1

class ProveedorUpdate(ProveedorCreate):
    razon_social: str | None = None
    status: str | None = None


# --- PRODUCTOS ---
class ProductoCreate(BaseModel):
    sku: str | None = None
    nombre: str
    descripcion: str | None = None
    codigo_hs: str | None = None
    categoria_id: int | None = None
    unidad_medida: str | None = "NIU"
    peso_kg: Decimal | None = None
    volumen_m3: Decimal | None = None
    proveedor_default_id: int | None = None
    color_ui: str | None = "#3B82F6"
    icono_ui: str | None = "inventory_2"

class ProductoUpdate(ProductoCreate):
    nombre: str | None = None
    status: str | None = None


# --- ALMACENES ---
class AlmacenCreate(BaseModel):
    codigo: str
    nombre: str
    responsable: str | None = None
    direccion: str | None = None
    notas: str | None = None

class AlmacenUpdate(AlmacenCreate):
    codigo: str | None = None
    nombre: str | None = None
    status: str | None = None


# --- CATEGORIAS ---
class CategoriaCreate(BaseModel):
    nombre: str
    descripcion: str | None = None
    color_ui: str | None = "#3B82F6"
    icono_ui: str | None = "category"


# --- TIPO CAMBIO ---
class TipoCambioRegistrar(BaseModel):
    moneda_codigo: str
    fecha: str
    tc_compra: Decimal
    tc_venta: Decimal
    fuente: str | None = "manual"


# --- PAGINACION ---
class PaginationParams(BaseModel):
    page: int = 1
    per_page: int = 20
    search: str | None = None
    status: str | None = None
