# views/almacen_form_view.py - VERSIÓN ACTUALIZADA con almacenes reales
import flet as ft
import threading
from datetime import datetime
from config_importaciones import (
    ImportacionesTheme, format_currency, format_date
)

class AlmacenFormView:
    def __init__(self, page: ft.Page, db, movimiento_id=None, po_id=None):
        self.page = page
        self.db = db
        self.movimiento_id = movimiento_id
        self.modo_edicion = movimiento_id is not None
        self.po_id = po_id or self._get_po_id_from_url()
        
        # Datos
        self.orden = None
        self.items_orden = []
        self.items_movimiento = []
        
        # CACHÉ de almacenes
        self._warehouses_cache = []
        
        # Contenedores para carga asíncrona
        self.main_container = None
        self.loading = True
    
    def _get_po_id_from_url(self):
        """Obtiene el po_id de la URL"""
        if hasattr(self.page, 'route') and '/ingreso/' in self.page.route:
            try:
                return int(self.page.route.split('/ingreso/')[-1])
            except:
                return None
        return None
    
    def form_view(self):
        """Vista del formulario con carga asíncrona"""
        
        # Contenedor de carga
        self.main_container = ft.Container(
            content=ft.Column([
                ft.ProgressRing(width=50, height=50),
                ft.Container(height=16),
                ft.Text("Cargando formulario...", color=ImportacionesTheme.TEXT_SECONDARY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               alignment=ft.MainAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True,
        )
        
        # Cargar datos en background
        threading.Thread(target=self._load_data_async, daemon=True).start()
        
        return ft.Container(
            content=self.main_container,
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )
    
    def _load_data_async(self):
        """Carga todos los datos necesarios"""
        try:
            # 1. Cargar almacenes
            self._load_warehouses()
            
            # 2. Cargar orden si existe
            if self.po_id:
                self._load_order()
                self._load_order_items()
            
            # 3. Cargar movimiento si es edición
            if self.modo_edicion:
                self._load_movement()
            
            # 4. Crear controles
            self._create_controls()
            
            # 5. Construir UI
            self._build_ui()
            
            self.page.update()
            
        except Exception as e:
            print(f"Error cargando datos: {e}")
            import traceback
            traceback.print_exc()
            self.main_container.content = ft.Column([
                ft.Icon(ft.Icons.ERROR, size=64, color=ImportacionesTheme.ERROR),
                ft.Text(f"Error: {str(e)}", color=ImportacionesTheme.ERROR),
                ft.ElevatedButton("Volver", on_click=lambda _: self.page.go("/ordenes")),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            self.page.update()
    
    def _load_warehouses(self):
        """Carga almacenes activos"""
        query = "SELECT id, code, name FROM warehouses WHERE status = 'active' ORDER BY name"
        self._warehouses_cache = self.db.execute_query(query) or []
        
        # Si no hay almacenes, crear uno por defecto
        if not self._warehouses_cache:
            self.db.execute_query(
                "INSERT INTO warehouses (code, name, status) VALUES ('ALM-01', 'Almacén Principal', 'active')",
                fetch=False
            )
            self._warehouses_cache = self.db.execute_query(query) or []
    
    def _load_order(self):
        """Carga datos de la orden"""
        query = """
            SELECT po.*, s.business_name as supplier_name
            FROM purchase_orders po
            LEFT JOIN suppliers s ON po.supplier_id = s.id
            WHERE po.id = %s
        """
        result = self.db.execute_query(query, (self.po_id,))
        if result:
            self.orden = result[0]
    
    def _load_order_items(self):
        """Carga items de la orden"""
        query = """
            SELECT 
                poi.id as po_item_id,
                p.id as product_id,
                p.sku,
                p.name as producto,
                poi.quantity,
                poi.unit_measure,
                -- LÓGICA HÍBRIDA DE COSTO:
                -- Si unit_landed_cost es NULL o 0.00, toma el unit_price (Compra Local)
                COALESCE(NULLIF(poi.unit_landed_cost, 0), poi.unit_price) as unit_cost,
                -- El total se calcula en base al costo detectado
                (poi.quantity * COALESCE(NULLIF(poi.unit_landed_cost, 0), poi.unit_price)) as total_cost
            FROM purchase_order_items poi
            JOIN products p ON poi.product_id = p.id
            WHERE poi.po_id = %s
        """
        result = self.db.execute_query(query, (self.po_id,))
        self.items_orden = result or []
        
        # Crear items de movimiento
        self.items_movimiento = []
        for item in self.items_orden:
            self.items_movimiento.append({
                'po_item_id': item['po_item_id'],
                'product_id': item['product_id'],
                'product_name': f"{item['sku']} - {item['producto']}",
                'cantidad_orden': float(item['quantity']),
                'costo_unitario': float(item['unit_cost']),
                'cantidad_recibida': float(item['quantity']),  # Por defecto, recibir todo
            })
    
    def _load_movement(self):
        """Carga movimiento existente"""
        query = "SELECT * FROM warehouse_movements WHERE id = %s"
        result = self.db.execute_query(query, (self.movimiento_id,))
        if result:
            self.movimiento = result[0]
            self.po_id = self.movimiento.get('po_id')
            
            # Cargar orden y items
            self._load_order()
            self._load_order_items()
            
            # Cargar detalles del movimiento
            details_query = "SELECT * FROM movement_details WHERE movement_id = %s"
            details = self.db.execute_query(details_query, (self.movimiento_id,))
            
            if details:
                for det in details:
                    for item in self.items_movimiento:
                        if item['po_item_id'] == det['po_item_id']:
                            item['cantidad_recibida'] = float(det['quantity'])
                            break
    
    def _create_controls(self):
        """Crea los controles del formulario"""
        
        # Número de movimiento
        self.ctrl_movement_number = ft.TextField(
            label="Número de Movimiento *",
            value=f"REC-{datetime.now().strftime('%Y%m%d')}-{self.po_id or '001'}",
            prefix_icon=ft.Icons.NUMBERS,
            border_color=ImportacionesTheme.BORDER,
            filled=True,
        )
        
        # Tipo de movimiento
        self.ctrl_movement_type = ft.Dropdown(
            label="Tipo de Movimiento *",
            value="receipt",
            options=[
                ft.dropdown.Option("receipt", "📥 Recepción de Mercadería"),
                ft.dropdown.Option("transfer", "🔄 Transferencia entre Almacenes"),
                ft.dropdown.Option("output", "📤 Salida de Mercadería"),
                ft.dropdown.Option("adjustment", "📊 Ajuste de Inventario"),
            ],
            border_color=ImportacionesTheme.BORDER,
            filled=True,
            on_change=self._on_type_change,
        )
        
        # Fecha
        self.ctrl_movement_date = ft.TextField(
            label="Fecha del Movimiento *",
            value=datetime.now().strftime("%Y-%m-%d"),
            prefix_icon=ft.Icons.EVENT,
            border_color=ImportacionesTheme.BORDER,
            filled=True,
        )
        
        # ALMACÉN DESTINO (usa caché)
        self.ctrl_warehouse = ft.Dropdown(
            label="Almacén Destino *",
            value=str(self._warehouses_cache[0]['id']) if self._warehouses_cache else None,
            options=[
                ft.dropdown.Option(str(w['id']), f"{w['code']} - {w['name']}")
                for w in self._warehouses_cache
            ],
            border_color=ImportacionesTheme.BORDER,
            filled=True,
        )
        
        # Almacén origen (para transferencias)
        self.ctrl_source_warehouse = ft.Dropdown(
            label="Almacén Origen",
            options=[
                ft.dropdown.Option(str(w['id']), f"{w['code']} - {w['name']}")
                for w in self._warehouses_cache
            ],
            border_color=ImportacionesTheme.BORDER,
            filled=True,
            visible=False,  # Solo visible en transferencias
        )
        
        # Documento de referencia
        self.ctrl_reference = ft.TextField(
            label="Documento de Referencia",
            prefix_icon=ft.Icons.DESCRIPTION,
            border_color=ImportacionesTheme.BORDER,
            filled=True,
        )
        
        # Estado
        self.ctrl_status = ft.Dropdown(
            label="Estado",
            value="draft",
            options=[
                ft.dropdown.Option("draft", "📝 Borrador"),
                ft.dropdown.Option("confirmed", "✅ Confirmado"),
                ft.dropdown.Option("completed", "🎉 Completado"),
            ],
            border_color=ImportacionesTheme.BORDER,
            filled=True,
        )
        
        # Notas
        self.ctrl_notes = ft.TextField(
            label="Notas / Observaciones",
            multiline=True,
            min_lines=2,
            max_lines=4,
            border_color=ImportacionesTheme.BORDER,
            filled=True,
        )
        
        # Campos de cantidad por item
        self.item_quantity_fields = {}
        for item in self.items_movimiento:
            self.item_quantity_fields[item['po_item_id']] = ft.TextField(
                value=str(item['cantidad_recibida']),
                width=100,
                text_align=ft.TextAlign.RIGHT,
                keyboard_type=ft.KeyboardType.NUMBER,
                on_change=lambda e, pid=item['po_item_id']: self._on_quantity_change(pid, e),
            )
    
    def _on_type_change(self, e):
        """Muestra/oculta campos según tipo de movimiento"""
        is_transfer = e.control.value == "transfer"
        self.ctrl_source_warehouse.visible = is_transfer
        self.page.update()
    
    def _on_quantity_change(self, po_item_id, e):
        """Actualiza cantidad recibida"""
        try:
            new_qty = float(e.control.value or 0)
            for item in self.items_movimiento:
                if item['po_item_id'] == po_item_id:
                    item['cantidad_recibida'] = new_qty
                    break
        except ValueError:
            pass
    
    def _build_ui(self):
        """Construye la interfaz del formulario"""
        
        if not self.orden:
            self.main_container.content = ft.Column([
                ft.Icon(ft.Icons.ERROR, size=64, color=ImportacionesTheme.ERROR),
                ft.Container(height=16),
                ft.Text("Orden de Compra no especificada", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=16),
                ft.ElevatedButton("Seleccionar Orden", on_click=lambda _: self.page.go("/ordenes")),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            return
        
        titulo = f"Editar Movimiento #{self.movimiento_id}" if self.modo_edicion else "Nuevo Ingreso de Mercadería"
        
        # Crear tabla de items
        items_table = self._build_items_table()
        
        self.main_container.content = ft.Column([
            # Header
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.INVENTORY, size=28, color=ImportacionesTheme.TEXT_PRIMARY),
                            ft.Text(titulo, size=24, weight=ft.FontWeight.BOLD),
                        ], spacing=12),
                        ft.Text(f"Orden: {self.orden['po_number']} - {self.orden.get('supplier_name', 'N/A')}",
                               color=ImportacionesTheme.TEXT_SECONDARY),
                    ]),
                    ft.ElevatedButton(
                        "Volver",
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda _: self.page.go(f"/ordenes/{self.po_id}"),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.symmetric(horizontal=24, vertical=20),
                bgcolor=ImportacionesTheme.BG_SECONDARY,
                border=ft.border.only(bottom=ft.BorderSide(1, ImportacionesTheme.BORDER)),
            ),
            
            # Formulario
            ft.Container(
                content=ft.Column([
                    # Sección 1: Información del movimiento
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.INFO, size=20),
                                ft.Text("Información del Movimiento", size=16, weight=ft.FontWeight.BOLD),
                            ], spacing=8),
                            ft.Divider(height=20),
                            
                            ft.ResponsiveRow([
                                ft.Column([self.ctrl_movement_number], col={"md": 4}),
                                ft.Column([self.ctrl_movement_type], col={"md": 4}),
                                ft.Column([self.ctrl_movement_date], col={"md": 4}),
                            ], spacing=16),
                            
                            ft.Container(height=16),
                            
                            ft.ResponsiveRow([
                                ft.Column([self.ctrl_warehouse], col={"md": 4}),
                                ft.Column([self.ctrl_source_warehouse], col={"md": 4}),
                                ft.Column([self.ctrl_status], col={"md": 4}),
                            ], spacing=16),
                            
                            ft.Container(height=16),
                            
                            ft.ResponsiveRow([
                                ft.Column([self.ctrl_reference], col={"md": 6}),
                            ], spacing=16),
                        ]),
                        padding=20,
                        bgcolor=ImportacionesTheme.BG_SECONDARY,
                        border_radius=12,
                        border=ft.border.all(1, ImportacionesTheme.BORDER),
                    ),
                    
                    ft.Container(height=24),
                    
                    # Sección 2: Items
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.LIST, size=20),
                                ft.Text("Productos a Recibir", size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(expand=True),
                                ft.Text(f"{len(self.items_movimiento)} items",
                                       color=ImportacionesTheme.TEXT_SECONDARY),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(height=20),
                            items_table,
                        ]),
                        padding=20,
                        bgcolor=ImportacionesTheme.BG_SECONDARY,
                        border_radius=12,
                        border=ft.border.all(1, ImportacionesTheme.BORDER),
                    ),
                    
                    ft.Container(height=24),
                    
                    # Sección 3: Notas
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.NOTES, size=20),
                                ft.Text("Observaciones", size=16, weight=ft.FontWeight.BOLD),
                            ], spacing=8),
                            ft.Divider(height=20),
                            self.ctrl_notes,
                        ]),
                        padding=20,
                        bgcolor=ImportacionesTheme.BG_SECONDARY,
                        border_radius=12,
                        border=ft.border.all(1, ImportacionesTheme.BORDER),
                    ),
                    
                    ft.Container(height=24),
                    
                    # Botones
                    ft.Row([
                        ft.ElevatedButton(
                            "Cancelar",
                            icon=ft.Icons.CANCEL,
                            on_click=lambda _: self.page.go(f"/ordenes/{self.po_id}"),
                        ),
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            "Guardar como Borrador",
                            icon=ft.Icons.SAVE,
                            on_click=lambda _: self._save_movement("draft"),
                            style=ft.ButtonStyle(
                                bgcolor=ImportacionesTheme.INFO,
                                color="white"
                            )
                        ),
                        ft.ElevatedButton(
                            "Confirmar y Actualizar Stock",
                            icon=ft.Icons.CHECK_CIRCLE,
                            on_click=lambda _: self._save_movement("completed"),
                            style=ft.ButtonStyle(
                                bgcolor=ImportacionesTheme.SUCCESS,
                                color="white"
                            )
                        ),
                    ], spacing=12),
                    
                    ft.Container(height=40),
                ], scroll=ft.ScrollMode.AUTO),
                padding=24,
                expand=True,
            ),
        ])
    
    def _build_items_table(self):
        """Construye tabla de items"""
        if not self.items_movimiento:
            return ft.Text("No hay items en la orden", color=ImportacionesTheme.TEXT_SECONDARY)
        
        rows = []
        for item in self.items_movimiento:
            qty_field = self.item_quantity_fields.get(item['po_item_id'])
            
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(item['product_name'][:50], size=13)),
                ft.DataCell(ft.Text(f"{item['cantidad_orden']:,.2f}", 
                                   color=ImportacionesTheme.TEXT_SECONDARY)),
                ft.DataCell(qty_field if qty_field else ft.Text(str(item['cantidad_recibida']))),
                ft.DataCell(ft.Text(format_currency(item['costo_unitario']),
                                   color=ImportacionesTheme.TEXT_SECONDARY)),
                ft.DataCell(ft.Text(format_currency(item['cantidad_recibida'] * item['costo_unitario']),
                                   weight=ft.FontWeight.BOLD)),
            ]))
        
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Producto")),
                ft.DataColumn(ft.Text("Ordenado"), numeric=True),
                ft.DataColumn(ft.Text("A Recibir"), numeric=True),
                ft.DataColumn(ft.Text("Costo Unit."), numeric=True),
                ft.DataColumn(ft.Text("Total"), numeric=True),
            ],
            rows=rows,
            heading_row_color=ImportacionesTheme.BG_PRIMARY,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
        )
    
    def _save_movement(self, status):
        """Guarda el movimiento"""
        
        # Validaciones
        if not self.ctrl_movement_number.value:
            self._show_snackbar("El número de movimiento es requerido", "error")
            return
        
        if not self.ctrl_warehouse.value:
            self._show_snackbar("Debe seleccionar un almacén destino", "error")
            return
        
        # Mostrar loading
        self._show_snackbar("Guardando...", "info")
        
        def save_background():
            try:
                warehouse_id = int(self.ctrl_warehouse.value)
                
                # 1. Insertar/Actualizar movimiento
                if self.modo_edicion:
                    query = """
                        UPDATE warehouse_movements 
                        SET movement_number = %s, movement_type = %s, movement_date = %s,
                            warehouse_id = %s, reference_document = %s, status = %s, notes = %s
                        WHERE id = %s
                    """
                    params = (
                        self.ctrl_movement_number.value,
                        self.ctrl_movement_type.value,
                        self.ctrl_movement_date.value,
                        warehouse_id,
                        self.ctrl_reference.value,
                        status,
                        self.ctrl_notes.value,
                        self.movimiento_id
                    )
                    self.db.execute_query(query, params, fetch=False)
                    
                    # Limpiar detalles anteriores
                    self.db.execute_query(
                        "DELETE FROM movement_details WHERE movement_id = %s",
                        (self.movimiento_id,), fetch=False
                    )
                else:
                    query = """
                        INSERT INTO warehouse_movements 
                        (movement_number, po_id, movement_type, movement_date,
                         warehouse_id, reference_document, status, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    params = (
                        self.ctrl_movement_number.value,
                        self.po_id,
                        self.ctrl_movement_type.value,
                        self.ctrl_movement_date.value,
                        warehouse_id,
                        self.ctrl_reference.value,
                        status,
                        self.ctrl_notes.value
                    )
                    self.movimiento_id = self.db.execute_query(query, params, fetch=False)
                
                if not self.movimiento_id:
                    raise Exception("No se pudo crear el movimiento")
                
                # 2. Insertar detalles y actualizar stock
                for item in self.items_movimiento:
                    cantidad = float(self.item_quantity_fields[item['po_item_id']].value or 0)
                    
                    if cantidad <= 0:
                        continue
                    
                    costo = item['costo_unitario']
                    total = cantidad * costo
                    
                    # Insertar detalle
                    det_query = """
                        INSERT INTO movement_details 
                        (movement_id, product_id, po_item_id, quantity, unit_cost, total_cost)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    self.db.execute_query(det_query, (
                        self.movimiento_id, item['product_id'], item['po_item_id'],
                        cantidad, costo, total
                    ), fetch=False)
                    
                    # Actualizar inventario si está confirmado/completado
                    if status in ['confirmed', 'completed']:
                        inv_query = """
                            INSERT INTO inventory (product_id, warehouse_id, quantity, unit_cost)
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE 
                                unit_cost = ((quantity * unit_cost) + (%s * %s)) / (quantity + %s),
                                quantity = quantity + %s,
                                last_movement_date = CURRENT_TIMESTAMP
                        """
                        self.db.execute_query(inv_query, (
                            item['product_id'], warehouse_id, cantidad, costo,
                            cantidad, costo, cantidad, cantidad
                        ), fetch=False)
                
                # 3. Actualizar estado de la orden
                if status == 'completed':
                    self.db.execute_query(
                        "UPDATE purchase_orders SET status = 'en_almacen' WHERE id = %s",
                        (self.po_id,), fetch=False
                    )
                
                # Commit si es necesario
                if hasattr(self.db.connection, 'commit'):
                    self.db.connection.commit()
                
                self._show_snackbar("✅ Movimiento guardado correctamente", "success")
                
                # Redirigir
                self.page.go("/inventario")
                
            except Exception as e:
                print(f"Error guardando: {e}")
                import traceback
                traceback.print_exc()
                
                if hasattr(self.db.connection, 'rollback'):
                    self.db.connection.rollback()
                
                mensaje = str(e)
                if "Duplicate" in mensaje:
                    mensaje = "El número de movimiento ya existe"
                
                self._show_snackbar(f"❌ Error: {mensaje}", "error")
        
        threading.Thread(target=save_background, daemon=True).start()
    
    def _show_snackbar(self, message, tipo="info"):
        colors = {
            "success": ImportacionesTheme.SUCCESS,
            "error": ImportacionesTheme.ERROR,
            "info": ImportacionesTheme.INFO,
        }
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="white"),
            bgcolor=colors.get(tipo, ImportacionesTheme.INFO),
        )
        self.page.snack_bar.open = True
        self.page.update()