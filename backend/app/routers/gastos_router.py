from fastapi import APIRouter, Depends, Query
from ..database import call_sp
from ..auth import get_current_user

router = APIRouter()


@router.get("/")
async def listar(
    importacion_id: int | None = None,
    oc_id: int | None = None,
    tipo_gasto: str | None = None,
    estado: str | None = None,
    user=Depends(get_current_user),
):
    return await call_sp(
        "sp_gasto_listar",
        (user["empresa_id"], importacion_id, oc_id, tipo_gasto, estado),
    )


@router.post("/")
async def crear(data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_gasto_crear",
        (
            user["empresa_id"], data.get("importacion_id"), data.get("oc_id"),
            data["tipo_gasto_codigo"], data.get("descripcion"),
            data.get("proveedor_ruc"), data.get("proveedor_nombre"),
            data.get("moneda_id"), data["monto"], data.get("tipo_cambio"),
            data.get("numero_comprobante"), data.get("fecha_gasto"),
            data.get("comprobante_path"), data.get("notas"),
            user["user_id"],
        ),
        fetch_one=True,
    )


@router.put("/{id}")
async def actualizar(id: int, data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_gasto_actualizar",
        (
            id, user["empresa_id"], data.get("tipo_gasto_codigo"), data.get("descripcion"),
            data.get("proveedor_ruc"), data.get("proveedor_nombre"),
            data.get("moneda_id"), data.get("monto"), data.get("tipo_cambio"),
            data.get("numero_comprobante"), data.get("fecha_gasto"),
            data.get("estado"), data.get("notas"), user["user_id"],
        ),
        fetch_one=True,
    )


@router.delete("/{id}")
async def eliminar(id: int, user=Depends(get_current_user)):
    return await call_sp("sp_gasto_eliminar", (id, user["empresa_id"]), fetch_one=True)


@router.get("/resumen/{importacion_id}")
async def resumen_por_tipo(importacion_id: int, user=Depends(get_current_user)):
    return await call_sp("sp_gasto_resumen_por_tipo", (user["empresa_id"], importacion_id))
