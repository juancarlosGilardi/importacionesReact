from fastapi import APIRouter, Depends, Query
from ..database import call_sp
from ..auth import get_current_user

router = APIRouter()


@router.get("/metricas")
async def metricas(user=Depends(get_current_user)):
    return await call_sp("sp_dashboard_metricas", (user["empresa_id"],), fetch_one=True)


@router.get("/pipeline")
async def pipeline(user=Depends(get_current_user)):
    return await call_sp("sp_dashboard_pipeline", (user["empresa_id"],))


@router.get("/importaciones-pipeline")
async def importaciones_pipeline(user=Depends(get_current_user)):
    return await call_sp("sp_dashboard_importaciones_pipeline", (user["empresa_id"],))


@router.get("/busqueda")
async def busqueda_global(q: str = Query("", min_length=1), user=Depends(get_current_user)):
    results = await call_sp("sp_busqueda_global", (user["empresa_id"], q), multi=True)
    categories = ["ordenes", "importaciones", "productos", "proveedores"]
    return {cat: items for cat, items in zip(categories, results) if items}


@router.get("/reporte-mensual")
async def reporte_mensual(anio: int | None = None, user=Depends(get_current_user)):
    return await call_sp("sp_reporte_resumen_mensual", (user["empresa_id"], anio))


@router.get("/reporte-proveedores")
async def reporte_proveedores(
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    user=Depends(get_current_user),
):
    return await call_sp(
        "sp_reporte_comparativo_proveedor",
        (user["empresa_id"], fecha_desde, fecha_hasta),
    )


@router.get("/reporte-producto")
async def reporte_producto(producto_id: int | None = None, user=Depends(get_current_user)):
    return await call_sp("sp_reporte_costo_producto", (user["empresa_id"], producto_id))
