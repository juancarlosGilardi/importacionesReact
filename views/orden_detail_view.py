# views/orden_detail_view.py - Detalle completo de una orden con pipeline
import flet as ft
from config_importaciones import (
    ImportacionesTheme, ImportacionesConfig,
    format_currency, format_date, get_status_color, get_status_icon
)

class OrdenDetailView:
    def __init__(self, page: ft.Page, db, orden_id):
        self.page = page
        self.db = db
        self.orden_id = orden_id
        self.orden = None
        self.cargar_datos()
    
    def cargar_datos(self):
        """Carga los datos de la orden"""
        query = """
            SELECT po.*, s.business_name as supplier_name,
                   c.code as currency_code, c.name as currency_name
            FROM purchase_orders po
            LEFT JOIN suppliers s ON po.supplier_id = s.id
            LEFT JOIN currencies c ON po.currency_id = c.id
            WHERE po.id = %s
        """
        result = self.db.execute_query(query, (self.orden_id,))
        if result:
            self.orden = result[0]
    
    def actualizar_estado(self, nuevo_estado):
        """Actualiza el estado de la orden"""
        try:
            query = "UPDATE purchase_orders SET status = %s WHERE id = %s"
            self.db.execute_query(query, (nuevo_estado, self.orden_id), fetch=False)
            self.cargar_datos()
            self.mostrar_mensaje(f"Estado actualizado a {nuevo_estado}", "success")
            return True
        except Exception as e:
            self.mostrar_mensaje(f"Error: {str(e)}", "error")
            return False
    
    def crear_pipeline_estados(self):
        """Crea el pipeline visual de estados"""
        estados = [
            {"codigo": "borrador", "nombre": "Borrador", "icono": "draft"},
            {"codigo": "confirmada", "nombre": "Confirmada", "icono": "check_circle"},
            {"codigo": "en_transito", "nombre": "En Tránsito", "icono": "local_shipping"},
            {"codigo": "en_aduana", "nombre": "En Aduana", "icono": "gavel"},
            {"codigo": "prorrateado", "nombre": "Prorrateado", "icono": "calculate"},
            {"codigo": "en_almacen", "nombre": "En Almacén", "icono": "warehouse"},
            {"codigo": "completada", "nombre": "Completada", "icono": "done_all"},
        ]
        
        current_status = self.orden.get("status", "borrador")
        current_index = next((i for i, e in enumerate(estados) if e["codigo"] == current_status), 0)
        
        pipeline_items = []
        for i, estado in enumerate(estados):
            es_activo = i <= current_index
            es_actual = i == current_index
            
            color = get_status_color(estado["codigo"]) if es_activo else ImportacionesTheme.TEXT_SECONDARY
            
            item = ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Icon(estado["icono"], 
                                       size=20, 
                                       color="white" if es_activo else ImportacionesTheme.TEXT_SECONDARY),
                        width=40,
                        height=40,
                        border_radius=20,
                        bgcolor=color if es_activo else ImportacionesTheme.BORDER,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(height=8),
                    ft.Text(estado["nombre"], 
                           size=12, 
                           weight=ft.FontWeight.BOLD if es_actual else ft.FontWeight.NORMAL,
                           color=color),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                padding=10,
                border=ft.border.all(2, color) if es_actual else None,
                border_radius=8,
            )
            pipeline_items.append(item)
            
            # Agregar línea conectora (excepto el último)
            if i < len(estados) - 1:
                pipeline_items.append(
                    ft.Container(
                        content=ft.Divider(height=2, color=color if es_activo else ImportacionesTheme.BORDER),
                        width=40,
                        alignment=ft.alignment.center,
                    )
                )
        
        return ft.Row(pipeline_items, spacing=0, alignment=ft.MainAxisAlignment.CENTER)
    
    def crear_botones_estado(self):
        """Crea botones para avanzar en el pipeline"""
        estados = ["borrador", "confirmada", "en_transito", "en_aduana", "prorrateado", "en_almacen", "completada"]
        current_status = self.orden.get("status", "borrador")
        current_index = estados.index(current_status) if current_status in estados else 0
        
        # Solo permitir avanzar al siguiente estado
        if current_index >= len(estados) - 1:
            return ft.Container()  # No hay más estados
        
        siguiente_estado = estados[current_index + 1]
        
        # Texto del botón según el estado
        textos_boton = {
            "confirmada": "Confirmar Orden",
            "en_transito": "Marcar como En Tránsito",
            "en_aduana": "Ingresar a Aduana",
            "prorrateado": "Prorratear Costos",
            "en_almacen": "Ingresar a Almacén",
            "completada": "Completar Importación",
        }
        
        return ft.ElevatedButton(
            textos_boton.get(siguiente_estado, "Avanzar Estado"),
            icon="arrow_forward",
            on_click=lambda e: self.avanzar_estado(siguiente_estado),
            style=ft.ButtonStyle(
                bgcolor=get_status_color(siguiente_estado),
                color="white"
            )
        )
    
    def avanzar_estado(self, nuevo_estado):
        """Avanza al siguiente estado y redirige al módulo correspondiente"""
        if self.actualizar_estado(nuevo_estado):
            # SI EL NUEVO ESTADO ES 'EN ALMACEN', VAMOS AL FORMULARIO DE INGRESO
            if nuevo_estado == "en_almacen":
                # Pasamos el po_id como parámetro para que el formulario cargue los productos automáticamente
                self.page.go(f"/almacen/ingreso?po_id={self.orden_id}")
            elif nuevo_estado == "prorrateado":
                self.page.go(f"/prorrateo?po_id={self.orden_id}")
            else:
                self.page.go(f"/ordenes/{self.orden_id}")
                
    def detail_view(self):
        """Vista de detalle de la orden"""
        if not self.orden:
            return ft.Container(
                content=ft.Column([
                    ft.Icon("error", size=64, color=ImportacionesTheme.ERROR),
                    ft.Text("Orden no encontrada", size=20, weight=ft.FontWeight.BOLD),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=100,
                alignment=ft.alignment.center
            )
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(f"Orden #{self.orden['po_number']}", 
                                   size=24, weight=ft.FontWeight.BOLD),
                            ft.Text(f"Proveedor: {self.orden['supplier_name']}", 
                                   color=ImportacionesTheme.TEXT_SECONDARY),
                        ]),
                        ft.Column([
                            ft.ElevatedButton(
                                "Recibir en Almacén",
                                icon=ft.Icons.INVENTORY_2,
                                # Navegamos a la ruta de ingreso pasando el ID de la orden
                                on_click=lambda e: self.page.go(f"/almacen/ingreso?po_id={self.orden_id}"),
                                style=ft.ButtonStyle(
                                    bgcolor=ImportacionesTheme.SUCCESS,
                                    color="white"
                                ),
                                expand=True,
                            )
                        ], col={"md": 4}),
                        ft.ElevatedButton(
                            "Volver a la lista",
                            icon="arrow_back",
                            on_click=lambda e: self.page.go("/ordenes"),
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=20,
                    bgcolor=ImportacionesTheme.BG_SECONDARY,
                ),
                
                # Pipeline de estados
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Estado de Importación", size=16, weight=ft.FontWeight.BOLD),
                            ft.Container(height=20),
                            self.crear_pipeline_estados(),
                            ft.Container(height=20),
                            self.crear_botones_estado(),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=20,
                    ),
                ),
                
                # Acciones rápidas
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Acciones Rápidas", size=16, weight=ft.FontWeight.BOLD),
                            ft.Container(height=16),
                            ft.ResponsiveRow([
                                ft.Column([
                                    ft.ElevatedButton(
                                        "Ver Facturas",
                                        icon="receipt",
                                        on_click=lambda e: self.page.go(f"/facturas?po_id={self.orden_id}"),
                                        style=ft.ButtonStyle(
                                            bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                                            color="white"
                                        ),
                                        expand=True,
                                    )
                                ], col={"md": 4}),
                                ft.Column([
                                    ft.ElevatedButton(
                                        "Registrar Gastos",
                                        icon="payments",
                                        on_click=lambda e: self.page.go(f"/gastos/nuevo?po_id={self.orden_id}"),
                                        style=ft.ButtonStyle(
                                            bgcolor=ImportacionesTheme.WARNING,
                                            color="white"
                                        ),
                                        expand=True,
                                    )
                                ], col={"md": 4}),
                                ft.Column([
                                    ft.ElevatedButton(
                                        "Prorratear Costos",
                                        icon="calculate",
                                        on_click=lambda e: self.page.go(f"/prorrateo?po_id={self.orden_id}"),
                                        style=ft.ButtonStyle(
                                            bgcolor=ImportacionesTheme.INFO,
                                            color="white"
                                        ),
                                        expand=True,
                                    )
                                ], col={"md": 4}),
                            ], spacing=12),
                        ]),
                        padding=20,
                    ),
                ),
                
                # Información detallada
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Información de la Orden", size=16, weight=ft.FontWeight.BOLD),
                            ft.Container(height=16),
                            ft.ResponsiveRow([
                                ft.Column([
                                    ft.Text("Fecha Orden:", color=ImportacionesTheme.TEXT_SECONDARY),
                                    ft.Text(format_date(self.orden["order_date"]), 
                                           weight=ft.FontWeight.BOLD),
                                ], col={"md": 3}),
                                ft.Column([
                                    ft.Text("Incoterm:", color=ImportacionesTheme.TEXT_SECONDARY),
                                    ft.Text(self.orden["incoterm"], weight=ft.FontWeight.BOLD),
                                ], col={"md": 3}),
                                ft.Column([
                                    ft.Text("Moneda:", color=ImportacionesTheme.TEXT_SECONDARY),
                                    ft.Text(self.orden.get("currency_name", "USD"), 
                                           weight=ft.FontWeight.BOLD),
                                ], col={"md": 3}),
                                ft.Column([
                                    ft.Text("Total FOB:", color=ImportacionesTheme.TEXT_SECONDARY),
                                    ft.Text(format_currency(self.orden.get("total_fob", 0)), 
                                           weight=ft.FontWeight.BOLD,
                                           color=ImportacionesTheme.STATUS_CONFIRMED),
                                ], col={"md": 3}),
                            ], spacing=16),
                        ]),
                        padding=20,
                    ),
                ),
            ], scroll=ft.ScrollMode.AUTO),
            padding=20,
            expand=True,
        )
    
    def mostrar_mensaje(self, mensaje, tipo="info"):
        """Muestra un mensaje"""
        colors = {
            "success": ImportacionesTheme.SUCCESS,
            "error": ImportacionesTheme.ERROR,
            "warning": ImportacionesTheme.WARNING,
            "info": ImportacionesTheme.STATUS_CONFIRMED
        }
        
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje, color="white"),
            bgcolor=colors.get(tipo, ImportacionesTheme.STATUS_CONFIRMED)
        )
        self.page.snack_bar.open = True
        self.page.update()