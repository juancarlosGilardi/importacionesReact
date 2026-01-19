# views/producto_form_view.py - Formulario para crear/editar productos
import flet as ft
from config_importaciones import ImportacionesTheme

class ProductoFormView:
    def __init__(self, page: ft.Page, db, producto_id=None):
        self.page = page
        self.db = db
        self.producto_id = producto_id
        self.producto_data = None
        
        if producto_id:
            self.load_producto()
    
    def load_producto(self):
        """Carga datos del producto si está editando"""
        try:
            query = "SELECT * FROM products WHERE id = %s"
            result = self.db.execute_query(query, (self.producto_id,))
            if result:
                self.producto_data = result[0]
        except Exception as e:
            print(f"Error cargando producto: {e}")
    
    def form_view(self):
        """Vista del formulario de producto"""
        
        # Campos del formulario
        sku_field = ft.TextField(
            label="SKU",
            hint_text="Código único del producto",
            value=self.producto_data.get("sku") if self.producto_data else "",
            width=300
        )
        
        nombre_field = ft.TextField(
            label="Nombre del Producto",
            hint_text="Nombre descriptivo",
            value=self.producto_data.get("name") if self.producto_data else "",
            expand=True
        )
        
        # ... agregar más campos según necesidad
        
        def save_producto(e):
            # Implementar lógica para guardar producto
            self.page.go("/productos")
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text("Nuevo Producto" if not self.producto_id else "Editar Producto", 
                                   size=24, weight=ft.FontWeight.BOLD),
                            ft.Text("Complete la información del producto", 
                                   color=ImportacionesTheme.TEXT_SECONDARY),
                        ], spacing=2),
                        ft.Row([
                            ft.TextButton(
                                "Cancelar",
                                on_click=lambda e: self.page.go("/productos")
                            ),
                            ft.ElevatedButton(
                                "Guardar Producto",
                                icon="save",
                                on_click=save_producto,
                                style=ft.ButtonStyle(
                                    bgcolor=ImportacionesTheme.SUCCESS,
                                    color="white"
                                )
                            ),
                        ])
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.symmetric(horizontal=24, vertical=20),
                    bgcolor=ImportacionesTheme.BG_SECONDARY,
                    border=ft.border.only(bottom=ft.BorderSide(1, ImportacionesTheme.BORDER)),
                ),
                
                # Formulario
                ft.Container(
                    content=ft.Column([
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Text("Información Básica", size=18, weight=ft.FontWeight.BOLD),
                                    ft.Divider(),
                                    ft.Row([sku_field, nombre_field], spacing=20),
                                    # ... agregar más campos
                                ], spacing=20),
                                padding=24
                            ),
                            elevation=2,
                        )
                    ], spacing=24),
                    padding=24,
                    expand=True,
                )
            ], scroll=ft.ScrollMode.AUTO),
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )