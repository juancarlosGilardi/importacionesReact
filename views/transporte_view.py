# views/transporte_view.py - VERSIÓN CON ACTUALIZACIÓN DE TABLA
import flet as ft
from config_importaciones import (
    ImportacionesTheme, ImportacionesConfig,
    format_currency, format_date
)

class TransporteView:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.documentos = []
        self.documento_a_eliminar = None
        self.dialog_eliminar = None
        self.contenedor_tabla = None  # ← Referencia al contenedor de la tabla
        self.cargar_documentos()
    
    def cargar_documentos(self):
        """Carga los documentos desde la base de datos"""
        try:
            query = """
                SELECT 
                    sd.*,
                    i.numero_importacion,
                    i.descripcion as importacion_descripcion
                FROM shipping_documents sd
                LEFT JOIN importaciones i ON sd.importacion_id = i.id
                ORDER BY sd.etd_date DESC, sd.created_at DESC
                LIMIT 50
            """
            result = self.db.execute_query(query)
            self.documentos = result if result else []
            print(f"[DEBUG] Documentos cargados: {len(self.documentos)}")
        except Exception as ex:
            print(f"[ERROR] Error cargando documentos: {ex}")
            self.documentos = []
    
    def crear_fila_documento(self, documento):
        """Crea una fila para la tabla de documentos"""
        doc_data = dict(documento)
        doc_id = documento['id']
        
        # Icono según tipo de documento
        tipo_iconos = {
            'bill_of_lading': ft.Icons.DIRECTIONS_BOAT,
            'air_waybill': ft.Icons.FLIGHT,
            'carta_porte': ft.Icons.LOCAL_SHIPPING,
            'other': ft.Icons.DESCRIPTION
        }
        tipo_icono = tipo_iconos.get(documento.get('document_type'), ft.Icons.DESCRIPTION)
        
        tipo_textos = {
            'bill_of_lading': 'BL',
            'air_waybill': 'AWB',
            'carta_porte': 'Carta Porte',
            'other': 'Otro'
        }
        tipo_texto = tipo_textos.get(documento.get('document_type'), 'Otro')
        
        tipo_badge = ft.Container(
            content=ft.Row([
                ft.Icon(tipo_icono, size=14, color=ImportacionesTheme.INFO),
                ft.Text(tipo_texto, size=12, color=ImportacionesTheme.TEXT_SECONDARY),
            ], spacing=4),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            bgcolor=f"{ImportacionesTheme.INFO}15",
            border_radius=8,
        )
        
        # Estado basado en fechas
        estado = "Pendiente"
        estado_color = ImportacionesTheme.WARNING
        
        if documento.get('actual_arrival'):
            estado = "Entregado"
            estado_color = ImportacionesTheme.SUCCESS
        elif documento.get('etd_date'):
            estado = "En Tránsito"
            estado_color = ImportacionesTheme.INFO
        
        estado_badge = ft.Container(
            content=ft.Text(estado, size=12, color="white", weight=ft.FontWeight.BOLD),
            bgcolor=estado_color,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=8,
        )
        
        numero_importacion = documento.get('numero_importacion') or 'Sin asignar'
        
        return ft.DataRow(
            cells=[
                ft.DataCell(
                    ft.Text(
                        numero_importacion, 
                        color=ImportacionesTheme.TEXT_PRIMARY,
                        weight=ft.FontWeight.BOLD
                    )
                ),
                ft.DataCell(tipo_badge),
                ft.DataCell(
                    ft.Text(
                        documento.get('document_number') or 'N/A', 
                        color=ImportacionesTheme.TEXT_PRIMARY
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        documento.get('carrier') or "N/A", 
                        color=ImportacionesTheme.TEXT_SECONDARY
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        format_date(documento.get('etd_date')) if documento.get('etd_date') else "-", 
                        color=ImportacionesTheme.TEXT_SECONDARY
                    )
                ),
                ft.DataCell(estado_badge),
                ft.DataCell(
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_size=18,
                            icon_color=ImportacionesTheme.INFO,
                            tooltip="Editar documento",
                            on_click=lambda e, did=doc_id: self.page.go(f"/transporte/{did}/editar")
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_size=18,
                            icon_color=ImportacionesTheme.ERROR,
                            tooltip="Eliminar documento",
                            on_click=lambda e, d=doc_data: self.mostrar_modal_confirmacion_eliminar(d)
                        ),
                    ], spacing=0)
                ),
            ]
        )
    
    def mostrar_modal_confirmacion_eliminar(self, documento):
        """Muestra un modal de confirmación para eliminar el documento"""
        print(f"[DEBUG] Mostrando modal para eliminar documento: {documento.get('document_number')}")
        
        self.documento_a_eliminar = documento
        
        doc_number = documento.get('document_number', 'N/A')
        doc_type = documento.get('document_type', 'N/A').replace('_', ' ').title()
        importacion = documento.get('numero_importacion') or 'Sin importación'
        carrier = documento.get('carrier') or 'N/A'
        
        self.dialog_eliminar = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING, color=ImportacionesTheme.WARNING),
                ft.Text("Confirmar Eliminación", weight=ft.FontWeight.BOLD),
            ], spacing=12),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("¿Estás seguro que deseas eliminar este documento?", size=14),
                    ft.Container(height=12),
                    ft.Text(f"📄 {doc_number}", 
                           size=16, weight=ft.FontWeight.BOLD,
                           color=ImportacionesTheme.TEXT_PRIMARY),
                    ft.Container(height=8),
                    ft.Text(f"📋 Tipo: {doc_type}", 
                           size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Text(f"📦 Importación: {importacion}", 
                           size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Text(f"🚢 Transportista: {carrier}", 
                           size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Container(height=16),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.WARNING_AMBER, size=16, color=ImportacionesTheme.WARNING),
                            ft.Text("Esta acción no se puede deshacer.", 
                                   size=12, color=ImportacionesTheme.WARNING, weight=ft.FontWeight.BOLD),
                        ], spacing=8),
                        bgcolor=f"{ImportacionesTheme.WARNING}20",
                        padding=10,
                        border_radius=8,
                    ),
                ], tight=True, spacing=4),
                width=400,
            ),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=self.cerrar_modal_eliminar,
                ),
                ft.ElevatedButton(
                    "Eliminar",
                    icon=ft.Icons.DELETE_FOREVER,
                    on_click=self.eliminar_documento_confirmado,
                    style=ft.ButtonStyle(
                        bgcolor=ImportacionesTheme.ERROR,
                        color="white"
                    )
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.open(self.dialog_eliminar)
    
    def eliminar_documento_confirmado(self, e):
        """Elimina el documento después de confirmación"""
        if not self.documento_a_eliminar:
            print("[DEBUG] No hay documento para eliminar")
            return
        
        doc_number = self.documento_a_eliminar.get('document_number', 'N/A')
        print(f"[DEBUG] Eliminando documento: {doc_number}")
        
        try:
            # Eliminar el documento
            delete_query = "DELETE FROM shipping_documents WHERE id = %s"
            self.db.execute_query(delete_query, (self.documento_a_eliminar['id'],), fetch=False)
            print(f"[DEBUG] Documento eliminado de la BD")
            
            # Cerrar modal
            self.cerrar_modal_eliminar(e)
            
            # Mostrar mensaje de éxito
            self.mostrar_mensaje_exito(f"✅ Documento {doc_number} eliminado correctamente")
            
            # ⭐ ACTUALIZAR LA TABLA SIN RECARGAR PÁGINA
            self.actualizar_tabla()
            
        except Exception as ex:
            print(f"[DEBUG] Error al eliminar: {str(ex)}")
            self.cerrar_modal_eliminar(e)
            self.mostrar_mensaje_error(f"Error al eliminar documento: {str(ex)}")
    
    def cerrar_modal_eliminar(self, e=None):
        """Cierra el modal de confirmación"""
        if self.dialog_eliminar:
            self.page.close(self.dialog_eliminar)
        self.documento_a_eliminar = None
    
    def actualizar_tabla(self):
        """Recarga los datos y actualiza la tabla sin recargar la página"""
        # Recargar datos de la BD
        self.cargar_documentos()
        
        # Reconstruir contenido de la tabla
        if self.documentos:
            nuevo_contenido = ft.Column([
                # Contador
                ft.Row([
                    ft.Text(
                        f"📄 {len(self.documentos)} documentos encontrados",
                        size=14,
                        color=ImportacionesTheme.TEXT_SECONDARY
                    ),
                ]),
                ft.Container(height=12),
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Importación", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Tipo", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Número", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Transportista", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("ETD", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Estado", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Acciones", weight=ft.FontWeight.BOLD)),
                    ],
                    rows=[self.crear_fila_documento(d) for d in self.documentos],
                    heading_row_color=ImportacionesTheme.BG_SECONDARY,
                    border=ft.border.all(1, ImportacionesTheme.BORDER),
                    border_radius=8,
                ),
            ])
        else:
            nuevo_contenido = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.LOCAL_SHIPPING, size=48, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Container(height=16),
                    ft.Text("No hay documentos de transporte registrados", 
                           color=ImportacionesTheme.TEXT_SECONDARY, size=16),
                    ft.Container(height=16),
                    ft.ElevatedButton(
                        "Registrar Primer Documento",
                        icon=ft.Icons.ADD,
                        on_click=lambda e: self.page.go("/transporte/nuevo"),
                        style=ft.ButtonStyle(
                            bgcolor=ImportacionesTheme.SUCCESS,
                            color="white"
                        ),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=40,
                alignment=ft.alignment.center
            )
        
        # Actualizar el contenedor
        if self.contenedor_tabla:
            self.contenedor_tabla.content = nuevo_contenido
            self.page.update()
    
    def mostrar_mensaje_exito(self, mensaje):
        """Muestra un mensaje de éxito"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje, color="white", weight=ft.FontWeight.BOLD),
            bgcolor=ImportacionesTheme.SUCCESS,
            duration=3000,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def mostrar_mensaje_error(self, mensaje):
        """Muestra un mensaje de error"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje, color="white"),
            bgcolor=ImportacionesTheme.ERROR,
            duration=4000,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def list_view(self):
        """Retorna la vista de lista de documentos"""
        
        # Crear contenido inicial de la tabla
        if self.documentos:
            contenido_tabla = ft.Column([
                # Contador
                ft.Row([
                    ft.Text(
                        f"📄 {len(self.documentos)} documentos encontrados",
                        size=14,
                        color=ImportacionesTheme.TEXT_SECONDARY
                    ),
                ]),
                ft.Container(height=12),
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Importación", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Tipo", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Número", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Transportista", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("ETD", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Estado", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Acciones", weight=ft.FontWeight.BOLD)),
                    ],
                    rows=[self.crear_fila_documento(d) for d in self.documentos],
                    heading_row_color=ImportacionesTheme.BG_SECONDARY,
                    border=ft.border.all(1, ImportacionesTheme.BORDER),
                    border_radius=8,
                ),
            ])
        else:
            contenido_tabla = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.LOCAL_SHIPPING, size=48, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Container(height=16),
                    ft.Text("No hay documentos de transporte registrados", 
                           color=ImportacionesTheme.TEXT_SECONDARY, size=16),
                    ft.Container(height=16),
                    ft.ElevatedButton(
                        "Registrar Primer Documento",
                        icon=ft.Icons.ADD,
                        on_click=lambda e: self.page.go("/transporte/nuevo"),
                        style=ft.ButtonStyle(
                            bgcolor=ImportacionesTheme.SUCCESS,
                            color="white"
                        ),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=40,
                alignment=ft.alignment.center
            )
        
        # ⭐ Guardar referencia al contenedor de la tabla
        self.contenedor_tabla = ft.Container(content=contenido_tabla)
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.LOCAL_SHIPPING, size=24, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text("Documentos de Transporte", size=24, 
                                       weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                            ], spacing=12),
                            ft.Text("Gestión de BL, AWB y documentos de transporte internacional", 
                                   size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                        ]),
                        ft.ElevatedButton(
                            "Nuevo Documento",
                            icon=ft.Icons.ADD,
                            on_click=lambda e: self.page.go("/transporte/nuevo"),
                            style=ft.ButtonStyle(
                                bgcolor=ImportacionesTheme.SUCCESS,
                                color="white"
                            ),
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.symmetric(vertical=16),
                ),
                
                # Filtros
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.TextField(
                                    label="Buscar documento",
                                    prefix_icon=ft.Icons.SEARCH,
                                    border_color=ImportacionesTheme.BORDER,
                                    filled=True,
                                    width=300,
                                ),
                                ft.Dropdown(
                                    label="Tipo",
                                    border_color=ImportacionesTheme.BORDER,
                                    filled=True,
                                    width=150,
                                    options=[
                                        ft.dropdown.Option("all", "Todos"),
                                        ft.dropdown.Option("bill_of_lading", "BL"),
                                        ft.dropdown.Option("air_waybill", "AWB"),
                                        ft.dropdown.Option("carta_porte", "Carta Porte"),
                                    ],
                                    value="all"
                                ),
                                ft.Dropdown(
                                    label="Estado",
                                    border_color=ImportacionesTheme.BORDER,
                                    filled=True,
                                    width=150,
                                    options=[
                                        ft.dropdown.Option("all", "Todos"),
                                        ft.dropdown.Option("pending", "Pendientes"),
                                        ft.dropdown.Option("in_transit", "En Tránsito"),
                                        ft.dropdown.Option("delivered", "Entregados"),
                                    ],
                                    value="all"
                                ),
                                ft.ElevatedButton(
                                    "Filtrar",
                                    icon=ft.Icons.FILTER_ALT,
                                    style=ft.ButtonStyle(
                                        bgcolor=ImportacionesTheme.INFO,
                                        color="white"
                                    ),
                                ),
                            ], spacing=12),
                        ]),
                        padding=20,
                    ),
                    elevation=1,
                ),
                
                # Card con la tabla (usa la referencia)
                ft.Card(
                    content=ft.Container(
                        content=self.contenedor_tabla,  # ← Usar la referencia
                        padding=20,
                    ),
                    elevation=1,
                ),
            ], scroll=ft.ScrollMode.AUTO),
            padding=24,
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )

