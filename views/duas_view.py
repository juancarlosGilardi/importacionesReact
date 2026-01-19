# views/duas_view.py - VERSIÓN CORREGIDA
import flet as ft
from config_importaciones import (
    ImportacionesTheme, ImportacionesConfig,
    format_currency, format_date, create_status_badge
)

class DUAView:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.dua_a_eliminar = None  # Para almacenar el DUA que se va a eliminar
        self.dialog_eliminar = None
        self.duas = []
        self.contenedor_tabla = None
        self.cargar_duas()
        
        # Controles de filtro
        self.busqueda_control = ft.TextField(
            label="Buscar DUA",
            prefix_icon="search",
            border_color=ImportacionesTheme.BORDER,
            filled=True,
            width=300,
            on_change=self.filtrar_duas
        )
        
        self.estado_control = ft.Dropdown(
            label="Estado",
            border_color=ImportacionesTheme.BORDER,
            filled=True,
            width=150,
            options=[
                ft.dropdown.Option("all", "Todos"),
                ft.dropdown.Option("registered", "Registrados"),
                ft.dropdown.Option("in_process", "En Proceso"),
                ft.dropdown.Option("cleared", "Despachados"),
                ft.dropdown.Option("cancelled", "Cancelados"),
            ],
            value="all",
            on_change=self.filtrar_duas
        )
        
        self.orden_control = ft.Dropdown(
            label="Ordenar por",
            border_color=ImportacionesTheme.BORDER,
            filled=True,
            width=150,
            options=[
                ft.dropdown.Option("date_desc", "Fecha (reciente)"),
                ft.dropdown.Option("date_asc", "Fecha (antigua)"),
                ft.dropdown.Option("tax_desc", "Impuestos (mayor)"),
                ft.dropdown.Option("tax_asc", "Impuestos (menor)"),
            ],
            value="date_desc",
            on_change=self.filtrar_duas
        )
    
    def cargar_duas(self):
        """Carga las DUAs desde la base de datos"""
        query = """
            SELECT dd.*, i.numero_importacion
            FROM dua_documents dd
            LEFT JOIN importaciones i ON dd.importacion_id = i.id
            ORDER BY dd.registration_date DESC
        """
        result = self.db.execute_query(query)
        if result:
            self.duas = result
    
    def filtrar_duas(self, e=None):
        """Filtra las DUAs según los criterios seleccionados"""
        # Esta función se activa cuando cambian los filtros
        # En una implementación real, aquí harías una nueva consulta a la BD
        self.list_view()
        self.page.update()
    
    def crear_fila_dua(self, dua):
        """Crea una fila para la tabla de DUAs con botón de eliminación"""
        importacion_codigo = dua.get('numero_importacion') or "Sin importación"
        
        status_badge = ft.Container(
            content=ft.Text(
                dua['status'].replace('_', ' ').title(),
                size=12,
                color="white",
                weight=ft.FontWeight.BOLD
            ),
            bgcolor=self.obtener_color_estado(dua['status']),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=8,
        )
        
        # Capturar el dua_id de forma segura
        dua_id = dua['id']
        dua_data = dict(dua)  # Crear copia del diccionario
        
        total_impuestos = dua.get('total_taxes') or 0 
        fecha_registro = dua.get('registration_date')

        return ft.DataRow(
            cells=[
                ft.DataCell(
                    ft.Text(dua['dua_number'], 
                        color=ImportacionesTheme.TEXT_PRIMARY,
                        weight=ft.FontWeight.BOLD)
                ),
                ft.DataCell(
                    ft.Text(importacion_codigo, 
                        color=ImportacionesTheme.TEXT_SECONDARY)
                ),
                ft.DataCell(
                    # CORRECCIÓN: Validar que exista fecha antes de formatear
                    ft.Text(format_date(fecha_registro) if fecha_registro else "-", 
                        color=ImportacionesTheme.TEXT_SECONDARY)
                ),
                ft.DataCell(status_badge),
                ft.DataCell(
                    # CORRECCIÓN: Pasar el valor saneado (total_impuestos) que nunca es None
                    ft.Text(format_currency(total_impuestos), 
                        color=ImportacionesTheme.TEXT_PRIMARY,
                        weight=ft.FontWeight.BOLD)
                ),
                ft.DataCell(
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_size=18,
                            icon_color=ImportacionesTheme.INFO,
                            tooltip="Editar DUA",
                            on_click=lambda e, did=dua_id: self.page.go(f"/dua/{did}/editar")
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_size=18,
                            icon_color=ImportacionesTheme.ERROR,
                            tooltip="Eliminar DUA",
                            on_click=lambda e, d=dua_data: self.mostrar_modal_confirmacion_eliminar(d)
                        ),
                    ], spacing=4)
                ),
            ]
        )

    def mostrar_modal_confirmacion_eliminar(self, dua):
        """Muestra un modal de confirmación para eliminar el DUA"""
        print(f"[DEBUG] Mostrando modal para eliminar DUA: {dua['dua_number']}")
        
        self.dua_a_eliminar = dua
        total_impuestos = dua.get('total_taxes') or 0
        # Crear el diálogo
        self.dialog_eliminar = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING, color=ImportacionesTheme.WARNING),
                ft.Text("Confirmar Eliminación", weight=ft.FontWeight.BOLD),
            ], spacing=12),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("¿Estás seguro que deseas eliminar el DUA:", size=14),
                    ft.Container(height=8),
                    ft.Text(f"📋 {dua['dua_number']}", 
                        size=16, weight=ft.FontWeight.BOLD,
                        color=ImportacionesTheme.TEXT_PRIMARY),
                    ft.Container(height=8),
                    ft.Text(f"🗂️ Asociado a: {dua.get('numero_importacion') or 'Sin importación'}", 
                        size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Container(height=8),
                    ft.Text(f"💰 Total Impuestos: {format_currency(total_impuestos)}", 
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
                    "Eliminar DUA",
                    icon=ft.Icons.DELETE_FOREVER,
                    on_click=self.eliminar_dua_confirmado,
                    style=ft.ButtonStyle(
                        bgcolor=ImportacionesTheme.ERROR,
                        color="white"
                    )
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        # MÉTODO PARA FLET 0.22+ - Usar page.open()
        self.page.open(self.dialog_eliminar)

    def eliminar_dua_confirmado(self, e):
        """Elimina el DUA después de confirmación"""
        if not self.dua_a_eliminar:
            return
        
        try:
            # Actualizar importación si existe
            if self.dua_a_eliminar.get('importacion_id'):
                update_query = "UPDATE importaciones SET estado = 'en_transito' WHERE id = %s"
                self.db.execute_query(update_query, (self.dua_a_eliminar['importacion_id'],), fetch=False)
            
            # Eliminar el DUA
            delete_query = "DELETE FROM dua_documents WHERE id = %s"
            self.db.execute_query(delete_query, (self.dua_a_eliminar['id'],), fetch=False)
            
            dua_number = self.dua_a_eliminar['dua_number']
            
            # Cerrar modal
            self.cerrar_modal_eliminar(e)
            
            # Mostrar mensaje
            self.mostrar_mensaje_exito(f"✅ DUA {dua_number} eliminado")
            
            # ⭐ ACTUALIZAR LA TABLA SIN RECARGAR PÁGINA
            self.actualizar_tabla()
            
        except Exception as ex:
            self.cerrar_modal_eliminar(e)
            self.mostrar_mensaje_error(f"Error: {str(ex)}")
                

    def cerrar_modal_eliminar(self, e=None):
        """Cierra el modal de confirmación"""
        if hasattr(self, 'dialog_eliminar') and self.dialog_eliminar:
            self.page.close(self.dialog_eliminar)
        self.dua_a_eliminar = None


    def obtener_color_estado(self, estado):
        """Obtiene el color según el estado del DUA"""
        colores = {
            'registered': ImportacionesTheme.INFO,
            'in_process': ImportacionesTheme.WARNING,
            'cleared': ImportacionesTheme.SUCCESS,
            'cancelled': ImportacionesTheme.ERROR,
        }
        return colores.get(estado, ImportacionesTheme.TEXT_SECONDARY)
    
    def mostrar_mensaje_exito(self, mensaje):
        """Muestra un mensaje de éxito"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje, color="white"),
            bgcolor=ImportacionesTheme.SUCCESS,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def mostrar_mensaje_error(self, mensaje):
        """Muestra un mensaje de error"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje, color="white"),
            bgcolor=ImportacionesTheme.ERROR,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def actualizar_tabla(self):
        """Recarga los datos y actualiza la tabla"""
        # Recargar datos de la BD
        self.cargar_duas()
        
        # Reconstruir contenido de la tabla
        if self.duas:
            nuevo_contenido = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("N° DUA")),
                    ft.DataColumn(ft.Text("Importación")),
                    ft.DataColumn(ft.Text("Fecha Registro")),
                    ft.DataColumn(ft.Text("Estado")),
                    ft.DataColumn(ft.Text("Total Impuestos")),
                    ft.DataColumn(ft.Text("Acciones")),
                ],
                rows=[self.crear_fila_dua(d) for d in self.duas],
                heading_row_color=ImportacionesTheme.BG_SECONDARY,
            )
        else:
            nuevo_contenido = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.DESCRIPTION, size=48, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Container(height=16),
                    ft.Text("No hay DUA registrados", color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.ElevatedButton(
                        "Registrar Primer DUA",
                        icon=ft.Icons.ADD,
                        on_click=lambda e: self.page.go("/dua/nuevo"),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=40,
                alignment=ft.alignment.center
            )
        
        # Actualizar el contenedor
        if self.contenedor_tabla:
            self.contenedor_tabla.content = nuevo_contenido
            self.page.update()
    
    def list_view(self):
        """Retorna la vista de lista de DUAs"""
        
        # Crear contenido de la tabla
        if self.duas:
            contenido_tabla = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("N° DUA")),
                    ft.DataColumn(ft.Text("Importación")),
                    ft.DataColumn(ft.Text("Fecha Registro")),
                    ft.DataColumn(ft.Text("Estado")),
                    ft.DataColumn(ft.Text("Total Impuestos")),
                    ft.DataColumn(ft.Text("Acciones")),
                ],
                rows=[self.crear_fila_dua(d) for d in self.duas],
                heading_row_color=ImportacionesTheme.BG_SECONDARY,
            )
        else:
            contenido_tabla = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.DESCRIPTION, size=48, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Container(height=16),
                    ft.Text("No hay DUA registrados", color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.ElevatedButton(
                        "Registrar Primer DUA",
                        icon=ft.Icons.ADD,
                        on_click=lambda e: self.page.go("/dua/nuevo"),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=40,
                alignment=ft.alignment.center
            )
        
        # Guardar referencia al contenedor de la tabla
        self.contenedor_tabla = ft.Container(
            content=contenido_tabla,
        )
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.DESCRIPTION, size=24, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text("Documentos Únicos de Aduana", size=24, 
                                    weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                            ], spacing=12),
                            ft.Text("Gestión de DUA y cálculo de impuestos", 
                                size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                        ]),
                        ft.ElevatedButton(
                            "Nuevo DUA",
                            icon=ft.Icons.ADD,
                            on_click=lambda e: self.page.go("/dua/nuevo"),
                            style=ft.ButtonStyle(
                                bgcolor=ImportacionesTheme.ERROR,
                                color="white"
                            ),
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.symmetric(vertical=16),
                ),
                
                # Filtros
                ft.Card(
                    content=ft.Container(
                        content=ft.Row([
                            self.busqueda_control,
                            self.estado_control,
                            self.orden_control,
                            ft.ElevatedButton(
                                "Filtrar",
                                icon=ft.Icons.FILTER_ALT,
                                on_click=self.filtrar_duas,
                                style=ft.ButtonStyle(bgcolor=ImportacionesTheme.INFO, color="white"),
                            ),
                            ft.ElevatedButton(
                                "Limpiar",
                                icon=ft.Icons.FILTER_ALT_OFF,
                                on_click=self.limpiar_filtros,
                                style=ft.ButtonStyle(
                                    bgcolor=ImportacionesTheme.BORDER,
                                    color=ImportacionesTheme.TEXT_PRIMARY
                                ),
                            ),
                        ], spacing=12),
                        padding=20,
                    ),
                    elevation=1,
                ),
                
                # Card con la tabla
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            self.contenedor_tabla,  # ← Usar la referencia
                            ft.Container(
                                content=ft.Row([
                                    ft.Text(f"Mostrando {len(self.duas)} DUAs", 
                                        color=ImportacionesTheme.TEXT_SECONDARY),
                                ]),
                                padding=ft.padding.only(top=20),
                            ),
                        ]),
                        padding=20,
                    ),
                    elevation=1,
                ),
            ], scroll=ft.ScrollMode.AUTO),
            padding=24,
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )

    def limpiar_filtros(self, e):
        """Limpia los filtros"""
        self.busqueda_control.value = ""
        self.estado_control.value = "all"
        self.orden_control.value = "date_desc"
        self.filtrar_duas()