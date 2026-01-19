# views/ordenes_view.py - Gestión de Órdenes de Compra con BD real
import flet as ft
from datetime import datetime, timedelta
from config_importaciones import (
    ImportacionesTheme, ImportacionesConfig, 
    get_status_color, get_status_icon, format_currency, format_date
)
import threading
import pyodbc
import os
print([x for x in pyodbc.drivers() if 'Access' in x])

class OrdenesView:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.current_filter = {}
        self.orders = []
        
        # ========== PAGINACIÓN ==========
        self.current_page = 1
        self.items_per_page = 25  # Cargar solo 25 a la vez
        self.total_orders = 0
        self.total_pages = 1
        
        # ========== REFERENCIAS A CONTENEDORES (para actualizar sin recargar toda la vista) ==========
        self.table_container = None
        self.pagination_container = None
        self.count_text = None
        self.loading_overlay = None
        
        # ========== DEBOUNCE PARA BÚSQUEDA ==========
        self.search_timer = None
    
    def get_total_count(self):
        """Obtiene el conteo total de órdenes (para paginación)"""
        try:
            query = """
                SELECT COUNT(*) as total
                FROM purchase_orders po
                LEFT JOIN suppliers s ON po.supplier_id = s.id
                WHERE 1=1
            """
            params = []
            
            # Aplicar los mismos filtros
            if self.current_filter.get("search"):
                query += " AND (po.po_number LIKE %s OR s.business_name LIKE %s)"
                params.extend([f"%{self.current_filter['search']}%", 
                              f"%{self.current_filter['search']}%"])
            
            if self.current_filter.get("status"):
                query += " AND po.status = %s"
                params.append(self.current_filter["status"])
            
            if self.current_filter.get("date_range"):
                query = self._apply_date_filter(query, params)
            
            result = self.db.execute_query(query, tuple(params) if params else None)
            return result[0]["total"] if result else 0
            
        except Exception as e:
            print(f"Error obteniendo conteo: {e}")
            return 0
    
    def _apply_date_filter(self, query, params):
        """Aplica filtro de fecha a la consulta"""
        date_filter = self.current_filter["date_range"]
        today = datetime.now().date()
        
        if date_filter == "today":
            query += " AND DATE(po.order_date) = %s"
            params.append(today.strftime("%Y-%m-%d"))
        elif date_filter == "week":
            week_ago = today - timedelta(days=7)
            query += " AND po.order_date >= %s"
            params.append(week_ago.strftime("%Y-%m-%d"))
        elif date_filter == "month":
            month_ago = today - timedelta(days=30)
            query += " AND po.order_date >= %s"
            params.append(month_ago.strftime("%Y-%m-%d"))
        elif date_filter == "last_month":
            first_day_current = today.replace(day=1)
            last_day_previous = first_day_current - timedelta(days=1)
            first_day_previous = last_day_previous.replace(day=1)
            query += " AND po.order_date >= %s AND po.order_date <= %s"
            params.extend([
                first_day_previous.strftime("%Y-%m-%d"),
                last_day_previous.strftime("%Y-%m-%d")
            ])
        
        return query
    
    def load_orders(self):
        """Carga órdenes CON PAGINACIÓN"""
        try:
            # Primero obtener el total
            self.total_orders = self.get_total_count()
            self.total_pages = max(1, (self.total_orders + self.items_per_page - 1) // self.items_per_page)
            
            # Asegurar que la página actual es válida
            if self.current_page > self.total_pages:
                self.current_page = self.total_pages
            if self.current_page < 1:
                self.current_page = 1
            
            # Calcular OFFSET
            offset = (self.current_page - 1) * self.items_per_page
            
            query = """
                SELECT 
                    po.*, 
                    s.business_name as supplier_name,
                    ip.importacion_id -- Si es NULL, la orden es LOCAL
                FROM purchase_orders po
                LEFT JOIN suppliers s ON po.supplier_id = s.id
                LEFT JOIN importacion_pos ip ON po.id = ip.po_id -- Tabla conectora corregida
                WHERE 1=1
            """
            
            params = []
            
            # Aplicar filtros
            if self.current_filter.get("search"):
                query += " AND (po.po_number LIKE %s OR s.business_name LIKE %s)"
                params.extend([f"%{self.current_filter['search']}%", 
                              f"%{self.current_filter['search']}%"])
            
            if self.current_filter.get("status"):
                query += " AND po.status = %s"
                params.append(self.current_filter["status"])
            
            if self.current_filter.get("date_range"):
                query = self._apply_date_filter(query, params)
            
            # ORDENAR Y PAGINAR
            query += f" ORDER BY po.order_date DESC, po.id DESC LIMIT {self.items_per_page} OFFSET {offset}"
            
            result = self.db.execute_query(query, tuple(params) if params else None)
            self.orders = result or []
            
        except Exception as e:
            print(f"Error cargando órdenes: {e}")
            self.orders = []
    
    def load_orders_async(self, show_loading=True):
        """Carga órdenes en segundo plano sin bloquear UI"""
        
        if show_loading and self.loading_overlay:
            self.loading_overlay.visible = True
            self.page.update()
        
        def background_load():
            try:
                self.load_orders()
                
                # Actualizar UI en el hilo principal
                if self.table_container:
                    self.table_container.content = self._create_table_content()
                
                if self.pagination_container:
                    self.pagination_container.content = self._create_pagination_controls()
                
                if self.count_text:
                    start = (self.current_page - 1) * self.items_per_page + 1
                    end = min(self.current_page * self.items_per_page, self.total_orders)
                    self.count_text.value = f"Mostrando {start}-{end} de {self.total_orders} órdenes"
                
                if self.loading_overlay:
                    self.loading_overlay.visible = False
                
                self.page.update()
                
            except Exception as e:
                print(f"Error en carga asíncrona: {e}")
                if self.loading_overlay:
                    self.loading_overlay.visible = False
                self.page.update()
        
        threading.Thread(target=background_load, daemon=True).start()

    def list_view(self):
        """Vista de lista de órdenes de compra - OPTIMIZADA"""
        self.load_orders()
        
        search_bar = ft.TextField(
            hint_text="Buscar por número, proveedor...",
            prefix_icon="search",
            expand=True,
            border_color=ImportacionesTheme.BORDER,
            on_change=self.on_search_change_debounced,  # <- CON DEBOUNCE
            text_size=14
        )
        
        status_filter = ft.Dropdown(
            label="Estado",
            options=[ft.dropdown.Option("", "Todos")] + [
                ft.dropdown.Option(status["code"], status["name"]) 
                for status in self.get_status_options()
            ],
            width=150,
            border_color=ImportacionesTheme.BORDER,
            on_change=self.on_status_filter_change,
            text_size=14
        )
        
        date_filter = ft.Dropdown(
            label="Fecha",
            options=[
                ft.dropdown.Option("", "Todas"),
                ft.dropdown.Option("today", "Hoy"),
                ft.dropdown.Option("week", "Esta semana"),
                ft.dropdown.Option("month", "Este mes"),
                ft.dropdown.Option("last_month", "Mes anterior"),
            ],
            width=150,
            border_color=ImportacionesTheme.BORDER,
            on_change=self.on_date_filter_change,
            text_size=14
        )
        
        new_order_btn = ft.ElevatedButton(
            "Nueva Orden",
            icon="add",
            on_click=lambda e: self.page.go("/ordenes/nueva"),
            style=ft.ButtonStyle(
                bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                color="white"
            )
        )
        
        # ========== CONTADOR DE RESULTADOS ==========
        start = (self.current_page - 1) * self.items_per_page + 1
        end = min(self.current_page * self.items_per_page, self.total_orders)
        self.count_text = ft.Text(
            f"Mostrando {start}-{end} de {self.total_orders} órdenes",
            color=ImportacionesTheme.TEXT_SECONDARY
        )
        
        # ========== CONTENEDOR DE TABLA (se actualiza sin recargar toda la vista) ==========
        self.table_container = ft.Container(
            content=self._create_table_content(),
            padding=ft.padding.symmetric(horizontal=24),
        )
        
        # ========== PAGINACIÓN ==========
        self.pagination_container = ft.Container(
            content=self._create_pagination_controls(),
            padding=ft.padding.symmetric(horizontal=24, vertical=16),
        )
        
        # ========== OVERLAY DE CARGA ==========
        self.loading_overlay = ft.Container(
            content=ft.Row([
                ft.ProgressRing(width=20, height=20, stroke_width=2),
                ft.Text("  Cargando...", color=ImportacionesTheme.TEXT_SECONDARY)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor="#80000000",
            visible=False,
            alignment=ft.alignment.center,
        )
        
        # ========== LAYOUT PRINCIPAL ==========
        return ft.Container(
            content=ft.Stack([
                ft.Column([
                    # Header
                    self.create_header("Órdenes de Compra", "Gestión de órdenes de compra internacionales"),
                    
                    # Barra de herramientas
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                search_bar,
                                status_filter,
                                date_filter,
                                ft.IconButton(
                                    icon="refresh",
                                    tooltip="Actualizar",
                                    icon_color=ImportacionesTheme.TEXT_SECONDARY,
                                    on_click=lambda e: self.load_orders_async()
                                ),
                                ft.ElevatedButton(
                                    "access 2003",
                                    icon="sync",
                                    tooltip="Sincronizar con Ditec (Access)",
                                    on_click=lambda e: self.sincronizar_con_access(),
                                    style=ft.ButtonStyle(
                                        bgcolor=ImportacionesTheme.INFO,
                                        color="white"
                                    ),
                                )
                            ], spacing=12),
                            ft.Container(height=12),
                            ft.Row([
                                new_order_btn,
                                self.count_text,
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ]),
                        padding=ft.padding.symmetric(horizontal=24, vertical=16),
                        bgcolor=ImportacionesTheme.BG_SECONDARY,
                        border_radius=12,
                        border=ft.border.all(1, ImportacionesTheme.BORDER),
                    ),
                    
                    ft.Container(height=16),
                    
                    # Tabla de órdenes
                    self.table_container,
                    
                    # Paginación
                    self.pagination_container,
                    
                    ft.Container(height=40),
                ], scroll=ft.ScrollMode.AUTO),
                
                # Overlay de carga
                self.loading_overlay,
            ]),
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )
    
    def _create_table_content(self):
        """Crea el contenido de la tabla (separado para poder actualizarlo)"""
        if not self.orders:
            return self.create_empty_state()
        
        return ft.Container(
            content=ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Número", weight=ft.FontWeight.BOLD, size=13)),
                    ft.DataColumn(ft.Text("Proveedor", weight=ft.FontWeight.BOLD, size=13)),
                    ft.DataColumn(ft.Text("Fecha", weight=ft.FontWeight.BOLD, size=13)),
                    ft.DataColumn(ft.Text("Estado", weight=ft.FontWeight.BOLD, size=13)),
                    ft.DataColumn(ft.Text("Total FOB", weight=ft.FontWeight.BOLD, size=13)),
                    ft.DataColumn(ft.Text("", weight=ft.FontWeight.BOLD, size=13)),
                ],
                rows=[self._create_order_row(order) for order in self.orders],
                heading_row_color=ImportacionesTheme.BG_SECONDARY,
                heading_row_height=44,
                data_row_min_height=48,
                horizontal_lines=ft.border.BorderSide(1, ImportacionesTheme.BORDER),
                column_spacing=16,
            ),
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
            bgcolor=ImportacionesTheme.BG_SECONDARY,
        )
    
    def _create_order_row(self, order):
        """Crea una fila de la tabla"""
        status_color = get_status_color(order["status"])
        status_icon = get_status_icon(order["status"])
        
        btn_almacen_local = ft.Container()

        total_fob = order.get("total_fob", 0) or 0
        if order.get("currency_id") == 1:
            total_display = f"$ {total_fob:,.2f}"
        else:
            total_display = f"S/ {total_fob:,.2f}"

        if order.get("importacion_id") is None:
            if order["status"] == "confirmada":
                btn_almacen_local = ft.IconButton(
                    icon=ft.Icons.INVENTORY_2,
                    icon_size=16,
                    icon_color=ImportacionesTheme.SUCCESS,
                    tooltip="Ingreso Directo a Almacén (Compra Local)",
                    on_click=lambda _: self.page.go(f"/almacen/ingreso/{order['id']}")
                )
            elif order["status"] in ["en_almacen", "completed"]:
                btn_almacen_local = ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=ImportacionesTheme.SUCCESS)
            
        return ft.DataRow(
            cells=[
                ft.DataCell(
                    ft.Text(order["po_number"], 
                           color=ImportacionesTheme.TEXT_PRIMARY,
                           weight=ft.FontWeight.BOLD,
                           size=13)
                ),
                ft.DataCell(
                    ft.Text(order.get("supplier_name") or "N/A", 
                           color=ImportacionesTheme.TEXT_SECONDARY,
                           size=12,
                           max_lines=1,
                           overflow=ft.TextOverflow.ELLIPSIS)
                ),
                ft.DataCell(
                    ft.Text(format_date(order["order_date"]), 
                           color=ImportacionesTheme.TEXT_SECONDARY,
                           size=12)
                ),
                ft.DataCell(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(status_icon, size=12, color=status_color),
                            ft.Text(
                                order["status"].replace("_", " ").title(), 
                                size=11,
                                color=status_color
                            )
                        ], spacing=4),
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        bgcolor=f"{status_color}15",
                        border_radius=6,
                    )
                ),
                ft.DataCell(
                    ft.Text(total_display, 
                           color=ImportacionesTheme.TEXT_PRIMARY,
                           weight=ft.FontWeight.BOLD,
                           size=12)
                ),
                ft.DataCell(
                    ft.Row([
                        ft.IconButton(
                            icon="visibility",
                            icon_size=16,
                            icon_color=ImportacionesTheme.TEXT_SECONDARY,
                            tooltip="Ver detalle",
                            on_click=lambda e, o=order: self.view_order_detail(o["id"])
                        ),
                        
                        ft.IconButton(
                            icon="edit",
                            icon_size=16,
                            icon_color=ImportacionesTheme.TEXT_SECONDARY,
                            tooltip="Editar",
                            on_click=lambda e, o=order: self.edit_order(o["id"])
                        ),
                        btn_almacen_local
                    ], spacing=0)
                ),
            ],
            on_select_changed=lambda e, o=order: self.view_order_detail(o["id"])
        )
    
    def _create_pagination_controls(self):
        """Crea los controles de paginación"""
        
        # Botones de página
        page_buttons = []
        
        # Siempre mostrar primera página
        if self.total_pages > 0:
            page_buttons.append(
                ft.TextButton(
                    "1",
                    on_click=lambda e: self.go_to_page(1),
                    style=ft.ButtonStyle(
                        bgcolor=ImportacionesTheme.STATUS_CONFIRMED if self.current_page == 1 else "transparent",
                        color="white" if self.current_page == 1 else ImportacionesTheme.TEXT_PRIMARY
                    )
                )
            )
        
        # Puntos suspensivos si hay gap
        if self.current_page > 3:
            page_buttons.append(ft.Text("...", color=ImportacionesTheme.TEXT_SECONDARY))
        
        # Páginas alrededor de la actual
        for p in range(max(2, self.current_page - 1), min(self.total_pages, self.current_page + 2)):
            page_buttons.append(
                ft.TextButton(
                    str(p),
                    on_click=lambda e, pg=p: self.go_to_page(pg),
                    style=ft.ButtonStyle(
                        bgcolor=ImportacionesTheme.STATUS_CONFIRMED if self.current_page == p else "transparent",
                        color="white" if self.current_page == p else ImportacionesTheme.TEXT_PRIMARY
                    )
                )
            )
        
        # Puntos suspensivos finales
        if self.current_page < self.total_pages - 2:
            page_buttons.append(ft.Text("...", color=ImportacionesTheme.TEXT_SECONDARY))
        
        # Última página
        if self.total_pages > 1:
            page_buttons.append(
                ft.TextButton(
                    str(self.total_pages),
                    on_click=lambda e: self.go_to_page(self.total_pages),
                    style=ft.ButtonStyle(
                        bgcolor=ImportacionesTheme.STATUS_CONFIRMED if self.current_page == self.total_pages else "transparent",
                        color="white" if self.current_page == self.total_pages else ImportacionesTheme.TEXT_PRIMARY
                    )
                )
            )
        
        return ft.Row([
            ft.IconButton(
                icon="chevron_left",
                icon_color=ImportacionesTheme.TEXT_SECONDARY if self.current_page > 1 else ImportacionesTheme.BORDER,
                disabled=self.current_page <= 1,
                on_click=lambda e: self.go_to_page(self.current_page - 1)
            ),
            ft.Row(page_buttons, spacing=4),
            ft.IconButton(
                icon="chevron_right",
                icon_color=ImportacionesTheme.TEXT_SECONDARY if self.current_page < self.total_pages else ImportacionesTheme.BORDER,
                disabled=self.current_page >= self.total_pages,
                on_click=lambda e: self.go_to_page(self.current_page + 1)
            ),
            ft.Container(width=20),
            ft.Text(f"Página {self.current_page} de {self.total_pages}", 
                   color=ImportacionesTheme.TEXT_SECONDARY, size=12),
        ], alignment=ft.MainAxisAlignment.CENTER)
    

    def go_to_page(self, page_num):
        """Navega a una página específica"""
        if page_num < 1 or page_num > self.total_pages:
            return
        self.current_page = page_num
        self.load_orders_async()
    
    # ========== DEBOUNCE PARA BÚSQUEDA ==========
    def on_search_change_debounced(self, e):
        """Búsqueda con debounce de 300ms"""
        # Cancelar timer anterior si existe
        if self.search_timer:
            self.search_timer.cancel()
        
        # Crear nuevo timer
        def do_search():
            self.current_filter["search"] = e.control.value
            self.current_page = 1  # Volver a página 1
            self.load_orders_async()
        
        self.search_timer = threading.Timer(0.3, do_search)
        self.search_timer.start()
    
    def on_status_filter_change(self, e):
        """Manejador de cambio en filtro de estado"""
        val = e.control.value
        self.current_filter["status"] = val if val and val != "" else None
        self.current_page = 1
        self.load_orders_async()
    
    def on_date_filter_change(self, e):
        """Manejador de cambio en filtro de fecha"""
        self.current_filter["date_range"] = e.control.value if e.control.value else None
        self.current_page = 1
        self.load_orders_async()
    
    def refresh_list(self, e=None):
        """Actualiza la lista de órdenes"""
        self.current_page = 1
        self.load_orders_async()




    def create_order_menu_items(self, order):
        """Crea los items del menú contextual de una orden"""
        
        items = []
        
        # Cambiar estado (solo si no está completada o cancelada)
        if order["status"] not in ["completada", "cancelada"]:
            items.append(
                ft.PopupMenuItem(
                    text="Cambiar estado",
                    icon="swap_vert",
                    on_click=lambda e, o=order: self.show_status_dialog(o)
                )
            )
        
        items.append(ft.PopupMenuItem())  # Separador
        
        # Duplicar orden
        items.append(
            ft.PopupMenuItem(
                text="Duplicar orden",
                icon="content_copy",
                on_click=lambda e, o=order: self.duplicate_order(o)
            )
        )
        
        # Cancelar o reactivar
        if order["status"] != "cancelada":
            items.append(
                ft.PopupMenuItem(
                    text="Cancelar orden",
                    icon="cancel",
                    on_click=lambda e, o=order: self.cancel_order(o)
                )
            )
        else:
            items.append(
                ft.PopupMenuItem(
                    text="Reactivar orden",
                    icon="refresh",
                    on_click=lambda e, o=order: self.reactivate_order(o)
                )
            )
        
        items.append(ft.PopupMenuItem())  # Separador
        
        # Eliminar (solo borradores)
        if order["status"] == "borrador":
            items.append(
                ft.PopupMenuItem(
                    text="Eliminar orden",
                    icon="delete",
                    on_click=lambda e, o=order: self.delete_order(o)
                )
            )
        
        return items
    
    def create_empty_state(self):
        """Crea estado vacío cuando no hay órdenes"""
        return ft.Container(
            content=ft.Column([
                ft.Container(height=60),
                ft.Icon("shopping_cart", size=48, color=ImportacionesTheme.TEXT_SECONDARY),
                ft.Container(height=16),
                ft.Text("No hay órdenes de compra", 
                       size=18, 
                       weight=ft.FontWeight.BOLD,
                       color=ImportacionesTheme.TEXT_PRIMARY),
                ft.Container(height=8),
                ft.Text("Crea tu primera orden o ajusta los filtros", 
                       color=ImportacionesTheme.TEXT_SECONDARY),
                ft.Container(height=24),
                ft.ElevatedButton(
                    "Crear primera orden",
                    icon="add",
                    on_click=lambda e: self.page.go("/ordenes/nueva"),
                    style=ft.ButtonStyle(
                        bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                        color="white"
                    )
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=40,
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
                           size=22, 
                           weight=ft.FontWeight.BOLD,
                           color=ImportacionesTheme.TEXT_PRIMARY),
                    ft.Text(subtitle, 
                           size=13,
                           color=ImportacionesTheme.TEXT_SECONDARY) if subtitle else ft.Container(),
                ], spacing=2),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=24, vertical=16),
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border=ft.border.only(bottom=ft.BorderSide(1, ImportacionesTheme.BORDER)),
        )
    def sincronizar_con_access(self):
        """Sincroniza con base de datos Access - en background"""
        
        # Mostrar mensaje de que está sincronizando
        self.show_snackbar("🔄 Sincronizando con Ditec...", "info")
        
        def sync_background():
            """Esta función corre en un hilo separado (no bloquea la UI)"""
            directorio_actual = os.path.dirname(os.path.abspath(__file__))
            ruta_access = os.path.join(directorio_actual, "db_bancos", "db_bancos.mdb")

            try:
                driver = '{Microsoft Access Driver (*.mdb, *.accdb)}'
                conn = pyodbc.connect(f'DRIVER={driver};DBQ={ruta_access};')
                cursor = conn.cursor()

                # ============================================================
                # --- PASO 1: PRODUCTOS ---
                # ============================================================
                cursor.execute("SELECT F3CODPRO, F5NOMPRO, F5PARTARA, UNIDAD FROM IF3ORDEN")
                productos_procesados = set()
                
                for prod in cursor.fetchall():
                    sku_clean = str(prod.F3CODPRO).strip()[:50] if prod.F3CODPRO else "SIN_SKU"
                    if sku_clean in productos_procesados or sku_clean == "SIN_SKU": 
                        continue
                    
                    query_prod = """
                        INSERT INTO products (sku, name, hs_code, status, unit_measure)
                        VALUES (%s, %s, %s, 'active', %s)
                        ON DUPLICATE KEY UPDATE name=VALUES(name), unit_measure=VALUES(unit_measure)
                    """
                    self.db.execute_query(
                        query_prod, 
                        (sku_clean, str(prod.F5NOMPRO)[:200], str(prod.F5PARTARA)[:12], str(prod.UNIDAD)[:20]), 
                        fetch=False
                    )
                    productos_procesados.add(sku_clean)
                
                print(f"✅ {len(productos_procesados)} productos procesados")

                # ============================================================
                # --- PASO 2: CABECERAS DE ÓRDENES ---
                # ============================================================
                cursor.execute("SELECT TOP 100 F4NUMORD, F4CODPRV, F4FECEMI, F4MONTO, F4TIPCAM FROM IF4ORDEN ORDER BY F4FECEMI DESC")
                ordenes = cursor.fetchall()
                ordenes_procesadas = 0

                for ord in ordenes:
                    query_po = """
                        INSERT INTO purchase_orders (po_number, supplier_id, order_date, total_fob, status, incoterm, currency_id, exchange_rate)
                        VALUES (%s, 1, %s, %s, 'confirmada', 'FOB', 1, %s)
                        ON DUPLICATE KEY UPDATE total_fob = VALUES(total_fob)
                    """
                    self.db.execute_query(
                        query_po, 
                        (ord.F4NUMORD, ord.F4FECEMI, ord.F4MONTO, ord.F4TIPCAM), 
                        fetch=False
                    )
                    
                    # Obtener ID para los items
                    res_po = self.db.execute_query(
                        "SELECT id FROM purchase_orders WHERE po_number = %s", 
                        (ord.F4NUMORD,)
                    )
                    if not res_po: 
                        continue
                        
                    po_id_mysql = res_po[0]['id']

                    # ============================================================
                    # --- PASO 3: ITEMS DE ESTA ORDEN ---
                    # ============================================================
                    cursor.execute(
                        f"SELECT F3CODPRO, F3CANPRO, F3PRECOS, F3TOTAL, UNIDAD FROM IF3ORDEN WHERE F4NUMORD = '{ord.F4NUMORD}'"
                    )
                    items = cursor.fetchall()

                    for itm in items:
                        sku_itm = str(itm.F3CODPRO).strip()[:50]
                        res_p = self.db.execute_query(
                            "SELECT id FROM products WHERE sku = %s", 
                            (sku_itm,)
                        )
                        
                        if res_p:
                            query_itm = """
                                INSERT INTO purchase_order_items (po_id, product_id, quantity, unit_price, total_cost, unit_measure)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE 
                                    quantity = VALUES(quantity), 
                                    unit_price = VALUES(unit_price),
                                    total_cost = VALUES(total_cost)
                            """
                            self.db.execute_query(
                                query_itm, 
                                (
                                    po_id_mysql, 
                                    res_p[0]['id'], 
                                    itm.F3CANPRO, 
                                    itm.F3PRECOS, 
                                    itm.F3TOTAL, 
                                    str(itm.UNIDAD)[:20]
                                ), 
                                fetch=False
                            )
                    
                    ordenes_procesadas += 1

                print(f"✅ {ordenes_procesadas} órdenes procesadas")

                # ============================================================
                # --- CERRAR CONEXIÓN ---
                # ============================================================
                cursor.close()
                conn.close()
                
                # ============================================================
                # --- RECARGAR DATOS Y MOSTRAR ÉXITO ---
                # ============================================================
                self.load_orders_async(show_loading=False)
                self.show_snackbar(f"✅ Sincronización exitosa: {ordenes_procesadas} órdenes", "success")
                
            except Exception as e:
                print(f"❌ Error en sincronización: {e}")
                import traceback
                traceback.print_exc()
                self.show_snackbar(f"❌ Error: {str(e)}", "error")
        
        # ============================================================
        # INICIAR EN HILO SEPARADO (no bloquea la UI)
        # ============================================================
        threading.Thread(target=sync_background, daemon=True).start()
        
    def get_status_options(self):
        """Obtiene opciones de estado para el filtro"""
        return [
            {"code": "borrador", "name": "Borrador"},
            {"code": "confirmada", "name": "Confirmada"},
            {"code": "en_transito", "name": "En Tránsito"},
            {"code": "en_aduana", "name": "En Aduana"},
            {"code": "prorrateado", "name": "Prorrateado"},
            {"code": "en_almacen", "name": "En Almacén"},
            {"code": "completada", "name": "Completada"},
            {"code": "cancelada", "name": "Cancelada"},
        ]
    
    def view_order_detail(self, order_id):
        """Ver detalle de una orden"""
        self.page.go(f"/ordenes/{order_id}")
    
    def edit_order(self, order_id):
        """Editar una orden"""
        self.page.go(f"/ordenes/{order_id}/editar")
    

    def show_snackbar(self, message: str, tipo: str = "info"):
        """Muestra un mensaje snackbar"""
        colors = {
            "success": ImportacionesTheme.SUCCESS,
            "error": ImportacionesTheme.ERROR,
            "warning": "#F59E0B",
            "info": ImportacionesTheme.STATUS_CONFIRMED
        }
        
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="white"),
            bgcolor=colors.get(tipo, ImportacionesTheme.STATUS_CONFIRMED)
        )
        self.page.snack_bar.open = True
        self.page.update()




    def on_search_change(self, e):
        """Manejador de cambio en búsqueda"""
        self.current_filter["search"] = e.control.value
        self.load_orders()
        self.page.go("/ordenes")  # Recargar vista
    
    def on_status_filter_change(self, e):
        """Manejador de cambio en filtro de estado"""
        self.current_filter["status"] = e.control.value if e.control.value else None
        self.load_orders()
        self.page.go("/ordenes")  # Recargar vista
    
    def on_date_filter_change(self, e):
        """Manejador de cambio en filtro de fecha"""
        self.current_filter["date_range"] = e.control.value if e.control.value else None
        self.load_orders()
        self.page.go("/ordenes")  # Recargar vista
    
    def refresh_list(self, e=None):
        """Actualiza la lista de órdenes"""
        self.load_orders()
        self.page.go("/ordenes")
    
    
    def duplicate_order(self, order):
        """Duplica una orden existente"""
        try:
            # Implementar lógica de duplicación
            print(f"Duplicando orden {order['id']}")
            # Mostrar mensaje de éxito
            self.show_snackbar(f"Orden {order['po_number']} duplicada", "success")
            self.refresh_list()
        except Exception as e:
            print(f"Error duplicando orden: {e}")
            self.show_snackbar("Error duplicando orden", "error")
    
    def cancel_order(self, order):
        """Cancela una orden"""
        try:
            # Actualizar estado en BD
            query = "UPDATE purchase_orders SET status = 'cancelada' WHERE id = %s"
            self.db.execute_query(query, (order["id"],), fetch=False)
            
            self.show_snackbar(f"Orden {order['po_number']} cancelada", "success")
            self.refresh_list()
        except Exception as e:
            print(f"Error cancelando orden: {e}")
            self.show_snackbar("Error cancelando orden", "error")
    
    def reactivate_order(self, order):
        """Reactivar una orden cancelada"""
        try:
            # Reactivar como borrador
            query = "UPDATE purchase_orders SET status = 'borrador' WHERE id = %s"
            self.db.execute_query(query, (order["id"],), fetch=False)
            
            self.show_snackbar(f"Orden {order['po_number']} reactivada", "success")
            self.refresh_list()
        except Exception as e:
            print(f"Error reactivando orden: {e}")
            self.show_snackbar("Error reactivando orden", "error")
    
    def delete_order(self, order):
        """Elimina una orden (solo borradores)"""
        def confirm_delete(e):
            try:
                # Eliminar items primero
                delete_items = "DELETE FROM purchase_order_items WHERE po_id = %s"
                self.db.execute_query(delete_items, (order["id"],), fetch=False)
                
                # Eliminar orden
                delete_order = "DELETE FROM purchase_orders WHERE id = %s"
                self.db.execute_query(delete_order, (order["id"],), fetch=False)
                
                self.page.close(dialog)
                self.show_snackbar(f"Orden {order['po_number']} eliminada", "success")
                self.refresh_list()
            except Exception as e:
                print(f"Error eliminando orden: {e}")
                self.show_snackbar("Error eliminando orden", "error")
        
        # Mostrar diálogo de confirmación
        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar eliminación"),
            content=ft.Text(f"¿Está seguro de eliminar la orden {order['po_number']}?\nEsta acción no se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dialog)),
                ft.TextButton("Eliminar", on_click=confirm_delete, style=ft.ButtonStyle(color=ImportacionesTheme.ERROR)),
            ]
        )
        
        self.page.open(dialog)


    