from pydantic import BaseModel
from decimal import Decimal


class ProrrateoCalcularRequest(BaseModel):
    importacion_id: int
    metodo: str = "valor_fob"


class ProrrateoAplicarRequest(BaseModel):
    importacion_id: int


class ProrrateoDetalleOut(BaseModel):
    id: int | None = None
    prorrateo_id: int | None = None
    oc_item_id: int | None = None
    producto_id: int | None = None
    producto_codigo: str | None = None
    producto_nombre: str | None = None
    valor_fob: Decimal | None = None
    peso_kg: Decimal | None = None
    volumen_m3: Decimal | None = None
    cantidad: Decimal | None = None
    factor_prorrateo: Decimal | None = None
    gasto_prorrateado: Decimal | None = None
    costo_unitario_final: Decimal | None = None


class ProrrateoOut(BaseModel):
    id: int
    importacion_id: int
    metodo: str
    total_gastos: Decimal | None = None
    total_fob: Decimal | None = None
    estado: str | None = None
    detalle: list[ProrrateoDetalleOut] | None = None


class FichaCosteoItem(BaseModel):
    producto_id: int | None = None
    producto_codigo: str | None = None
    producto_nombre: str | None = None
    cantidad: Decimal | None = None
    precio_fob_unitario: Decimal | None = None
    total_fob: Decimal | None = None
    flete_unitario: Decimal | None = None
    seguro_unitario: Decimal | None = None
    cif_unitario: Decimal | None = None
    ad_valorem_unitario: Decimal | None = None
    igv_unitario: Decimal | None = None
    gastos_prorrateados_unitario: Decimal | None = None
    costo_unitario_final: Decimal | None = None
    costo_total: Decimal | None = None
