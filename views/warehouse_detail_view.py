# views/warehouse_detail_view.py - Detalle de Almacén PROFESIONAL
import flet as ft
import threading
from datetime import datetime
from config_importaciones import ImportacionesTheme, format_currency, format_date

class WarehouseDetailView:
    def __init__(self, page: ft.Page, db, warehouse_id):
        self.page = page
        self.db = db
        self.warehouse_id = warehouse_id
        
        # Datos
        self.warehouse = None
        self.products = []
        self.movements = []
        self.stats = {
            "product_count": 0,
            "total_units": 0,
            "total_value": 0,
            "movements_count": 0,
            "last_movement": None
        }
        
        # Contenedor principal
        self.main_container = None
    
    def detail_view(self):
        """Vista principal con carga asíncrona"""
        
        # Contenedor de carga inicial
        self.main_container = ft.Container(
            content=ft.Column([
                ft.ProgressRing(width=50, height=50),
                ft.Container(height=16),
                ft.Text("Cargando información del almacén...", 
                       color=ImportacionesTheme.TEXT_SECONDARY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               alignment=ft.MainAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True,
        )
        
        # Cargar datos en background
        threading.Thread(target=self._load_all_data, daemon=True).start()
        
        return ft.Container(
            content=self.main_container,
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )
    
    def _load_all_data(self):
        """Carga todos los datos de forma independiente"""
        try:
            # ==========================================
            # QUERY 1: Datos del almacén
            # ==========================================
            self._load_warehouse_info()
            
            if not self.warehouse:
                self._show_not_found()
                return
            
            # ==========================================
            # QUERY 2: Estadísticas de stock
            # ==========================================
            self._load_stock_stats()
            
            # ==========================================
            # QUERY 3: Productos en stock
            # ==========================================
            self._load_products()
            
            # ==========================================
            # QUERY 4: Últimos movimientos
            # ==========================================
            self._load_movements()
            
            # ==========================================
            # Construir UI
            # ==========================================
            self._build_complete_ui()
            
            self.page.update()
            
        except Exception as e:
            print(f"❌ Error cargando detalle de almacén: {e}")
            import traceback
            traceback.print_exc()
            self._show_error(str(e))
    
    def _load_warehouse_info(self):
        """Query 1: Información básica del almacén"""
        query = """
            SELECT 
                id, code, name, address, manager_name, 
                notes, status, created_at
            FROM warehouses 
            WHERE id = %s
        """
        result = self.db.execute_query(query, (self.warehouse_id,))
        self.warehouse = result[0] if result else None
        
        if self.warehouse:
            print(f"✅ Almacén cargado: {self.warehouse['code']} - {self.warehouse['name']}")
    
    def _load_stock_stats(self):
        """Query 2: Estadísticas de stock"""
        query = """
            SELECT 
                COUNT(DISTINCT i.product_id) as product_count,
                COALESCE(SUM(i.quantity), 0) as total_units,
                COALESCE(SUM(i.quantity * i.unit_cost), 0) as total_value
            FROM inventory i
            WHERE i.warehouse_id = %s AND i.quantity > 0
        """
        result = self.db.execute_query(query, (self.warehouse_id,))
        
        if result and result[0]:
            self.stats["product_count"] = int(result[0]["product_count"] or 0)
            self.stats["total_units"] = float(result[0]["total_units"] or 0)
            self.stats["total_value"] = float(result[0]["total_value"] or 0)
        
        # Contar movimientos
        mov_query = """
            SELECT COUNT(*) as count, MAX(movement_date) as last_date
            FROM warehouse_movements 
            WHERE warehouse_id = %s
        """
        mov_result = self.db.execute_query(mov_query, (self.warehouse_id,))
        
        if mov_result and mov_result[0]:
            self.stats["movements_count"] = int(mov_result[0]["count"] or 0)
            self.stats["last_movement"] = mov_result[0]["last_date"]
        
        print(f"📊 Stats: {self.stats['product_count']} productos, {self.stats['total_units']} unidades, ${self.stats['total_value']}")
    
    def _load_products(self):
        """Query 3: Productos en stock (top 20 por valor)"""
        query = """
            SELECT 
                p.id as product_id,
                p.sku, 
                p.name,
                COALESCE(p.unit_measure, 'UND') as unit_measure,
                i.quantity,
                i.unit_cost,
                (i.quantity * i.unit_cost) as total_value,
                i.last_movement_date
            FROM inventory i
            INNER JOIN products p ON i.product_id = p.id
            WHERE i.warehouse_id = %s AND i.quantity > 0
            ORDER BY (i.quantity * i.unit_cost) DESC
            LIMIT 20
        """
        self.products = self.db.execute_query(query, (self.warehouse_id,)) or []
        print(f"📦 Productos cargados: {len(self.products)}")
    
    def _load_movements(self):
        """Query 4: Últimos 15 movimientos"""
        query = """
            SELECT 
                wm.id,
                wm.movement_number,
                wm.movement_type,
                wm.movement_date,
                wm.status,
                wm.reference_document,
                wm.notes,
                wm.warehouse_id,
                COALESCE(
                    (SELECT SUM(md.quantity) FROM movement_details md WHERE md.movement_id = wm.id), 
                    0
                ) as total_quantity,
                COALESCE(
                    (SELECT COUNT(*) FROM movement_details md WHERE md.movement_id = wm.id), 
                    0
                ) as items_count
            FROM warehouse_movements wm
            WHERE wm.warehouse_id = %s
            ORDER BY wm.movement_date DESC, wm.id DESC
            LIMIT 15
        """
        self.movements = self.db.execute_query(query, (self.warehouse_id,)) or []
        print(f"📋 Movimientos cargados: {len(self.movements)}")
    
    def _show_not_found(self):
        """Muestra mensaje de almacén no encontrado"""
        self.main_container.content = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ERROR_OUTLINE, size=80, color=ImportacionesTheme.ERROR),
                ft.Container(height=24),
                ft.Text("Almacén no encontrado", size=24, weight=ft.FontWeight.BOLD,
                       color=ImportacionesTheme.TEXT_PRIMARY),
                ft.Container(height=8),
                ft.Text(f"El almacén con ID {self.warehouse_id} no existe o fue eliminado.",
                       color=ImportacionesTheme.TEXT_SECONDARY),
                ft.Container(height=32),
                ft.Row([
                    ft.ElevatedButton(
                        "Ver Lista de Almacenes",
                        icon=ft.Icons.LIST,
                        on_click=lambda _: self.page.go("/almacenes"),
                        style=ft.ButtonStyle(
                            bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                            color="white"
                        )
                    ),
                    ft.ElevatedButton(
                        "Ir al Inventario",
                        icon=ft.Icons.INVENTORY,
                        on_click=lambda _: self.page.go("/inventario"),
                    ),
                ], spacing=16, alignment=ft.MainAxisAlignment.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               alignment=ft.MainAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True,
        )
        self.page.update()
    
    def _show_error(self, message):
        """Muestra mensaje de error"""
        self.main_container.content = ft.Column([
            ft.Icon(ft.Icons.ERROR, size=64, color=ImportacionesTheme.ERROR),
            ft.Container(height=16),
            ft.Text("Error al cargar", size=20, weight=ft.FontWeight.BOLD),
            ft.Text(message, color=ImportacionesTheme.TEXT_SECONDARY),
            ft.Container(height=24),
            ft.ElevatedButton("Volver", on_click=lambda _: self.page.go("/almacenes")),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
           alignment=ft.MainAxisAlignment.CENTER)
        self.page.update()
    
    def _build_complete_ui(self):
        """Construye la interfaz completa profesional"""
        w = self.warehouse
        
        # ==========================================
        # HEADER
        # ==========================================
        header = self._build_header()
        
        # ==========================================
        # LAYOUT PRINCIPAL (ResponsiveRow)
        # ==========================================
        # Izquierda: Panel de información (pequeño)
        # Derecha: Stock y estadísticas (grande)
        
        info_panel = self._build_info_panel()
        stats_panel = self._build_stats_panel()
        stock_section = self._build_stock_section()
        movements_timeline = self._build_movements_timeline()
        
        self.main_container.content = ft.Column([
            header,
            
            # Contenido con scroll
            ft.Container(
                content=ft.Column([
                    # Fila superior: Info + Stats
                    ft.ResponsiveRow([
                        # Panel izquierdo - Información del almacén
                        ft.Column([info_panel], col={"xs": 12, "md": 4, "lg": 3}),
                        
                        # Panel derecho - Estadísticas
                        ft.Column([stats_panel], col={"xs": 12, "md": 8, "lg": 9}),
                    ], spacing=24, run_spacing=24),
                    
                    ft.Container(height=24),
                    
                    # Fila inferior: Stock + Movimientos
                    ft.ResponsiveRow([
                        # Stock de productos
                        ft.Column([stock_section], col={"xs": 12, "lg": 7}),
                        
                        # Timeline de movimientos
                        ft.Column([movements_timeline], col={"xs": 12, "lg": 5}),
                    ], spacing=24, run_spacing=24),
                    
                    ft.Container(height=40),
                ], scroll=ft.ScrollMode.AUTO),
                padding=24,
                expand=True,
            ),
        ])
    
    def _build_header(self):
        """Construye el header con breadcrumb y acciones"""
        w = self.warehouse
        
        # Badge de estado
        status_color = ImportacionesTheme.SUCCESS if w['status'] == 'active' else ImportacionesTheme.TEXT_SECONDARY
        status_text = "ACTIVO" if w['status'] == 'active' else "INACTIVO"
        
        return ft.Container(
            content=ft.Row([
                # Info del almacén
                ft.Column([
                    # Breadcrumb
                    ft.Row([
                        ft.TextButton(
                            "Almacenes",
                            on_click=lambda _: self.page.go("/almacenes"),
                            style=ft.ButtonStyle(color=ImportacionesTheme.TEXT_SECONDARY)
                        ),
                        ft.Text("/", color=ImportacionesTheme.TEXT_SECONDARY),
                        ft.Text(w['code'], color=ImportacionesTheme.TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
                    ], spacing=4),
                    
                    # Título principal
                    ft.Row([
                        ft.Icon(ft.Icons.WAREHOUSE, size=32, color=ImportacionesTheme.STATUS_CONFIRMED),
                        ft.Column([
                            ft.Row([
                                ft.Text(f"{w['code']} - {w['name']}", size=24, weight=ft.FontWeight.BOLD,
                                       color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Container(
                                    content=ft.Text(status_text, size=11, color="white", weight=ft.FontWeight.BOLD),
                                    bgcolor=status_color,
                                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                    border_radius=12,
                                ),
                            ], spacing=12),
                            ft.Text(w.get('address') or "Sin dirección registrada",
                                   size=14, color=ImportacionesTheme.TEXT_SECONDARY),
                        ], spacing=4),
                    ], spacing=16),
                ]),
                
                # Botones de acción
                ft.Row([
                    ft.ElevatedButton(
                        "Nuevo Ingreso",
                        icon=ft.Icons.ADD_BOX,
                        on_click=lambda _: self.page.go(f"/almacen/ingreso?warehouse_id={self.warehouse_id}"),
                        style=ft.ButtonStyle(
                            bgcolor=ImportacionesTheme.SUCCESS,
                            color="white"
                        )
                    ),
                    ft.ElevatedButton(
                        "Transferir",
                        icon=ft.Icons.SWAP_HORIZ,
                        on_click=lambda _: self.page.go(f"/transferencia/nueva?source_warehouse={self.warehouse_id}"),
                        style=ft.ButtonStyle(
                            bgcolor=ImportacionesTheme.INFO,
                            color="white"
                        )
                    ),
                    ft.PopupMenuButton(
                        icon=ft.Icons.MORE_VERT,
                        items=[
                            ft.PopupMenuItem(
                                text="Editar Almacén",
                                icon=ft.Icons.EDIT,
                                on_click=lambda _: self._show_edit_dialog(),
                            ),
                            ft.PopupMenuItem(
                                text="Ver en Inventario General",
                                icon=ft.Icons.INVENTORY_2,
                                on_click=lambda _: self.page.go(f"/inventario?warehouse={self.warehouse_id}"),
                            ),
                            ft.PopupMenuItem(),  # Separador
                            ft.PopupMenuItem(
                                text="Exportar Stock",
                                icon=ft.Icons.DOWNLOAD,
                                on_click=lambda _: self._export_stock(),
                            ),
                        ],
                    ),
                ], spacing=12),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=24, vertical=20),
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border=ft.border.only(bottom=ft.BorderSide(1, ImportacionesTheme.BORDER)),
        )
    
    def _build_info_panel(self):
        """Panel lateral con información del almacén"""
        w = self.warehouse
        
        # Información detallada
        info_items = [
            ("Código", w['code'], ft.Icons.TAG),
            ("Nombre", w['name'], ft.Icons.BUSINESS),
            ("Dirección", w.get('address') or "No especificada", ft.Icons.LOCATION_ON),
            ("Responsable", w.get('manager_name') or "Sin asignar", ft.Icons.PERSON),
            ("Creado", format_date(w.get('created_at')) if w.get('created_at') else "N/A", ft.Icons.CALENDAR_TODAY),
        ]
        
        info_rows = []
        for label, value, icon in info_items:
            info_rows.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(icon, size=18, color=ImportacionesTheme.TEXT_SECONDARY),
                        ft.Column([
                            ft.Text(label, size=11, color=ImportacionesTheme.TEXT_SECONDARY),
                            ft.Text(str(value)[:30], size=13, weight=ft.FontWeight.W_500,
                                   color=ImportacionesTheme.TEXT_PRIMARY),
                        ], spacing=2, expand=True),
                    ], spacing=12),
                    padding=ft.padding.symmetric(vertical=8),
                    border=ft.border.only(bottom=ft.BorderSide(1, ImportacionesTheme.BORDER)),
                )
            )
        
        # Notas del almacén
        notas_section = ft.Container()
        if w.get('notes'):
            notas_section = ft.Container(
                content=ft.Column([
                    ft.Text("📝 Notas", size=12, weight=ft.FontWeight.BOLD,
                           color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Text(w['notes'], size=12, color=ImportacionesTheme.TEXT_PRIMARY),
                ], spacing=8),
                padding=ft.padding.only(top=16),
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                    ft.Text("Información del Local", size=16, weight=ft.FontWeight.BOLD,
                           color=ImportacionesTheme.TEXT_PRIMARY),
                ], spacing=8),
                ft.Divider(height=20),
                *info_rows,
                notas_section,
            ]),
            padding=20,
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
        )
    
    def _build_stats_panel(self):
        """Panel de estadísticas principales"""
        
        stats_grid = ft.ResponsiveRow(
            [
                # Cada tarjeta ahora usa la propiedad 'col'
                self._create_stat_card(
                    title="Productos en Stock",
                    value="5",
                    icon=ft.Icons.INVENTORY_2,
                    color=ImportacionesTheme.INFO,
                    col={"xs": 12, "sm": 6, "md": 4, "lg": 3} # Rejilla adaptable
                ),
                self._create_stat_card(
                    title="Unidades Totales",
                    value="9",
                    icon=ft.Icons.NUMBERS,
                    color=ImportacionesTheme.STATUS_CONFIRMED,
                    col={"xs": 12, "sm": 6, "md": 4, "lg": 3}
                ),
                self._create_stat_card(
                    title="Valor del Inventario",
                    value="S/ 13,344.08",
                    icon=ft.Icons.ATTACH_MONEY,
                    color=ImportacionesTheme.SUCCESS,
                    col={"xs": 12, "sm": 6, "md": 4, "lg": 3}
                ),
                self._create_stat_card(
                    title="Movimientos",
                    value="4",
                    icon=ft.Icons.SYNC_ALT,
                    color=ImportacionesTheme.WARNING,
                    col={"xs": 12, "sm": 6, "md": 4, "lg": 3}
                ),
            ],
            spacing=16,
            run_spacing=16, # Espacio vertical cuando las tarjetas se apilan
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ANALYTICS, size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                    ft.Text("Resumen del Almacén", size=16, weight=ft.FontWeight.BOLD,
                           color=ImportacionesTheme.TEXT_PRIMARY),
                ], spacing=8),
                ft.Divider(height=20),
                stats_grid,
            ]),
            padding=20,
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
            height=200,
        )
    
    def _create_stat_card(self, title, value, icon, color, subtitle=None,col=None):
        """Crea una tarjeta de estadística"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, size=20, color="white"),
                        bgcolor=color,
                        border_radius=8,
                        padding=8,
                    ),
                    ft.Column([
                        ft.Text(title, size=11, color=ImportacionesTheme.TEXT_SECONDARY),
                        ft.Text(value, size=20, weight=ft.FontWeight.BOLD,
                               color=ImportacionesTheme.TEXT_PRIMARY),
                    ], spacing=2, expand=True),
                ], spacing=12),
                ft.Text(subtitle, size=10, color=ImportacionesTheme.TEXT_SECONDARY) if subtitle else ft.Container(),
            ], spacing=4),
            padding=16,
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
            col=col,
            expand=1,
            height=100,
        )
    
    def _build_stock_section(self):
        """Sección de productos en stock"""
        
        # Header de la sección
        header = ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.INVENTORY_2, size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                ft.Text("Productos en Stock", size=16, weight=ft.FontWeight.BOLD,
                       color=ImportacionesTheme.TEXT_PRIMARY),
            ], spacing=8),
            ft.Text(f"Top {len(self.products)} por valor", size=12,
                   color=ImportacionesTheme.TEXT_SECONDARY),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # Contenido
        if not self.products:
            content = self._build_empty_stock_state()
        else:
            content = self._build_products_table()
        
        return ft.Container(
            content=ft.Column([
                header,
                ft.Divider(height=20),
                content,
            ]),
            padding=20,
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
        )
    
    def _build_empty_stock_state(self):
        """Estado vacío para stock"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.INVENTORY_2, size=56, color=ImportacionesTheme.TEXT_SECONDARY),
                ft.Container(height=16),
                ft.Text("Este almacén no tiene stock registrado", size=16,
                       color=ImportacionesTheme.TEXT_SECONDARY),
                ft.Text("Registre un ingreso para comenzar a controlar el inventario",
                       size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                ft.Container(height=20),
                ft.Row([
                    ft.ElevatedButton(
                        "Registrar Primer Ingreso",
                        icon=ft.Icons.ADD_BOX,
                        on_click=lambda _: self.page.go("/ordenes"),
                        style=ft.ButtonStyle(
                            bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                            color="white"
                        )
                    ),
                    ft.OutlinedButton(
                        "Transferir desde otro almacén",
                        icon=ft.Icons.SWAP_HORIZ,
                        on_click=lambda _: self.page.go(f"/transferencia/nueva?destination_warehouse={self.warehouse_id}"),
                    ),
                ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=40,
            alignment=ft.alignment.center,
        )
    
    def _build_products_table(self):
        """Tabla de productos en stock"""
        rows = []
        
        for p in self.products:
            quantity = float(p['quantity'] or 0)
            unit_cost = float(p['unit_cost'] or 0)
            total_value = float(p['total_value'] or 0)
            
            # Color según nivel de stock
            qty_color = ImportacionesTheme.ERROR if quantity < 10 else (
                ImportacionesTheme.WARNING if quantity < 50 else ImportacionesTheme.SUCCESS
            )
            
            rows.append(ft.DataRow(
                cells=[
                    ft.DataCell(
                        ft.Text(p['sku'], weight=ft.FontWeight.BOLD, size=12,
                               color=ImportacionesTheme.TEXT_PRIMARY)
                    ),
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(p['name'][:35], size=12),
                            width=180,
                        )
                    ),
                    ft.DataCell(
                        ft.Text(f"{quantity:,.2f}", color=qty_color, 
                               weight=ft.FontWeight.BOLD, size=12)
                    ),
                    ft.DataCell(
                        ft.Text(format_currency(unit_cost), size=12,
                               color=ImportacionesTheme.TEXT_SECONDARY)
                    ),
                    ft.DataCell(
                        ft.Text(format_currency(total_value), weight=ft.FontWeight.BOLD,
                               size=12, color=ImportacionesTheme.SUCCESS)
                    ),
                    ft.DataCell(
                        ft.IconButton(
                            icon=ft.Icons.HISTORY,
                            icon_size=16,
                            tooltip="Ver Kardex",
                            on_click=lambda e, pid=p['product_id']: self.page.go(f"/movimientos?product_id={pid}&warehouse_id={self.warehouse_id}"),
                        )
                    ),
                ],
            ))
        
        # Calcular total
        total_stock_value = sum(float(p['total_value'] or 0) for p in self.products)
        
        return ft.Column([
            ft.Container(
                content=ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("SKU", size=12, weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Producto", size=12, weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Cantidad", size=12, weight=ft.FontWeight.BOLD), numeric=True),
                        ft.DataColumn(ft.Text("Costo Unit.", size=12, weight=ft.FontWeight.BOLD), numeric=True),
                        ft.DataColumn(ft.Text("Valor", size=12, weight=ft.FontWeight.BOLD), numeric=True),
                        ft.DataColumn(ft.Text("", size=12)),
                    ],
                    rows=rows,
                    heading_row_color=ImportacionesTheme.BG_PRIMARY,
                    heading_row_height=40,
                    data_row_min_height=44,
                    border=ft.border.all(1, ImportacionesTheme.BORDER),
                    horizontal_lines=ft.border.BorderSide(1, ImportacionesTheme.BORDER),
                ),
                border_radius=8,
            ),
            
            ft.Container(height=12),
            
            # Total
            ft.Container(
                content=ft.Row([
                    ft.Text("VALOR TOTAL EN ESTE ALMACÉN:", 
                           weight=ft.FontWeight.BOLD, size=13),
                    ft.Text(format_currency(total_stock_value),
                           size=18, weight=ft.FontWeight.BOLD,
                           color=ImportacionesTheme.STATUS_CONFIRMED),
                ], alignment=ft.MainAxisAlignment.END, spacing=12),
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
                bgcolor=f"{ImportacionesTheme.STATUS_CONFIRMED}15",
                border_radius=8,
            ),
        ])
    
    def _build_movements_timeline(self):
        """Timeline de movimientos recientes"""
        
        header = ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.HISTORY, size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                ft.Text("Últimos Movimientos", size=16, weight=ft.FontWeight.BOLD,
                       color=ImportacionesTheme.TEXT_PRIMARY),
            ], spacing=8),
            ft.TextButton(
                "Ver todos",
                on_click=lambda _: self.page.go(f"/movimientos?warehouse_id={self.warehouse_id}"),
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # Contenido
        if not self.movements:
            content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.HISTORY, size=48, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Container(height=12),
                    ft.Text("Sin movimientos registrados", color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Text("Los ingresos y salidas aparecerán aquí", 
                           size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=40,
                alignment=ft.alignment.center,
            )
        else:
            content = ft.Column([
                self._create_movement_item(m) for m in self.movements
            ], spacing=8)
        
        return ft.Container(
            content=ft.Column([
                header,
                ft.Divider(height=20),
                content,
            ]),
            padding=20,
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
        )
    
    def _create_movement_item(self, movement):
        """Crea un item de la línea de tiempo"""
        
        # Configuración por tipo
        type_config = {
            'receipt': {
                'icon': ft.Icons.ADD_BOX,
                'color': ImportacionesTheme.SUCCESS,
                'label': 'Entrada',
                'bg': f"{ImportacionesTheme.SUCCESS}15"
            },
            'output': {
                'icon': ft.Icons.OUTPUT,
                'color': ImportacionesTheme.ERROR,
                'label': 'Salida',
                'bg': f"{ImportacionesTheme.ERROR}15"
            },
            'transfer': {
                'icon': ft.Icons.SWAP_HORIZ,
                'color': ImportacionesTheme.INFO,
                'label': 'Transferencia',
                'bg': f"{ImportacionesTheme.INFO}15"
            },
            'adjustment': {
                'icon': ft.Icons.TUNE,
                'color': ImportacionesTheme.WARNING,
                'label': 'Ajuste',
                'bg': f"{ImportacionesTheme.WARNING}15"
            },
        }
        
        config = type_config.get(movement['movement_type'], {
            'icon': ft.Icons.HELP,
            'color': ImportacionesTheme.TEXT_SECONDARY,
            'label': movement['movement_type'],
            'bg': ImportacionesTheme.BG_PRIMARY
        })
        
        # Estado badge
        status_colors = {
            'draft': ImportacionesTheme.TEXT_SECONDARY,
            'confirmed': ImportacionesTheme.INFO,
            'completed': ImportacionesTheme.SUCCESS,
            'cancelled': ImportacionesTheme.ERROR,
        }
        status_color = status_colors.get(movement['status'], ImportacionesTheme.TEXT_SECONDARY)
        
        # Formatear fecha
        mov_date = movement['movement_date']
        if mov_date:
            if isinstance(mov_date, str):
                date_str = mov_date[:10]
            else:
                date_str = mov_date.strftime("%d/%m/%Y")
        else:
            date_str = "N/A"
        
        return ft.Container(
            content=ft.Row([
                # Icono de tipo
                ft.Container(
                    content=ft.Icon(config['icon'], size=18, color="white"),
                    bgcolor=config['color'],
                    border_radius=20,
                    padding=8,
                ),
                
                # Info
                ft.Column([
                    ft.Row([
                        ft.Text(movement['movement_number'], size=13, weight=ft.FontWeight.BOLD,
                               color=ImportacionesTheme.TEXT_PRIMARY),
                        ft.Container(
                            content=ft.Text(config['label'], size=10, color=config['color']),
                            bgcolor=config['bg'],
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            border_radius=4,
                        ),
                    ], spacing=8),
                    ft.Row([
                        ft.Text(f"{movement['items_count']} items", size=11,
                               color=ImportacionesTheme.TEXT_SECONDARY),
                        ft.Text("•", color=ImportacionesTheme.TEXT_SECONDARY),
                        ft.Text(date_str, size=11, color=ImportacionesTheme.TEXT_SECONDARY),
                    ], spacing=4),
                ], spacing=4, expand=True),
                
                # Estado
                ft.Container(
                    content=ft.Text(movement['status'].upper(), size=9, color="white"),
                    bgcolor=status_color,
                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                    border_radius=10,
                ),
            ], spacing=12),
            padding=12,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
            border_radius=10,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
            on_click=lambda e, mid=movement['id']: self.page.go(f"/movimientos/{mid}"),
            ink=True,
        )
    
    def _show_edit_dialog(self):
        """Muestra diálogo para editar almacén"""
        w = self.warehouse
        
        code_field = ft.TextField(label="Código", value=w['code'], width=150)
        name_field = ft.TextField(label="Nombre", value=w['name'], expand=True)
        address_field = ft.TextField(label="Dirección", value=w.get('address') or "", expand=True)
        manager_field = ft.TextField(label="Responsable", value=w.get('manager_name') or "", width=200)
        notes_field = ft.TextField(label="Notas", value=w.get('notes') or "", 
                                   multiline=True, min_lines=2, max_lines=4)
        status_dropdown = ft.Dropdown(
            label="Estado",
            value=w['status'],
            width=150,
            options=[
                ft.dropdown.Option("active", "Activo"),
                ft.dropdown.Option("inactive", "Inactivo"),
            ],
        )
        
        def save_changes(e):
            try:
                query = """
                    UPDATE warehouses 
                    SET code = %s, name = %s, address = %s, 
                        manager_name = %s, status = %s, notes = %s
                    WHERE id = %s
                """
                self.db.execute_query(query, (
                    code_field.value, name_field.value, address_field.value,
                    manager_field.value, status_dropdown.value, notes_field.value,
                    self.warehouse_id
                ), fetch=False)
                
                self.page.close(dialog)
                self._show_snackbar("✅ Almacén actualizado correctamente", "success")
                
                # Recargar vista
                threading.Thread(target=self._load_all_data, daemon=True).start()
                
            except Exception as ex:
                self._show_snackbar(f"Error: {str(ex)}", "error")
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"Editar Almacén: {w['code']}"),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([code_field, name_field], spacing=16),
                    address_field,
                    ft.Row([manager_field, status_dropdown], spacing=16),
                    notes_field,
                ], spacing=16, tight=True),
                width=500,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton(
                    "Guardar Cambios",
                    on_click=save_changes,
                    style=ft.ButtonStyle(
                        bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                        color="white"
                    )
                ),
            ],
        )
        
        self.page.open(dialog)
    
    def _export_stock(self):
        """Exportar stock del almacén"""
        self._show_snackbar("Función de exportación en desarrollo...", "info")
    
    def _show_snackbar(self, message, tipo="info"):
        """Muestra mensaje snackbar"""
        colors = {
            "success": ImportacionesTheme.SUCCESS,
            "error": ImportacionesTheme.ERROR,
            "info": ImportacionesTheme.INFO,
            "warning": ImportacionesTheme.WARNING,
        }
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="white"),
            bgcolor=colors.get(tipo, ImportacionesTheme.INFO),
        )
        self.page.snack_bar.open = True
        self.page.update()