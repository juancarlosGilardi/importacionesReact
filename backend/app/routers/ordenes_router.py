from fastapi import APIRouter, Depends, Query
from ..database import call_sp
from ..auth import get_current_user

router = APIRouter()


@router.get("/")
async def listar(
    search: str | None = None,
    estado: str | None = None,
    proveedor_id: int | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user),
):
    items = await call_sp(
        "sp_oc_listar",
        (user["empresa_id"], search, estado, proveedor_id, fecha_desde, fecha_hasta, page, per_page),
    )
    total = await call_sp(
        "sp_oc_contar",
        (user["empresa_id"], search, estado, proveedor_id, fecha_desde, fecha_hasta),
        fetch_one=True,
    )
    return {"items": items, "total": total["total"], "page": page, "per_page": per_page}


@router.get("/{id}")
async def obtener(id: int, user=Depends(get_current_user)):
    results = await call_sp("sp_oc_obtener", (id, user["empresa_id"]), multi=True)
    if not results or not results[0]:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return {"cabecera": results[0][0] if results[0] else None, "items": results[1] if len(results) > 1 else []}


@router.post("/")
async def crear(data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_oc_crear",
        (
            user["empresa_id"], data.get("numero_oc"), data.get("proveedor_id"),
            data.get("fecha_orden"), data.get("fecha_llegada_est"),
            data.get("incoterm"), data.get("moneda_id"), data.get("tipo_cambio"),
            data.get("puerto_embarque"), data.get("puerto_destino"),
            data.get("agente_aduanero"), data.get("agente_carga"),
            data.get("notas"), user["user_id"],
        ),
        fetch_one=True,
    )


@router.put("/{id}")
async def actualizar(id: int, data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_oc_actualizar",
        (
            id, user["empresa_id"], data.get("numero_oc"), data.get("proveedor_id"),
            data.get("fecha_orden"), data.get("fecha_llegada_est"),
            data.get("incoterm"), data.get("moneda_id"), data.get("tipo_cambio"),
            data.get("puerto_embarque"), data.get("puerto_destino"),
            data.get("agente_aduanero"), data.get("agente_carga"),
            data.get("notas"), user["user_id"],
        ),
        fetch_one=True,
    )


@router.patch("/{id}/estado")
async def cambiar_estado(id: int, data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_oc_cambiar_estado",
        (id, user["empresa_id"], data["estado"], user["user_id"]),
        fetch_one=True,
    )


@router.delete("/{id}")
async def eliminar(id: int, user=Depends(get_current_user)):
    return await call_sp("sp_oc_eliminar", (id, user["empresa_id"]), fetch_one=True)


# --- Items ---
@router.post("/{oc_id}/items")
async def agregar_item(oc_id: int, data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_oc_item_agregar",
        (
            oc_id, data["producto_id"], data["cantidad"], data["precio_unitario"],
            data.get("unidad_medida"), data.get("peso_kg"), data.get("volumen_m3"),
            user["user_id"],
        ),
        fetch_one=True,
    )


@router.put("/items/{item_id}")
async def actualizar_item(item_id: int, data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_oc_item_actualizar",
        (item_id, data.get("cantidad"), data.get("precio_unitario"), data.get("peso_kg"), data.get("volumen_m3"), user["user_id"]),
        fetch_one=True,
    )


@router.delete("/items/{item_id}")
async def eliminar_item(item_id: int, _=Depends(get_current_user)):
    return await call_sp("sp_oc_item_eliminar", (item_id,), fetch_one=True)
