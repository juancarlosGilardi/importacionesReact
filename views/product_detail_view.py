# views/producto_detail_view.py - Vista de detalle de producto
import flet as ft
from config_importaciones import (
    ImportacionesTheme, format_date, format_currency
)

class ProductoDetailView:
    def __init__(self, page: ft.Page, db, producto_id):
        self.page = page
        self.db = db
        self.producto_id = producto_id
        self.producto = None
        self.order_history = []
        self.load_data()
    
    def load_data(self):
        """Carga datos del producto y su historial"""
        try:
            # Cargar datos del producto
            query = "SELECT * FROM products WHERE id = %s"
            result = self.db.execute_query(query, (self.producto_id,))
            if result:
                self.producto = result[0]
            
            # Cargar historial de órdenes
            order_query = """
                SELECT po.id, po.po_number, po.order_date, po.status,
                       poi.quantity, poi.unit_price, poi.total_price,
                       s.business_name as supplier_name
                FROM purchase_order_items poi
                JOIN purchase_orders po ON poi.po_id = po.id
                LEFT JOIN suppliers s ON po.supplier_id = s.id
                WHERE poi.product_id = %s
                ORDER BY po.order_date DESC
            """
            self.order_history = self.db.execute_query(order_query, (self.producto_id,)) or []
            
        except Exception as e:
            print(f"Error cargando datos del producto: {e}")
    
    def detail_view(self):
        """Vista de detalle del producto"""
        
        if not self.producto:
            return ft.Container(
                content=ft.Column([
                    ft.Container(height=100),
                    ft.Icon("error", size=64, color=ImportacionesTheme.ERROR),
                    ft.Text("Producto no encontrado", 
                           size=20, 
                           weight=ft.FontWeight.BOLD),
                    ft.TextButton(
                        "Volver a productos",
                        icon="arrow_back",
                        on_click=lambda e: self.page.go("/productos")
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True
            )
        
        # Información básica
        info_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(self.producto.get("icono_ui", "inventory_2"), 
                               size=32, 
                               color=self.producto.get("color_ui", "#3B82F6")),
                        ft.Column([
                            ft.Text(self.producto["sku"], 
                                   size=20, weight=ft.FontWeight.BOLD),
                            ft.Text(self.producto["name"], 
                                   color=ImportacionesTheme.TEXT_SECONDARY),
                        ], spacing=2, expand=True),
                        ft.Container(
                            content=ft.Text(
                                self.producto["status"].upper(),
                                size=12,
                                color="white",
                                weight=ft.FontWeight.BOLD
                            ),
                            bgcolor={
                                "active": ImportacionesTheme.SUCCESS,
                                "inactive": ImportacionesTheme.WARNING,
                                "discontinued": ImportacionesTheme.ERROR
                            }.get(self.producto["status"], ImportacionesTheme.TEXT_SECONDARY),
                            padding=ft.padding.symmetric(horizontal=12, vertical=6),
                            border_radius=20,
                        )
                    ]),
                    ft.Divider(),
                    ft.ResponsiveRow([
                        ft.Column([
                            ft.Text("Código HS", size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                            ft.Text(self.producto["hs_code"] or "N/A", 
                                   weight=ft.FontWeight.BOLD),
                        ], col={"sm": 6, "md": 3}),
                        ft.Column([
                            ft.Text("Unidad de Medida", size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                            ft.Text(self.producto["unit_measure"] or "N/A", 
                                   weight=ft.FontWeight.BOLD),
                        ], col={"sm": 6, "md": 3}),
                        ft.Column([
                            ft.Text("Peso (kg)", size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                            ft.Text(str(self.producto.get("weight_kg", 0)) or "0.00", 
                                   weight=ft.FontWeight.BOLD),
                        ], col={"sm": 6, "md": 3}),
                        ft.Column([
                            ft.Text("Volumen (m³)", size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                            ft.Text(str(self.producto.get("volume_m3", 0)) or "0.00", 
                                   weight=ft.FontWeight.BOLD),
                        ], col={"sm": 6, "md": 3}),
                    ], spacing=20, run_spacing=16),
                    ft.Divider(),
                    ft.Column([
                        ft.Text("Descripción", size=14, weight=ft.FontWeight.BOLD),
                        ft.Text(self.producto.get("description") or "Sin descripción", 
                               color=ImportacionesTheme.TEXT_SECONDARY),
                    ], spacing=8),
                ], spacing=16),
                padding=24
            ),
            elevation=2,
        )
        
        # Historial de órdenes
        def create_order_row(order):
            return ft.DataRow(
                cells=[
                    ft.DataCell(
                        ft.Text(order["po_number"], 
                               color=ImportacionesTheme.TEXT_PRIMARY,
                               weight=ft.FontWeight.BOLD)
                    ),
                    ft.DataCell(
                        ft.Text(order["supplier_name"] or "N/A", 
                               color=ImportacionesTheme.TEXT_SECONDARY)
                    ),
                    ft.DataCell(
                        ft.Text(format_date(order["order_date"]), 
                               color=ImportacionesTheme.TEXT_SECONDARY)
                    ),
                    ft.DataCell(
                        ft.Text(str(order["quantity"]), 
                               color=ImportacionesTheme.TEXT_PRIMARY,
                               weight=ft.FontWeight.BOLD)
                    ),
                    ft.DataCell(
                        ft.Text(format_currency(order["unit_price"]), 
                               color=ImportacionesTheme.TEXT_PRIMARY)
                    ),
                    ft.DataCell(
                        ft.Text(format_currency(order["total_price"]), 
                               color=ImportacionesTheme.TEXT_PRIMARY,
                               weight=ft.FontWeight.BOLD)
                    ),
                    ft.DataCell(
                        ft.IconButton(
                            icon="visibility",
                            icon_size=18,
                            icon_color=ImportacionesTheme.TEXT_SECONDARY,
                            on_click=lambda e, o=order: self.page.go(f"/ordenes/{o['id']}")
                        )
                    ),
                ]
            )
        
        orders_section = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Historial en Órdenes", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(f"({len(self.order_history)} registros)", 
                               color=ImportacionesTheme.TEXT_SECONDARY),
                    ], spacing=8),
                    ft.Divider(),
                    ft.Container(
                        content=ft.DataTable(
                            columns=[
                                ft.DataColumn(ft.Text("Orden")),
                                ft.DataColumn(ft.Text("Proveedor")),
                                ft.DataColumn(ft.Text("Fecha")),
                                ft.DataColumn(ft.Text("Cantidad")),
                                ft.DataColumn(ft.Text("Precio Unit.")),
                                ft.DataColumn(ft.Text("Total")),
                                ft.DataColumn(ft.Text("")),
                            ],
                            rows=[create_order_row(order) for order in self.order_history],
                            heading_row_color=ImportacionesTheme.BG_SECONDARY,
                        ) if self.order_history else ft.Container(
                            content=ft.Column([
                                ft.Icon("shopping_cart", size=48, color=ImportacionesTheme.TEXT_SECONDARY),
                                ft.Text("No hay historial de órdenes", 
                                       color=ImportacionesTheme.TEXT_SECONDARY),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=40,
                        ),
                        border_radius=8,
                    ),
                ], spacing=16),
                padding=24
            ),
            elevation=2,
        )
        
        # Botones de acción
        action_buttons = ft.Row([
            ft.ElevatedButton(
                "Editar Producto",
                icon="edit",
                on_click=lambda e: self.page.go(f"/productos/{self.producto_id}/editar"),
                style=ft.ButtonStyle(
                    bgcolor=ImportacionesTheme.INFO,
                    color="white"
                )
            ),
            ft.ElevatedButton(
                "Nueva Orden con este Producto",
                icon="add_shopping_cart",
                on_click=self.create_new_order_with_product,
                style=ft.ButtonStyle(
                    bgcolor=ImportacionesTheme.SUCCESS,
                    color="white"
                )
            ),
            ft.ElevatedButton(
                "Volver a Productos",
                icon="arrow_back",
                on_click=lambda e: self.page.go("/productos"),
                style=ft.ButtonStyle(
                    bgcolor=ImportacionesTheme.TEXT_SECONDARY,
                    color="white"
                )
            ),
        ], spacing=12)
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text("Detalle de Producto", 
                                   size=24, 
                                   weight=ft.FontWeight.BOLD,
                                   color=ImportacionesTheme.TEXT_PRIMARY),
                            ft.Text(f"SKU: {self.producto['sku']}", 
                                   color=ImportacionesTheme.TEXT_SECONDARY),
                        ], spacing=2),
                        ft.Row([
                            ft.IconButton(
                                icon="print",
                                icon_color=ImportacionesTheme.TEXT_SECONDARY,
                                tooltip="Imprimir etiqueta"
                            ),
                            ft.IconButton(
                                icon="share",
                                icon_color=ImportacionesTheme.TEXT_SECONDARY,
                                tooltip="Compartir"
                            ),
                        ])
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.symmetric(horizontal=24, vertical=20),
                    bgcolor=ImportacionesTheme.BG_SECONDARY,
                    border=ft.border.only(bottom=ft.BorderSide(1, ImportacionesTheme.BORDER)),
                ),
                
                # Contenido principal
                ft.Container(
                    content=ft.Column([
                        ft.Container(height=24),
                        info_card,
                        ft.Container(height=24),
                        orders_section,
                        ft.Container(height=24),
                        action_buttons,
                        ft.Container(height=40),
                    ], scroll=ft.ScrollMode.AUTO),
                    padding=ft.padding.symmetric(horizontal=24),
                    expand=True,
                )
            ]),
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )
    
    def create_new_order_with_product(self, e):
        """Crea una nueva orden con este producto"""
        # Aquí podrías redirigir al formulario de nueva orden
        # con este producto ya agregado
        self.show_snackbar(f"Producto {self.producto['sku']} agregado a nueva orden", "info")
        self.page.go(f"/ordenes/nueva?product_id={self.producto_id}")
    
    def show_snackbar(self, message: str, tipo: str = "info"):
        """Muestra un mensaje snackbar"""
        colors = {
            "success": ImportacionesTheme.SUCCESS,
            "error": ImportacionesTheme.ERROR,
            "warning": "#F59E0B",
            "info": ImportacionesTheme.INFO
        }
        
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="white"),
            bgcolor=colors.get(tipo, ImportacionesTheme.INFO)
        )
        self.page.snack_bar.open = True
        self.page.update()