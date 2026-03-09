import math
from fastapi import APIRouter, Depends, HTTPException

from ..database import call_sp
from ..auth import get_current_user

router = APIRouter()


# --- Listar ---
@router.get("")
async def listar_tomas(
    almacen_id: int | None = None,
    estado: str | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user),
):
    items = await call_sp(
        "sp_toma_inventario_listar",
        (user["empresa_id"], almacen_id, estado, search, page, per_page),
    )
    count_result = await call_sp(
        "sp_toma_inventario_contar",
        (user["empresa_id"], almacen_id, estado, search),
        fetch_one=True,
    )
    total = count_result["total"] if count_result else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if per_page > 0 else 0,
    }


# --- Obtener ---
@router.get("/{id}")
async def obtener_toma(id: int, user=Depends(get_current_user)):
    results = await call_sp(
        "sp_toma_inventario_obtener", (id, user["empresa_id"]), multi=True
    )
    return {
        "cabecera": results[0][0] if results and results[0] else None,
        "items": results[1] if len(results) > 1 else [],
    }


# --- Crear ---
@router.post("")
async def crear_toma(data: dict, user=Depends(get_current_user)):
    try:
        return await call_sp(
            "sp_toma_inventario_crear",
            (
                user["empresa_id"],
                data["almacen_id"],
                data["responsable"],
                data.get("fecha_inicio"),
                data.get("notas"),
                user["user_id"],
            ),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Actualizar item (conteo) ---
@router.put("/{toma_id}/items/{item_id}")
async def actualizar_item(
    toma_id: int, item_id: int, data: dict, user=Depends(get_current_user)
):
    try:
        return await call_sp(
            "sp_toma_inventario_actualizar_item",
            (
                toma_id,
                item_id,
                user["empresa_id"],
                data["stock_contado"],
                data.get("observacion"),
            ),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Completar ---
@router.post("/{id}/completar")
async def completar_toma(id: int, user=Depends(get_current_user)):
    try:
        return await call_sp(
            "sp_toma_inventario_completar",
            (id, user["empresa_id"]),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Regularizar ---
@router.post("/{id}/regularizar")
async def regularizar_toma(id: int, user=Depends(get_current_user)):
    try:
        return await call_sp(
            "sp_toma_inventario_regularizar",
            (id, user["empresa_id"], user["user_id"]),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
