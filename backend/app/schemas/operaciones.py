from pydantic import BaseModel
from decimal import Decimal


# --- ORDENES DE COMPRA ---
class OCCreate(BaseModel):
    numero_oc: str | None = None
    proveedor_id: int
    fecha_orden: str | None = None
    fecha_llegada_est: str | None = None
    incoterm: str | None = "FOB"
    moneda_id: int | None = 1
    tipo_cambio: Decimal | None = Decimal("1.0000")
    puerto_embarque: str | None = None
    puerto_destino: str | None = None
    agente_aduanero: str | None = None
    agente_carga: str | None = None
    notas: str | None = None

class OCUpdate(OCCreate):
    proveedor_id: int | None = None

class OCCambiarEstado(BaseModel):
    estado: str

class OCItemCreate(BaseModel):
    producto_id: int
    cantidad: Decimal
    precio_unitario: Decimal
    unidad_medida: str | None = None
    peso_kg: Decimal | None = None
    volumen_m3: Decimal | None = None

class OCItemUpdate(BaseModel):
    cantidad: Decimal | None = None
    precio_unitario: Decimal | None = None
    peso_kg: Decimal | None = None
    volumen_m3: Decimal | None = None


# --- IMPORTACIONES ---
class ImportacionCreate(BaseModel):
    numero_importacion: str | None = None
    descripcion: str | None = None
    via_transporte: str | None = "maritimo"
    bl_number: str | None = None
    container_number: str | None = None
    nombre_nave: str | None = None
    numero_viaje: str | None = None
    fecha_embarque: str | None = None
    fecha_arribo_estimada: str | None = None
    agente_aduanero: str | None = None
    agente_carga: str | None = None
    notas: str | None = None

class ImportacionUpdate(ImportacionCreate):
    fecha_arribo_real: str | None = None
    fecha_desaduanaje: str | None = None
    estado: str | None = None

class ImportacionAsociarOC(BaseModel):
    oc_id: int
