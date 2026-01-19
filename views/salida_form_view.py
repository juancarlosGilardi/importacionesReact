# views/salida_form_view.py
import flet as ft
from datetime import datetime
from config_importaciones import ImportacionesTheme, format_date

class SalidaFormView:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.items_salida = []
        
        # 1. Definimos la tabla como un atributo global de la clase
        self.tabla = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Producto")), 
                ft.DataColumn(ft.Text("Cantidad"), numeric=True),
                ft.DataColumn(ft.Text("Acciones"))
            ],
            rows=[],
            border=ft.border.all(1, ImportacionesTheme.BORDER),
            heading_row_color=ImportacionesTheme.BG_SECONDARY,
        )
        
        # Controles y datos iniciales
        self.controls = self.crear_controles()
        self.cargar_productos()

    def crear_controles(self):
        return {
            'movimiento_num': ft.TextField(
                label="N° Movimiento (Salida) *",
                prefix_icon=ft.Icons.NUMBERS,
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value=f"SAL-{int(datetime.now().timestamp())}"
            ),
            'fecha': ft.TextField(
                label="Fecha *",
                prefix_icon=ft.Icons.EVENT,
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value=datetime.now().strftime("%Y-%m-%d")
            ),
            'cliente_proyecto': ft.TextField(
                label="Cliente / Proyecto / Destino *",
                prefix_icon=ft.Icons.PERSON,
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                hint_text="Ej: Proyecto Minero X / Cliente Final"
            ),
            'ubicacion': ft.TextField(
                label="Almacén/Ubicación Origen",
                prefix_icon=ft.Icons.PLACE,
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="ALMACEN CENTRAL"
            ),
            'ref_doc': ft.TextField(
                label="Documento de Referencia",
                prefix_icon=ft.Icons.DESCRIPTION,
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                hint_text="Ej: Factura de Venta / Guía de Remisión"
            ),
            'notas': ft.TextField(
                label="Observaciones",
                prefix_icon=ft.Icons.NOTES,
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                multiline=True
            ),
            'producto_select': ft.Dropdown(
                label="Seleccionar Producto",
                expand=True,
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                options=[]
            ),
            'cantidad': ft.TextField(
                label="Cant.",
                width=100,
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                keyboard_type=ft.KeyboardType.NUMBER,
                value="1"
            )
        }

    def cargar_productos(self):
        """Carga los productos activos de la BD"""
        try:
            # Consultamos productos que tengan cantidad > 0 en la tabla inventory
            query = """
                SELECT DISTINCT p.id, p.name, p.sku 
                FROM products p
                INNER JOIN inventory i ON p.id = i.product_id
                WHERE p.status = 'active' AND i.quantity > 0
            """
            prods = self.db.execute_query(query)
            if prods:
                self.controls['producto_select'].options = [
                    ft.dropdown.Option(key=str(p['id']), text=f"{p['sku']} - {p['name']}") for p in prods
                ]
        except Exception as e:
            print(f"Error cargando productos con stock: {e}")

    def agregar_item(self, e):
        prod_id = self.controls['producto_select'].value
        qty = self.controls['cantidad'].value
        
        if not prod_id or not qty or float(qty) <= 0:
            self.page.snack_bar = ft.SnackBar(ft.Text("Ingrese producto y cantidad válida"))
            self.page.snack_bar.open = True
            self.page.update()
            return

        prod_text = next((o.text for o in self.controls['producto_select'].options if o.key == prod_id))
        
        self.items_salida.append({
            "id": prod_id,
            "nombre": prod_text,
            "cantidad": float(qty)
        })
        
        # Limpiar campos
        self.controls['producto_select'].value = None
        self.controls['cantidad'].value = "1"
        
        # 2. Refrescar la tabla visual
        self.actualizar_tabla()

    def eliminar_item(self, item):
        """Elimina un producto de la lista temporal"""
        self.items_salida.remove(item)
        self.actualizar_tabla()

    def actualizar_tabla(self):
        """Reconstruye las filas de la DataTable"""
        self.tabla.rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(i['nombre'])),
                    ft.DataCell(ft.Text(str(i['cantidad']))),
                    ft.DataCell(
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color="red",
                            on_click=lambda e, item=i: self.eliminar_item(item)
                        )
                    )
                ]
            ) for i in self.items_salida
        ]
        self.page.update()

    def guardar_salida(self, e):
        """Registra el movimiento en la BD"""
        if not self.controls['cliente_proyecto'].value or not self.items_salida:
            self.page.snack_bar = ft.SnackBar(ft.Text("Complete el destino y agregue productos"), bgcolor=ImportacionesTheme.WARNING)
            self.page.snack_bar.open = True
            self.page.update()
            return

        try:
            # 1. Cabecera (Tipo 'output')
            sql_mov = """
                INSERT INTO warehouse_movements 
                (movement_number, movement_type, movement_date, warehouse_location, reference_document, status, notes, created_by)
                VALUES (%s, 'output', %s, %s, %s, 'completed', %s, 1)
            """
            ref = f"{self.controls['ref_doc'].value} | Dest: {self.controls['cliente_proyecto'].value}"
            mov_id = self.db.execute_query(sql_mov, (
                self.controls['movimiento_num'].value, self.controls['fecha'].value,
                self.controls['ubicacion'].value, ref, self.controls['notas'].value
            ), fetch=False)
            
            # 2. Detalles (Incluimos NULL en po_item_id para evitar errores de restricción)
            for item in self.items_salida:
                # 1. Recuperar el costo promedio del inventario
                res_inv = self.db.execute_query("SELECT unit_cost FROM inventory WHERE product_id = %s LIMIT 1", (item['id'],))
                costo_promedio = float(res_inv[0]['unit_cost']) if res_inv else 0.0
                
                print(f"📦 DEBUG: Salida de Prod ID {item['id']} al costo de: {costo_promedio}")

                # 2. Registrar detalle de salida con el costo del inventario
                self.db.execute_query(
                    """INSERT INTO movement_details (movement_id, product_id, quantity, unit_cost, total_cost, po_item_id) 
                    VALUES (%s, %s, %s, %s, %s, NULL)""",
                    (mov_id, item['id'], item['cantidad'], costo_promedio, item['cantidad'] * costo_promedio), 
                    fetch=False
                )
                
                # 3. Descontar stock
                self.db.execute_query("UPDATE inventory SET quantity = quantity - %s WHERE product_id = %s", (item['cantidad'], item['id']), fetch=False)
            
            if hasattr(self.db.connection, 'commit'):
                self.db.connection.commit()
                
            self.page.snack_bar = ft.SnackBar(ft.Text("✅ Salida registrada con éxito"), bgcolor=ImportacionesTheme.SUCCESS)
            self.page.snack_bar.open = True
            self.page.go("/movimientos/salidas")
            
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {str(ex)}"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()

    def form_view(self):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.OUTBOX, size=28, color=ImportacionesTheme.ERROR),
                    ft.Text("Nueva Salida de Almacén", size=24, weight="bold"),
                ], spacing=12),
                ft.Divider(),
                ft.ResponsiveRow([
                    ft.Column([self.controls['movimiento_num']], col={"md": 4}),
                    ft.Column([self.controls['fecha']], col={"md": 4}),
                    ft.Column([self.controls['ubicacion']], col={"md": 4}),
                ]),
                self.controls['cliente_proyecto'],
                self.controls['ref_doc'],
                self.controls['notas'],
                ft.Divider(),
                ft.Text("Agregar Productos", size=16, weight="bold"),
                ft.Row([
                    self.controls['producto_select'], 
                    self.controls['cantidad'], 
                    ft.IconButton(
                        icon=ft.Icons.ADD_CIRCLE, 
                        icon_color=ImportacionesTheme.SUCCESS,
                        icon_size=32,
                        on_click=self.agregar_item
                    )
                ]),
                # 3. Usamos la tabla persistente de la clase
                self.tabla, 
                ft.Row([
                    ft.ElevatedButton("Cancelar", on_click=lambda e: self.page.go("/movimientos")),
                    ft.ElevatedButton(
                        "Registrar Salida", 
                        bgcolor=ImportacionesTheme.ERROR, 
                        color="white", 
                        on_click=self.guardar_salida
                    )
                ], alignment=ft.MainAxisAlignment.END, spacing=10)
            ], scroll=ft.ScrollMode.AUTO),
            padding=24, expand=True, bgcolor="white"
        )