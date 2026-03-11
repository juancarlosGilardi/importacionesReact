from fastapi import APIRouter, Depends, Query
from app.database import call_sp, call_sp_multi
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/metricas")
async def metricas(user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_dashboard_metricas", (user["empresa_id"],))
    return rows[0] if rows else {}


@router.get("/pipeline")
async def pipeline(user: dict = Depends(get_current_user)):
    return await call_sp("sp_dashboard_pipeline", (user["empresa_id"],))


@router.get("/importaciones-pipeline")
async def importaciones_pipeline(user: dict = Depends(get_current_user)):
    return await call_sp("sp_dashboard_importaciones_pipeline", (user["empresa_id"],))


@router.get("/busqueda")
async def busqueda_global(q: str = Query(..., min_length=2), user: dict = Depends(get_current_user)):
    results = await call_sp_multi("sp_busqueda_global", (user["empresa_id"], q))
    # Unir todos los result sets
    combined = []
    for rs in results:
        combined.extend(rs)
    return combined


# ==================== REPORTES ====================
@router.get("/reporte/costo-producto")
async def reporte_costo_producto(
    producto_id: int | None = None,
    user: dict = Depends(get_current_user),
):
    return await call_sp("sp_reporte_costo_producto", (user["empresa_id"], producto_id))


@router.get("/reporte/comparativo-proveedor")
async def reporte_comparativo_proveedor(
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    user: dict = Depends(get_current_user),
):
    return await call_sp("sp_reporte_comparativo_proveedor", (user["empresa_id"], fecha_desde, fecha_hasta))


@router.get("/reporte/resumen-mensual")
async def reporte_resumen_mensual(
    anio: int | None = None,
    user: dict = Depends(get_current_user),
):
    return await call_sp("sp_reporte_resumen_mensual", (user["empresa_id"], anio))
