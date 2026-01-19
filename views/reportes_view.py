# views/reportes_view.py
import os
import flet as ft
from datetime import datetime, timedelta
from config_importaciones import (
    ImportacionesTheme, ImportacionesConfig,
    format_currency, format_date, get_status_color, get_status_icon
)
from reports.sunat_kardex_pdf import SunatKardexReport
class ReportesView:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.report_data = {}
        self.cargar_datos()
        
        self._inicializar_campos_kardex()
        self._cargar_productos_dropdown()
    

    def _inicializar_campos_kardex(self):
        """Inicializa los controles del Kardex para que existan desde el inicio"""
        self.mes_field = ft.Dropdown(
            label="Mes",
            width=150,
            options=[ft.dropdown.Option(str(i), datetime(2024, i, 1).strftime('%B').title()) for i in range(1, 13)],
            value=str(datetime.now().month)
        )
        self.anio_field = ft.TextField(
            label="Año", value=str(datetime.now().year), width=100
        )
        self.producto_field = ft.Dropdown(
            label="Producto (Opcional)",
            hint_text="Todos los productos",
            expand=True,
            # IMPORTANTE: El key debe ser "" para indicar "Todos"
            options=[ft.dropdown.Option("", "--- TODOS LOS PRODUCTOS ---")],
            value="" 
        )
    def cargar_datos(self):
        """Carga datos para los reportes"""
        # Estadísticas generales
        self.report_data = self.obtener_estadisticas()
        
        # Datos para gráficos
        self.report_data['importaciones_mes'] = self.obtener_importaciones_por_mes()
        self.report_data['gastos_por_tipo'] = self.obtener_gastos_por_tipo()
        self.report_data['top_productos'] = self.obtener_top_productos()
        self.report_data['estado_ordenes'] = self.obtener_estado_ordenes()
    
    def obtener_estadisticas(self):
        """Obtiene estadísticas generales"""
        stats = {
            'total_importaciones': 0,
            'total_valor': 0,
            'promedio_tiempo': 0,
            'gasto_promedio': 0,
            'ordenes_activas': 0,
            'ordenes_completadas': 0
        }
        
        try:
            # Total de importaciones
            query = "SELECT COUNT(*) as total FROM purchase_orders"
            result = self.db.execute_query(query)
            if result:
                stats['total_importaciones'] = result[0]['total']
            
            # Valor total de importaciones
            query = "SELECT COALESCE(SUM(total_import_cost), 0) as total FROM purchase_orders WHERE status = 'completada'"
            result = self.db.execute_query(query)
            if result:
                stats['total_valor'] = float(result[0]['total'] or 0)
            
            # Órdenes activas
            query = "SELECT COUNT(*) as total FROM purchase_orders WHERE status NOT IN ('completada', 'cancelada')"
            result = self.db.execute_query(query)
            if result:
                stats['ordenes_activas'] = result[0]['total']
            
            # Órdenes completadas
            query = "SELECT COUNT(*) as total FROM purchase_orders WHERE status = 'completada'"
            result = self.db.execute_query(query)
            if result:
                stats['ordenes_completadas'] = result[0]['total']
            
            # Tiempo promedio de importación
            query = """
                SELECT AVG(DATEDIFF(updated_at, order_date)) as promedio 
                FROM purchase_orders 
                WHERE status = 'completada' 
                AND updated_at > order_date
            """
            result = self.db.execute_query(query)
            if result and result[0]['promedio']:
                stats['promedio_tiempo'] = int(result[0]['promedio'])
            
            # Gasto promedio por importación
            query = """
                SELECT AVG(total_import_cost) as promedio 
                FROM purchase_orders 
                WHERE status = 'completada' 
                AND total_import_cost > 0
            """
            result = self.db.execute_query(query)
            if result and result[0]['promedio']:
                stats['gasto_promedio'] = float(result[0]['promedio'])
                
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
        
        return stats
    
    def obtener_importaciones_por_mes(self):
        """Obtiene importaciones por mes para el gráfico"""
        query = """
            SELECT 
                DATE_FORMAT(order_date, '%Y-%m') as mes,
                COUNT(*) as cantidad,
                COALESCE(SUM(total_import_cost), 0) as valor_total
            FROM purchase_orders 
            WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(order_date, '%Y-%m')
            ORDER BY mes
        """
        result = self.db.execute_query(query)
        return result or []
    
    def obtener_gastos_por_tipo(self):
        """Obtiene distribución de gastos por tipo"""
        query = """
            SELECT 
                etu.nombre_ui as tipo_gasto,
                etu.color_ui as color,
                COALESCE(SUM(ie.amount_pen), 0) as total
            FROM import_expenses ie
            LEFT JOIN expense_types_ui etu ON ie.expense_type = etu.tipo_gasto
            WHERE ie.status = 'paid'
            GROUP BY ie.expense_type, etu.nombre_ui, etu.color_ui
            ORDER BY total DESC
            LIMIT 8
        """
        result = self.db.execute_query(query)
        return result or []
    
    def obtener_top_productos(self):
        """Obtiene los productos más importados"""
        query = """
            SELECT 
                p.sku,
                p.name,
                COUNT(DISTINCT poi.po_id) as importaciones,
                SUM(poi.quantity) as cantidad_total,
                AVG(poi.total_cost / poi.quantity) as costo_promedio
            FROM purchase_order_items poi
            LEFT JOIN products p ON poi.product_id = p.id
            LEFT JOIN purchase_orders po ON poi.po_id = po.id
            WHERE po.status = 'completada'
            GROUP BY p.id, p.sku, p.name
            ORDER BY cantidad_total DESC
            LIMIT 10
        """
        result = self.db.execute_query(query)
        return result or []
    
    def obtener_estado_ordenes(self):
        """Obtiene distribución de órdenes por estado"""
        query = """
            SELECT 
                status,
                COUNT(*) as cantidad,
                COALESCE(SUM(total_import_cost), 0) as valor
            FROM purchase_orders 
            GROUP BY status
            ORDER BY cantidad DESC
        """
        result = self.db.execute_query(query)
        return result or []
    
    def crear_metricas_principales(self):
        """Crea las métricas principales del dashboard"""
        stats = self.report_data
        
        return ft.ResponsiveRow([
            ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon("shopping_cart", size=20, color="white"),
                                bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                                border_radius=8,
                                padding=8,
                            ),
                            ft.Text("Importaciones", size=14, 
                                   color=ImportacionesTheme.TEXT_SECONDARY, expand=True),
                        ]),
                        ft.Container(height=12),
                        ft.Text(str(stats['total_importaciones']), size=28, 
                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                        ft.Text("Total registradas", size=12, 
                               color=ImportacionesTheme.TEXT_SECONDARY),
                    ]),
                    padding=20,
                    bgcolor=ImportacionesTheme.BG_SECONDARY,
                    border_radius=12,
                    border=ft.border.all(1, ImportacionesTheme.BORDER),
                )
            ], col={"sm": 6, "md": 3}),
            
            ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon("attach_money", size=20, color="white"),
                                bgcolor=ImportacionesTheme.SUCCESS,
                                border_radius=8,
                                padding=8,
                            ),
                            ft.Text("Valor Total", size=14, 
                                   color=ImportacionesTheme.TEXT_SECONDARY, expand=True),
                        ]),
                        ft.Container(height=12),
                        ft.Text(format_currency(stats['total_valor']), size=28, 
                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                        ft.Text("Importaciones completadas", size=12, 
                               color=ImportacionesTheme.TEXT_SECONDARY),
                    ]),
                    padding=20,
                    bgcolor=ImportacionesTheme.BG_SECONDARY,
                    border_radius=12,
                    border=ft.border.all(1, ImportacionesTheme.BORDER),
                )
            ], col={"sm": 6, "md": 3}),
            
            ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon("schedule", size=20, color="white"),
                                bgcolor=ImportacionesTheme.INFO,
                                border_radius=8,
                                padding=8,
                            ),
                            ft.Text("Tiempo Promedio", size=14, 
                                   color=ImportacionesTheme.TEXT_SECONDARY, expand=True),
                        ]),
                        ft.Container(height=12),
                        ft.Text(f"{stats['promedio_tiempo']} días", size=28, 
                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                        ft.Text("Duración promedio", size=12, 
                               color=ImportacionesTheme.TEXT_SECONDARY),
                    ]),
                    padding=20,
                    bgcolor=ImportacionesTheme.BG_SECONDARY,
                    border_radius=12,
                    border=ft.border.all(1, ImportacionesTheme.BORDER),
                )
            ], col={"sm": 6, "md": 3}),
            
            ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon("trending_up", size=20, color="white"),
                                bgcolor=ImportacionesTheme.WARNING,
                                border_radius=8,
                                padding=8,
                            ),
                            ft.Text("Órdenes Activas", size=14, 
                                   color=ImportacionesTheme.TEXT_SECONDARY, expand=True),
                        ]),
                        ft.Container(height=12),
                        ft.Text(str(stats['ordenes_activas']), size=28, 
                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                        ft.Text("En proceso", size=12, 
                               color=ImportacionesTheme.TEXT_SECONDARY),
                    ]),
                    padding=20,
                    bgcolor=ImportacionesTheme.BG_SECONDARY,
                    border_radius=12,
                    border=ft.border.all(1, ImportacionesTheme.BORDER),
                )
            ], col={"sm": 6, "md": 3}),
        ], spacing=16, run_spacing=16)
    
    def crear_grafico_importaciones_mes(self):
        """Crea gráfico de importaciones por mes"""
        datos = self.report_data.get('importaciones_mes', [])
        
        if not datos:
            return ft.Container(
                content=ft.Text("No hay datos para mostrar", 
                               color=ImportacionesTheme.TEXT_SECONDARY),
                padding=20,
                alignment=ft.alignment.center
            )
        
        # Crear barras del gráfico
        barras = []
        max_valor = max([d['valor_total'] for d in datos]) if datos else 1
        
        for dato in datos:
            altura = (dato['valor_total'] / max_valor * 150) if max_valor > 0 else 10
            porcentaje = (dato['valor_total'] / max_valor * 100) if max_valor > 0 else 0
            
            barras.append(
                ft.Column([
                    ft.Container(
                        content=ft.Text(f"{dato['cantidad']}", size=10, color="white"),
                        bgcolor=ImportacionesTheme.INFO,
                        height=altura,
                        width=40,
                        border_radius=4,
                        alignment=ft.alignment.bottom_center,
                    ),
                    ft.Container(height=8),
                    ft.Text(dato['mes'][5:], size=11, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Text(format_currency(dato['valor_total']), size=10, 
                           color=ImportacionesTheme.TEXT_SECONDARY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Row(barras, alignment=ft.MainAxisAlignment.SPACE_EVENLY),
                ft.Divider(height=20),
                ft.Row([
                    ft.Container(
                        content=ft.Container(width=12, height=12, 
                                           bgcolor=ImportacionesTheme.INFO,
                                           border_radius=2),
                        padding=ft.padding.only(right=8),
                    ),
                    ft.Text("Importaciones por mes (últimos 6 meses)", 
                           size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                ], spacing=4),
            ]),
            padding=20,
        )
    
    def crear_grafico_gastos_tipo(self):
        """Crea gráfico de distribución de gastos por tipo"""
        datos = self.report_data.get('gastos_por_tipo', [])
        
        if not datos:
            return ft.Container(
                content=ft.Text("No hay datos para mostrar", 
                               color=ImportacionesTheme.TEXT_SECONDARY),
                padding=20,
                alignment=ft.alignment.center
            )
        
        total = sum([d['total'] for d in datos])
        
        # Crear elementos del gráfico
        elementos = []
        for dato in datos:
            porcentaje = (dato['total'] / total * 100) if total > 0 else 0
            
            elementos.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                width=12,
                                height=12,
                                bgcolor=dato['color'],
                                border_radius=2,
                            ),
                            ft.Text(dato['tipo_gasto'], size=12, 
                                   color=ImportacionesTheme.TEXT_PRIMARY, expand=True),
                            ft.Text(f"{porcentaje:.1f}%", size=12, 
                                   color=ImportacionesTheme.TEXT_SECONDARY),
                        ], spacing=8),
                        ft.Container(
                            content=ft.Container(
                                width=f"{porcentaje}%",
                                height=8,
                                bgcolor=dato['color'],
                                border_radius=4,
                            ),
                            width=200,
                            height=8,
                            bgcolor=ImportacionesTheme.BORDER,
                            border_radius=4,
                            padding=0,
                        ),
                        ft.Text(format_currency(dato['total']), size=11, 
                               color=ImportacionesTheme.TEXT_SECONDARY),
                    ], spacing=6),
                    padding=ft.padding.symmetric(vertical=8),
                )
            )
        
        return ft.Container(
            content=ft.Column([
                *elementos,
                ft.Divider(height=20),
                ft.Row([
                    ft.Text("Total:", size=12, color=ImportacionesTheme.TEXT_PRIMARY),
                    ft.Text(format_currency(total), size=14, 
                           color=ImportacionesTheme.TEXT_PRIMARY,
                           weight=ft.FontWeight.BOLD),
                ], spacing=8),
            ]),
            padding=20,
        )
    
    def crear_tabla_top_productos(self):
        """Crea tabla de productos más importados"""
        productos = self.report_data.get('top_productos', [])
        
        if not productos:
            return ft.Container(
                content=ft.Text("No hay datos para mostrar", 
                               color=ImportacionesTheme.TEXT_SECONDARY),
                padding=20,
                alignment=ft.alignment.center
            )
        
        rows = []
        for i, producto in enumerate(productos):
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(i + 1), 
                                           color=ImportacionesTheme.TEXT_SECONDARY,
                                           text_align=ft.TextAlign.CENTER)),
                        ft.DataCell(ft.Text(producto['sku'], 
                                           color=ImportacionesTheme.TEXT_PRIMARY)),
                        ft.DataCell(ft.Text(producto['name'], 
                                           color=ImportacionesTheme.TEXT_SECONDARY)),
                        ft.DataCell(ft.Text(str(producto['importaciones']), 
                                           color=ImportacionesTheme.TEXT_SECONDARY,
                                           text_align=ft.TextAlign.RIGHT)),
                        ft.DataCell(ft.Text(str(producto['cantidad_total']), 
                                           color=ImportacionesTheme.TEXT_SECONDARY,
                                           text_align=ft.TextAlign.RIGHT)),
                        ft.DataCell(ft.Text(format_currency(producto.get('costo_promedio', 0)), 
                                           color=ImportacionesTheme.TEXT_PRIMARY,
                                           text_align=ft.TextAlign.RIGHT)),
                    ]
                )
            )
        
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("#", text_align=ft.TextAlign.CENTER)),
                ft.DataColumn(ft.Text("SKU")),
                ft.DataColumn(ft.Text("Producto")),
                ft.DataColumn(ft.Text("Importaciones", text_align=ft.TextAlign.RIGHT)),
                ft.DataColumn(ft.Text("Cantidad Total", text_align=ft.TextAlign.RIGHT)),
                ft.DataColumn(ft.Text("Costo Promedio", text_align=ft.TextAlign.RIGHT)),
            ],
            rows=rows,
            heading_row_color=ImportacionesTheme.BG_SECONDARY,
        )
    
    def crear_estado_ordenes(self):
        """Crea visualización del estado de órdenes"""
        estados = self.report_data.get('estado_ordenes', [])
        
        if not estados:
            return ft.Container(
                content=ft.Text("No hay datos para mostrar", 
                               color=ImportacionesTheme.TEXT_SECONDARY),
                padding=20,
                alignment=ft.alignment.center
            )
        
        total_ordenes = sum([e['cantidad'] for e in estados])
        elementos = []
        
        for estado in estados:
            color = get_status_color(estado['status'])
            porcentaje = (estado['cantidad'] / total_ordenes * 100) if total_ordenes > 0 else 0
            
            elementos.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(get_status_icon(estado['status']), size=16, color=color),
                        ft.Text(estado['status'].replace('_', ' ').title(), size=12, 
                               color=ImportacionesTheme.TEXT_PRIMARY, expand=True),
                        ft.Text(f"{estado['cantidad']}", size=12, 
                               color=ImportacionesTheme.TEXT_SECONDARY, width=40),
                        ft.Container(
                            content=ft.Container(
                                width=f"{porcentaje}%",
                                height=6,
                                bgcolor=color,
                                border_radius=3,
                            ),
                            width=100,
                            height=6,
                            bgcolor=f"{color}30",
                            border_radius=3,
                            padding=0,
                        ),
                        ft.Text(f"{porcentaje:.1f}%", size=11, 
                               color=ImportacionesTheme.TEXT_SECONDARY, width=50),
                    ], spacing=8),
                    padding=ft.padding.symmetric(vertical=6),
                )
            )
        
        return ft.Container(
            content=ft.Column([
                *elementos,
                ft.Divider(height=20),
                ft.Row([
                    ft.Text("Total órdenes:", size=12, color=ImportacionesTheme.TEXT_PRIMARY),
                    ft.Text(str(total_ordenes), size=14, 
                           color=ImportacionesTheme.TEXT_PRIMARY,
                           weight=ft.FontWeight.BOLD),
                ], spacing=8),
            ]),
            padding=20,
        )
    
    def crear_card_contenido(self, titulo, contenido, icono=None, col_size={"md": 6}):
        """Crea una tarjeta de contenido para el dashboard"""
        header = ft.Row([
            ft.Icon(icono, size=20, color=ImportacionesTheme.TEXT_PRIMARY) if icono else ft.Container(),
            ft.Text(titulo, size=16, weight=ft.FontWeight.BOLD, 
                   color=ImportacionesTheme.TEXT_PRIMARY),
            ft.Container(expand=True),
        ], spacing=8) if icono else ft.Row([
            ft.Text(titulo, size=16, weight=ft.FontWeight.BOLD, 
                   color=ImportacionesTheme.TEXT_PRIMARY),
            ft.Container(expand=True),
        ])
        
        return ft.Column([
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        header,
                        ft.Divider(height=20),
                        contenido,
                    ]),
                    padding=20,
                ),
                elevation=1,
            )
        ], col=col_size)
    
    def generar_reporte_excel(self, e):
        """Genera reporte en formato Excel"""
        self.mostrar_mensaje("Generando reporte Excel...", ImportacionesTheme.INFO)
        # Aquí iría la lógica para generar el Excel
        # Por ahora solo mostramos un mensaje
        import threading
        timer = threading.Timer(2.0, lambda: self.mostrar_mensaje("Reporte Excel generado", ImportacionesTheme.SUCCESS))
        timer.start()
    
    def generar_reporte_pdf(self, e):
        """Genera reporte en formato PDF"""
        self.mostrar_mensaje("Generando reporte PDF...", ImportacionesTheme.INFO)
        # Aquí iría la lógica para generar el PDF
        import threading
        timer = threading.Timer(2.0, lambda: self.mostrar_mensaje("Reporte PDF generado", ImportacionesTheme.SUCCESS))
        timer.start()
    
    def mostrar_mensaje(self, mensaje, color):
        """Muestra un mensaje en snackbar"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje, color="white"),
            bgcolor=color,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _crear_seccion_kardex(self):
        # Campo para el Mes (el que ya tenías)
        self.mes_field = ft.Dropdown(
            label="Mes",
            hint_text="Seleccione mes",
            width=150,
            border_color=ImportacionesTheme.BORDER,
            options=[
                ft.dropdown.Option("1", "Enero"), ft.dropdown.Option("2", "Febrero"),
                ft.dropdown.Option("3", "Marzo"), ft.dropdown.Option("4", "Abril"),
                ft.dropdown.Option("5", "Mayo"), ft.dropdown.Option("6", "Junio"),
                ft.dropdown.Option("7", "Julio"), ft.dropdown.Option("8", "Agosto"),
                ft.dropdown.Option("9", "Septiembre"), ft.dropdown.Option("10", "Octubre"),
                ft.dropdown.Option("11", "Noviembre"), ft.dropdown.Option("12", "Diciembre"),
            ],
            value=str(datetime.now().month)
        )

        # Asegúrate de tener definidos estos campos en tu clase (vienen de tu reportes_view.py original)
        self.anio_field = ft.TextField(
            label="Año", 
            value=str(datetime.now().year), 
            width=100,
            border_color=ImportacionesTheme.BORDER
        )
        
        # El producto puede venir del método cargar_productos() que ya tienes
        self.producto_field = ft.Dropdown(
            label="Producto (Opcional)",
            hint_text="Todos los productos",
            expand=True,
            border_color=ImportacionesTheme.BORDER,
            options=[ft.dropdown.Option("", "--- TODOS LOS PRODUCTOS ---")]
        )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.PICTURE_AS_PDF, color=ImportacionesTheme.ERROR),
                    ft.Text("GENERACIÓN OFICIAL SUNAT 13.1", size=18, weight="bold")
                ]),
                ft.Divider(),
                ft.Text("Seleccione los filtros para generar el reporte valorizado acumulado.", size=12),
                
                # FILTROS JUNTOS
                ft.Row([
                    self.anio_field,
                    self.mes_field,
                    self.producto_field
                ], spacing=10),
                
                ft.Container(height=10),
                
                # BOTONES DE ACCIÓN
                ft.Row([
                    ft.ElevatedButton(
                        "Generar Kardex SUNAT (PDF)",
                        icon=ft.Icons.PICTURE_AS_PDF,
                        on_click=self._generar_kardex_sunat,
                        style=ft.ButtonStyle(bgcolor=ImportacionesTheme.SUCCESS, color="white")
                    )
                ], spacing=10)
            ]),
            padding=20,
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=10,
            border=ft.border.all(1, ImportacionesTheme.BORDER)
        )
        
    def _generar_kardex_sunat(self, e):
        anio = self.anio_field.value
        mes = int(self.mes_field.value)
        raw_val = self.producto_field.value
        prod_id = raw_val if raw_val and raw_val.strip() != "" else None
        
        print(f"\n--- INTENTO DE GENERACIÓN DE KARDEX ---")
        print(f"📅 Periodo: {mes}/{anio}")
        print(f"📦 Producto Seleccionado (ID): {prod_id if prod_id else 'TODOS'}")

        if not anio:
            self.page.snack_bar = ft.SnackBar(ft.Text("Por favor, ingrese el año"))
            self.page.snack_bar.open = True
            self.page.update()
            return

        try:
            # Importamos el motor que creamos
            
            reporte_motor = SunatKardexReport(self.db)
            
            # Nombre del archivo dinámico
            label_mes = next(o.text for o in self.mes_field.options if o.key == str(mes))
            nombre_archivo = f"KARDEX_{anio}_{mes}_{label_mes}.pdf"
            
            # Ejecutamos el reporte mensual (procesa todos si prod_id es None)
            exito, msg = reporte_motor.generar_reporte_mensual(
                anio=int(anio), 
                mes=mes, 
                producto_id=prod_id, 
                filename=nombre_archivo
            )
            
            if exito:
                
                os.startfile(nombre_archivo) # Abre el PDF automáticamente
                self.mostrar_mensaje(f"✅ Kardex generado con éxito: {nombre_archivo}", "success")
            else:
                self.mostrar_mensaje(f"⚠️ {msg}", "warning")
                
        except Exception as ex:
            self.mostrar_mensaje(f"❌ Error crítico: {str(ex)}", "error")
            
    
    def _cargar_productos_dropdown(self):
        """Llena el dropdown con productos reales (CORREGIDO)"""
        try:
            # CORRECCIÓN: Usar self.producto_field en lugar de self.dd_producto
            prods = self.db.execute_query("SELECT id, name, sku FROM products WHERE status='active' ORDER BY name")
            if prods:
                opciones = [ft.dropdown.Option("", "TODOS")]
                for p in prods:
                    opciones.append(ft.dropdown.Option(key=str(p['id']), text=f"{p['sku']} - {p['name']}"))
                self.producto_field.options = opciones
                print(f"✅ {len(prods)} productos cargados al filtro")
        except Exception as e:
            print(f"❌ Error cargando productos al dropdown: {e}")

    def _generar_reporte_click(self, e):
        """Lógica que se ejecuta al dar clic en el botón"""
        prod_id = self.dd_producto.value
        anio = self.dd_anio.value
        
        if not prod_id:
            self.page.snack_bar = ft.SnackBar(ft.Text("⚠️ Selecciona un producto"), bgcolor="orange")
            self.page.snack_bar.open = True
            self.page.update()
            return

        # Notificar inicio
        self.page.snack_bar = ft.SnackBar(ft.Text("Generando reporte..."), bgcolor="blue")
        self.page.snack_bar.open = True
        self.page.update()

        try:
            # LLAMADA AL MOTOR DE REPORTE
            reporte = SunatKardexReport(self.db)
            nombre_archivo = f"Kardex_SUNAT_{anio}_{prod_id}.pdf"
            
            # Generar
            exito, mensaje = reporte.generar_reporte_mensual(prod_id, anio, nombre_archivo)
            
            if exito:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"✅ {mensaje}"), bgcolor="green")
                # Opcional: abrir el archivo automáticamente
                # import os; os.startfile(nombre_archivo)
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"❌ {mensaje}"), bgcolor="red")
                
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {str(ex)}"), bgcolor="red")
        
        self.page.snack_bar.open = True
        self.page.update()

    def dashboard_view(self):
        """Retorna la vista del dashboard de reportes"""
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Row([
                                ft.Icon("assessment", size=24, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text("Dashboard de Reportes", size=24, 
                                       weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                            ], spacing=12),
                            ft.Text("Análisis y estadísticas del sistema de importaciones", 
                                   size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                        ]),
                        ft.Row([
                            ft.ElevatedButton(
                                "Exportar Excel",
                                icon="download",
                                on_click=self.generar_reporte_excel,
                                style=ft.ButtonStyle(
                                    bgcolor=ImportacionesTheme.SUCCESS,
                                    color="white"
                                ),
                            ),
                            ft.Container(width=10),
                            ft.ElevatedButton(
                                "Exportar PDF",
                                icon="picture_as_pdf",
                                on_click=self.generar_reporte_pdf,
                                style=ft.ButtonStyle(
                                    bgcolor=ImportacionesTheme.ERROR,
                                    color="white"
                                ),
                            ),
                        ]),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.symmetric(vertical=16),
                ),
                
                # Filtros de fecha
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon("filter_alt", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text("Filtros de Reporte", size=16, 
                                       weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                            ], spacing=8),
                            ft.Divider(height=20),
                            ft.ResponsiveRow([
                                ft.Column([
                                    ft.TextField(
                                        label="Fecha Inicio",
                                        value=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                                        border_color=ImportacionesTheme.BORDER,
                                        filled=True,
                                    )
                                ], col={"md": 3}),
                                ft.Column([
                                    ft.TextField(
                                        label="Fecha Fin",
                                        value=datetime.now().strftime("%Y-%m-%d"),
                                        border_color=ImportacionesTheme.BORDER,
                                        filled=True,
                                    )
                                ], col={"md": 3}),
                                ft.Column([
                                    ft.Dropdown(
                                        label="Proveedor",
                                        border_color=ImportacionesTheme.BORDER,
                                        filled=True,
                                        options=[
                                            ft.dropdown.Option("all", "Todos los proveedores"),
                                        ],
                                        value="all"
                                    )
                                ], col={"md": 3}),
                                ft.Column([
                                    ft.Dropdown(
                                        label="Tipo Reporte",
                                        border_color=ImportacionesTheme.BORDER,
                                        filled=True,
                                        options=[
                                            ft.dropdown.Option("general", "General"),
                                            ft.dropdown.Option("detallado", "Detallado"),
                                            ft.dropdown.Option("costos", "Análisis de Costos"),
                                        ],
                                        value="general"
                                    )
                                ], col={"md": 3}),
                            ], spacing=16, run_spacing=16),
                            ft.Container(height=10),
                            ft.Row([
                                ft.ElevatedButton(
                                    "Aplicar Filtros",
                                    icon="check",
                                ),
                                ft.Container(width=10),
                                ft.OutlinedButton(
                                    "Limpiar Filtros",
                                    icon="clear",
                                ),
                            ]),
                        ]),
                        padding=20,
                    ),
                    elevation=1,
                ),
                
                # Métricas principales
                ft.Text("Métricas Principales", size=18, 
                       weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                ft.Container(height=10),
                self.crear_metricas_principales(),
                ft.Container(height=24),
                
                ft.Text("Reportes y Análisis", size=24, weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                ft.Container(height=20),
                
                # --- AQUÍ VA EL KARDEX (Primero y separado) ---
                self._crear_seccion_kardex(),
                # ---------------------------------------------

                ft.Container(height=20),
                # Gráficos y tablas
                ft.ResponsiveRow([
                    # Gráfico de importaciones por mes
                    self.crear_card_contenido(
                        "Importaciones por Mes",
                        self.crear_grafico_importaciones_mes(),
                        "timeline",
                        {"md": 6}
                    ),
                    
                    # Distribución de gastos
                    self.crear_card_contenido(
                        "Distribución de Gastos",
                        self.crear_grafico_gastos_tipo(),
                        "pie_chart",
                        {"md": 6}
                    ),
                    
                    # Top productos
                    self.crear_card_contenido(
                        "Productos Más Importados",
                        ft.Container(
                            content=self.crear_tabla_top_productos(),
                            padding=ft.padding.all(1),
                        ),
                        "star",
                        {"md": 8}
                    ),
                    
                    # Estado de órdenes
                    self.crear_card_contenido(
                        "Estado de Órdenes",
                        self.crear_estado_ordenes(),
                        "stacked_bar_chart",
                        {"md": 4}
                    ),
                ], spacing=16, run_spacing=16),
                
                # Reportes específicos
                ft.Container(height=24),
                ft.Text("Reportes Específicos", size=18, 
                       weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                ft.Container(height=10),
                
                ft.ResponsiveRow([
                    ft.Column([
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon("receipt", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Text("Reporte de Facturas", size=16, 
                                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Container(expand=True),
                                        ft.IconButton(
                                            icon="chevron_right",
                                            icon_size=20,
                                            on_click=lambda e: self.page.go("/reportes/facturas")
                                        ),
                                    ], spacing=8),
                                    ft.Divider(height=20),
                                    ft.Text("Análisis de facturas por periodo, proveedor y estado", 
                                           size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                                    ft.Container(height=20),
                                    ft.ElevatedButton(
                                        "Generar Reporte",
                                        icon="description",
                                        on_click=lambda e: self.page.go("/reportes/facturas"),
                                    ),
                                ]),
                                padding=20,
                            ),
                            elevation=1,
                        )
                    ], col={"md": 4}),
                    
                    ft.Column([
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon("account_balance_wallet", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Text("Reporte de Costos", size=16, 
                                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Container(expand=True),
                                        ft.IconButton(
                                            icon="chevron_right",
                                            icon_size=20,
                                            on_click=lambda e: self.page.go("/reportes/costos")
                                        ),
                                    ], spacing=8),
                                    ft.Divider(height=20),
                                    ft.Text("Análisis detallado de costos por producto y tipo de gasto", 
                                           size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                                    ft.Container(height=20),
                                    ft.ElevatedButton(
                                        "Generar Reporte",
                                        icon="calculate",
                                        on_click=lambda e: self.page.go("/reportes/costos"),
                                    ),
                                ]),
                                padding=20,
                            ),
                            elevation=1,
                        )
                    ], col={"md": 4}),
                    
                    ft.Column([
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon("schedule", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Text("Reporte de Tiempos", size=16, 
                                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Container(expand=True),
                                        ft.IconButton(
                                            icon="chevron_right",
                                            icon_size=20,
                                            on_click=lambda e: self.page.go("/reportes/tiempos")
                                        ),
                                    ], spacing=8),
                                    ft.Divider(height=20),
                                    ft.Text("Análisis de tiempos de importación por etapa y proveedor", 
                                           size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                                    ft.Container(height=20),
                                    ft.ElevatedButton(
                                        "Generar Reporte",
                                        icon="timeline",
                                        on_click=lambda e: self.page.go("/reportes/tiempos"),
                                    )
                                ]),
                                padding=20,
                            ),
                            elevation=1,
                        )
                    ], col={"md": 4}),
                ], spacing=16, run_spacing=16),
                
                # Últimas importaciones
                ft.Container(height=24),
                ft.Text("Últimas Importaciones", size=18, 
                       weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                ft.Container(height=10),
                
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.DataTable(
                                columns=[
                                    ft.DataColumn(ft.Text("PO")),
                                    ft.DataColumn(ft.Text("Proveedor")),
                                    ft.DataColumn(ft.Text("Fecha")),
                                    ft.DataColumn(ft.Text("Estado")),
                                    ft.DataColumn(ft.Text("Valor")),
                                    ft.DataColumn(ft.Text("")),
                                ],
                                rows=self.obtener_ultimas_importaciones(),
                                heading_row_color=ImportacionesTheme.BG_SECONDARY,
                            ),
                            ft.Container(height=10),
                            ft.Row([
                                ft.Text("Mostrando 10 importaciones recientes", 
                                       size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                                ft.Container(expand=True),
                                ft.TextButton(
                                    "Ver todas las importaciones",
                                    icon="chevron_right",
                                    on_click=lambda e: self.page.go("/ordenes")
                                ),
                            ]),
                        ]),
                        padding=20,
                    ),
                    elevation=1,
                ),
                
                ft.Container(height=40),
            ], scroll=ft.ScrollMode.AUTO),
            padding=24,
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )
    
    def obtener_ultimas_importaciones(self):
        """Obtiene las últimas importaciones para la tabla"""
        query = """
            SELECT po.id, po.po_number, po.order_date, po.status, po.total_import_cost,
                   s.business_name as supplier_name
            FROM purchase_orders po
            LEFT JOIN suppliers s ON po.supplier_id = s.id
            ORDER BY po.order_date DESC
            LIMIT 10
        """
        result = self.db.execute_query(query)
        
        rows = []
        if result:
            for orden in result:
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(orden['po_number'], 
                                               color=ImportacionesTheme.TEXT_PRIMARY,
                                               weight=ft.FontWeight.BOLD)),
                            ft.DataCell(ft.Text(orden['supplier_name'] or "N/A", 
                                               color=ImportacionesTheme.TEXT_SECONDARY)),
                            ft.DataCell(ft.Text(format_date(orden['order_date']), 
                                               color=ImportacionesTheme.TEXT_SECONDARY)),
                            ft.DataCell(ft.Container(
                                content=ft.Row([
                                    ft.Icon(get_status_icon(orden['status']), size=14, 
                                           color=get_status_color(orden['status'])),
                                    ft.Text(orden['status'].replace("_", " ").title(), size=12,
                                           color=get_status_color(orden['status']))
                                ], spacing=4),
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                bgcolor=f"{get_status_color(orden['status'])}15",
                                border_radius=8,
                            )),
                            ft.DataCell(ft.Text(format_currency(orden.get('total_import_cost', 0)), 
                                               color=ImportacionesTheme.TEXT_PRIMARY,
                                               weight=ft.FontWeight.BOLD)),
                            ft.DataCell(ft.IconButton(
                                icon="visibility",
                                icon_size=18,
                                icon_color=ImportacionesTheme.TEXT_SECONDARY,
                                on_click=lambda e, o=orden: self.page.go(f"/ordenes/{o['id']}")
                            )),
                        ]
                    )
                )
        
        return rows


        