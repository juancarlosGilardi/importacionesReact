from pydantic import BaseModel
from decimal import Decimal


# --- DUA ---
class DUACreate(BaseModel):
    importacion_id: int
    numero_dua: str
    fecha_registro: str | None = None
    fecha_levante: str | None = None
    agencia_aduanas: str | None = None
    ruc_agente: str | None = None
    numero_operacion: str | None = None
    valor_fob_usd: Decimal | None = Decimal(0)
    flete_usd: Decimal | None = Decimal(0)
    seguro_usd: Decimal | None = Decimal(0)
    tasa_ad_valorem: Decimal | None = Decimal(0)
    tasa_igv: Decimal | None = Decimal(18)
    tasa_ipm: Decimal | None = Decimal(0)
    monto_isc: Decimal | None = Decimal(0)
    monto_antidumping: Decimal | None = Decimal(0)
    tasa_percepcion: Decimal | None = Decimal("3.5")
    gastos_despacho: Decimal | None = Decimal(0)
    honorarios_agente: Decimal | None = Decimal(0)
    almacenaje: Decimal | None = Decimal(0)
    otros_gastos: Decimal | None = Decimal(0)
    tipo_cambio: Decimal | None = Decimal("1.0000")
    archivo_pdf: str | None = None
    notas: str | None = None

class DUAUpdate(BaseModel):
    fecha_levante: str | None = None
    valor_fob_usd: Decimal | None = None
    flete_usd: Decimal | None = None
    seguro_usd: Decimal | None = None
    tasa_ad_valorem: Decimal | None = None
    tasa_igv: Decimal | None = None
    tasa_ipm: Decimal | None = None
    monto_isc: Decimal | None = None
    monto_antidumping: Decimal | None = None
    tasa_percepcion: Decimal | None = None
    gastos_despacho: Decimal | None = None
    honorarios_agente: Decimal | None = None
    almacenaje: Decimal | None = None
    otros_gastos: Decimal | None = None
    estado: str | None = None
    notas: str | None = None

class DUAItemCreate(BaseModel):
    numero_serie: int
    producto_id: int | None = None
    codigo_hs: str | None = None
    descripcion: str | None = None
    cantidad: Decimal | None = None
    unidad_medida: str | None = None
    valor_fob_usd: Decimal | None = None
    peso_kg: Decimal | None = None
    tasa_ad_valorem: Decimal | None = Decimal(0)


# --- DOCUMENTOS DE TRANSPORTE ---
class DocTransporteCreate(BaseModel):
    importacion_id: int
    tipo_documento: str = "BL"
    numero_documento: str
    transportista: str | None = None
    nombre_nave: str | None = None
    numero_viaje: str | None = None
    fecha_etd: str | None = None
    fecha_eta: str | None = None
    total_bultos: int | None = None
    peso_bruto_kg: Decimal | None = None
    volumen_m3: Decimal | None = None
    archivo_path: str | None = None
    tracking_url: str | None = None
    notas: str | None = None

class DocTransporteUpdate(BaseModel):
    numero_documento: str | None = None
    transportista: str | None = None
    nombre_nave: str | None = None
    numero_viaje: str | None = None
    fecha_etd: str | None = None
    fecha_eta: str | None = None
    fecha_arribo_real: str | None = None
    total_bultos: int | None = None
    peso_bruto_kg: Decimal | None = None
    volumen_m3: Decimal | None = None
    tracking_url: str | None = None
    notas: str | None = None


# --- FACTURAS ---
class FacturaCreate(BaseModel):
    numero_factura: str
    oc_id: int | None = None
    proveedor_id: int
    fecha_factura: str | None = None
    moneda_id: int | None = 1
    tipo_cambio: Decimal | None = Decimal("1.0000")
    subtotal: Decimal | None = Decimal(0)
    impuesto: Decimal | None = Decimal(0)
    total: Decimal | None = Decimal(0)
    xml_file_path: str | None = None
    xml_hash: str | None = None
    archivo_pdf: str | None = None
    notas: str | None = None

class FacturaItemCreate(BaseModel):
    producto_id: int
    cantidad: Decimal
    precio_unitario: Decimal
    precio_total: Decimal | None = None
