import math
from fastapi import APIRouter, Depends, HTTPException
from ..database import call_sp
from ..auth import get_current_user

router = APIRouter()


# --- Conceptos de Almacén ---
@router.get("/conceptos/{almacen_id}")
async def listar_conceptos(almacen_id: int, tipo: str | None = None, user=Depends(get_current_user)):
    return await call_sp("sp_concepto_almacen_listar", (user["empresa_id"], almacen_id, tipo))


@router.put("/conceptos/{almacen_id}")
async def toggle_concepto(almacen_id: int, data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_concepto_almacen_toggle",
        (user["empresa_id"], almacen_id, data["concepto_id"], data["habilitado"]),
        fetch_one=True,
    )


# --- Vales de Ingreso ---
@router.get("/ingreso")
async def listar_ingreso(
    almacen_id: int | None = None,
    concepto_id: int | None = None,
    estado: str | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user),
):
    items = await call_sp(
        "sp_vale_ingreso_listar",
        (user["empresa_id"], almacen_id, concepto_id, estado, search, page, per_page),
    )
    count_result = await call_sp(
        "sp_vale_ingreso_contar",
        (user["empresa_id"], almacen_id, concepto_id, estado, search),
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


@router.get("/ingreso/{id}")
async def obtener_ingreso(id: int, user=Depends(get_current_user)):
    results = await call_sp("sp_vale_ingreso_obtener", (id, user["empresa_id"]), multi=True)
    return {
        "cabecera": results[0][0] if results and results[0] else None,
        "items": results[1] if len(results) > 1 else [],
    }


@router.post("/ingreso")
async def crear_ingreso(data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_vale_ingreso_crear",
        (
            user["empresa_id"], data["almacen_id"], data.get("concepto_id"),
            data.get("proveedor_id"), data.get("documento_referencia"),
            data.get("fecha"), data.get("notas"), user["user_id"],
        ),
        fetch_one=True,
    )


@router.put("/ingreso/{id}")
async def actualizar_ingreso(id: int, data: dict, user=Depends(get_current_user)):
    try:
        return await call_sp(
            "sp_vale_ingreso_actualizar",
            (
                id, user["empresa_id"], data.get("almacen_id"), data.get("concepto_id"),
                data.get("proveedor_id"), data.get("documento_referencia"),
                data.get("fecha"), data.get("notas"), user["user_id"],
            ),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ingreso/{id}/items")
async def agregar_item_ingreso(id: int, data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_vale_ingreso_item_agregar",
        (
            id, user["empresa_id"], data["producto_id"], data["cantidad"],
            data["costo_unitario"], data.get("lote"),
            data.get("fecha_vencimiento"), data.get("ubicacion"),
        ),
        fetch_one=True,
    )


@router.delete("/ingreso/{id}/items/{item_id}")
async def eliminar_item_ingreso(id: int, item_id: int, user=Depends(get_current_user)):
    try:
        return await call_sp(
            "sp_vale_ingreso_item_eliminar",
            (id, item_id, user["empresa_id"]),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ingreso/{id}/completar")
async def completar_ingreso(id: int, user=Depends(get_current_user)):
    try:
        return await call_sp(
            "sp_vale_ingreso_completar",
            (id, user["empresa_id"], user["user_id"]),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Vales de Salida ---
@router.get("/salida")
async def listar_salida(
    almacen_id: int | None = None,
    concepto_id: int | None = None,
    estado: str | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user),
):
    items = await call_sp(
        "sp_vale_salida_listar",
        (user["empresa_id"], almacen_id, concepto_id, estado, search, page, per_page),
    )
    count_result = await call_sp(
        "sp_vale_salida_contar",
        (user["empresa_id"], almacen_id, concepto_id, estado, search),
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


@router.get("/salida/{id}")
async def obtener_salida(id: int, user=Depends(get_current_user)):
    results = await call_sp("sp_vale_salida_obtener", (id, user["empresa_id"]), multi=True)
    return {
        "cabecera": results[0][0] if results and results[0] else None,
        "items": results[1] if len(results) > 1 else [],
    }


@router.post("/salida")
async def crear_salida(data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_vale_salida_crear",
        (
            user["empresa_id"], data["almacen_id"], data.get("concepto_id"),
            data.get("centro_costo"), data.get("solicitante"),
            data.get("documento_referencia"), data.get("fecha"),
            data.get("notas"), user["user_id"],
        ),
        fetch_one=True,
    )


@router.put("/salida/{id}")
async def actualizar_salida(id: int, data: dict, user=Depends(get_current_user)):
    try:
        return await call_sp(
            "sp_vale_salida_actualizar",
            (
                id, user["empresa_id"], data.get("almacen_id"), data.get("concepto_id"),
                data.get("centro_costo"), data.get("solicitante"),
                data.get("documento_referencia"), data.get("fecha"),
                data.get("notas"), user["user_id"],
            ),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/salida/{id}/items")
async def agregar_item_salida(id: int, data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_vale_salida_item_agregar",
        (id, user["empresa_id"], data["producto_id"], data["cantidad"], data.get("lote")),
        fetch_one=True,
    )


@router.delete("/salida/{id}/items/{item_id}")
async def eliminar_item_salida(id: int, item_id: int, user=Depends(get_current_user)):
    try:
        return await call_sp(
            "sp_vale_salida_item_eliminar",
            (id, item_id, user["empresa_id"]),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/salida/{id}/completar")
async def completar_salida(id: int, user=Depends(get_current_user)):
    try:
        return await call_sp(
            "sp_vale_salida_completar",
            (id, user["empresa_id"], user["user_id"]),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Lista Unificada ---
@router.get("/unificado")
async def listar_unificado(
    tipo: str | None = None,
    almacen_id: int | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user),
):
    items = await call_sp(
        "sp_vales_listar_unificado",
        (user["empresa_id"], tipo, almacen_id, fecha_desde, fecha_hasta, search, page, per_page),
    )
    count_result = await call_sp(
        "sp_vales_contar_unificado",
        (user["empresa_id"], tipo, almacen_id, fecha_desde, fecha_hasta, search),
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
