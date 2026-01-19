# views/productos_view.py - Gestión de Productos desde Kardex
import flet as ft
from datetime import datetime
from config_importaciones import (
    ImportacionesTheme, ImportacionesConfig, 
    format_currency, format_date
)

class ProductosView:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.current_filter = {}
        self.products = []
        self.load_products()
    
    def load_products(self):
        """Carga productos desde la base de datos"""
        try:
            query = """
                SELECT p.*, 
                    COALESCE(inv.stock_actual, 0) as stock_actual,
                    COALESCE(inv.unit_cost, 0) as unit_cost,
                    COALESCE(ord.used_in_orders, 0) as used_in_orders
                FROM products p
                LEFT JOIN (
                    -- Consolidamos el inventario por producto antes de unir
                    SELECT product_id, SUM(quantity) as stock_actual, MAX(unit_cost) as unit_cost
                    FROM inventory
                    GROUP BY product_id
                ) inv ON p.id = inv.product_id
                LEFT JOIN (
                    -- Consolidamos el uso en órdenes antes de unir
                    SELECT product_id, COUNT(id) as used_in_orders
                    FROM purchase_order_items
                    GROUP BY product_id
                ) ord ON p.id = ord.product_id
                WHERE 1=1
            """
            
            params = []
            
            # Aplicar filtros
            if self.current_filter.get("search"):
                query += """ AND (
                    p.sku LIKE %s OR 
                    p.name LIKE %s OR 
                    p.description LIKE %s OR
                    p.hs_code LIKE %s
                )"""
                search_term = f"%{self.current_filter['search']}%"
                params.extend([search_term, search_term, search_term, search_term])
            
            if self.current_filter.get("status"):
                query += " AND p.status = %s"
                params.append(self.current_filter["status"])
            
            if self.current_filter.get("hs_code"):
                query += " AND p.hs_code LIKE %s"
                params.append(f"%{self.current_filter['hs_code']}%")
            
            query += """
                GROUP BY p.id
                ORDER BY p.created_at DESC, p.name ASC
            """
            
            result = self.db.execute_query(query, tuple(params) if params else None)
            self.products = result or []
            
        except Exception as e:
            print(f"Error cargando productos: {e}")
            import traceback
            traceback.print_exc()
            self.products = []
    
    def list_view(self):
        """Vista de lista de productos"""
        
        # Crear barra de búsqueda y filtros
        search_bar = ft.TextField(
            hint_text="Buscar por SKU, nombre, descripción o código HS...",
            prefix_icon="search",
            expand=True,
            border_color=ImportacionesTheme.BORDER,
            on_change=self.on_search_change,
            text_size=14
        )
        
        status_filter = ft.Dropdown(
            label="Estado",
            options=[
                ft.dropdown.Option("", "Todos"),
                ft.dropdown.Option("active", "Activo"),
                ft.dropdown.Option("inactive", "Inactivo"),
                ft.dropdown.Option("discontinued", "Descontinuado"),
            ],
            width=150,
            border_color=ImportacionesTheme.BORDER,
            on_change=self.on_status_filter_change,
            text_size=14
        )
        
        hs_code_filter = ft.TextField(
            label="Código HS",
            hint_text="Ej: 8504.40.00",
            width=150,
            border_color=ImportacionesTheme.BORDER,
            on_change=self.on_hs_code_filter_change,
            text_size=14
        )
        
        # Botón de nuevo producto
        new_product_btn = ft.ElevatedButton(
            "Nuevo Producto",
            icon="add",
            on_click=lambda e: self.page.go("/productos/nuevo"),
            style=ft.ButtonStyle(
                bgcolor=ImportacionesTheme.SUCCESS,
                color="white"
            )
        )
        
        # Botón para importar desde Excel
        import_btn = ft.ElevatedButton(
            "Importar Excel",
            icon="upload_file",
            on_click=lambda e: self.page.kardex_file_picker.pick_files(
                allowed_extensions=["xlsx", "xls"],
                allow_multiple=False,
                dialog_title="Seleccionar archivo Kardex Excel"
            ) if hasattr(self.page, 'kardex_file_picker') else None,
            style=ft.ButtonStyle(
                bgcolor=ImportacionesTheme.INFO,
                color="white"
            ),
            disabled=not hasattr(self.page, 'kardex_file_picker')
        )
        
        # Layout principal
        return ft.Container(
            content=ft.Column([
                # Header
                self.create_header("Productos", "Gestión de productos importados desde Kardex"),
                
                # Barra de herramientas
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            search_bar,
                            status_filter,
                            hs_code_filter,
                            ft.IconButton(
                                icon="filter_list",
                                tooltip="Más filtros",
                                icon_color=ImportacionesTheme.TEXT_SECONDARY,
                                on_click=self.show_advanced_filters
                            ),
                            ft.IconButton(
                                icon="refresh",
                                tooltip="Actualizar",
                                icon_color=ImportacionesTheme.TEXT_SECONDARY,
                                on_click=self.refresh_list
                            ),
                            ft.IconButton(
                                icon="download",
                                tooltip="Exportar",
                                icon_color=ImportacionesTheme.TEXT_SECONDARY,
                                on_click=self.export_products
                            ),
                        ], spacing=12),
                        ft.Container(height=16),
                        ft.Row([
                            new_product_btn,
                            import_btn,
                            ft.Text(f"{len(self.products)} productos encontrados", 
                                   color=ImportacionesTheme.TEXT_SECONDARY),
                        ], spacing=12),
                    ]),
                    padding=ft.padding.symmetric(horizontal=24, vertical=16),
                    bgcolor=ImportacionesTheme.BG_SECONDARY,
                    border_radius=12,
                    border=ft.border.all(1, ImportacionesTheme.BORDER),
                ),
                
                ft.Container(height=24),
                
                # Tabla de productos
                self.create_products_table() if self.products else self.create_empty_state(),
                
                ft.Container(height=40),
            ], scroll=ft.ScrollMode.AUTO),
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )
    
    def create_products_table(self):
        """Crea la tabla de productos"""
        
        def create_product_row(product):
            # Determinar color basado en estado
            status_color = {
                "active": ImportacionesTheme.SUCCESS,
                "inactive": ImportacionesTheme.TEXT_SECONDARY,
                "discontinued": ImportacionesTheme.ERROR
            }.get(product["status"], ImportacionesTheme.TEXT_SECONDARY)
            
            # Icono basado en icono_ui o default
            icon_name = product.get("icono_ui", "inventory_2")
            
            return ft.DataRow(
                cells=[
                    ft.DataCell(
                        ft.Row([
                            ft.Icon(icon_name, 
                                   size=16, 
                                   color=product.get("color_ui", "#3B82F6")),
                            ft.Text(product["sku"], 
                                   color=ImportacionesTheme.TEXT_PRIMARY,
                                   weight=ft.FontWeight.BOLD,
                                   size=14)
                        ], spacing=8)
                    ),
                    ft.DataCell(
                        ft.Text(product["name"][:50] + "..." if len(product["name"]) > 50 else product["name"], 
                               color=ImportacionesTheme.TEXT_PRIMARY,
                               size=13)
                    ),
                    
                    ft.DataCell(
                        ft.Text(product["hs_code"], 
                               color=ImportacionesTheme.TEXT_SECONDARY,
                               size=13)
                    ),
                    ft.DataCell(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon("check_circle" if product["status"] == "active" else "cancel",
                                       size=14, 
                                       color=status_color),
                                ft.Text(
                                    product["status"].title(), 
                                    size=12,
                                    color=status_color
                                )
                            ], spacing=6),
                            padding=ft.padding.symmetric(horizontal=10, vertical=6),
                            bgcolor=f"{status_color}15",
                            border_radius=8,
                        )
                    ),
                    ft.DataCell(ft.Text(f"{product.get('stock_actual', 0) or 0}")), # Cantidad en inventario
                    ft.DataCell(ft.Text(format_currency(product.get('unit_cost', 0) or 0), weight="bold")),
                    ft.DataCell(
                        ft.Text(product["unit_measure"], 
                               color=ImportacionesTheme.TEXT_SECONDARY,
                               size=13)
                    ),
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(str(product.get("used_in_orders", 0)), 
                                        size=11, color="white"),
                            bgcolor=ImportacionesTheme.INFO if product.get("used_in_orders", 0) > 0 
                                else ImportacionesTheme.TEXT_SECONDARY,
                            border_radius=8,
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        )
                    ),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(
                                icon="visibility",
                                icon_size=18,
                                icon_color=ImportacionesTheme.TEXT_SECONDARY,
                                tooltip="Ver detalle",
                                on_click=lambda e, p=product: self.view_product_detail(p["id"])
                            ),
                            ft.IconButton(
                                icon="edit",
                                icon_size=18,
                                icon_color=ImportacionesTheme.TEXT_SECONDARY,
                                tooltip="Editar",
                                on_click=lambda e, p=product: self.edit_product(p["id"])
                            ),
                            ft.PopupMenuButton(
                                icon=ft.Icons.MORE_VERT,
                                icon_size=18,
                                icon_color=ImportacionesTheme.TEXT_SECONDARY,
                                tooltip="Más opciones",
                                items=self.create_product_menu_items(product)
                            )
                        ], spacing=2)
                    ),
                ],
                on_select_changed=lambda e, p=product: self.view_product_detail(p["id"])
            )
        
        table = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("SKU", weight=ft.FontWeight.BOLD, size=14)),
                            ft.DataColumn(ft.Text("Nombre", weight=ft.FontWeight.BOLD, size=14)),
                            ft.DataColumn(ft.Text("Código HS", weight=ft.FontWeight.BOLD, size=14)),
                            ft.DataColumn(ft.Text("Estado", weight=ft.FontWeight.BOLD, size=14)),
                            ft.DataColumn(ft.Text("Stock")),      # Nueva
                            ft.DataColumn(ft.Text("Costo Unit.")),
                            ft.DataColumn(ft.Text("Unidad", weight=ft.FontWeight.BOLD, size=14)),
                            ft.DataColumn(ft.Text("En Órdenes", weight=ft.FontWeight.BOLD, size=14)),
                            ft.DataColumn(ft.Text("Acciones", weight=ft.FontWeight.BOLD, size=14)),
                        ],
                        rows=[create_product_row(product) for product in self.products],
                        heading_row_color=ImportacionesTheme.BG_SECONDARY,
                        heading_row_height=48,
                        data_row_min_height=56,
                        horizontal_lines=ft.border.BorderSide(1, ImportacionesTheme.BORDER),
                        vertical_lines=ft.border.BorderSide(1, ImportacionesTheme.BORDER),
                        column_spacing=20,
                    ),
                    border_radius=12,
                    border=ft.border.all(1, ImportacionesTheme.BORDER),
                    bgcolor=ImportacionesTheme.BG_SECONDARY,
                )
            ]),
            padding=ft.padding.symmetric(horizontal=24),
        )
        
        return table
    
    def create_product_menu_items(self, product):
        """Crea los items del menú contextual de un producto"""
        
        items = []
        
        # Cambiar estado
        if product["status"] == "active":
            items.append(
                ft.PopupMenuItem(
                    text="Desactivar",
                    icon="toggle_off",
                    on_click=lambda e, p=product: self.change_product_status(p, "inactive")
                )
            )
        else:
            items.append(
                ft.PopupMenuItem(
                    text="Activar",
                    icon="toggle_on",
                    on_click=lambda e, p=product: self.change_product_status(p, "active")
                )
            )
        
        items.append(ft.PopupMenuItem())  # Separador
        
        # Ver en órdenes
        if product.get("used_in_orders", 0) > 0:
            items.append(
                ft.PopupMenuItem(
                    text="Ver en órdenes",
                    icon="shopping_cart",
                    on_click=lambda e, p=product: self.view_product_orders(p)
                )
            )
        
        # Duplicar producto
        items.append(
            ft.PopupMenuItem(
                text="Duplicar",
                icon="content_copy",
                on_click=lambda e, p=product: self.duplicate_product(p)
            )
        )
        
        items.append(ft.PopupMenuItem())  # Separador
        
        # Marcar como descontinuado
        if product["status"] != "discontinued":
            items.append(
                ft.PopupMenuItem(
                    text="Marcar como descontinuado",
                    icon="block",
                    on_click=lambda e, p=product: self.change_product_status(p, "discontinued")
                )
            )
        
        # Eliminar
        items.append(
            ft.PopupMenuItem(
                text="Eliminar",
                icon="delete",
                on_click=lambda e, p=product: self.delete_product(p)
            )
        )
        
        return items
    
    def create_empty_state(self):
        """Crea estado vacío cuando no hay productos"""
        return ft.Container(
            content=ft.Column([
                ft.Container(height=100),
                ft.Icon("inventory_2", size=64, color=ImportacionesTheme.TEXT_SECONDARY),
                ft.Container(height=20),
                ft.Text("No hay productos registrados", 
                       size=20, 
                       weight=ft.FontWeight.BOLD,
                       color=ImportacionesTheme.TEXT_PRIMARY),
                ft.Container(height=10),
                ft.Text("Importa productos desde un archivo Kardex Excel o crea uno nuevo", 
                       color=ImportacionesTheme.TEXT_SECONDARY),
                ft.Container(height=30),
                ft.Row([
                    ft.ElevatedButton(
                        "Crear producto",
                        icon="add",
                        on_click=lambda e: self.page.go("/productos/nuevo"),
                        style=ft.ButtonStyle(
                            bgcolor=ImportacionesTheme.SUCCESS,
                            color="white"
                        )
                    ),
                    ft.ElevatedButton(
                        "Importar Excel",
                        icon="upload_file",
                        on_click=lambda e: self.page.kardex_file_picker.pick_files(
                            allowed_extensions=["xlsx", "xls"],
                            allow_multiple=False,
                            dialog_title="Seleccionar archivo Kardex Excel"
                        ) if hasattr(self.page, 'kardex_file_picker') else None,
                        style=ft.ButtonStyle(
                            bgcolor=ImportacionesTheme.INFO,
                            color="white"
                        ),
                        disabled=not hasattr(self.page, 'kardex_file_picker')
                    ),
                ], spacing=12, alignment=ft.MainAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=24,
            alignment=ft.alignment.center,
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
        )
    
    def create_header(self, title: str, subtitle: str = None):
        """Crea el header de la página"""
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(title, 
                        size=24, 
                        weight=ft.FontWeight.BOLD,
                        color=ImportacionesTheme.TEXT_PRIMARY),
                    ft.Text(subtitle, 
                        color=ImportacionesTheme.TEXT_SECONDARY) if subtitle else ft.Container(),
                ], spacing=2),
                ft.Row([
                    # CORREGIDO: Usar Container en lugar de Badge con parámetro 'content'
                    ft.Container(
                        content=ft.Text(f"Total: {len(self.products)}", size=12, color="white"),
                        bgcolor=ImportacionesTheme.INFO,
                        border_radius=8,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    ),
                    ft.Container(
                        content=ft.Text(f"Activos: {sum(1 for p in self.products if p['status'] == 'active')}", 
                                    size=12, color="white"),
                        bgcolor=ImportacionesTheme.SUCCESS,
                        border_radius=8,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    ),
                ], spacing=8)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=24, vertical=20),
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border=ft.border.only(bottom=ft.BorderSide(1, ImportacionesTheme.BORDER)),
        )
    
    def on_search_change(self, e):
        """Manejador de cambio en búsqueda"""
        self.current_filter["search"] = e.control.value
        self.load_products()
        self.page.go("/productos")  # Recargar vista
    
    def on_status_filter_change(self, e):
        """Manejador de cambio en filtro de estado"""
        self.current_filter["status"] = e.control.value if e.control.value else None
        self.load_products()
        self.page.go("/productos")  # Recargar vista
    
    def on_hs_code_filter_change(self, e):
        """Manejador de cambio en filtro de código HS"""
        self.current_filter["hs_code"] = e.control.value if e.control.value else None
        self.load_products()
        self.page.go("/productos")  # Recargar vista
    
    def refresh_list(self, e=None):
        """Actualiza la lista de productos"""
        self.load_products()
        self.page.go("/productos")
    
    def view_product_detail(self, product_id):
        """Ver detalle de un producto"""
        self.page.go(f"/productos/{product_id}")
    
    def edit_product(self, product_id):
        """Editar un producto"""
        self.page.go(f"/productos/{product_id}/editar")
    
    def show_advanced_filters(self, e):
        """Muestra filtros avanzados"""
        # Implementar diálogo de filtros avanzados
        dialog = ft.AlertDialog(
            title=ft.Text("Filtros avanzados"),
            content=ft.Column([
                ft.Text("Filtros avanzados para productos", color=ImportacionesTheme.TEXT_SECONDARY),
                # Agregar más controles de filtro aquí
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dialog)),
                ft.TextButton("Aplicar filtros", on_click=lambda e: self.apply_advanced_filters(dialog)),
            ]
        )
        self.page.open(dialog)
    
    def apply_advanced_filters(self, dialog):
        """Aplicar filtros avanzados"""
        # Implementar lógica de filtros avanzados
        self.page.close(dialog)
        self.refresh_list()
    
    def export_products(self, e):
        """Exporta productos a Excel"""
        self.show_snackbar("Función de exportación en desarrollo", "info")
    
    def change_product_status(self, product, new_status):
        """Cambia el estado de un producto"""
        try:
            query = "UPDATE products SET status = %s WHERE id = %s"
            self.db.execute_query(query, (new_status, product["id"]), fetch=False)
            
            status_display = {
                "active": "activado",
                "inactive": "desactivado",
                "discontinued": "marcado como descontinuado"
            }.get(new_status, new_status)
            
            self.show_snackbar(f"Producto {product['sku']} {status_display}", "success")
            self.refresh_list()
        except Exception as e:
            print(f"Error cambiando estado: {e}")
            self.show_snackbar("Error cambiando estado del producto", "error")
    
    def duplicate_product(self, product):
        """Duplica un producto existente"""
        try:
            # Obtener el producto original
            query = """
                SELECT * FROM products WHERE id = %s
            """
            original = self.db.execute_query(query, (product["id"],))
            
            if original:
                original = original[0]
                # Crear nuevo SKU
                new_sku = f"{original['sku']}-COPY"
                
                # Insertar copia
                insert_query = """
                    INSERT INTO products 
                    (sku, name, description, hs_code, unit_measure, 
                     weight_kg, volume_m3, status, color_ui, icono_ui, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
                """
                
                params = (
                    new_sku,
                    f"Copia de {original['name']}",
                    original['description'],
                    original['hs_code'],
                    original['unit_measure'],
                    original['weight_kg'],
                    original['volume_m3'],
                    'active',
                    original['color_ui'],
                    original['icono_ui']
                )
                
                self.db.execute_query(insert_query, params, fetch=False)
                
                self.show_snackbar(f"Producto {product['sku']} duplicado como {new_sku}", "success")
                self.refresh_list()
        except Exception as e:
            print(f"Error duplicando producto: {e}")
            self.show_snackbar("Error duplicando producto", "error")
    
    def delete_product(self, product):
        """Elimina un producto"""
        def confirm_delete(e):
            try:
                # Verificar si está en uso
                check_query = "SELECT COUNT(*) as count FROM purchase_order_items WHERE product_id = %s"
                result = self.db.execute_query(check_query, (product["id"],))
                
                if result and result[0]["count"] > 0:
                    self.show_snackbar("No se puede eliminar: producto está en órdenes de compra", "error")
                    self.page.close(dialog)
                    return
                
                # Eliminar producto
                delete_query = "DELETE FROM products WHERE id = %s"
                self.db.execute_query(delete_query, (product["id"],), fetch=False)
                
                self.page.close(dialog)
                self.show_snackbar(f"Producto {product['sku']} eliminado", "success")
                self.refresh_list()
            except Exception as e:
                print(f"Error eliminando producto: {e}")
                self.show_snackbar("Error eliminando producto", "error")
        
        # Mostrar diálogo de confirmación
        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar eliminación"),
            content=ft.Text(f"¿Está seguro de eliminar el producto {product['sku']}?\nEsta acción no se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dialog)),
                ft.TextButton("Eliminar", on_click=confirm_delete, 
                             style=ft.ButtonStyle(color=ImportacionesTheme.ERROR)),
            ]
        )
        
        self.page.open(dialog)
    
    def view_product_orders(self, product):
        """Ver órdenes que contienen este producto"""
        self.show_snackbar(f"Mostrando órdenes para {product['sku']}...", "info")
        # En una implementación completa, esto podría redirigir a una vista filtrada de órdenes
        # Por ahora solo mostramos un mensaje
        self.page.go(f"/ordenes?search={product['sku']}")
    
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