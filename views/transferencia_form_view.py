import flet as ft
from datetime import datetime
from config_importaciones import ImportacionesTheme

class TransferenciaFormView:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.items_transferencia = []
        
        # Inicializamos la tabla aquí para poder usarla en todos los métodos
        self.tabla_items = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Producto")), 
                ft.DataColumn(ft.Text("Cantidad"), numeric=True),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[],
            border=ft.border.all(1, ImportacionesTheme.BORDER),
            heading_row_color=ImportacionesTheme.BG_SECONDARY,
            expand=True
        )
        
        # Controles
        self.controls = self.crear_controles()
        self.cargar_datos_iniciales()

    def crear_controles(self):
        return {
            'origen': ft.Dropdown(
                label="Almacén Origen *",
                prefix_icon=ft.Icons.STORE,
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                options=[], 
            ),
            'destino': ft.Dropdown(
                label="Almacén Destino *",
                prefix_icon=ft.Icons.STORE_MALL_DIRECTORY,
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                options=[],
            ),
            'fecha': ft.TextField(
                label="Fecha *",
                prefix_icon=ft.Icons.EVENT,
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value=datetime.now().strftime("%Y-%m-%d")
            ),
            'notas': ft.TextField(
                label="Motivo / Observaciones",
                prefix_icon=ft.Icons.NOTES,
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                multiline=True,
                min_lines=2
            ),
            # Controles para agregar producto
            'producto_add': ft.Dropdown(
                label="Seleccionar Producto",
                expand=True,
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                options=[],
                hint_text="Buscar producto..."
            ),
            'cantidad_add': ft.TextField(
                label="Cant.",
                width=100,
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                keyboard_type=ft.KeyboardType.NUMBER,
                value="1"
            )
        }

    def cargar_datos_iniciales(self):
        """Carga almacenes y productos"""
        # 1. Cargar Almacenes
        locs = ["ALMACEN CENTRAL", "TIENDA", "OBRA", "MERMAS"]
        try:
            res = self.db.execute_query("SELECT DISTINCT warehouse_location FROM warehouse_movements WHERE warehouse_location IS NOT NULL")
            if res:
                locs.extend([r['warehouse_location'] for r in res])
        except: pass
        
        opts = [ft.dropdown.Option(l) for l in sorted(list(set(locs)))]
        self.controls['origen'].options = opts
        self.controls['destino'].options = opts

        # 2. Cargar Productos
        try:
            query = """
                SELECT DISTINCT p.id, p.name, p.sku 
                FROM products p
                INNER JOIN inventory i ON p.id = i.product_id
                WHERE p.status = 'active' AND i.quantity > 0
            """
            prods = self.db.execute_query(query)
            if prods:
                self.controls['producto_add'].options = [
                    ft.dropdown.Option(key=str(p['id']), text=f"{p['sku']} - {p['name']}") for p in prods
                ]
        except Exception as e:
            print(f"Error: {e}")

    def agregar_producto(self, e):
        prod_id = self.controls['producto_add'].value
        qty = self.controls['cantidad_add'].value
        
        if not prod_id or not qty:
            self.page.snack_bar = ft.SnackBar(ft.Text("Seleccione producto y cantidad"))
            self.page.snack_bar.open = True
            self.page.update()
            return

        # Obtener nombre del producto seleccionado
        prod_text = next((o.text for o in self.controls['producto_add'].options if o.key == prod_id), "Producto Desconocido")
        
        # Agregar a la lista lógica
        self.items_transferencia.append({
            "id": prod_id,
            "nombre": prod_text,
            "cantidad": float(qty)
        })
        
        # Limpiar campos
        self.controls['producto_add'].value = None
        self.controls['cantidad_add'].value = "1"
        
        # ¡AQUÍ ESTÁ LA SOLUCIÓN! Actualizamos visualmente
        self.actualizar_tabla()

    def eliminar_item(self, item):
        """Elimina un item de la lista y refresca"""
        if item in self.items_transferencia:
            self.items_transferencia.remove(item)
            self.actualizar_tabla()

    def actualizar_tabla(self):
        self.tabla_items.rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(item['nombre'])),
                    ft.DataCell(ft.Text(str(item['cantidad']))), # El Text NO lleva numeric
                    ft.DataCell(
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color="red",
                            on_click=lambda e, x=item: self.eliminar_item(x)
                        )
                    ),
                ]
            ) for item in self.items_transferencia
        ]
        self.page.update()

    def guardar_transferencia(self, e):
        origen = self.controls['origen'].value
        destino = self.controls['destino'].value
        fecha = self.controls['fecha'].value
        
        if not origen or not destino or not self.items_transferencia:
            self.page.snack_bar = ft.SnackBar(ft.Text("Complete origen, destino y agregue productos"), bgcolor=ImportacionesTheme.WARNING)
            self.page.snack_bar.open = True
            self.page.update()
            return

        if origen == destino:
            self.page.snack_bar = ft.SnackBar(ft.Text("El origen y destino no pueden ser iguales"), bgcolor=ImportacionesTheme.WARNING)
            self.page.snack_bar.open = True
            self.page.update()
            return

        try:
            timestamp = int(datetime.now().timestamp())
            
            # 1. SALIDA (Output)
            sql_out = """
                INSERT INTO warehouse_movements 
                (movement_number, movement_type, movement_date, warehouse_location, reference_document, status, notes, created_by)
                VALUES (%s, 'output', %s, %s, %s, 'completed', %s, 1)
            """
            mov_out_id = self.db.execute_query(sql_out, (
                f"TRF-OUT-{timestamp}", fecha, origen, 
                f"Transferencia a {destino}", self.controls['notas'].value
            ), fetch=False)

            # 2. INGRESO (Receipt)
            sql_in = """
                INSERT INTO warehouse_movements 
                (movement_number, movement_type, movement_date, warehouse_location, reference_document, status, notes, created_by)
                VALUES (%s, 'receipt', %s, %s, %s, 'completed', %s, 1)
            """
            mov_in_id = self.db.execute_query(sql_in, (
                f"TRF-IN-{timestamp}", fecha, destino, 
                f"Transferencia desde {origen}", self.controls['notas'].value
            ), fetch=False)

            # 3. Detalles
            for item in self.items_transferencia:
                # Buscamos el costo para que la transferencia sea valorizada
                res_costo = self.db.execute_query(
                    "SELECT unit_cost FROM inventory WHERE product_id = %s LIMIT 1", 
                    (item['id'],)
                )
                costo_actual = float(res_costo[0]['unit_cost']) if res_costo else 0.0

                # Insertar en salida (Origen)
                self.db.execute_query(
                    "INSERT INTO movement_details (movement_id, product_id, quantity, unit_cost, total_cost) VALUES (%s, %s, %s, %s, %s)",
                    (mov_out_id, item['id'], item['cantidad'], costo_actual, costo_actual * item['cantidad']), fetch=False
                )
                # Insertar en entrada (Destino)
                self.db.execute_query(
                    "INSERT INTO movement_details (movement_id, product_id, quantity, unit_cost, total_cost) VALUES (%s, %s, %s, %s, %s)",
                    (mov_in_id, item['id'], item['cantidad'], costo_actual, costo_actual * item['cantidad']), fetch=False
                )
                
                # Actualizar saldos en inventory (Esto es vital para el Kardex)
                # Restar de origen
                self.db.execute_query("UPDATE inventory SET quantity = quantity - %s WHERE product_id = %s AND warehouse_location = %s",
                                    (item['cantidad'], item['id'], origen), fetch=False)
                # Sumar a destino
                self.db.execute_query("""INSERT INTO inventory (product_id, warehouse_location, quantity, unit_cost) 
                                        VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)""",
                                    (item['id'], destino, item['cantidad'], costo_actual), fetch=False)
                
                
            # Confirmar transacción si es necesario (depende de tu configuración de DB, pero execute_query con fetch=False suele hacer commit)
            if hasattr(self.db.connection, 'commit'):
                self.db.connection.commit()
            
            self.page.snack_bar = ft.SnackBar(ft.Text("✅ Transferencia registrada correctamente"), bgcolor=ImportacionesTheme.SUCCESS)
            self.page.snack_bar.open = True
            
            # Regresar a la lista de transferencias
            self.page.go("/movimientos/transferencias")
            
        except Exception as ex:
            print(f"Error al guardar: {ex}")
            import traceback
            traceback.print_exc()
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {str(ex)}"), bgcolor=ImportacionesTheme.ERROR)
            self.page.snack_bar.open = True
            self.page.update()

    def form_view(self):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SWAP_HORIZ, size=28, color=ImportacionesTheme.INFO),
                    ft.Text("Nueva Transferencia", size=24, weight="bold"),
                ], spacing=12),
                
                ft.Divider(),
                
                ft.ResponsiveRow([
                    ft.Column([self.controls['origen']], col={"md": 4}),
                    ft.Column([
                        ft.Icon(ft.Icons.ARROW_FORWARD, color=ImportacionesTheme.TEXT_SECONDARY),
                    ], col={"md": 1}, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Column([self.controls['destino']], col={"md": 4}),
                    ft.Column([self.controls['fecha']], col={"md": 3}),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                
                self.controls['notas'],
                
                ft.Divider(height=40),
                
                ft.Text("Productos a transferir", size=16, weight="bold"),
                
                ft.Row([
                    self.controls['producto_add'],
                    self.controls['cantidad_add'],
                    ft.IconButton(
                        icon=ft.Icons.ADD_CIRCLE, 
                        icon_color=ImportacionesTheme.SUCCESS, 
                        icon_size=32,
                        tooltip="Agregar a la lista",
                        on_click=self.agregar_producto
                    )
                ], vertical_alignment=ft.CrossAxisAlignment.START),
                
                ft.Container(
                    content=self.tabla_items, # Usamos la tabla global
                    border_radius=8,
                    margin=ft.margin.only(top=10, bottom=20)
                ),
                
                ft.Row([
                    ft.ElevatedButton(
                        "Cancelar", 
                        on_click=lambda e: self.page.go("/movimientos/transferencias"),
                        style=ft.ButtonStyle(color=ImportacionesTheme.TEXT_SECONDARY)
                    ),
                    ft.ElevatedButton(
                        "Procesar Transferencia", 
                        bgcolor=ImportacionesTheme.INFO, 
                        color="white", 
                        icon=ft.Icons.SAVE,
                        on_click=self.guardar_transferencia
                    )
                ], alignment=ft.MainAxisAlignment.END, spacing=20)
            ], scroll=ft.ScrollMode.AUTO),
            padding=30,
            bgcolor="white",
            expand=True
        )