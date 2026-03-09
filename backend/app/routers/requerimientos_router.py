import math
from fastapi import APIRouter, Depends, HTTPException

from ..database import call_sp
from ..auth import get_current_user

router = APIRouter()


# --- Listar ---
@router.get("")
async def listar_requerimientos(
    estado: str | None = None,
    prioridad: str | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user),
):
    items = await call_sp(
        "sp_requerimiento_listar",
        (user["empresa_id"], estado, prioridad, search, page, per_page),
    )
    count_result = await call_sp(
        "sp_requerimiento_contar",
        (user["empresa_id"], estado, prioridad, search),
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
async def obtener_requerimiento(id: int, user=Depends(get_current_user)):
    results = await call_sp(
        "sp_requerimiento_obtener", (id, user["empresa_id"]), multi=True
    )
    return {
        "cabecera": results[0][0] if results and results[0] else None,
        "items": results[1] if len(results) > 1 else [],
    }


# --- Crear ---
@router.post("")
async def crear_requerimiento(data: dict, user=Depends(get_current_user)):
    try:
        return await call_sp(
            "sp_requerimiento_crear",
            (
                user["empresa_id"],
                data.get("almacen_id"),
                data.get("centro_costo"),
                data.get("prioridad"),
                data.get("proveedor_sugerido_id"),
                data["solicitante"],
                data.get("fecha"),
                data.get("notas"),
                user["user_id"],
            ),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Actualizar ---
@router.put("/{id}")
async def actualizar_requerimiento(id: int, data: dict, user=Depends(get_current_user)):
    try:
        return await call_sp(
            "sp_requerimiento_actualizar",
            (
                id,
                user["empresa_id"],
                data.get("almacen_id"),
                data.get("centro_costo"),
                data.get("prioridad"),
                data.get("proveedor_sugerido_id"),
                data.get("solicitante"),
                data.get("fecha"),
                data.get("notas"),
            ),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Items ---
@router.post("/{id}/items")
async def agregar_item(id: int, data: dict, user=Depends(get_current_user)):
    try:
        return await call_sp(
            "sp_requerimiento_item_agregar",
            (
                id,
                user["empresa_id"],
                data["producto_id"],
                data["cantidad"],
                data.get("precio_estimado"),
                data.get("notas"),
            ),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{id}/items/{item_id}")
async def eliminar_item(id: int, item_id: int, user=Depends(get_current_user)):
    try:
        return await call_sp(
            "sp_requerimiento_item_eliminar",
            (id, item_id, user["empresa_id"]),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Workflow ---
@router.post("/{id}/firmar")
async def firmar_requerimiento(id: int, data: dict, user=Depends(get_current_user)):
    try:
        return await call_sp(
            "sp_requerimiento_firmar",
            (id, user["empresa_id"], data.get("firmado_por", user.get("nombre", ""))),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id}/derivar")
async def derivar_requerimiento(id: int, user=Depends(get_current_user)):
    try:
        return await call_sp(
            "sp_requerimiento_derivar",
            (id, user["empresa_id"]),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id}/cerrar")
async def cerrar_requerimiento(id: int, user=Depends(get_current_user)):
    try:
        return await call_sp(
            "sp_requerimiento_cerrar",
            (id, user["empresa_id"]),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Eliminar ---
@router.delete("/{id}")
async def eliminar_requerimiento(id: int, user=Depends(get_current_user)):
    try:
        return await call_sp(
            "sp_requerimiento_eliminar",
            (id, user["empresa_id"]),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
