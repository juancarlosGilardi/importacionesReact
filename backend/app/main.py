from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .database import create_pool, close_pool
from .routers import (
    auth_router,
    catalogos_router,
    dashboard_router,
    proveedores_router,
    productos_router,
    ordenes_router,
    importaciones_router,
    gastos_router,
    documentos_router,
    prorrateo_router,
    almacenes_router,
    inventario_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_pool()
    yield
    await close_pool()


app = FastAPI(
    title="ImportCost Pro API",
    version="1.0.0",
    description="Sistema de Costeo de Importaciones para Pymes",
    lifespan=lifespan,
)

s = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=s.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/api/auth", tags=["Auth"])
app.include_router(catalogos_router.router, prefix="/api/catalogos", tags=["Catalogos"])
app.include_router(dashboard_router.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(proveedores_router.router, prefix="/api/proveedores", tags=["Proveedores"])
app.include_router(productos_router.router, prefix="/api/productos", tags=["Productos"])
app.include_router(ordenes_router.router, prefix="/api/ordenes", tags=["Ordenes de Compra"])
app.include_router(importaciones_router.router, prefix="/api/importaciones", tags=["Importaciones"])
app.include_router(gastos_router.router, prefix="/api/gastos", tags=["Gastos"])
app.include_router(documentos_router.router, prefix="/api/documentos", tags=["Documentos"])
app.include_router(prorrateo_router.router, prefix="/api/prorrateo", tags=["Prorrateo"])
app.include_router(almacenes_router.router, prefix="/api/almacenes", tags=["Almacenes"])
app.include_router(inventario_router.router, prefix="/api/inventario", tags=["Inventario"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "ImportCost Pro"}
