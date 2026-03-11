from pydantic import BaseModel
from decimal import Decimal


class MovimientoIngresoCreate(BaseModel):
    almacen_id: int
    oc_id: int | None = None
    documento_referencia: str | None = None
    fecha: str | None = None
    notas: str | None = None

class MovimientoTransferenciaCreate(BaseModel):
    almacen_origen_id: int
    almacen_destino_id: int
    documento_referencia: str | None = None
    fecha: str | None = None
    notas: str | None = None

class MovimientoSalidaCreate(BaseModel):
    almacen_id: int
    documento_referencia: str | None = None
    fecha: str | None = None
    notas: str | None = None

class MovimientoItemCreate(BaseModel):
    producto_id: int
    oc_item_id: int | None = None
    cantidad: Decimal
    costo_unitario: Decimal
    lote: str | None = None
    fecha_vencimiento: str | None = None
    ubicacion: str | None = None

class KardexParams(BaseModel):
    producto_id: int
    almacen_id: int | None = None
    fecha_desde: str | None = None
    fecha_hasta: str | None = None
