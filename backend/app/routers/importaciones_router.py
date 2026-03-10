import math
from fastapi import APIRouter, Depends, Query, HTTPException
from ..database import call_sp
from ..auth import get_current_user

router = APIRouter()


@router.get("/")
async def listar(
    search: str | None = None,
    estado: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user),
):
    items = await call_sp(
        "sp_importacion_listar",
        (user["empresa_id"], search, estado, page, per_page),
    )
    total = await call_sp(
        "sp_importacion_contar",
        (user["empresa_id"], search, estado),
        fetch_one=True,
    )
    total_count = total["total"]
    return {
        "items": items,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total_count / per_page) if per_page > 0 else 0,
    }


@router.get("/{id}")
async def obtener(id: int, user=Depends(get_current_user)):
    results = await call_sp("sp_importacion_obtener", (id, user["empresa_id"]), multi=True)
    if not results or not results[0]:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Importacion no encontrada")
    return {
        "cabecera": results[0][0] if results[0] else None,
        "ordenes": results[1] if len(results) > 1 else [],
        "duas": results[2] if len(results) > 2 else [],
        "gastos": results[3] if len(results) > 3 else [],
    }


@router.post("/")
async def crear(data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_importacion_crear",
        (
            user["empresa_id"], data.get("numero_importacion"), data.get("descripcion"),
            data.get("via_transporte"), data.get("bl_number"), data.get("container_number"),
            data.get("nombre_nave"), data.get("numero_viaje"),
            data.get("fecha_embarque"), data.get("fecha_arribo_estimada"),
            data.get("agente_aduanero"), data.get("agente_carga"),
            data.get("notas"), user["user_id"],
        ),
        fetch_one=True,
    )


@router.put("/{id}")
async def actualizar(id: int, data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_importacion_actualizar",
        (
            id, user["empresa_id"], data.get("descripcion"), data.get("via_transporte"),
            data.get("bl_number"), data.get("container_number"),
            data.get("nombre_nave"), data.get("numero_viaje"),
            data.get("fecha_embarque"), data.get("fecha_arribo_estimada"),
            data.get("fecha_arribo_real"), data.get("fecha_desaduanaje"),
            data.get("agente_aduanero"), data.get("agente_carga"),
            data.get("estado"), data.get("notas"), user["user_id"],
        ),
        fetch_one=True,
    )


@router.post("/{id}/asociar-oc")
async def asociar_oc(id: int, data: dict, _=Depends(get_current_user)):
    return await call_sp("sp_importacion_asociar_oc", (id, data["oc_id"]), fetch_one=True)


@router.delete("/{id}/desasociar-oc/{oc_id}")
async def desasociar_oc(id: int, oc_id: int, _=Depends(get_current_user)):
    return await call_sp("sp_importacion_desasociar_oc", (id, oc_id), fetch_one=True)


@router.delete("/{id}")
async def eliminar(id: int, user=Depends(get_current_user)):
    try:
        return await call_sp("sp_importacion_eliminar", (id, user["empresa_id"]), fetch_one=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
