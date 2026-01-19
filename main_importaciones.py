# main_importaciones.py - Sistema independiente de costeo de importaciones
import threading
import flet as ft
import traceback
import mysql.connector
from mysql.connector import Error
from config_importaciones import (
    ImportacionesTheme, ImportacionesConfig, IMPORTACIONES_MENU,
    create_placeholder_view, get_status_color, get_status_icon, 
    format_currency, format_date, create_status_badge, create_error_view
)

from datetime import datetime, timedelta
from excel_kardex_processor import ExcelKardexProcessor
import json 

from views.import_details_view import ImportDetailsView


try:
    from views.ordenes_view import OrdenesView
    from views.facturas_view import FacturasView
    from views.orden_form_view import OrdenFormView
    from views.orden_detail_view import OrdenDetailView
    from views.product_view import ProductosView
    from views.transporte_view import TransporteView
    from views.duas_view import DUAView
    from views.reportes_view import ReportesView
    from views.product_form_view import ProductoFormView
    from views.product_detail_view import ProductoDetailView
    from views.almacen_form_view import AlmacenFormView
    from views.movimientos_view import MovimientosView
    from views.transferencia_form_view import TransferenciaFormView
    from views.salida_form_view import SalidaFormView
    VIEWS_LOADED = True
except ImportError as e:
    print(f"⚠️ Algunas vistas no disponibles: {e}")
    VIEWS_LOADED = False




class ImportacionesDatabase:
    """Gestor de base de datos para el módulo de importaciones"""
    
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Establece conexión con la base de datos MySQL"""
        try:
            self.connection = mysql.connector.connect(
                host=ImportacionesConfig.DB_HOST,
                port=ImportacionesConfig.DB_PORT,
                database=ImportacionesConfig.DB_NAME,
                user=ImportacionesConfig.DB_USER,
                password=ImportacionesConfig.DB_PASSWORD
            )
            print("✅ Conexión a MySQL establecida")
            return True
        except Error as e:
            print(f"❌ Error conectando a MySQL: {e}")
            return False
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = True):
        """Ejecuta una consulta SQL"""
        cursor = None
        try:
            # Asegurarse de que haya conexión válida antes de usar el cursor
            if not self.connection or not getattr(self.connection, 'is_connected', lambda: False)():
                # Intentar reconectar
                connected = self.connect()
                if not connected:
                    print("❌ No hay conexión a la base de datos. Abortando consulta.")
                    return None

            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch:
                result = cursor.fetchall()
                return result
            else:
                self.connection.commit()
                return cursor.lastrowid
                
        except Error as e:
            print(f"❌ Error en consulta SQL: {e}")
            print(f"Consulta: {query}")
            print(f"Parámetros: {params}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def get_dashboard_stats(self):
        """Obtiene estadísticas para el dashboard"""
        stats = {
            "total_orders": 0,
            "in_transit": 0,
            "in_customs": 0,
            "completed_month": 0,
            "pending_invoices": 0,
            "total_value": 0,
            "recent_orders": []
        }
        
        try:
            # Una sola consulta para todas las métricas
            query = """
                SELECT 
                    (SELECT COUNT(*) FROM purchase_orders) as total_orders,
                    (SELECT COUNT(*) FROM purchase_orders WHERE status = 'en_transito') as in_transit,
                    (SELECT COUNT(*) FROM purchase_orders WHERE status = 'en_aduana') as in_customs,
                    (SELECT COUNT(*) FROM purchase_orders 
                    WHERE status = 'completada' 
                    AND MONTH(order_date) = MONTH(CURDATE())
                    AND YEAR(order_date) = YEAR(CURDATE())) as completed_month,
                    (SELECT COUNT(*) FROM supplier_invoices WHERE status = 'pending') as pending_invoices,
                    (SELECT COALESCE(SUM(total_import_cost), 0) FROM purchase_orders WHERE status = 'completada') as total_value
            """
            result = self.execute_query(query)
            if result:
                stats.update(result[0])
            
            # Segunda consulta solo para las órdenes recientes
            query = """
                SELECT po.id, po.po_number, po.order_date, po.status, po.total_import_cost,
                    s.business_name as supplier_name
                FROM purchase_orders po
                LEFT JOIN suppliers s ON po.supplier_id = s.id
                ORDER BY po.order_date DESC
                LIMIT 10
            """
            stats["recent_orders"] = self.execute_query(query) or []
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
        return stats

def create_sidebar(page: ft.Page, on_navigate):
    """Crea el sidebar de navegación"""
    
    def create_menu_item(item):
        """Crea un item del menú"""
        is_active = page.route == item["route"]
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(item["icon"], size=20, 
                       color=ImportacionesTheme.TEXT_LIGHT if is_active else ImportacionesTheme.TEXT_SECONDARY),
                ft.Text(item["label"], 
                       color=ImportacionesTheme.TEXT_LIGHT if is_active else ImportacionesTheme.TEXT_SECONDARY,
                       weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL),
                ft.Container(
                    content=ft.Text(str(item.get("badge", "")), size=10, color="white"),
                    bgcolor=ImportacionesTheme.ERROR,
                    border_radius=10,
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    visible=item.get("badge", 0) > 0
                ) if "badge" in item else ft.Container()
            ], spacing=12),
            padding=ft.padding.symmetric(vertical=12, horizontal=16),
            bgcolor=f"{ImportacionesTheme.STATUS_CONFIRMED}30" if is_active else "transparent",
            border_radius=8,
            on_click=lambda e, r=item["route"]: on_navigate(r),
            ink=True,
        )
    
    # Crear todos los items del menú
    menu_items = []
    for section in IMPORTACIONES_MENU:
        # Título de sección
        menu_items.append(
            ft.Container(
                content=ft.Text(section["section"], size=11, 
                               color=ImportacionesTheme.TEXT_SECONDARY,
                               weight=ft.FontWeight.BOLD),
                padding=ft.padding.only(left=16, top=20, bottom=8),
            )
        )
        
        # Items de la sección
        for item in section["items"]:
            menu_items.append(create_menu_item(item))
    
    return ft.Container(
        content=ft.Column([
            # Header del sidebar
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon("account_balance_wallet", size=28, color=ImportacionesTheme.TEXT_LIGHT),
                        ft.Column([
                            ft.Text(ImportacionesConfig.APP_NAME, 
                                   size=18, weight=ft.FontWeight.BOLD, 
                                   color=ImportacionesTheme.TEXT_LIGHT),
                            ft.Text("Sistema de Costeo", 
                                   size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                        ], spacing=0)
                    ], spacing=12),
                    ft.Container(height=20),
                ]),
                padding=20,
                border=ft.border.only(bottom=ft.BorderSide(1, ImportacionesTheme.BORDER_DARK)),
            ),
            
            # Menú
            ft.Container(
                content=ft.Column(menu_items, scroll=ft.ScrollMode.AUTO),
                expand=True,
            ),
            
            # Footer del sidebar
            ft.Container(
                content=ft.Column([
                    ft.Divider(color=ImportacionesTheme.BORDER_DARK),
                    ft.Container(height=10),
                    ft.Row([
                        ft.CircleAvatar(
                            content=ft.Text("AD", size=12, color=ImportacionesTheme.BG_SIDEBAR),
                            bgcolor=ImportacionesTheme.TEXT_LIGHT,
                            radius=16
                        ),
                        ft.Column([
                            ft.Text("Administrador", size=13, 
                                   color=ImportacionesTheme.TEXT_LIGHT,
                                   weight=ft.FontWeight.BOLD),
                            ft.Text("admin@empresa.com", size=11, 
                                   color=ImportacionesTheme.TEXT_SECONDARY),
                        ], spacing=2, expand=True),
                        ft.IconButton(
                            icon="logout",
                            icon_size=18,
                            icon_color=ImportacionesTheme.TEXT_SECONDARY,
                            on_click=lambda e: print("Cerrar sesión")
                        )
                    ], spacing=12)
                ]),
                padding=16,
            )
        ]),
        width=ImportacionesConfig.SIDEBAR_WIDTH,
        bgcolor=ImportacionesTheme.BG_SIDEBAR,
    )

def create_header(page: ft.Page, title: str = None):
    """Crea el header de la aplicación"""
    
    return ft.Container(
        content=ft.Row([
            ft.Column([
                ft.Text(title or "Dashboard", 
                       size=20, weight=ft.FontWeight.BOLD,
                       color=ImportacionesTheme.TEXT_PRIMARY),
                ft.Text("Sistema de Costeo de Importaciones", 
                       size=13, color=ImportacionesTheme.TEXT_SECONDARY),
            ], spacing=2) if title else ft.Container(expand=True),
            
            ft.Row([
                ft.IconButton(
                    icon="notifications",
                    icon_size=22,
                    icon_color=ImportacionesTheme.TEXT_SECONDARY,
                    tooltip="Notificaciones"
                ),
                ft.Container(
                    content=ft.Text("3", size=10, color="white"),
                    bgcolor=ImportacionesTheme.ERROR,
                    border_radius=10,
                    padding=ft.padding.all(2),
                ),
                ft.IconButton(
                    icon="help",
                    icon_size=22,
                    icon_color=ImportacionesTheme.TEXT_SECONDARY,
                    tooltip="Ayuda"
                ),
                ft.Container(width=1, height=24, bgcolor=ImportacionesTheme.BORDER),
                ft.Text("v" + ImportacionesConfig.APP_VERSION, 
                       size=12, color=ImportacionesTheme.TEXT_SECONDARY),
            ], spacing=8)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.padding.symmetric(horizontal=24, vertical=16),
        bgcolor=ImportacionesTheme.BG_SECONDARY,
        border=ft.border.only(bottom=ft.BorderSide(1, ImportacionesTheme.BORDER)),
        height=ImportacionesConfig.HEADER_HEIGHT,
    )

def create_metric_card(title: str, value, subtitle: str = None, 
                       icon: str = None, color: str = ImportacionesTheme.STATUS_CONFIRMED,
                       on_click=None):
    """Crea una tarjeta de métrica"""
    
    content = ft.Column([
        ft.Row([
            ft.Container(
                content=ft.Icon(icon, size=20, color="white") if icon else ft.Container(),
                bgcolor=color,
                border_radius=8,
                padding=8,
            ) if icon else ft.Container(),
            ft.Text(title, size=14, color=ImportacionesTheme.TEXT_SECONDARY, expand=True),
        ], spacing=12),
        ft.Container(height=12),
        ft.Text(str(value), size=28, weight=ft.FontWeight.BOLD, 
               color=ImportacionesTheme.TEXT_PRIMARY),
        ft.Text(subtitle, size=12, color=ImportacionesTheme.TEXT_SECONDARY) if subtitle else ft.Container(),
    ])
    
    return ft.Container(
        content=content,
        padding=20,
        bgcolor=ImportacionesTheme.BG_SECONDARY,
        border_radius=12,
        border=ft.border.all(1, ImportacionesTheme.BORDER),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=10,
            color=ImportacionesTheme.BORDER + "30",
            offset=ft.Offset(0, 2)
        ),
        on_click=on_click,
        ink=on_click is not None,
    )

def dashboard_view(page: ft.Page, db: ImportacionesDatabase, file_picker: ft.FilePicker = None):
    """Vista del dashboard principal - VERSIÓN CON CARGA ASÍNCRONA"""
    
    # Configurar file picker para Kardex si no existe
    if not hasattr(page, 'kardex_file_picker'):
        page.kardex_file_picker = ft.FilePicker()
        page.overlay.append(page.kardex_file_picker)
    
    # ========== CONTENEDORES CON SPINNERS INICIALES ==========
    metrics_container = ft.Container(
        content=ft.Row([
            ft.ProgressRing(width=30, height=30),
            ft.Text("  Cargando métricas...", color=ImportacionesTheme.TEXT_SECONDARY)
        ], alignment=ft.MainAxisAlignment.CENTER),
        alignment=ft.alignment.center,
        height=170,
        bgcolor=ImportacionesTheme.BG_SECONDARY,
        border_radius=12,
        border=ft.border.all(1, ImportacionesTheme.BORDER),
    )
    
    orders_container = ft.Container(
        content=ft.Column([
            ft.ProgressRing(width=30, height=30),
            ft.Text("Cargando órdenes recientes...", color=ImportacionesTheme.TEXT_SECONDARY)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
        alignment=ft.alignment.center,
        height=400,
        bgcolor=ImportacionesTheme.BG_SECONDARY,
        border_radius=12,
        border=ft.border.all(1, ImportacionesTheme.BORDER),
        padding=24,
    )
    
    # ========== FUNCIÓN DE CARGA ASÍNCRONA ==========
    def load_data_async():
        """Carga datos en hilo secundario"""
        try:
            stats = db.get_dashboard_stats()
            
            # Actualizar métricas
            metrics_container.content = ft.ResponsiveRow([
                ft.Column([
                    create_metric_card(
                        title="Órdenes Activas",
                        value=stats["total_orders"],
                        subtitle="Total registradas",
                        icon="shopping_cart",
                        color=ImportacionesTheme.STATUS_CONFIRMED,
                        on_click=lambda e: page.go("/ordenes")
                    )
                ], col={"sm": 6, "md": 3}),
                
                ft.Column([
                    create_metric_card(
                        title="En Tránsito",
                        value=stats["in_transit"],
                        subtitle="En camino",
                        icon="local_shipping",
                        color=ImportacionesTheme.STATUS_IN_TRANSIT,
                        on_click=lambda e: page.go("/transporte")
                    )
                ], col={"sm": 6, "md": 3}),
                
                ft.Column([
                    create_metric_card(
                        title="En Aduana",
                        value=stats["in_customs"],
                        subtitle="En despacho",
                        icon="gavel",
                        color=ImportacionesTheme.STATUS_IN_CUSTOMS,
                        on_click=lambda e: page.go("/dua")
                    )
                ], col={"sm": 6, "md": 3}),
                
                ft.Column([
                    create_metric_card(
                        title="Valor Total",
                        value=format_currency(stats["total_value"]),
                        subtitle="Importaciones completadas",
                        icon="attach_money",
                        color=ImportacionesTheme.SUCCESS,
                        on_click=lambda e: page.go("/reportes")
                    )
                ], col={"sm": 6, "md": 3}),
            ], spacing=16, run_spacing=16)
            
            # Actualizar tabla de órdenes
            if stats["recent_orders"]:
                def create_order_row(order):
                    return ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(order["po_number"], 
                                               color=ImportacionesTheme.TEXT_PRIMARY,
                                               weight=ft.FontWeight.BOLD)),
                            ft.DataCell(ft.Text(order["supplier_name"] or "N/A", 
                                               color=ImportacionesTheme.TEXT_SECONDARY)),
                            ft.DataCell(ft.Text(format_date(order["order_date"]), 
                                               color=ImportacionesTheme.TEXT_SECONDARY)),
                            ft.DataCell(ft.Container(
                                content=ft.Row([
                                    ft.Icon(get_status_icon(order["status"]), size=14, 
                                           color=get_status_color(order["status"])),
                                    ft.Text(order["status"].replace("_", " ").title(), size=12,
                                           color=get_status_color(order["status"]))
                                ], spacing=4),
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                bgcolor=f"{get_status_color(order['status'])}15",
                                border_radius=8,
                            )),
                            ft.DataCell(ft.Text(format_currency(order.get("total_import_cost", 0)), 
                                               color=ImportacionesTheme.TEXT_PRIMARY,
                                               weight=ft.FontWeight.BOLD)),
                            ft.DataCell(ft.IconButton(
                                icon="visibility",
                                icon_size=18,
                                icon_color=ImportacionesTheme.TEXT_SECONDARY,
                                on_click=lambda e, o=order: page.go(f"/ordenes/{o['id']}")
                            )),
                        ]
                    )
                
                orders_table = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("N° Orden")),
                        ft.DataColumn(ft.Text("Proveedor")),
                        ft.DataColumn(ft.Text("Fecha")),
                        ft.DataColumn(ft.Text("Estado")),
                        ft.DataColumn(ft.Text("Total")),
                        ft.DataColumn(ft.Text("")),
                    ],
                    rows=[create_order_row(order) for order in stats["recent_orders"]],
                    heading_row_color=ImportacionesTheme.BG_SECONDARY,
                )
                
                orders_container.content = ft.Column([
                    ft.Row([
                        ft.Row([
                            ft.Icon("history", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                            ft.Text("Órdenes Recientes", size=16, 
                                   weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                        ], spacing=8),
                        ft.TextButton(
                            "Ver todas",
                            icon="chevron_right",
                            on_click=lambda e: page.go("/ordenes")
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=16),
                    orders_table,
                ])
            else:
                orders_container.content = ft.Column([
                    ft.Icon("inventory", size=48, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Container(height=16),
                    ft.Text("No hay órdenes registradas", 
                           color=ImportacionesTheme.TEXT_SECONDARY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            
            page.update()
            
        except Exception as e:
            print(f"Error en carga asíncrona: {e}")
            traceback.print_exc()
            
            # Mostrar error en la UI
            metrics_container.content = ft.Row([
                ft.Icon("error", color=ImportacionesTheme.ERROR),
                ft.Text(f"  Error al cargar datos", color=ImportacionesTheme.ERROR)
            ], alignment=ft.MainAxisAlignment.CENTER)
            
            orders_container.content = ft.Text(
                "No se pudieron cargar las órdenes. Verifica la conexión a la base de datos.",
                color=ImportacionesTheme.TEXT_SECONDARY
            )
            
            page.update()
    
    # Iniciar carga en background
    threading.Thread(target=load_data_async, daemon=True).start()
    
    # ========== HANDLER PARA KARDEX ==========
    def handle_kardex_upload(e: ft.FilePickerResultEvent):
        """Manejador para subida de archivo Kardex Excel"""
        if not e.files:
            return
        
        uploaded_file = e.files[0]
        
        try:
            excel_content = open(uploaded_file.path, 'rb').read()
            processor = ExcelKardexProcessor(db) 
            result = processor.process_and_save_to_db(excel_content, uploaded_file.name)
            
            if result.get('success'):
                kardex_count = result.get('total_kardex', result.get('inserted', 0))
                import_count = result.get('importaciones_insertadas', 0)
                
                detalles = []
                if kardex_count > 0: detalles.append(f"{kardex_count} productos")
                if import_count > 0: detalles.append(f"{import_count} importaciones")
                
                texto_resumen = ", ".join(detalles) if detalles else "Proceso completado"
                message = f"✅ Éxito: {texto_resumen} registrados."
                color = ImportacionesTheme.SUCCESS
                
                if result.get('errors'):
                    message += f" (⚠️ {len(result['errors'])} errores)"
                    color = ImportacionesTheme.WARNING
            else:
                message = f"❌ Error: {result.get('message', 'Error desconocido')}"
                color = ImportacionesTheme.ERROR
            
            page.snack_bar = ft.SnackBar(content=ft.Text(message, color="white"), bgcolor=color)
            page.snack_bar.open = True
            
        except Exception as ex:
            print(f"❌ Error procesando archivo: {str(ex)}")
            traceback.print_exc()
            
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error crítico: {str(ex)}", color="white"),
                bgcolor=ImportacionesTheme.ERROR,
            )
            page.snack_bar.open = True
        
        page.update()
    
    page.kardex_file_picker.on_result = handle_kardex_upload
    
    # ========== PIPELINE (estático, no necesita datos) ==========
    pipeline_steps = [
        {"name": "Borrador", "color": ImportacionesTheme.STATUS_DRAFT},
        {"name": "Confirmada", "color": ImportacionesTheme.STATUS_CONFIRMED},
        {"name": "En Tránsito", "color": ImportacionesTheme.STATUS_IN_TRANSIT},
        {"name": "En Aduana", "color": ImportacionesTheme.STATUS_IN_CUSTOMS},
        {"name": "Prorrateado", "color": ImportacionesTheme.STATUS_PROPORTIONED},
        {"name": "En Almacén", "color": ImportacionesTheme.STATUS_IN_WAREHOUSE},
        {"name": "Completada", "color": ImportacionesTheme.STATUS_COMPLETED},
    ]
    
    def create_pipeline_step(step, index):
        is_active = index <= 3
        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Text(str(index + 1), size=14, 
                                       color="white" if is_active else ImportacionesTheme.TEXT_SECONDARY),
                        bgcolor=step["color"] if is_active else ImportacionesTheme.BORDER,
                        width=32,
                        height=32,
                        border_radius=16,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(height=8),
                    ft.Text(step["name"], size=12, 
                           color=step["color"] if is_active else ImportacionesTheme.TEXT_SECONDARY,
                           weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                padding=12,
                bgcolor=f"{step['color']}15" if is_active else ImportacionesTheme.BG_SECONDARY,
                border_radius=12,
                border=ft.border.all(2, step["color"] if is_active else ImportacionesTheme.BORDER),
            ),
            ft.Container(
                content=ft.Icon("arrow_forward", size=16, color=ImportacionesTheme.TEXT_SECONDARY),
                padding=ft.padding.symmetric(horizontal=8),
                visible=index < 6
            ),
        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    pipeline = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon("timeline", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                ft.Text("Pipeline de Importaciones", size=16, 
                       weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
            ], spacing=8),
            ft.Container(height=16),
            ft.Row([create_pipeline_step(step, i) for i, step in enumerate(pipeline_steps)], 
                   spacing=4, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ]),
        padding=24,
        bgcolor=ImportacionesTheme.BG_SECONDARY,
        border_radius=12,
        border=ft.border.all(1, ImportacionesTheme.BORDER),
    )
    
    # ========== LAYOUT PRINCIPAL (se renderiza inmediatamente) ==========
    return ft.Container(
        content=ft.Column([
            create_header(page, "Dashboard"),
            ft.Container(
                content=ft.Column([
                    # Métricas (con spinner inicial, luego se actualiza)
                    metrics_container,
                    ft.Container(height=24),
                    
                    # Pipeline (estático)
                    pipeline,
                    ft.Container(height=24),
                    
                    # Órdenes (con spinner inicial, luego se actualiza)
                    orders_container,
                    ft.Container(height=24),
                    
                    # Acciones rápidas
                    ft.Row([
                        ft.ElevatedButton(
                            "Nueva Orden de Compra",
                            icon="add",
                            on_click=lambda e: page.go("/ordenes/nueva"),
                            style=ft.ButtonStyle(
                                bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                                color="white"
                            )
                        ),
                        ft.ElevatedButton(
                            "Importar Facturas (XML/PDF)",
                            icon="upload_file",
                            on_click=lambda e: file_picker.pick_files(
                                allowed_extensions=["xml", "pdf"],
                                allow_multiple=True,
                                dialog_title="Seleccionar facturas (XML o PDF)"
                            ) if file_picker else None,
                            style=ft.ButtonStyle(
                                bgcolor=ImportacionesTheme.INFO,
                                color="white"
                            ),
                            disabled=file_picker is None,
                        ),
                        ft.ElevatedButton(
                            "Registrar DUA",
                            icon="description",
                            on_click=lambda e: page.go("/dua/nuevo"),
                            style=ft.ButtonStyle(
                                bgcolor=ImportacionesTheme.ERROR,
                                color="white"
                            )
                        ),
                        ft.ElevatedButton(
                            "Importar Kardex (Excel)",
                            icon="upload_file",
                            on_click=lambda e: page.kardex_file_picker.pick_files(
                                allowed_extensions=["xlsx", "xls"],
                                allow_multiple=False,
                                dialog_title="Seleccionar archivo Kardex Excel"
                            ),
                            style=ft.ButtonStyle(
                                bgcolor=ImportacionesTheme.WARNING,
                                color="white"
                            ),
                        ),
                    ], spacing=12, wrap=True),
                ], scroll=ft.ScrollMode.AUTO),
                padding=24,
                expand=True,
            )
        ]),
        expand=True,
        bgcolor=ImportacionesTheme.BG_PRIMARY,
    )

def main(page: ft.Page):
    """Función principal de la aplicación con mejor manejo de errores"""
    
    try:
        # Configurar página
        page.title = f"{ImportacionesConfig.APP_NAME} - Sistema de Costeo de Importaciones"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 0
        page.spacing = 0
        page.fonts = {
            "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
        }
        page.theme = ft.Theme(font_family="Inter")
        
        file_picker = ft.FilePicker()
        page.overlay.append(file_picker)

        db = ImportacionesDatabase()
        
        if not db.connection or not db.connection.is_connected():
            print("⚠️ ADVERTENCIA: No hay conexión a la base de datos")
            print("   La aplicación funcionará en modo limitado")
        else:
            print("✅ Conexión a base de datos establecida")

        def handle_file_upload(e: ft.FilePickerResultEvent):
            if not e.files:
                return
            
            # Mostrar indicador inmediatamente
            page.snack_bar = ft.SnackBar(
                content=ft.Row([
                    ft.ProgressRing(width=20, height=20, stroke_width=2),
                    ft.Text(f"  Procesando {len(e.files)} archivo(s)...", color="white")
                ]),
                bgcolor=ImportacionesTheme.INFO,
                duration=60000  # Mantener abierto
            )
            page.snack_bar.open = True
            page.update()
            
            def background_processing():
                processed_count = 0
                error_count = 0
                
                for uploaded_file in e.files:
                    try:
                        if uploaded_file.name.lower().endswith('.xml'):
                            result = process_xml_file(uploaded_file)
                        elif uploaded_file.name.lower().endswith('.pdf'):
                            result = process_pdf_file(uploaded_file)
                        else:
                            error_count += 1
                            continue
                        
                        if result == "processed":
                            processed_count += 1
                        elif result == "error":
                            error_count += 1
                            
                    except Exception as ex:
                        print(f"❌ Error procesando {uploaded_file.name}: {str(ex)}")
                        error_count += 1
                
                # Notificar resultado final
                mostrar_resultado_upload(processed_count, error_count)
                
                if processed_count > 0:
                    page.go("/facturas")
            
            threading.Thread(target=background_processing, daemon=True).start()
        
        def process_xml_file(xml_file):
            """Procesa un archivo XML - Versión CORREGIDA"""
            try:
                with open(xml_file.path, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                
                # Parsear XML
                from xml_parser import XMLInvoiceParser
                parser = XMLInvoiceParser()
                invoice_data = parser.parse_invoice_xml(xml_content)
                
                if not invoice_data:
                    print(f"❌ No se pudo parsear {xml_file.name}")
                    return "error"
                
                # Validar datos mínimos
                if not invoice_data.get('invoice_number'):
                    print(f"⚠️ Factura sin número, usando nombre de archivo")
                    invoice_number = xml_file.name.replace('.xml', '')
                else:
                    invoice_number = invoice_data['invoice_number']
                
                if not invoice_data['supplier'].get('ruc'):
                    print(f"❌ Factura sin RUC, omitiendo: {xml_file.name}")
                    return "skipped"
                
                # Usar el nombre del proveedor correctamente
                supplier_ruc = invoice_data['supplier'].get('ruc', '')
                supplier_name = invoice_data['supplier'].get('business_name')
                if not supplier_name:
                    supplier_name = invoice_data['supplier'].get('trade_name', f"Proveedor {supplier_ruc}")
                
                # Asegurar que supplier_name no sea None
                if not supplier_name:
                    supplier_name = f"Proveedor {supplier_ruc}"
                
                total_amount = invoice_data['totals'].get('payable_amount', 0)
                
                # Verificar si ya existe esta factura
                check_query = """
                    SELECT id FROM supplier_invoices 
                    WHERE invoice_number = %s OR xml_hash = MD5(%s)
                """
                existing = db.execute_query(check_query, (invoice_number, xml_content))
                
                if existing:
                    print(f"⚠️ Factura {invoice_number} ya existe, omitiendo...")
                    return "skipped"
                
                # Buscar proveedor por RUC
                supplier_query = "SELECT id FROM suppliers WHERE ruc = %s"
                supplier_result = db.execute_query(supplier_query, (supplier_ruc,))
                
                supplier_id = None
                if supplier_result:
                    supplier_id = supplier_result[0]['id']
                else:
                    # Crear proveedor si no existe
                    insert_supplier = """
                        INSERT INTO suppliers (ruc, business_name, status)
                        VALUES (%s, %s, 'active')
                    """
                    supplier_id = db.execute_query(
                        insert_supplier, 
                        (supplier_ruc, supplier_name), 
                        fetch=False
                    )
                
                if not supplier_id:
                    print(f"❌ Error creando proveedor para {xml_file.name}")
                    return "error"
                
                # Preparar parámetros
                params = (
                    invoice_number,
                    None,  # po_id (asociar manualmente después)
                    invoice_data.get('issue_date'),
                    supplier_id,
                    4,  # PEN por defecto
                    1.0,  # Tipo de cambio
                    invoice_data['totals'].get('tax_exclusive_amount', 0),
                    invoice_data['totals'].get('tax_inclusive_amount', 0) - invoice_data['totals'].get('tax_exclusive_amount', 0),
                    total_amount,
                    xml_file.path,
                    xml_content
                )
                
                # Crear factura en la base de datos
                insert_query = """
                    INSERT INTO supplier_invoices 
                    (invoice_number, po_id, invoice_date, supplier_id, currency_id,
                    exchange_rate, subtotal, tax_amount, total_amount, xml_file_path,
                    xml_hash, status, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, MD5(%s), 'pending', 1)
                """
                
                factura_id = db.execute_query(insert_query, params, fetch=False)
                
                if factura_id:
                    print(f"✅ Factura {invoice_number} importada (ID: {factura_id})")
                    return "processed"
                else:
                    print(f"❌ Error importando {invoice_number}")
                    return "error"
                    
            except Exception as ex:
                print(f"❌ Error procesando XML {xml_file.name}: {str(ex)}")
            
                traceback.print_exc()
                return "error"

        # En tu main_importaciones.py, dentro de la función main() donde está process_pdf_file

        def process_pdf_file(pdf_file):
            """Procesa un archivo PDF - Versión MEJORADA con parser real y SIN self"""
            try:
                # Importar aquí para evitar dependencias circulares
                from pdf_parser import parse_pdf_invoice
                from pdf_utils import get_or_create_supplier, process_invoice_item, get_currency_id
                
                # Usar el parser REAL que extrae datos
                invoice_data = parse_pdf_invoice(pdf_file.path)
                
                if not invoice_data:
                    print(f"❌ No se pudo parsear PDF {pdf_file.name}")
                    return "error"
                
                # Validar datos mínimos
                invoice_number = invoice_data.get('invoice_number')
                if not invoice_number:
                    print(f"⚠️ Factura PDF sin número, usando nombre de archivo")
                    invoice_number = pdf_file.name.replace('.pdf', '')
                
                supplier_info = invoice_data.get('supplier', {})
                supplier_name = supplier_info.get('business_name')
                if not supplier_name:
                    print(f"❌ Factura PDF sin nombre de proveedor, omitiendo: {pdf_file.name}")
                    return "skipped"
                
                supplier_ruc = supplier_info.get('ruc', '')
                totals = invoice_data.get('totals', {})
                total_amount = totals.get('total_amount', 0)
                
                # Verificar si ya existe esta factura
                check_query = """
                    SELECT id FROM supplier_invoices 
                    WHERE invoice_number = %s
                """
                existing = db.execute_query(check_query, (invoice_number,))
                
                if existing:
                    print(f"⚠️ Factura {invoice_number} ya existe, omitiendo...")
                    return "skipped"
                

                invoice_date = invoice_data.get('issue_date')
                if not invoice_date:
                    invoice_date = datetime.now().strftime("%Y-%m-%d")
                    print(f"⚠️ Usando fecha actual para factura {invoice_number}")
                # Buscar/crear proveedor usando función independiente
                supplier_id = get_or_create_supplier(db, supplier_ruc, supplier_name, invoice_data)
                
                if not supplier_id:
                    print(f"❌ Error con proveedor para PDF {pdf_file.name}")
                    return "error"
                
                # Buscar PO relacionada
                po_id = None
                logistics = invoice_data.get('logistics', {})
                po_number = logistics.get('purchase_order')
                if po_number:
                    po_query = "SELECT id FROM purchase_orders WHERE po_number = %s"
                    po_result = db.execute_query(po_query, (po_number,))
                    if po_result:
                        po_id = po_result[0]['id']
                
                # Determinar moneda
                currency_code = invoice_data.get('currency', 'USD')
                currency_id = get_currency_id(currency_code)
                
                # Preparar notas
                notes = json.dumps({
                    "ocr_used": invoice_data.get('ocr_used', False),
                    "extracted_from": "pdf_parser",
                    "original_data": {
                        "invoice_number": invoice_number,
                        "date_found": invoice_data.get('issue_date') is not None,
                        "supplier_found": bool(supplier_name),
                        "total_found": total_amount > 0
                    },
                    "file_name": pdf_file.name
                }, ensure_ascii=False)
                
                # Insertar factura
                insert_query = """
                    INSERT INTO supplier_invoices 
                    (invoice_number, po_id, invoice_date, supplier_id, currency_id,
                    exchange_rate, subtotal, tax_amount, total_amount, archivo_pdf,
                    status, notes, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s, 1)
                """
                
                params = (
                    invoice_number,
                    po_id,
                    invoice_date,  # <-- AHORA SIEMPRE TIENE VALOR
                    supplier_id,
                    currency_id,
                    1.0,
                    totals.get('subtotal', 0),
                    totals.get('tax_amount', 0),
                    total_amount,
                    pdf_file.path,
                    notes[:500]
                )
                
                factura_id = db.execute_query(insert_query, params, fetch=False)
                
                if factura_id:
                    print(f"✅ Factura PDF {invoice_number} importada (ID: {factura_id})")
                    
                    # Insertar items usando función independiente
                    items = invoice_data.get('items', [])
                    items_processed = 0
                    
                    for item in items:
                        if process_invoice_item(db, factura_id, item, invoice_number):
                            items_processed += 1
                    
                    print(f"  📦 {items_processed} items procesados")
                    
                    return "processed"
                else:
                    print(f"❌ Error importando PDF {invoice_number}")
                    return "error"
                    
            except Exception as ex:
                print(f"❌ Error procesando PDF {pdf_file.name}: {str(ex)}")
            
                traceback.print_exc()
                return "error"
    
        def mostrar_resultado_upload(processed, errors):
            """Muestra resultado de la subida de archivos"""
            mensaje = ""
            color = ImportacionesTheme.INFO
            
            if processed > 0:
                mensaje = f"✅ {processed} factura(s) importada(s) correctamente"
                color = ImportacionesTheme.SUCCESS
                
                if errors > 0:
                    mensaje += f", {errors} con error(es)"
                    color = ImportacionesTheme.WARNING
            elif errors > 0:
                mensaje = f"❌ {errors} error(es) al importar"
                color = ImportacionesTheme.ERROR
            else:
                mensaje = " No se procesaron archivos"
            
            page.snack_bar = ft.SnackBar(
                content=ft.Text(mensaje, color="white"),
                bgcolor=color,
            )
            page.snack_bar.open = True
        # Asignar manejador
        file_picker.on_result = handle_file_upload
        
        def route_change(e):
            """Manejador de cambios de ruta con mejor manejo de errores"""
            try:
                print(f"\n=== NAVEGANDO A: {page.route} ===")
                
                page.views.clear()
                
                # Determinar qué vista mostrar basado en la ruta
                content = None
                
                try:
                    route_base = page.route.split('?')[0] if page.route else '/'
                    if route_base == "/" or route_base == "":
                        print("Cargando dashboard...")
                        content = dashboard_view(page, db, file_picker)
                    
                    # ========== RUTAS DE ÓRDENES DE COMPRA ==========
                    elif page.route == "/ordenes":
                            ordenes_view = OrdenesView(page, db)
                            content = ordenes_view.list_view()
                    
                    elif page.route == "/ordenes/nueva":
                            orden_form = OrdenFormView(page, db)
                            content = orden_form.form_view()
                    
                    elif page.route.endswith("/editar") and "/ordenes/" in page.route:
                        try:
                            parts = page.route.split("/")
                            orden_id = int(parts[2])  # /ordenes/{id}/editar
                            print(f"Cargando edición de orden #{orden_id}...")
                            orden_form = OrdenFormView(page, db, orden_id)
                            content = orden_form.form_view()
                        except (ValueError, IndexError):
                            content = create_error_view("Error", "ID de orden no válido")
                        except Exception as e:
                            content = create_error_view("Error al editar", str(e))
                    
                    elif page.route.startswith("/ordenes/") and len(page.route.split("/")) >= 3:
                            po_number = page.route.replace("/ordenes/", "")
                            if po_number != "nueva" and not po_number.endswith("/editar"):
                                orden_detail = OrdenDetailView(page,db, po_number)
                                content = orden_detail.detail_view()

                    # ========== RUTAS DE PRODUCTOS ==========
                    elif page.route == "/productos":
                        try:
                            productos_view = ProductosView(page, db)
                            content = productos_view.list_view()
                            print("✅ Vista de productos cargada")
                        except Exception as e:
                            print(f"❌ Error cargando productos: {e}")
                            traceback.print_exc()
                            content = create_error_view("Error al cargar productos", str(e))

                    elif page.route == "/productos/nuevo":
                            producto_form = ProductoFormView(page, db)
                            content = producto_form.form_view()
                            print("✅ Formulario de producto cargado")
                    elif page.route.startswith("/productos/") and page.route.endswith("/editar"):
                        try:
                            partes = page.route.split("/")
                            producto_id = int(partes[2])
                            producto_form = ProductoFormView(page, db, producto_id=producto_id)
                            content = producto_form.form_view()
                        except (IndexError, ValueError) as e:
                            content = create_error_view("Error en ruta", "ID de producto no válido")
                            page.go("/productos")
                        except Exception as e:
                            print(f"❌ Error cargando edición de producto: {e}")
                            traceback.print_exc()
                            content = create_error_view("Error al editar producto", str(e))

                    elif page.route.startswith("/productos/") and len(page.route.split("/")) == 3:
                        try:
                            producto_id = int(page.route.split("/")[2])
                            print(f"Cargando detalle de producto #{producto_id}...")
                            producto_detail = ProductoDetailView(page, db, producto_id)
                            content = producto_detail.detail_view()
                        except (ValueError, IndexError) as e:
                            content = create_error_view("Error", f"ID de producto no válido: {str(e)}")
                            page.go("/productos")
                        except Exception as e:
                            content = create_error_view("Error al cargar detalle de producto", str(e))
                                    
                    # ========== RUTAS DE FACTURAS ==========
                    elif page.route == "/facturas":
                        print("Cargando vista de facturas...")
                        try:
                            facturas_view = FacturasView(page, db, file_picker)
                            content = facturas_view.list_view()
                            print("✅ Vista de facturas cargada")
                        except Exception as e:
                            print(f"❌ Error cargando facturas: {e}")
                        
                            traceback.print_exc()
                            content = create_error_view("Error al cargar facturas", str(e))

                    elif page.route == "/facturas/nueva":
                        print("Cargando formulario de nueva factura...")
                        try:
                            factura_form = FacturaFormView(page, db)
                            content = factura_form.form_view()
                            print("✅ Formulario de factura cargado")
                        except Exception as e:
                            print(f"❌ Error cargando formulario de factura: {e}")
                        
                            traceback.print_exc()
                            content = create_error_view("Error en formulario de factura", str(e))
                    

                    # ========== RUTAS DE INVENTARIO Y STOCK ==========
                    
                    elif page.route == "/almacenes":
                        print("Cargando gestión de almacenes...")
                        from views.warehouses_view import WarehousesView
                        view = WarehousesView(page, db)
                        content = view.list_view()

                    elif page.route.startswith("/almacenes/") and page.route.split("/")[-1].isdigit():
                        warehouse_id = int(page.route.split("/")[-1])
                        print(f"Cargando detalle de almacén #{warehouse_id}...")
                        from views.warehouse_detail_view import WarehouseDetailView
                        view = WarehouseDetailView(page, db, warehouse_id)
                        content = view.detail_view()
                    
                    
                    elif page.route.startswith("/almacen/ingreso/"):
                        # Extraemos el ID directamente del final de la URL
                        po_id = int(page.route.split("/")[-1])
                        form = AlmacenFormView(page, db, po_id=po_id) 
                        content = form.form_view()
                        
                    elif page.route == "/inventario":
                        print("Cargando vista de Stock Actual...")
                        from views.almacen_stock_view import AlmacenStockView
                        view = AlmacenStockView(page, db)
                        content = view.stock_view()
                    
                    # ========== RUTA PARA EDITAR FACTURA ==========
                    elif page.route.startswith("/facturas/") and page.route.endswith("/editar"):
                        print("Cargando edición de factura...")
                        try:
                            # Extraer ID de la URL: /facturas/3/editar
                            partes = page.route.split("/")
                            factura_id = int(partes[2])  # El tercer elemento es el ID
                            
                            from views.factura_form_view import FacturaFormView
                            factura_form = FacturaFormView(page, db, factura_id=factura_id)
                            content = factura_form.form_view()
                            print(f"✅ Formulario de edición para factura #{factura_id} cargado")
                            
                        except (IndexError, ValueError) as e:
                            print(f"❌ Error en ruta de edición: {e}")
                            content = create_error_view("Error en ruta", "ID de factura no válido")
                            page.go("/facturas")
                        except Exception as e:
                            print(f"❌ Error cargando edición de factura: {e}")
                        
                            traceback.print_exc()
                            content = create_error_view("Error al editar factura", str(e))

                    # ========== RUTAS DE IMPORTACIONES (MANILA) ==========
                    elif page.route == "/importaciones":
                        print("Cargando vista de importaciones...")
                        try:
                            from views.import_view import ImportacionesView
                            importaciones_view = ImportacionesView(page, db)
                            content = importaciones_view.list_view()
                            print("✅ Vista de importaciones cargada")
                        except Exception as e:
                            print(f"❌ Error cargando importaciones: {e}")
                        
                            traceback.print_exc()
                            content = create_error_view("Error al cargar importaciones", str(e))

                    elif page.route == "/importaciones/nueva":
                        print("Cargando formulario de nueva importación...")
                        try:
                            from views.import_form_view import ImportacionFormView
                            importacion_form = ImportacionFormView(page, db)
                            content = importacion_form.form_view()
                            print("✅ Formulario de importación cargado")
                        except Exception as e:
                            print(f"❌ Error cargando formulario de importación: {e}")
                        
                            traceback.print_exc()
                            content = create_error_view("Error en formulario de importación", str(e))

                    # ===== RUTA NUEVA: DETALLES DE IMPORTACIÓN =====
                    elif page.route.startswith("/importaciones/") and not any(x in page.route for x in ["/editar", "/agregar-pos", "/nueva", "/asignar-dua"]):
                        try:
                            # Extraer el ID de la URL: /importaciones/123
                            importacion_id = int(page.route.split("/")[-1])
                            print(f"Cargando detalles de importación #{importacion_id}...")
                            
                            from views.import_details_view import ImportDetailsView
                            detalles_view = ImportDetailsView(page, db, importacion_id)
                            content = detalles_view.vista_detallada()
                            print(f"✅ Detalles de importación #{importacion_id} cargados")
                            
                        except (ValueError, IndexError) as e:
                            print(f"❌ Error en ruta de detalles de importación: {e}")
                            content = create_error_view("Error en ruta", f"ID de importación no válido: {str(e)}")
                            page.go("/importaciones")
                        except ImportError as e:
                            print(f"❌ Módulo import_details_view no encontrado: {e}")
                            content = create_placeholder_view(
                                "Detalles en desarrollo",
                                f"La vista de detalles está siendo implementada.\nError: {str(e)}",
                                "info"
                            )
                        except Exception as e:
                            print(f"❌ Error cargando detalles de importación: {e}")
                        
                            traceback.print_exc()
                            content = create_error_view("Error al cargar detalles de importación", str(e))

                    elif page.route.startswith("/importaciones/") and page.route.endswith("/editar"):
                        try:
                            partes = page.route.split("/")
                            importacion_id = int(partes[2])  # /importaciones/3/editar
                            print(f"Cargando edición de importación #{importacion_id}...")
                            
                            from views.import_form_view import ImportacionFormView
                            importacion_form = ImportacionFormView(page, db, importacion_id)
                            content = importacion_form.form_view()
                            print(f"✅ Edición de importación #{importacion_id} cargada")
                            
                        except (IndexError, ValueError) as e:
                            print(f"❌ Error en ruta de edición: {e}")
                            content = create_error_view("Error en ruta", "ID de importación no válido")
                        except Exception as e:
                            print(f"❌ Error cargando edición de importación: {e}")
                        
                            traceback.print_exc()
                            content = create_error_view("Error al editar importación", str(e))

                    elif page.route.startswith("/importaciones/") and "agregar-pos" in page.route:
                        try:
                            from views.add_order_view import AddOrderView
                            importacion_id = int(page.route.split("/")[-2])
                            print(f"Cargando agregar POs a importación #{importacion_id}...")
                            
                            view = AddOrderView(page, db, importacion_id)
                            content = view.vista_principal()
                            print(f"✅ Vista para agregar POs a importación #{importacion_id} cargada")
                            
                        except (ValueError, IndexError) as e:
                            print(f"❌ Error en ruta para agregar POs: {e}")
                            content = create_error_view("Error en ruta", "ID de importación no válido")
                            page.go("/importaciones")
                        except Exception as e:
                            print(f"❌ Error cargando vista para agregar POs: {e}")
                        
                            traceback.print_exc()
                            content = create_error_view("Error al cargar vista de POs", str(e))

                    elif page.route == "/gastos":
                        print("Cargando vista de gastos...")
                        try:
                            from views.gastos_view import GastosView
                            gastos_view = GastosView(page, db)
                            content = gastos_view.list_view()
                        except Exception as e:
                            print(f"❌ Error cargando gastos: {e}")
                            content = create_placeholder_view("Gastos", "Módulo en desarrollo", "payments")
                    
                    elif page.route == "/gastos/nuevo":
                        try:
                            from views.gasto_form_view import GastoFormView
                            gasto_form = GastoFormView(page, db)
                            content = gasto_form.form_view()
                        except Exception as e:
                            print(f"Error cargando formulario de gasto: {e}")
                        
                            traceback.print_exc()
                            content = create_error_view("Error al cargar formulario de gasto", str(e))
                    # ========== RUTAS DE PRORRATEO ==========
                    elif route_base == "/prorrateo":
                        print("Cargando vista de prorrateo...")
                        try:
                            from views.prorrateo_view import ProrrateoView
                            prorrateo_view = ProrrateoView(page, db)
                            content = prorrateo_view.prorrateo_view()
                            print("✅ Vista de prorrateo cargada")
                        except Exception as e:
                            print(f"❌ Error cargando prorrateo: {e}")
                        
                            traceback.print_exc()
                            content = create_error_view("Error en prorrateo", str(e))
                    
                    # ========== RUTAS DE REPORTES ==========
                    elif page.route == "/reportes":
                        print("Cargando reportes...")
                        try:
                            from views.reportes_view import ReportesView
                            reportes_view = ReportesView(page, db)
                            content = reportes_view.dashboard_view()
                        except Exception as e:
                            print(f"❌ Error cargando reportes: {e}")
                            content = create_placeholder_view("Reportes", "Módulo en desarrollo", "assessment")
                    
                    elif page.route == "/reportes/facturas":
                        try:
                            from views.reporte_facturas_view import ReporteFacturasView
                            reporte_facturas = ReporteFacturasView(page, db)
                            content = reporte_facturas.reporte_view()
                        except Exception as e:
                            content = create_placeholder_view("Reporte Facturas", "Módulo en desarrollo", "receipt")
                    
                    # ========== RUTAS EXISTENTES ==========
                    elif page.route == "/transporte":
                        try:
                            from views.transporte_view import TransporteView
                            transporte_view = TransporteView(page, db)
                            content = transporte_view.list_view()
                        except Exception as e:
                            print(f"❌ Error cargando transporte: {e}")
                            content = create_placeholder_view("Transporte", f"Error: {str(e)}", "local_shipping")

                    elif page.route == "/transporte/nuevo":
                        try:
                            from views.transporte_form_view import TransporteFormView
                            transporte_form = TransporteFormView(page, db)
                            content = transporte_form.form_view()
                        except Exception as e:
                            print(f"❌ Error cargando formulario de transporte: {e}")
                            content = create_error_view("Error en formulario de transporte", str(e))
                    elif page.route.endswith("/editar") and "/transporte/" in page.route:
                        try:
                            parts = page.route.split("/")
                            transporte_id = int(parts[2])  # /transporte/{id}/editar
                            from views.transporte_form_view import TransporteFormView
                            transporte_form = TransporteFormView(page, db, transporte_id)
                            content = transporte_form.form_view()
                        except (ValueError, IndexError):
                            content = create_error_view("Error", "ID de documento no válido")
                        except Exception as e:
                            content = create_error_view("Error al editar documento", str(e))


                    elif page.route == "/dua":
                        print("Cargando vista de DUAs...")
                        try:
                            from views.duas_view import DUAView
                            dua_view = DUAView(page, db)
                            content = dua_view.list_view()
                            print("✅ Vista de DUAs cargada")
                        except ImportError as e:
                            print(f"❌ Módulo de DUAs no encontrado: {e}")
                            content = create_placeholder_view(
                                "DUAs en desarrollo",
                                "El módulo de Documentos Únicos de Aduana está siendo implementado",
                                "description"
                            )
                        except Exception as e:
                            print(f"❌ Error cargando DUAs: {e}")
                            content = create_error_view("Error en DUAs", str(e))        
                    elif page.route == "/dua/nuevo":
                        print("Cargando formulario de nuevo DUA...")
                        try:
                            print("Intentando importar DUAFormView...")
                            from views.dua_form_view import DUAFormView
                            print("✅ DUAFormView importado exitosamente")
                            
                            print("Creando instancia de DUAFormView...")
                            dua_form = DUAFormView(page, db)
                            print("✅ Instancia de DUAFormView creada")
                            
                            print("Obteniendo form_view...")
                            content = dua_form.form_view()
                            print("✅ form_view obtenido exitosamente")
                            
                        except ImportError as e:
                            print(f"❌ Error de importación: {e}")
                        
                            traceback.print_exc()
                            content = create_error_view("Error de importación", str(e))
                        except Exception as e:
                            print(f"❌ Error general en formulario DUA: {e}")
                        
                            traceback.print_exc()
                            content = create_error_view("Error en formulario de DUA", str(e))
                            
                    elif page.route.startswith("/dua/") and page.route.endswith("/editar"):
                        try:
                            parts = page.route.split("/")
                            dua_id = int(parts[2])  # /dua/{id}/editar
                            from views.dua_form_view import DUAFormView
                            dua_form = DUAFormView(page, db, dua_id)
                            content = dua_form.form_view()
                        except (ValueError, IndexError):
                            content = create_error_view("Error", "ID de DUA no válido")
                        except Exception as e:
                            content = create_error_view("Error al editar DUA", str(e))

                    # ========== RUTAS DE MOVIMIENTOS (KARDEX) ==========
                    elif page.route == "/movimientos" or \
                         page.route in ["/movimientos/ingresos", "/movimientos/salidas", "/movimientos/transferencias"]:
                        
                        print(f"Cargando lista de movimientos: {page.route}...")
                        
                        # Determinar el tipo según la URL
                        tipo = None
                        if "/ingresos" in page.route: tipo = 'receipt'
                        elif "/salidas" in page.route: tipo = 'output'
                        elif "/transferencias" in page.route: tipo = 'transfer'
                        
                        try:
                            view = MovimientosView(page, db, tipo_movimiento=tipo)
                            content = view.list_view()
                        except Exception as e:
                            print(f"❌ Error: {e}")
                            traceback.print_exc()
                            content = create_error_view("Error", str(e))
                    # Editar Movimiento existente (Reutiliza tu AlmacenFormView)
                    elif page.route.startswith("/movimientos/") and page.route.endswith("/editar"):
                        try:
                            # Ruta ejemplo: /movimientos/15/editar
                            parts = page.route.split("/")
                            mov_id = int(parts[2])

                            form = AlmacenFormView(page, db, movimiento_id=mov_id)
                            content = form.form_view()
                            
                        except Exception as e:
                            print(f"❌ Error cargando edición de movimiento: {e}")
                            traceback.print_exc() # Ahora sí funcionará porque usa el global
                            content = create_error_view("Error al editar movimiento", str(e))   
                    
                    elif page.route == "/transferencia/nueva":
                        try:
                            form = TransferenciaFormView(page, db)
                            content = form.form_view()
                        except Exception as e:
                            print(f"❌ Error cargando transferencia: {e}")
                            traceback.print_exc()
                            content = create_error_view("Error", str(e))
                    
                    elif page.route == "/salida/nueva":
                        try:
                            form = SalidaFormView(page, db)
                            content = form.form_view()
                        except Exception as e:
                            print(f"❌ Error: {e}")
                            traceback.print_exc()
                            content = create_error_view("Error", str(e))

                    elif page.route == "/almacen":
                        content = create_placeholder_view("Almacén", "Módulo en desarrollo", "inventory")
                    elif page.route == "/inventario":
                        content = create_placeholder_view("Inventario", "Módulo en desarrollo", "warehouse")
                    elif page.route == "/estadisticas":
                        content = create_placeholder_view("Estadísticas", "Módulo en desarrollo", "analytics")
                    elif page.route == "/documentos":
                        content = create_placeholder_view("Documentos", "Módulo en desarrollo", "description")
                    elif page.route == "/exportaciones":
                        content = create_placeholder_view("Exportaciones", "Módulo en desarrollo", "download")
                    elif page.route == "/proveedores":
                        content = create_placeholder_view("Proveedores", "Módulo en desarrollo", "business")
                    elif page.route == "/productos":
                        content = create_placeholder_view("Productos", "Módulo en desarrollo", "category")
                    elif page.route == "/ajustes":
                        content = create_placeholder_view("Ajustes", "Módulo en desarrollo", "settings")
                    elif page.route == "/cuenta":
                        content = create_placeholder_view("Mi Cuenta", "Módulo en desarrollo", "person")
                    elif page.route == "/notificaciones":
                        content = create_placeholder_view("Notificaciones", "Módulo en desarrollo", "notifications")
                    else:
                        # Ruta no encontrada
                        print(f"❌ Ruta no encontrada: {page.route}")
                        content = ft.Container(
                            content=ft.Column([
                                ft.Container(height=100),
                                ft.Icon("error", size=80, color=ImportacionesTheme.ERROR),
                                ft.Container(height=20),
                                ft.Text("404 - Página no encontrada", size=24, 
                                       weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Container(height=10),
                                ft.Text(f"La ruta {page.route} no existe en el sistema.", 
                                       color=ImportacionesTheme.TEXT_SECONDARY),
                                ft.Container(height=30),
                                ft.Row([
                                    ft.ElevatedButton(
                                        "Volver al Dashboard",
                                        icon="home",
                                        on_click=lambda e: page.go("/"),
                                        style=ft.ButtonStyle(
                                            bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                                            color="white"
                                        )
                                    ),
                                    ft.ElevatedButton(
                                        "Ver rutas disponibles",
                                        icon="list",
                                        on_click=lambda e: print_routes(),
                                        style=ft.ButtonStyle(
                                            bgcolor=ImportacionesTheme.TEXT_SECONDARY,
                                            color="white"
                                        )
                                    )
                                ], spacing=12)
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            expand=True,
                            alignment=ft.alignment.center
                        )
                
                except Exception as view_error:
                    print(f"❌ Error crítico al cargar vista: {view_error}")
                    traceback.print_exc()
                    content = create_error_view(
                        "Error crítico en la aplicación",
                        f"Tipo: {type(view_error).__name__}\nMensaje: {str(view_error)}\n\nTraceback completo en consola."
                    )
                
                # Crear layout principal con sidebar y contenido
                try:
                    sidebar = create_sidebar(page, lambda route: page.go(route))
                    
                    page.views.append(
                        ft.View(
                            route=page.route,
                            padding=0,
                            controls=[
                                ft.Row([
                                    # Sidebar
                                    sidebar,
                                    
                                    # Contenido principal
                                    ft.Container(
                                        content=content,
                                        expand=True,
                                    ),
                                ], expand=True, spacing=0)
                            ]
                        )
                    )
                    
                    page.update()
                    print(f"✅ Vista {page.route} cargada correctamente")
                    
                except Exception as layout_error:
                    print(f"❌ Error creando layout: {layout_error}")
                    traceback.print_exc()
                    # Vista de fallback
                    page.views.append(
                        ft.View(
                            route=page.route,
                            controls=[
                                create_error_view(
                                    "Error de diseño",
                                    f"No se pudo crear el layout de la página: {str(layout_error)}"
                                )
                            ]
                        )
                    )
                    page.update()
                
            except Exception as route_error:
                print(f"❌ Error fatal en route_change: {route_error}")
                traceback.print_exc()
                # Último recurso: mostrar error crítico
                page.views.clear()
                page.views.append(
                    ft.View(
                        route="/error",
                        controls=[
                            create_error_view(
                                "Error crítico de aplicación",
                                f"La aplicación encontró un error fatal.\n\n{str(route_error)}"
                            )
                        ]
                    )
                )
                page.update()
        
        def print_routes():
            """Imprime todas las rutas disponibles en consola"""
            print("\n=== RUTAS DISPONIBLES ===")
            routes = [
                "/ - Dashboard principal",
                "/ordenes - Lista de órdenes de compra",
                "/ordenes/nueva - Nueva orden",
                "/facturas - Facturas de proveedor",
                "/gastos - Gastos de importación",
                "/prorrateo - Prorrateo de costos",
                "/reportes - Reportes de costeo",
                "/transporte - Documentos de transporte",
                "/dua - Documento Único de Aduana",
                "/almacen - Ingreso a almacén",
                "/inventario - Inventario",
                "/movimientos - Movimientos de almacén",
                "/estadisticas - Estadísticas",
                "/documentos - Documentos",
                "/exportaciones - Exportaciones",
                "/proveedores - Proveedores",
                "/productos - Productos",
                "/ajustes - Ajustes del sistema",
                "/cuenta - Mi cuenta",
                "/notificaciones - Notificaciones"
            ]
            for route in routes:
                print(route)
            print("=========================\n")
        
        # Configurar manejadores de eventos
        page.on_route_change = route_change
        
        # Navegar a la ruta inicial
        print("\nNavegando a ruta inicial...")
        page.go("/")
        
        print("✅ Aplicación inicializada correctamente")
        
    except Exception as app_error:
        print(f"❌ ERROR FATAL AL INICIAR APLICACIÓN: {app_error}")
        traceback.print_exc()
        
        # Mostrar error en la ventana si es posible
        try:
            page.clean()
            page.add(
                ft.Container(
                    content=ft.Column([
                        ft.Icon("error_outline", size=100, color="red"),
                        ft.Text("Error fatal al iniciar", size=24, weight="bold"),
                        ft.Text(str(app_error), size=16, color="gray"),
                        ft.Text("Ver consola para más detalles", size=14, color="darkgray"),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    expand=True
                )
            )
            page.update()
        except:
            print("No se pudo mostrar error en interfaz")

# Punto de entrada
if __name__ == "__main__":
    print("=== IMPORTACIONES COSTEO - INICIANDO ===")
    try:
        ft.app(target=main, view=ft.AppView.WEB_BROWSER)
    except Exception as launch_error:
        print(f"❌ ERROR AL LANZAR APLICACIÓN: {launch_error}")
        traceback.print_exc()
        input("Presiona Enter para salir...")
