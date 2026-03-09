from fastapi import APIRouter, Depends

from ..database import call_sp
from ..auth import get_current_user

router = APIRouter()


# --- Reportes Inventario ---


@router.get("/inventario/resumen")
async def reporte_inventario_resumen(user=Depends(get_current_user)):
    results = await call_sp(
        "sp_reporte_inventario_resumen",
        (user["empresa_id"],),
        multi=True,
    )
    return {
        "resumen": results[0][0] if results and results[0] else None,
        "top_productos": results[1] if len(results) > 1 else [],
        "por_familia": results[2] if len(results) > 2 else [],
    }


@router.get("/inventario/movimientos")
async def reporte_inventario_movimientos(
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    almacen_id: int | None = None,
    user=Depends(get_current_user),
):
    results = await call_sp(
        "sp_reporte_inventario_movimientos",
        (user["empresa_id"], fecha_desde, fecha_hasta, almacen_id),
        multi=True,
    )
    return {
        "resumen": results[0][0] if results and results[0] else None,
        "movimientos": results[1] if len(results) > 1 else [],
    }


@router.get("/inventario/rotacion")
async def reporte_inventario_rotacion(
    meses: int = 12,
    user=Depends(get_current_user),
):
    items = await call_sp(
        "sp_reporte_inventario_rotacion",
        (user["empresa_id"], meses),
    )
    return items


# --- Reportes Almacen ---


@router.get("/almacen/ocupacion")
async def reporte_almacen_ocupacion(user=Depends(get_current_user)):
    items = await call_sp(
        "sp_reporte_almacen_ocupacion",
        (user["empresa_id"],),
    )
    return items


@router.get("/almacen/movimientos")
async def reporte_almacen_movimientos(
    almacen_id: int | None = None,
    meses: int = 6,
    user=Depends(get_current_user),
):
    results = await call_sp(
        "sp_reporte_almacen_movimientos",
        (user["empresa_id"], almacen_id, meses),
        multi=True,
    )
    return {
        "resumen_mensual": results[0] if results else [],
        "top_productos": results[1] if len(results) > 1 else [],
    }


@router.get("/almacen/comparativo")
async def reporte_almacen_comparativo(user=Depends(get_current_user)):
    items = await call_sp(
        "sp_reporte_almacen_comparativo",
        (user["empresa_id"],),
    )
    return items


# --- Reportes Compras ---


@router.get("/compras/resumen")
async def reporte_compras_resumen(
    anio: int | None = None,
    user=Depends(get_current_user),
):
    results = await call_sp(
        "sp_reporte_compras_resumen",
        (user["empresa_id"], anio),
        multi=True,
    )
    return {
        "resumen": results[0][0] if results and results[0] else None,
        "por_estado": results[1] if len(results) > 1 else [],
        "por_mes": results[2] if len(results) > 2 else [],
    }


@router.get("/compras/por-proveedor")
async def reporte_compras_por_proveedor(
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    user=Depends(get_current_user),
):
    items = await call_sp(
        "sp_reporte_compras_por_proveedor",
        (user["empresa_id"], fecha_desde, fecha_hasta),
    )
    return items


@router.get("/compras/pendientes")
async def reporte_compras_pendientes(user=Depends(get_current_user)):
    items = await call_sp(
        "sp_reporte_compras_pendientes",
        (user["empresa_id"],),
    )
    return items
