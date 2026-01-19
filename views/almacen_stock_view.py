# views/almacen_stock_view.py - Vista de Inventario con DIAGNÓSTICO
import flet as ft
import threading
from config_importaciones import ImportacionesTheme, format_currency

class AlmacenStockView:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        
        # Datos
        self.stock_data = []
        self.warehouses = []
        self.total_inventario = 0
        
        # Diagnóstico
        self.diagnostic_info = {
            "warehouses_count": 0,
            "products_count": 0,
            "inventory_count": 0,
            "error": None
        }
        
        # Filtros
        self.filtro_almacen = "all"
        self.filtro_busqueda = ""
        
        # Contenedores para actualización dinámica
        self.table_container = None
        self.stats_container = None
        self.warehouse_dropdown = None
        self.loading_overlay = None
        self.diagnostic_container = None

    def stock_view(self):
        """Vista principal de inventario"""
        
        # Contenedor de carga inicial
        self.loading_overlay = ft.Container(
            content=ft.Column([
                ft.ProgressRing(width=50, height=50),
                ft.Container(height=16),
                ft.Text("Cargando inventario...", color=ImportacionesTheme.TEXT_SECONDARY)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               alignment=ft.MainAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True,
            visible=True,
        )
        
        # Contenedor de estadísticas
        self.stats_container = ft.Container(
            content=ft.Row([
                self._create_stat_card("Total Productos", "0", ft.Icons.INVENTORY_2, ImportacionesTheme.INFO),
                self._create_stat_card("Valor Total", "$0.00", ft.Icons.ATTACH_MONEY, ImportacionesTheme.SUCCESS),
                self._create_stat_card("Almacenes", "0", ft.Icons.WAREHOUSE, ImportacionesTheme.STATUS_CONFIRMED),
                self._create_stat_card("Items Bajo Stock", "0", ft.Icons.WARNING, ImportacionesTheme.WARNING),
            ], spacing=16, wrap=True),
            visible=False,
        )
        
        # Contenedor de diagnóstico (nuevo)
        self.diagnostic_container = ft.Container(
            content=None,
            visible=False,
        )
        
        # Dropdown de almacenes
        self.warehouse_dropdown = ft.Dropdown(
            label="Almacén",
            width=250,
            value="all",
            options=[ft.dropdown.Option("all", "Todos los almacenes")],
            border_color=ImportacionesTheme.BORDER,
            on_change=self._on_warehouse_filter_change,
        )
        
        # Campo de búsqueda
        self.search_field = ft.TextField(
            hint_text="Buscar por SKU o Nombre...",
            expand=True,
            prefix_icon=ft.Icons.SEARCH,
            border_color=ImportacionesTheme.BORDER,
            on_change=self._on_search_change,
        )
        
        # Contenedor de tabla
        self.table_container = ft.Container(
            content=ft.Text("Cargando..."),
            visible=False,
        )
        
        # Iniciar carga asíncrona
        threading.Thread(target=self._load_data_async, daemon=True).start()
        
        return ft.Container(
            content=ft.Stack([
                ft.Column([
                    # Header
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.INVENTORY_2, size=28, color=ImportacionesTheme.TEXT_PRIMARY),
                                    ft.Text("Inventario Valorizado", size=26, weight=ft.FontWeight.BOLD,
                                           color=ImportacionesTheme.TEXT_PRIMARY),
                                ], spacing=12),
                                ft.Text("Control de stock por almacén con costo promedio ponderado",
                                       size=14, color=ImportacionesTheme.TEXT_SECONDARY),
                            ]),
                            ft.Row([
                                ft.ElevatedButton(
                                    "Gestionar Almacenes",
                                    icon=ft.Icons.WAREHOUSE,
                                    on_click=lambda _: self.page.go("/almacenes"),
                                    style=ft.ButtonStyle(
                                        bgcolor=ImportacionesTheme.BG_SECONDARY,
                                        color=ImportacionesTheme.TEXT_PRIMARY
                                    )
                                ),
                                ft.ElevatedButton(
                                    "Nueva Transferencia",
                                    icon=ft.Icons.SWAP_HORIZ,
                                    on_click=lambda _: self.page.go("/transferencia/nueva"),
                                    style=ft.ButtonStyle(
                                        bgcolor=ImportacionesTheme.INFO,
                                        color="white"
                                    )
                                ),
                                ft.ElevatedButton(
                                    "Nueva Salida",
                                    icon=ft.Icons.OUTPUT,
                                    on_click=lambda _: self.page.go("/salida/nueva"),
                                    style=ft.ButtonStyle(
                                        bgcolor=ImportacionesTheme.WARNING,
                                        color="white"
                                    )
                                ),
                            ], spacing=12),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=ft.padding.symmetric(horizontal=24, vertical=20),
                        bgcolor=ImportacionesTheme.BG_SECONDARY,
                        border=ft.border.only(bottom=ft.BorderSide(1, ImportacionesTheme.BORDER)),
                    ),
                    
                    # Contenido principal
                    ft.Container(
                        content=ft.Column([
                            # Diagnóstico (solo visible cuando hay problemas)
                            self.diagnostic_container,
                            
                            # Estadísticas
                            self.stats_container,
                            
                            ft.Container(height=24),
                            
                            # Filtros
                            ft.Container(
                                content=ft.Row([
                                    self.search_field,
                                    self.warehouse_dropdown,
                                    ft.IconButton(
                                        icon=ft.Icons.REFRESH,
                                        tooltip="Actualizar",
                                        on_click=lambda _: self._refresh_data(),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DOWNLOAD,
                                        tooltip="Exportar a Excel",
                                        on_click=self._export_to_excel,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.BUG_REPORT,
                                        tooltip="Ver Diagnóstico",
                                        on_click=lambda _: self._show_diagnostic_dialog(),
                                    ),
                                ], spacing=16),
                                padding=16,
                                bgcolor=ImportacionesTheme.BG_SECONDARY,
                                border_radius=12,
                                border=ft.border.all(1, ImportacionesTheme.BORDER),
                            ),
                            
                            ft.Container(height=16),
                            
                            # Tabla
                            self.table_container,
                            
                        ], scroll=ft.ScrollMode.AUTO),
                        padding=24,
                        expand=True,
                    ),
                ]),
                
                # Overlay de carga
                self.loading_overlay,
            ]),
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )
    
    def _create_stat_card(self, title, value, icon, color):
        """Crea una tarjeta de estadística"""
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, size=24, color="white"),
                    bgcolor=color,
                    border_radius=8,
                    padding=12,
                ),
                ft.Column([
                    ft.Text(title, size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Text(str(value), size=20, weight=ft.FontWeight.BOLD, 
                           color=ImportacionesTheme.TEXT_PRIMARY),
                ], spacing=2),
            ], spacing=16),
            padding=16,
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
            expand=1,
        )
    
    def _run_diagnostics(self):
        """Ejecuta diagnóstico de las tablas"""
        try:
            # Contar almacenes
            result = self.db.execute_query("SELECT COUNT(*) as count FROM warehouses WHERE status = 'active'")
            self.diagnostic_info["warehouses_count"] = result[0]['count'] if result else 0
            
            # Contar productos
            result = self.db.execute_query("SELECT COUNT(*) as count FROM products WHERE status = 'active'")
            self.diagnostic_info["products_count"] = result[0]['count'] if result else 0
            
            # Contar registros de inventario
            result = self.db.execute_query("SELECT COUNT(*) as count FROM inventory WHERE quantity > 0")
            self.diagnostic_info["inventory_count"] = result[0]['count'] if result else 0
            
            # Ver registros de inventario (sin importar cantidad)
            result = self.db.execute_query("SELECT COUNT(*) as count FROM inventory")
            self.diagnostic_info["inventory_total"] = result[0]['count'] if result else 0
            
            # Verificar si hay movimientos
            result = self.db.execute_query("SELECT COUNT(*) as count FROM warehouse_movements")
            self.diagnostic_info["movements_count"] = result[0]['count'] if result else 0
            
            print(f"📊 DIAGNÓSTICO:")
            print(f"   - Almacenes activos: {self.diagnostic_info['warehouses_count']}")
            print(f"   - Productos activos: {self.diagnostic_info['products_count']}")
            print(f"   - Registros inventario (qty>0): {self.diagnostic_info['inventory_count']}")
            print(f"   - Registros inventario (total): {self.diagnostic_info['inventory_total']}")
            print(f"   - Movimientos: {self.diagnostic_info['movements_count']}")
            
        except Exception as e:
            self.diagnostic_info["error"] = str(e)
            print(f"❌ Error en diagnóstico: {e}")
    
    def _load_data_async(self):
        """Carga todos los datos en segundo plano"""
        try:
            # 0. Ejecutar diagnóstico primero
            self._run_diagnostics()
            
            # 1. Cargar almacenes
            self._load_warehouses()
            
            # 2. Cargar stock
            self._load_stock()
            
            # 3. Verificar si hay datos
            if not self.stock_data:
                self._show_empty_state_with_options()
            else:
                # 3. Actualizar UI
                self._update_stats()
                self._update_table()
            
            # 4. Ocultar loading
            self.loading_overlay.visible = False
            self.stats_container.visible = True
            self.table_container.visible = True
            
            self.page.update()
            
        except Exception as e:
            print(f"Error cargando datos: {e}")
            import traceback
            traceback.print_exc()
            
            self.loading_overlay.content = ft.Column([
                ft.Icon(ft.Icons.ERROR, size=50, color=ImportacionesTheme.ERROR),
                ft.Container(height=16),
                ft.Text(f"Error: {str(e)}", color=ImportacionesTheme.ERROR),
                ft.Container(height=16),
                ft.ElevatedButton(
                    "Ver Diagnóstico",
                    on_click=lambda _: self._show_diagnostic_dialog(),
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            self.page.update()
    
    def _load_warehouses(self):
        """Carga lista de almacenes"""
        query = "SELECT id, code, name FROM warehouses WHERE status = 'active' ORDER BY name"
        result = self.db.execute_query(query)
        self.warehouses = result or []
        
        print(f"📦 Almacenes cargados: {len(self.warehouses)}")
        
        # Actualizar dropdown
        options = [ft.dropdown.Option("all", "Todos los almacenes")]
        for w in self.warehouses:
            options.append(ft.dropdown.Option(str(w['id']), f"{w['code']} - {w['name']}"))
        
        self.warehouse_dropdown.options = options
    
    def _load_stock(self):
        """Carga datos de stock"""
        
        # Query simplificada para debug
        query = """
            SELECT 
                p.id as product_id,
                p.sku, 
                p.name as producto, 
                COALESCE(p.unit_measure, 'UND') as unit_measure,
                i.warehouse_id,
                COALESCE(w.code, 'N/A') as warehouse_code,
                COALESCE(w.name, 'Sin Almacén') as warehouse_name, 
                i.quantity, 
                COALESCE(i.unit_cost, 0) as unit_cost,
                (i.quantity * COALESCE(i.unit_cost, 0)) as total_value,
                i.last_movement_date
            FROM inventory i
            INNER JOIN products p ON i.product_id = p.id
            LEFT JOIN warehouses w ON i.warehouse_id = w.id 
            WHERE i.quantity > 0
        """
        
        params = []
        
        # Filtro de almacén
        if self.filtro_almacen and self.filtro_almacen != "all":
            query += " AND i.warehouse_id = %s"
            params.append(int(self.filtro_almacen))
        
        # Filtro de búsqueda
        if self.filtro_busqueda:
            query += " AND (p.sku LIKE %s OR p.name LIKE %s)"
            params.extend([f"%{self.filtro_busqueda}%", f"%{self.filtro_busqueda}%"])
        
        query += " ORDER BY p.name"
        
        print(f"🔍 Ejecutando query de stock...")
        result = self.db.execute_query(query, tuple(params) if params else None)
        self.stock_data = result or []
        
        print(f"📊 Registros de stock encontrados: {len(self.stock_data)}")
        
        # Calcular total
        self.total_inventario = sum(float(item['total_value'] or 0) for item in self.stock_data)
    
    def _show_empty_state_with_options(self):
        """Muestra estado vacío con opciones para poblar datos"""
        
        diag = self.diagnostic_info
        
        # Determinar el problema
        problems = []
        solutions = []
        
        if diag['warehouses_count'] == 0:
            problems.append("❌ No hay almacenes registrados")
            solutions.append(("Crear Almacén", self._create_default_warehouse))
        
        if diag['products_count'] == 0:
            problems.append("❌ No hay productos registrados")
            solutions.append(("Ir a Productos", lambda _: self.page.go("/productos")))
        
        if diag['inventory_count'] == 0 and diag['products_count'] > 0:
            problems.append("❌ No hay stock registrado en inventario")
            if diag['warehouses_count'] > 0:
                solutions.append(("Crear Datos de Prueba", self._create_sample_inventory))
            solutions.append(("Registrar Ingreso", lambda _: self.page.go("/ordenes")))
        
        # Construir UI de diagnóstico
        problem_items = [ft.Text(p, size=14, color=ImportacionesTheme.ERROR) for p in problems]
        
        solution_buttons = [
            ft.ElevatedButton(
                text,
                on_click=action,
                style=ft.ButtonStyle(
                    bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                    color="white"
                )
            )
            for text, action in solutions
        ]
        
        self.table_container.content = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.INVENTORY_2, size=64, color=ImportacionesTheme.TEXT_SECONDARY),
                ft.Container(height=20),
                ft.Text("No hay stock registrado", size=22, weight=ft.FontWeight.BOLD,
                       color=ImportacionesTheme.TEXT_PRIMARY),
                ft.Container(height=16),
                
                # Diagnóstico
                ft.Container(
                    content=ft.Column([
                        ft.Text("📊 Diagnóstico del Sistema:", size=16, weight=ft.FontWeight.BOLD),
                        ft.Container(height=8),
                        ft.Text(f"• Almacenes activos: {diag['warehouses_count']}", size=14),
                        ft.Text(f"• Productos activos: {diag['products_count']}", size=14),
                        ft.Text(f"• Registros de inventario: {diag['inventory_count']}", size=14),
                        ft.Text(f"• Movimientos registrados: {diag.get('movements_count', 0)}", size=14),
                        ft.Container(height=12),
                        *problem_items,
                    ]),
                    padding=20,
                    bgcolor=ImportacionesTheme.BG_SECONDARY,
                    border_radius=12,
                    border=ft.border.all(1, ImportacionesTheme.BORDER),
                    width=400,
                ),
                
                ft.Container(height=24),
                
                # Soluciones
                ft.Text("Acciones sugeridas:", size=14, color=ImportacionesTheme.TEXT_SECONDARY),
                ft.Container(height=8),
                ft.Row(solution_buttons, spacing=12, wrap=True, 
                      alignment=ft.MainAxisAlignment.CENTER),
                
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=60,
            alignment=ft.alignment.center,
        )
    
    def _create_default_warehouse(self, e=None):
        """Crea un almacén por defecto"""
        try:
            # Verificar si ya existe
            check = self.db.execute_query("SELECT id FROM warehouses WHERE code = 'ALM-01'")
            if check:
                self._show_snackbar("El almacén ALM-01 ya existe", "info")
                return
            
            query = """
                INSERT INTO warehouses (code, name, address, status) 
                VALUES ('ALM-01', 'Almacén Principal', 'Dirección por definir', 'active')
            """
            self.db.execute_query(query, fetch=False)
            
            self._show_snackbar("✅ Almacén 'ALM-01' creado correctamente", "success")
            self._refresh_data()
            
        except Exception as ex:
            self._show_snackbar(f"Error: {str(ex)}", "error")
    
    def _create_sample_inventory(self, e=None):
        """Crea datos de prueba en inventario"""
        try:
            # Obtener primer almacén
            warehouses = self.db.execute_query(
                "SELECT id FROM warehouses WHERE status = 'active' LIMIT 1"
            )
            if not warehouses:
                self._show_snackbar("Primero debe crear un almacén", "error")
                return
            
            warehouse_id = warehouses[0]['id']
            
            # Obtener productos
            products = self.db.execute_query(
                "SELECT id, name FROM products WHERE status = 'active' LIMIT 5"
            )
            if not products:
                self._show_snackbar("No hay productos para agregar al inventario", "error")
                return
            
            # Insertar inventario de prueba
            count = 0
            for prod in products:
                try:
                    query = """
                        INSERT INTO inventory (product_id, warehouse_id, quantity, unit_cost)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                            quantity = quantity + VALUES(quantity)
                    """
                    import random
                    cantidad = random.randint(10, 100)
                    costo = round(random.uniform(10, 500), 2)
                    
                    self.db.execute_query(query, (
                        prod['id'], warehouse_id, cantidad, costo
                    ), fetch=False)
                    count += 1
                    print(f"  ✓ {prod['name']}: {cantidad} unidades a ${costo}")
                except Exception as item_error:
                    print(f"  ✗ Error con producto {prod['id']}: {item_error}")
            
            self._show_snackbar(f"✅ {count} productos agregados al inventario", "success")
            self._refresh_data()
            
        except Exception as ex:
            print(f"Error creando inventario de prueba: {ex}")
            import traceback
            traceback.print_exc()
            self._show_snackbar(f"Error: {str(ex)}", "error")
    
    def _show_diagnostic_dialog(self):
        """Muestra diálogo con información de diagnóstico"""
        diag = self.diagnostic_info
        
        # Ejecutar consultas adicionales para más info
        try:
            # Ver algunos registros de inventario
            inv_sample = self.db.execute_query(
                "SELECT i.*, p.sku FROM inventory i LEFT JOIN products p ON i.product_id = p.id LIMIT 5"
            ) or []
            
            # Ver movimientos recientes
            mov_sample = self.db.execute_query(
                "SELECT id, movement_number, movement_type, status FROM warehouse_movements ORDER BY id DESC LIMIT 5"
            ) or []
        except:
            inv_sample = []
            mov_sample = []
        
        content = ft.Column([
            ft.Text("📊 Estado del Sistema", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            ft.Row([
                ft.Text("Almacenes activos:", width=200),
                ft.Text(str(diag.get('warehouses_count', 0)), weight=ft.FontWeight.BOLD),
            ]),
            ft.Row([
                ft.Text("Productos activos:", width=200),
                ft.Text(str(diag.get('products_count', 0)), weight=ft.FontWeight.BOLD),
            ]),
            ft.Row([
                ft.Text("Registros inventory (qty>0):", width=200),
                ft.Text(str(diag.get('inventory_count', 0)), weight=ft.FontWeight.BOLD),
            ]),
            ft.Row([
                ft.Text("Registros inventory (total):", width=200),
                ft.Text(str(diag.get('inventory_total', 0)), weight=ft.FontWeight.BOLD),
            ]),
            ft.Row([
                ft.Text("Movimientos registrados:", width=200),
                ft.Text(str(diag.get('movements_count', 0)), weight=ft.FontWeight.BOLD),
            ]),
            
            ft.Divider(),
            ft.Text("📋 Muestra de Inventario:", weight=ft.FontWeight.BOLD),
            ft.Text(
                "\n".join([f"  - {r.get('sku', 'N/A')}: {r.get('quantity', 0)} uds @ ${r.get('unit_cost', 0)}" 
                          for r in inv_sample]) or "  (vacío)",
                size=12
            ),
            
            ft.Divider(),
            ft.Text("📋 Últimos Movimientos:", weight=ft.FontWeight.BOLD),
            ft.Text(
                "\n".join([f"  - {r.get('movement_number', 'N/A')}: {r.get('movement_type', '')} ({r.get('status', '')})" 
                          for r in mov_sample]) or "  (ninguno)",
                size=12
            ),
            
        ], spacing=8, tight=True)
        
        dialog = ft.AlertDialog(
            title=ft.Text("Diagnóstico de Inventario"),
            content=ft.Container(content=content, width=450, height=400),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda _: self.page.close(dialog)),
                ft.ElevatedButton(
                    "Crear Datos de Prueba",
                    on_click=lambda _: [self.page.close(dialog), self._create_sample_inventory()],
                    style=ft.ButtonStyle(bgcolor=ImportacionesTheme.STATUS_CONFIRMED, color="white")
                ),
            ],
        )
        
        self.page.open(dialog)
    
    def _update_stats(self):
        """Actualiza las estadísticas"""
        total_productos = len(set(item['product_id'] for item in self.stock_data))
        total_almacenes = len(self.warehouses)
        
        # Contar items con bajo stock (menos de 10 unidades)
        bajo_stock = sum(1 for item in self.stock_data if float(item['quantity']) < 10)
        self.stats_container.height = 100
        self.stats_container.content = ft.Row([
            self._create_stat_card("Total Productos", str(total_productos), 
                                  ft.Icons.INVENTORY_2, ImportacionesTheme.INFO),
            self._create_stat_card("Valor Total", format_currency(self.total_inventario), 
                                  ft.Icons.ATTACH_MONEY, ImportacionesTheme.SUCCESS),
            self._create_stat_card("Almacenes Activos", str(total_almacenes), 
                                  ft.Icons.WAREHOUSE, ImportacionesTheme.STATUS_CONFIRMED),
            self._create_stat_card("Bajo Stock (<10)", str(bajo_stock), 
                                  ft.Icons.WARNING, ImportacionesTheme.WARNING),
        ], spacing=16, wrap=False)
    
    def _update_table(self):
        """Actualiza la tabla de stock"""
        if not self.stock_data:
            self._show_empty_state_with_options()
            return
        
        rows = []
        for item in self.stock_data:
            quantity = float(item['quantity'] or 0)
            unit_cost = float(item['unit_cost'] or 0)
            total_value = float(item['total_value'] or 0)
            
            # Color de cantidad según nivel
            qty_color = ImportacionesTheme.ERROR if quantity < 10 else (
                ImportacionesTheme.WARNING if quantity < 50 else ImportacionesTheme.SUCCESS
            )
            
            rows.append(ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(item['sku'] or 'N/A', weight=ft.FontWeight.BOLD,
                                       color=ImportacionesTheme.TEXT_PRIMARY)),
                    ft.DataCell(ft.Container(
                        content=ft.Text((item['producto'] or 'Sin nombre')[:40], size=13),
                        width=200,
                    )),
                    ft.DataCell(ft.Container(
                        content=ft.Text(f"{item['warehouse_code']}", size=12,
                                       color=ImportacionesTheme.INFO),
                        bgcolor=f"{ImportacionesTheme.INFO}15",
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=4,
                    )),
                    ft.DataCell(ft.Text(f"{quantity:,.2f} {item['unit_measure'] or 'UND'}",
                                       color=qty_color, weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(format_currency(unit_cost),
                                       color=ImportacionesTheme.TEXT_SECONDARY)),
                    ft.DataCell(ft.Text(format_currency(total_value),
                                       weight=ft.FontWeight.BOLD,
                                       color=ImportacionesTheme.STATUS_CONFIRMED)),
                    ft.DataCell(ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.VISIBILITY,
                            icon_size=18,
                            tooltip="Ver movimientos",
                            on_click=lambda e, p=item['product_id']: self._view_product_movements(p),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SWAP_HORIZ,
                            icon_size=18,
                            tooltip="Transferir",
                            on_click=lambda e, p=item: self._transfer_product(p),
                        ),
                    ], spacing=0)),
                ],
            ))
        
        # Tabla con resumen
        self.table_container.content = ft.Column([
            ft.Container(
                content=ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("SKU", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Producto", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Almacén", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Existencia", weight=ft.FontWeight.BOLD), numeric=True),
                        ft.DataColumn(ft.Text("Costo Unit. (CPP)", weight=ft.FontWeight.BOLD), numeric=True),
                        ft.DataColumn(ft.Text("Valor Total", weight=ft.FontWeight.BOLD), numeric=True),
                        ft.DataColumn(ft.Text("", weight=ft.FontWeight.BOLD)),
                    ],
                    rows=rows,
                    heading_row_color=ImportacionesTheme.BG_SECONDARY,
                    heading_row_height=48,
                    data_row_min_height=52,
                    border=ft.border.all(1, ImportacionesTheme.BORDER),
                    horizontal_lines=ft.border.BorderSide(1, ImportacionesTheme.BORDER),
                ),
                border_radius=12,
                bgcolor=ImportacionesTheme.BG_SECONDARY,
            ),
            
            ft.Container(height=20),
            
            # Resumen total
            ft.Container(
                content=ft.Row([
                    ft.Text(f"Mostrando {len(self.stock_data)} registros", 
                           color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Container(expand=True),
                    ft.Text("VALOR TOTAL DEL INVENTARIO:", 
                           size=16, weight=ft.FontWeight.BOLD,
                           color=ImportacionesTheme.TEXT_PRIMARY),
                    ft.Text(format_currency(self.total_inventario),
                           size=20, weight=ft.FontWeight.BOLD,
                           color=ImportacionesTheme.STATUS_CONFIRMED),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=20,
                bgcolor=f"{ImportacionesTheme.STATUS_CONFIRMED}15",
                border_radius=12,
                border=ft.border.all(2, ImportacionesTheme.STATUS_CONFIRMED),
            ),
        ])
    
    def _on_warehouse_filter_change(self, e):
        """Filtro por almacén"""
        self.filtro_almacen = e.control.value
        self._refresh_data()
    
    def _on_search_change(self, e):
        """Filtro por búsqueda (con debounce)"""
        self.filtro_busqueda = e.control.value
        if hasattr(self, '_search_timer'):
            self._search_timer.cancel()
        
        self._search_timer = threading.Timer(0.3, self._refresh_data)
        self._search_timer.start()
    
    def _refresh_data(self):
        """Recarga los datos"""
        self.loading_overlay.visible = True
        self.page.update()
        
        threading.Thread(target=self._load_data_async, daemon=True).start()
    
    def _view_product_movements(self, product_id):
        """Ver movimientos de un producto"""
        self.page.go(f"/movimientos")
    
    def _transfer_product(self, item):
        """Iniciar transferencia de producto"""
        self.page.go(f"/movimientos/transferencias")
    
    def _export_to_excel(self, e):
        """Exportar a Excel"""
        self._show_snackbar("Función de exportación en desarrollo...", "info")
    
    def _show_snackbar(self, message, tipo="info"):
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