# config_importaciones.py - Configuración específica del módulo de Importaciones
import flet as ft
from datetime import datetime

class ImportacionesTheme:
    """Tema específico para el módulo de Importaciones"""
    # Paleta de colores para estados de importación
    STATUS_DRAFT = "#94A3B8"
    STATUS_CONFIRMED = "#3B82F6"
    STATUS_IN_TRANSIT = "#F59E0B"
    STATUS_IN_CUSTOMS = "#EF4444"
    STATUS_PROPORTIONED = "#8B5CF6"
    STATUS_IN_WAREHOUSE = "#10B981"
    STATUS_COMPLETED = "#059669"
    STATUS_CANCELLED = "#DC2626"
    
    # Colores para tipos de gastos
    EXPENSE_FREIGHT = "#3B82F6"
    EXPENSE_INSURANCE = "#10B981"
    EXPENSE_CUSTOMS = "#EF4444"
    EXPENSE_AGENCY = "#8B5CF6"
    EXPENSE_STORAGE = "#6366F1"
    EXPENSE_BANK = "#059669"
    EXPENSE_OTHER = "#94A3B8"
    
    # Fondos
    BG_PRIMARY = "#F8FAFC"
    BG_SECONDARY = "#FFFFFF"
    BG_SIDEBAR = "#1E293B"
    
    # Textos
    TEXT_PRIMARY = "#1E293B"
    TEXT_SECONDARY = "#64748B"
    TEXT_LIGHT = "#F1F5F9"
    
    # Bordes
    BORDER = "#E2E8F0"
    BORDER_DARK = "#334155"
    
    # Estados
    SUCCESS = "#059669"
    WARNING = "#D97706"
    ERROR = "#DC2626"
    INFO = "#0284C7"

class ImportacionesConfig:
    """Configuración de la aplicación de Importaciones"""
    APP_NAME = "ImportCost Pro"
    APP_VERSION = "1.0.0"
    SIDEBAR_WIDTH = 280
    HEADER_HEIGHT = 64
    
    # Configuración de la base de datos
    DB_HOST = "localhost"
    DB_PORT = 3306
    DB_NAME = "importaciones_costeo"
    DB_USER = "root"
    DB_PASSWORD = "root"
    
    # Rutas de archivos
    UPLOAD_FOLDER = "uploads"
    XML_FOLDER = "xml_importados"
    REPORT_FOLDER = "reportes"
    
    # Configuración SUNAT (para Perú)
    SUNAT_IGV_RATE = 0.18
    SUNAT_IPM_RATE = 0.00
    SUNAT_AD_VALOREM_RATES = {
        "general": 0.06,  # 6% general
        "especifico": 0.00  # Puede variar por producto
    }
    
    # Incoterms soportados
    INCOTERMS = ["EXW", "FOB", "CFR", "CIF", "DAP", "DDP"]
    
    # Puertos comunes en Perú
    PORTS_PERU = {
        "callao": "Puerto del Callao",
        "paita": "Puerto de Paita", 
        "matarani": "Puerto de Matarani",
        "iquitos": "Puerto de Iquitos"
    }

# Menú principal de Importaciones
IMPORTACIONES_MENU = [
    {
        "section": "PRINCIPAL",
        "items": [
            {"icon": "dashboard", "label": "Dashboard", "route": "/"},
            {"icon": "notifications", "label": "Notificaciones", "route": "/notificaciones", "badge": 3},
        ]
    },
    {
        "section": "GESTIÓN DE IMPORTACIONES", 
        "items": [
            {"icon": "folder", "label": "Importaciones", "route": "/importaciones"}, 
            {"icon": "shopping_cart", "label": "Órdenes de Compra", "route": "/ordenes"},
            {"icon": "receipt", "label": "Facturas Proveedor", "route": "/facturas"},
            {"icon": "local_shipping", "label": "Documentos Transporte", "route": "/transporte"},
            {"icon": "description", "label": "DUA", "route": "/dua"},
            {"icon": "account_balance_wallet", "label": "Gastos Importación", "route": "/gastos"},
        ]
    },
    {
        "section": "COSTEO Y ALMACÉN",
        "items": [
            {"icon": "calculate", "label": "Prorrateo de Costos", "route": "/prorrateo"},
            {"icon": "inventory", "label": "Ingreso Almacén", "route": "/almacen"},
            {"icon": "warehouse", "label": "Inventario", "route": "/inventario"},
            {"icon": "sync_alt", "label": "Movimientos", "route": "/movimientos"},
        ]
    },
    {
        "section": "REPORTES Y ANÁLISIS",
        "items": [
            {"icon": "assessment", "label": "Reportes Costeo", "route": "/reportes"},
            {"icon": "analytics", "label": "Estadísticas", "route": "/estadisticas"},
            {"icon": "description", "label": "Documentos", "route": "/documentos"},
            {"icon": "download", "label": "Exportaciones", "route": "/exportaciones"},
        ]
    },
    {
        "section": "CONFIGURACIÓN",
        "items": [
            {"icon": "business", "label": "Proveedores", "route": "/proveedores"},
            {"icon": "category", "label": "Productos", "route": "/productos"},
            {"icon": "settings", "label": "Ajustes Sistema", "route": "/ajustes"},
            {"icon": "person", "label": "Mi Cuenta", "route": "/cuenta"},
        ]
    }
]

# Estados del flujo de importación
IMPORT_FLOW_STATES = [
    {"id": 1, "code": "draft", "name": "Borrador", "color": "#94A3B8", "icon": "edit"},
    {"id": 2, "code": "confirmed", "name": "Confirmada", "color": "#3B82F6", "icon": "check_circle"},
    {"id": 3, "code": "in_transit", "name": "En Tránsito", "color": "#F59E0B", "icon": "local_shipping"},
    {"id": 4, "code": "in_customs", "name": "En Aduana", "color": "#EF4444", "icon": "gavel"},
    {"id": 5, "code": "proportioned", "name": "Prorrateado", "color": "#8B5CF6", "icon": "calculate"},
    {"id": 6, "code": "in_warehouse", "name": "En Almacén", "color": "#10B981", "icon": "inventory"},
    {"id": 7, "code": "completed", "name": "Completada", "color": "#059669", "icon": "done_all"},
    {"id": 8, "code": "cancelled", "name": "Cancelada", "color": "#DC2626", "icon": "cancel"},
]

# Tipos de documentos de transporte
TRANSPORT_DOC_TYPES = [
    {"code": "bl", "name": "Conocimiento de Embarque", "icon": "description"},
    {"code": "awb", "name": "Guía Aérea", "icon": "flight"},
    {"code": "cmr", "name": "Carta de Porte", "icon": "local_shipping"},
    {"code": "tif", "name": "Tránsito Internacional", "icon": "border_clear"},
]

# Tipos de gastos de importación
EXPENSE_TYPES = [
    {"code": "freight", "name": "Flete Internacional", "color": "#3B82F6", "icon": "flight"},
    {"code": "insurance", "name": "Seguro", "color": "#10B981", "icon": "security"},
    {"code": "local_freight", "name": "Flete Local", "color": "#F59E0B", "icon": "local_shipping"},
    {"code": "customs_fees", "name": "Gastos Aduaneros", "color": "#EF4444", "icon": "gavel"},
    {"code": "agency_fees", "name": "Honorarios Agente", "color": "#8B5CF6", "icon": "badge"},
    {"code": "storage", "name": "Almacenaje", "color": "#6366F1", "icon": "warehouse"},
    {"code": "bank_charges", "name": "Gastos Bancarios", "color": "#059669", "icon": "account_balance"},
    {"code": "inspection", "name": "Inspección", "color": "#D97706", "icon": "search"},
    {"code": "other", "name": "Otros Gastos", "color": "#94A3B8", "icon": "payments"},
]

def create_placeholder_view(title: str, description: str = None, icon: str = "build"):
    """Crea una vista de marcador de posición para módulos en desarrollo"""
    return ft.Container(
        content=ft.Column([
            ft.Container(height=100),
            ft.Icon(icon, size=80, color=ImportacionesTheme.TEXT_SECONDARY),
            ft.Container(height=20),
            ft.Text(title, size=24, weight=ft.FontWeight.BOLD, 
                   color=ImportacionesTheme.TEXT_PRIMARY, text_align=ft.TextAlign.CENTER),
            ft.Container(height=10),
            ft.Text(
                description or "Esta funcionalidad está en desarrollo y estará disponible próximamente.",
                size=16, 
                color=ImportacionesTheme.TEXT_SECONDARY,
                text_align=ft.TextAlign.CENTER
            ),
            ft.Container(height=40),
            ft.ElevatedButton(
                "Volver al Dashboard",
                icon="dashboard",
                on_click=lambda e: e.page.go("/"),
                style=ft.ButtonStyle(
                    bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                    color=ImportacionesTheme.TEXT_LIGHT
                )
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        expand=True,
        alignment=ft.alignment.center
    )

# En config_importaciones.py, asegúrate de tener estas funciones:

def get_status_color(status_code: str) -> str:
    """Obtiene el color correspondiente a un estado"""
    for state in IMPORT_FLOW_STATES:
        if state["code"] == status_code:
            return state["color"]
    return ImportacionesTheme.TEXT_SECONDARY

def get_status_icon(status_code: str) -> str:
    """Obtiene el icono correspondiente a un estado"""
    for state in IMPORT_FLOW_STATES:
        if state["code"] == status_code:
            return state["icon"]
    return "help"

def format_currency(amount: float, currency: str = "PEN") -> str:
    """Formatea una cantidad de dinero"""
    symbols = {"PEN": "S/", "USD": "$", "EUR": "€"}
    symbol = symbols.get(currency, "")
    return f"{symbol} {amount:,.2f}"

def format_date(date_str: str, format: str = "%d/%m/%Y") -> str:
    """Formatea una fecha"""
    try:
        if isinstance(date_str, str):
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            date_obj = date_str
        return date_obj.strftime(format)
    except:
        return date_str

# Agrega esto en config_importaciones.py, por ejemplo después de create_placeholder_view

def create_error_view(error_title: str, error_details: str = None, show_reload: bool = True):
    """Crea una vista de error detallada"""
    return ft.Container(
        content=ft.Column([
            ft.Container(height=50),
            ft.Icon("error_outline", size=80, color=ImportacionesTheme.ERROR),
            ft.Container(height=20),
            ft.Text(error_title, 
                   size=24, weight=ft.FontWeight.BOLD, 
                   color=ImportacionesTheme.ERROR),
            ft.Container(height=10),
            ft.Text("Ha ocurrido un error en la aplicación", 
                   size=16, color=ImportacionesTheme.TEXT_SECONDARY,
                   text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            
            # Panel de detalles del error
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon("info", size=20, color=ImportacionesTheme.INFO),
                        ft.Text("Detalles del error:", 
                               size=14, weight=ft.FontWeight.BOLD,
                               color=ImportacionesTheme.TEXT_PRIMARY),
                    ], spacing=8),
                    ft.Container(height=8),
                    ft.Text(
                        error_details or "No hay detalles disponibles del error.",
                        size=13, 
                        color=ImportacionesTheme.TEXT_SECONDARY,
                        selectable=True  # Permite seleccionar texto para copiar
                    ),
                ]),
                padding=16,
                bgcolor=f"{ImportacionesTheme.BG_SECONDARY}",
                border_radius=10,
                border=ft.border.all(1, ImportacionesTheme.BORDER),
                width=600
            ) if error_details else ft.Container(),
            
            ft.Container(height=30),
            
            # Acciones
            ft.Row([
                ft.ElevatedButton(
                    "Recargar aplicación",
                    icon="refresh",
                    on_click=lambda e: e.page.go("/"),
                    style=ft.ButtonStyle(
                        bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                        color="white"
                    )
                ) if show_reload else ft.Container(),
                
                ft.ElevatedButton(
                    "Volver al Dashboard",
                    icon="dashboard",
                    on_click=lambda e: e.page.go("/"),
                    style=ft.ButtonStyle(
                        bgcolor=ImportacionesTheme.SUCCESS,
                        color="white"
                    )
                ),
                
                ft.ElevatedButton(
                    "Reportar problema",
                    icon="bug_report",
                    on_click=lambda e: print(f"=== REPORTE DE ERROR ===\nTítulo: {error_title}\nDetalles: {error_details}"),
                    style=ft.ButtonStyle(
                        bgcolor=ImportacionesTheme.WARNING,
                        color="white"
                    )
                ),
            ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
            
            # Información adicional
            ft.Container(height=20),
            ft.Text(
                "Si el problema persiste, contacte al administrador del sistema.",
                size=12,
                color=ImportacionesTheme.TEXT_SECONDARY,
                italic=True
            ),
            
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        expand=True,
        alignment=ft.alignment.center,
        bgcolor=ImportacionesTheme.BG_PRIMARY
    )

def create_status_badge(status_code: str, show_icon: bool = True) -> ft.Container:
    """Crea un badge de estado"""
    color = get_status_color(status_code)
    icon = get_status_icon(status_code)
    status_name = next((s["name"] for s in IMPORT_FLOW_STATES if s["code"] == status_code), status_code)
    
    return ft.Container(
        content=ft.Row([
            ft.Icon(icon, size=14, color=color) if show_icon else ft.Container(),
            ft.Text(status_name.capitalize(), size=12, weight=ft.FontWeight.BOLD, color=color),
        ], spacing=4),
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        bgcolor=f"{color}15",
        border_radius=8,
        border=ft.border.all(1, color)
    )