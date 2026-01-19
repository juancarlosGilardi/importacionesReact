# views/import_view.py - VERSIÓN CORREGIDA CON MODAL DUA FUNCIONANDO
import flet as ft
from datetime import datetime
from config_importaciones import ImportacionesTheme, format_currency, format_date
from imports.excel_importaciones_processor import ExcelImportacionesProcessor

class ImportacionesView:
    """Vista para gestionar las importaciones (folders Manila)"""
    
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.selected_dua_id = None
        self.current_importacion_id = None
        self.todas_importaciones = []
        self.importacion_a_eliminar = None
        self.dialog_eliminar_importacion = None

        self.pagina_actual = 1
        self.items_por_pagina = 25
        self.total_registros = 0
        self.total_paginas = 1

        self.txt_pagina_actual = None
        self.controles_paginacion = None
        self.txt_busqueda = None
        self.dd_estado = None
        self.txt_contador = None
        self.contenedor_tabla = None
        
        # Referencias a controles del modal

        self.radio_group = None
        self.btn_guardar_modal = None
        self.modal_dialog = None
        self.file_picker = ft.FilePicker(on_result=self.procesar_archivo_excel)
        if self.file_picker not in self.page.overlay:
            self.page.overlay.append(self.file_picker)


    def list_view(self):
        """Vista principal con filtros y paginación"""
        
        # Cargar primera página
        self.pagina_actual = 1
        self.todas_importaciones = self.cargar_importaciones(pagina=1, limite=self.items_por_pagina)
        
        # Controles de filtro
        self.txt_busqueda = ft.TextField(
            label="Buscar importaciones",
            hint_text="Por número, descripción...",
            prefix_icon=ft.Icons.SEARCH,
            filled=True,
            border_radius=8,
            expand=True,
            on_change=self.filtrar_tiempo_real
        )
        
        self.dd_estado = ft.Dropdown(
            label="Estado",
            options=[
                ft.dropdown.Option("todos", "Todos los estados"),
                ft.dropdown.Option("planificada", "Planificada"),
                ft.dropdown.Option("en_transito", "En Tránsito"),
                ft.dropdown.Option("en_aduana", "En Aduana"),
                ft.dropdown.Option("completada", "Completada"),
            ],
            value="todos",
            filled=True,
            border_radius=8,
            width=200,
            on_change=self.filtrar_tiempo_real
        )
        
        # Contador
        self.txt_contador = ft.Text(
            f"{self.total_registros} importaciones encontradas",
            size=14, 
            color=ImportacionesTheme.TEXT_SECONDARY
        )
        
        # Contenedor de tabla
        self.contenedor_tabla = ft.Container(
            content=self.crear_data_table(self.todas_importaciones) if self.todas_importaciones else self.crear_vista_vacia()
        )
        
        # Controles de paginación
        self.txt_pagina_actual = ft.Text(
            f"Página {self.pagina_actual} de {self.total_paginas}",
            size=14, 
            weight=ft.FontWeight.BOLD
        )
        
        self.btn_primera = ft.IconButton(
            icon=ft.Icons.FIRST_PAGE,
            tooltip="Primera página",
            on_click=lambda e: self.ir_a_pagina(1),
            disabled=self.pagina_actual <= 1
        )
        self.btn_anterior = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            tooltip="Página anterior",
            on_click=lambda e: self.ir_a_pagina(self.pagina_actual - 1),
            disabled=self.pagina_actual <= 1
        )
        self.btn_siguiente = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            tooltip="Página siguiente",
            on_click=lambda e: self.ir_a_pagina(self.pagina_actual + 1),
            disabled=self.pagina_actual >= self.total_paginas
        )
        self.btn_ultima = ft.IconButton(
            icon=ft.Icons.LAST_PAGE,
            tooltip="Última página",
            on_click=lambda e: self.ir_a_pagina(self.total_paginas),
            disabled=self.pagina_actual >= self.total_paginas
        )
        self.txt_total_registros = ft.Text(
            f"Total: {self.total_registros} registros", 
            size=12, 
            color=ImportacionesTheme.TEXT_SECONDARY
        )
        
        self.controles_paginacion = ft.Row([
            self.btn_primera,
            self.btn_anterior,
            ft.Container(width=8),
            self.txt_pagina_actual,
            ft.Container(width=8),
            self.btn_siguiente,
            self.btn_ultima,
            ft.Container(width=24),
            self.txt_total_registros,
        ], alignment=ft.MainAxisAlignment.CENTER)
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.FOLDER, size=24, color=ImportacionesTheme.STATUS_CONFIRMED),
                                ft.Text("Importaciones", size=20, 
                                    weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                            ], spacing=12),
                            ft.Text("Gestiona tus folders de importación", 
                                size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                        ]),
                        ft.Row([
                            ft.ElevatedButton(
                                "Importar Excel",
                                icon=ft.Icons.UPLOAD_FILE,
                                on_click=lambda _: self.file_picker.pick_files(
                                    allow_multiple=False,
                                    allowed_extensions=["csv", "xlsx", "xls"]
                                ),
                                style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color="white")
                            ),
                            ft.ElevatedButton(
                                "Nueva Importación",
                                icon=ft.Icons.ADD,
                                on_click=lambda e: self.page.go("/importaciones/nueva"),
                                style=ft.ButtonStyle(bgcolor=ImportacionesTheme.STATUS_CONFIRMED, color="white")
                            ),
                        ], spacing=12),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.only(bottom=24)
                ),
                
                # Filtros
                ft.Container(
                    content=ft.Row([
                        self.txt_busqueda,
                        self.dd_estado,
                        ft.ElevatedButton(
                            "Limpiar",
                            icon=ft.Icons.FILTER_ALT_OFF,
                            on_click=self.limpiar_filtros,
                            style=ft.ButtonStyle(
                                bgcolor=ImportacionesTheme.BORDER,
                                color=ImportacionesTheme.TEXT_PRIMARY
                            )
                        )
                    ], spacing=12),
                    padding=ft.padding.only(bottom=16)
                ),
                
                # Tabla
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            self.txt_contador,
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.Icons.REFRESH,
                                tooltip="Actualizar",
                                on_click=self.refrescar_datos
                            )
                        ]),
                        ft.Container(height=16),
                        self.contenedor_tabla,
                    ]),
                    bgcolor=ImportacionesTheme.BG_SECONDARY,
                    border_radius=12,
                    padding=24,
                    border=ft.border.all(1, ImportacionesTheme.BORDER),
                ),
                
                # Paginación
                ft.Container(
                    content=self.controles_paginacion,
                    padding=ft.padding.symmetric(vertical=16),
                ),
                
            ], scroll=ft.ScrollMode.AUTO),
            padding=24,
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )
    
    def ir_a_pagina(self, pagina):
        """Navegar a una página específica"""
        if pagina < 1:
            pagina = 1
        if pagina > self.total_paginas:
            pagina = self.total_paginas
        
        self.pagina_actual = pagina
        
        # Obtener filtros actuales
        texto = self.txt_busqueda.value.strip() if self.txt_busqueda and self.txt_busqueda.value else ""
        estado = self.dd_estado.value if self.dd_estado and self.dd_estado.value else "todos"
        
        # Cargar página
        self.todas_importaciones = self.cargar_importaciones(
            pagina=pagina,
            limite=self.items_por_pagina,
            filtro_texto=texto,
            filtro_estado=estado
        )
        
        # Actualizar UI
        self.actualizar_tabla(self.todas_importaciones)
        self.actualizar_controles_paginacion()
    
    def filtrar_tiempo_real(self, e=None):
        """Filtra con paginación - vuelve a página 1"""
        self.pagina_actual = 1
        
        texto = self.txt_busqueda.value.strip() if self.txt_busqueda and self.txt_busqueda.value else ""
        estado = self.dd_estado.value if self.dd_estado and self.dd_estado.value else "todos"
        
        self.todas_importaciones = self.cargar_importaciones(
            pagina=1,
            limite=self.items_por_pagina,
            filtro_texto=texto,
            filtro_estado=estado
        )
        
        self.actualizar_tabla(self.todas_importaciones)
        self.actualizar_controles_paginacion()
        
    def actualizar_controles_paginacion(self):
        """Actualizar estado de controles de paginación"""
        if self.txt_pagina_actual:
            self.txt_pagina_actual.value = f"Página {self.pagina_actual} de {self.total_paginas}"
        
        if self.txt_total_registros:
            self.txt_total_registros.value = f"Total: {self.total_registros} registros"
        
        if self.txt_contador:
            self.txt_contador.value = f"{self.total_registros} importaciones encontradas"
        
        # Actualizar estado de botones
        if self.btn_primera:
            self.btn_primera.disabled = self.pagina_actual <= 1
        if self.btn_anterior:
            self.btn_anterior.disabled = self.pagina_actual <= 1
        if self.btn_siguiente:
            self.btn_siguiente.disabled = self.pagina_actual >= self.total_paginas
        if self.btn_ultima:
            self.btn_ultima.disabled = self.pagina_actual >= self.total_paginas
        
        self.page.update()

    def procesar_archivo_excel(self, e: ft.FilePickerResultEvent):
        """Maneja el archivo seleccionado y ejecuta el procesador"""
        if not e.files:
            return

        archivo = e.files[0]
        
        # Feedback visual de carga
        loading_dialog = ft.AlertDialog(
            modal=True,
            content=ft.Row([
                ft.ProgressRing(),
                ft.Text(f" Procesando {archivo.name}...", size=16)
            ], alignment=ft.MainAxisAlignment.CENTER, height=100),
        )
        self.page.dialog = loading_dialog
        loading_dialog.open = True
        self.page.update()

        try:
            # 1. Leer bytes del archivo
            with open(archivo.path, "rb") as f:
                file_bytes = f.read()

            # 2. Instanciar procesador
            processor = ExcelImportacionesProcessor(self.db)

            # 3. Procesar
            resultado = processor.process_and_save_to_db(file_bytes, archivo.name)

            # 4. Cerrar loading
            loading_dialog.open = False
            self.page.update()

            # 5. Mostrar resultados
            if resultado['success']:
                self.mostrar_resumen_importacion(resultado)
                self.refrescar_datos(None) # Actualizar tabla
            else:
                self.mostrar_mensaje_error(resultado['message'])

        except Exception as ex:
            if loading_dialog.open:
                loading_dialog.open = False
                self.page.update()
            self.mostrar_mensaje_error(f"Error crítico: {str(ex)}")

    def mostrar_resumen_importacion(self, resultado):
        """Muestra un modal con el resumen de lo importado"""
        
        # Construir lista de errores/advertencias si existen
        lista_errores = []
        if resultado.get('errors'):
            lista_errores = [
                ft.Text(f"⚠️ {err}", size=12, color=ft.Colors.RED_400) 
                for err in resultado['errors']
            ]

        content = ft.Column([
            ft.Text("Proceso Completado", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
            ft.Divider(),
            ft.Row([
                ft.Icon(ft.Icons.FOLDER_COPY, color=ft.Colors.BLUE),
                ft.Text(f"Importaciones creadas: {resultado['importaciones_insertadas']}")
            ]),
            ft.Row([
                ft.Icon(ft.Icons.LINK, color=ft.Colors.ORANGE),
                ft.Text(f"POs vinculadas: {resultado['pos_vinculadas']}")
            ]),
            ft.Row([
                ft.Icon(ft.Icons.SEARCH, color=ft.Colors.GREY),
                ft.Text(f"Total encontrados en Excel: {resultado['total_importaciones_found']}")
            ]),
            ft.Divider(),
            ft.Text("Advertencias:", visible=len(lista_errores)>0, weight=ft.FontWeight.BOLD),
            *lista_errores
        ], tight=True, width=400)

        resumen_dialog = ft.AlertDialog(
            title=ft.Text("Resumen de Importación"),
            content=content,
            actions=[
                ft.TextButton("Entendido", on_click=lambda e: self.page.close(resumen_dialog))
            ],
        )
        self.page.open(resumen_dialog)

    def refrescar_datos(self, e):
        """Refresca manteniendo página y filtros actuales"""
        texto = self.txt_busqueda.value.strip() if self.txt_busqueda and self.txt_busqueda.value else ""
        estado = self.dd_estado.value if self.dd_estado and self.dd_estado.value else "todos"
        
        self.todas_importaciones = self.cargar_importaciones(
            pagina=self.pagina_actual,
            limite=self.items_por_pagina,
            filtro_texto=texto,
            filtro_estado=estado
        )
        
        self.actualizar_tabla(self.todas_importaciones)
        self.actualizar_controles_paginacion()
        
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("✅ Datos actualizados", color="white"),
            bgcolor=ImportacionesTheme.SUCCESS,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def cargar_importaciones(self, pagina=1, limite=25, filtro_texto="", filtro_estado="todos"):
        """Cargar importaciones con paginación y filtros SQL"""
        offset = (pagina - 1) * limite
        
        # Construir WHERE dinámico
        where_clauses = ["1=1"]
        params = []
        
        if filtro_texto:
            where_clauses.append("(i.numero_importacion LIKE %s OR i.descripcion LIKE %s)")
            params.extend([f"%{filtro_texto}%", f"%{filtro_texto}%"])
        
        if filtro_estado and filtro_estado != "todos":
            where_clauses.append("i.estado = %s")
            params.append(filtro_estado)
        
        where_sql = " AND ".join(where_clauses)
        
        # Contar total para paginación
        count_query = f"""
            SELECT COUNT(DISTINCT i.id) as total
            FROM importaciones i
            WHERE {where_sql}
        """
        count_result = self.db.execute_query(count_query, tuple(params) if params else None)
        self.total_registros = count_result[0]['total'] if count_result else 0
        self.total_paginas = max(1, (self.total_registros + limite - 1) // limite)
        
        # Consulta principal con LIMIT
        query = f"""
            SELECT 
                i.id,
                i.numero_importacion,
                i.descripcion,
                i.estado,
                i.fecha_creacion,
                i.fecha_embarque,
                i.total_fob_importacion,
                COUNT(DISTINCT ip.po_id) as cantidad_pos
            FROM importaciones i
            LEFT JOIN importacion_pos ip ON i.id = ip.importacion_id
            WHERE {where_sql}
            GROUP BY i.id
            ORDER BY i.fecha_creacion DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limite, offset])
        
        return self.db.execute_query(query, tuple(params)) or []

    def crear_filtros(self):
        """Crear controles de filtrado simples"""
        return ft.Row([
            ft.TextField(
                label="Buscar importaciones",
                hint_text="Por número, descripción...",
                prefix_icon=ft.Icons.SEARCH,
                filled=True,
                border_radius=8,
                expand=True,
                on_change=self.on_buscar_change
            ),
            ft.Dropdown(
                label="Estado",
                options=[
                    ft.dropdown.Option("todos", "Todos los estados"),
                    ft.dropdown.Option("planificada", "Planificada"),
                    ft.dropdown.Option("en_transito", "En Tránsito"),
                    ft.dropdown.Option("en_aduana", "En Aduana"),
                    ft.dropdown.Option("completada", "Completada"),
                ],
                value="todos",
                filled=True,
                border_radius=8,
                width=200,
                on_change=self.on_estado_change
            ),
            ft.ElevatedButton(
                "Filtrar",
                icon=ft.Icons.FILTER_LIST,
                on_click=self.aplicar_filtros,
                style=ft.ButtonStyle(
                    bgcolor=ImportacionesTheme.TEXT_SECONDARY,
                    color="white"
                )
            ),
            ft.ElevatedButton(
                "Limpiar",
                icon=ft.Icons.FILTER_ALT_OFF,
                on_click=self.limpiar_filtros,
                style=ft.ButtonStyle(
                    bgcolor=ImportacionesTheme.BORDER,
                    color=ImportacionesTheme.TEXT_PRIMARY
                )
            )
        ], spacing=12)
    
    def crear_data_table(self, importaciones):
        """Crear DataTable con las filas"""
        rows = [self.crear_data_row(imp) for imp in importaciones]
        
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("N° Importación", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Descripción", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Estado", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Fecha Creación", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("POs", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Valor FOB", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Acciones", weight=ft.FontWeight.BOLD)),
            ],
            rows=rows,
            heading_row_color=ImportacionesTheme.BG_SECONDARY,
            data_row_color={"hovered": "0x30" + ImportacionesTheme.STATUS_CONFIRMED[1:]},
            show_checkbox_column=False,
        )
    
    def crear_data_row(self, importacion):
        """Crear una DataRow para la tabla"""
        estado_colors = {
            'planificada': ImportacionesTheme.STATUS_DRAFT,
            'en_transito': ImportacionesTheme.STATUS_IN_TRANSIT,
            'en_aduana': ImportacionesTheme.STATUS_IN_CUSTOMS,
            'completada': ImportacionesTheme.STATUS_COMPLETED,
            'cancelada': ImportacionesTheme.ERROR,
        }
        
        estado = importacion.get('estado', 'planificada')
        estado_color = estado_colors.get(estado, ImportacionesTheme.TEXT_SECONDARY)
        
        badge_pos = ft.Container(
            content=ft.Text(
                str(importacion.get('cantidad_pos', 0)),
                size=12,
                color="white",
                weight=ft.FontWeight.BOLD
            ),
            bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            border_radius=12,
            alignment=ft.alignment.center,
        )
        
        badge_estado = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CIRCLE, size=8, color=estado_color),
                ft.Text(estado.replace('_', ' ').title(), size=12, color=estado_color)
            ], spacing=6),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            bgcolor=f"{estado_color}15",
            border_radius=8,
            border=ft.border.all(1, estado_color)
        )
        
        acciones = ft.Row([
            ft.IconButton(
                icon=ft.Icons.VISIBILITY,
                icon_size=18,
                icon_color=ImportacionesTheme.TEXT_SECONDARY,
                tooltip="Ver detalle",
                on_click=lambda e, id=importacion['id']: self.page.go(f"/importaciones/{id}")
            ),
            ft.PopupMenuButton(
                icon=ft.Icons.MORE_VERT,
                icon_size=18,
                icon_color=ImportacionesTheme.TEXT_SECONDARY,
                tooltip="Opciones",
                items=[
                    ft.PopupMenuItem(
                        text="Editar",
                        icon=ft.Icons.EDIT,
                        on_click=lambda e, id=importacion['id']: self.page.go(f"/importaciones/{id}/editar")
                    ),
                    ft.PopupMenuItem(
                        text="Agregar POs",
                        icon=ft.Icons.ADD_SHOPPING_CART,
                        on_click=lambda e, id=importacion['id']: self.agregar_pos(id)
                    ),
                    ft.PopupMenuItem(
                        text="Asignar DUA",
                        icon=ft.Icons.DESCRIPTION,
                        on_click=lambda e, id=importacion['id']: self.registrar_dua(id)
                    ),
                    ft.PopupMenuItem(),
                    ft.PopupMenuItem(
                        text="Eliminar",
                        icon=ft.Icons.DELETE,
                        on_click=lambda e, imp=importacion: self.mostrar_modal_confirmacion_eliminar(imp)
                    ),
                ]
            )
        ], spacing=0)
        
        return ft.DataRow(
            cells=[
                ft.DataCell(
                    ft.Text(
                        importacion.get('numero_importacion', ''),
                        weight=ft.FontWeight.BOLD,
                        color=ImportacionesTheme.TEXT_PRIMARY
                    ),
                    on_tap=lambda e, id=importacion['id']: self.page.go(f"/importaciones/{id}")
                ),
                ft.DataCell(
                    ft.Text(
                        importacion.get('descripcion', 'Sin descripción'),
                        color=ImportacionesTheme.TEXT_PRIMARY
                    )
                ),
                ft.DataCell(badge_estado),
                ft.DataCell(
                    ft.Text(
                        format_date(importacion.get('fecha_creacion', '')) if importacion.get('fecha_creacion') else "-",
                        color=ImportacionesTheme.TEXT_SECONDARY
                    )
                ),
                ft.DataCell(badge_pos),
                ft.DataCell(
                    ft.Text(
                        format_currency(importacion.get('total_fob_importacion', 0)),
                        color=ImportacionesTheme.TEXT_PRIMARY,
                        weight=ft.FontWeight.BOLD
                    )
                ),
                ft.DataCell(acciones),
            ],
            on_select_changed=lambda e, id=importacion['id']: self.page.go(f"/importaciones/{id}")
        )
    
    def crear_vista_vacia(self):
        """Crear vista cuando no hay importaciones"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.FOLDER_OPEN, size=64, color=ImportacionesTheme.TEXT_SECONDARY),
                ft.Container(height=16),
                ft.Text("No hay importaciones registradas", 
                       size=16, weight=ft.FontWeight.BOLD,
                       color=ImportacionesTheme.TEXT_PRIMARY),
                ft.Text("Crea tu primera importación para comenzar a agrupar POs", 
                       size=14, color=ImportacionesTheme.TEXT_SECONDARY),
                ft.Container(height=24),
                ft.ElevatedButton(
                    "Crear primera importación",
                    icon=ft.Icons.ADD,
                    on_click=lambda e: self.page.go("/importaciones/nueva"),
                    style=ft.ButtonStyle(
                        bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                        color="white"
                    )
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=40,
            alignment=ft.alignment.center
        )
    
    def on_buscar_change(self, e):
        """Manejador para cambio en búsqueda"""
        pass
    
    def on_estado_change(self, e):
        """Manejador para cambio en estado"""
        pass
    
    def aplicar_filtros(self, e):
        """Aplicar filtros"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("Filtros aplicados", color="white"),
            bgcolor=ImportacionesTheme.SUCCESS,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def limpiar_filtros(self, e):
        """Limpiar filtros y volver a página 1"""
        if self.txt_busqueda:
            self.txt_busqueda.value = ""
        if self.dd_estado:
            self.dd_estado.value = "todos"
        
        self.pagina_actual = 1
        self.todas_importaciones = self.cargar_importaciones(pagina=1, limite=self.items_por_pagina)
        
        self.actualizar_tabla(self.todas_importaciones)
        self.actualizar_controles_paginacion()
        
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("Filtros limpiados", color="white"),
            bgcolor=ImportacionesTheme.INFO,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def actualizar_vista(self):
        """Actualizar la vista"""
        self.page.go("/importaciones")
    
    def agregar_pos(self, importacion_id):
        """Agregar POs a importación"""
        self.page.go(f"/importaciones/{importacion_id}/agregar-pos")
    
    # ==================== MODAL DUA - CORREGIDO ====================
    
    def registrar_dua(self, importacion_id):
        """Registrar DUA para importación - ABRE MODAL"""
        self.current_importacion_id = importacion_id
        self.selected_dua_id = None
        duas = self.cargar_duas_disponibles()
        self.abrir_modal_dua(duas)
    
    def cargar_duas_disponibles(self):
        """Cargar DUAs disponibles"""
        query = """
            SELECT d.id, d.dua_number, d.registration_date, d.customs_agency, 
                   d.status, d.fob_value_usd
            FROM dua_documents d
            WHERE d.importacion_id IS NULL OR d.importacion_id = 0
            ORDER BY d.registration_date DESC
        """
        return self.db.execute_query(query) or []
    
    def abrir_modal_dua(self, duas):
        """Abrir modal para seleccionar DUA"""
        if not duas:
            content = self._crear_contenido_sin_duas()
        else:
            content = self._crear_contenido_con_duas(duas)
        
        self.modal_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.DESCRIPTION, color=ImportacionesTheme.STATUS_CONFIRMED, size=28),
                ft.Container(width=12),
                ft.Text("Asignar DUA a Importación", weight=ft.FontWeight.BOLD, size=18)
            ]),
            content=ft.Container(content=content, width=600, padding=10),
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(self.modal_dialog)
        self.modal_dialog.open = True
        self.page.update()
    
    def _crear_contenido_sin_duas(self):
        """Contenido cuando no hay DUAs"""
        return ft.Column([
            ft.Container(height=20),
            ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=64, color=ImportacionesTheme.TEXT_SECONDARY),
            ft.Container(height=16),
            ft.Text("No hay DUAs disponibles", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(height=24),
            ft.Row([
                ft.ElevatedButton("Cerrar", on_click=self.cerrar_modal),
                ft.Container(width=12),
                ft.ElevatedButton("Crear nueva DUA", icon=ft.Icons.ADD, 
                    on_click=lambda e: self.ir_a_crear_dua(),
                    style=ft.ButtonStyle(bgcolor=ImportacionesTheme.STATUS_CONFIRMED, color="white")),
            ], alignment=ft.MainAxisAlignment.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    def _crear_contenido_con_duas(self, duas):
        """Contenido con lista de DUAs"""
        self.radio_group = ft.RadioGroup(
            content=ft.Column([self._crear_fila_dua(dua) for dua in duas], 
                spacing=8, scroll=ft.ScrollMode.AUTO, height=250),
            on_change=self.on_dua_selected
        )
        
        self.btn_guardar_modal = ft.ElevatedButton(
            "Guardar", icon=ft.Icons.SAVE,
            on_click=self.asignar_dua_a_importacion,
            style=ft.ButtonStyle(bgcolor=ImportacionesTheme.STATUS_CONFIRMED, color="white"),
            disabled=True
        )
        
        return ft.Column([
            ft.Text("Selecciona una DUA:", size=14, weight=ft.FontWeight.W_500),
            ft.Container(height=16),
            self.radio_group,
            ft.Container(height=20),
            ft.Row([
                ft.ElevatedButton("Cancelar", on_click=self.cerrar_modal),
                ft.Container(expand=True),
                self.btn_guardar_modal,
            ]),
        ])
    
    def _crear_fila_dua(self, dua):
        """Crear fila para DUA"""
        fob_value = float(dua.get('fob_value_usd') or 0)
        fecha = format_date(dua.get('registration_date')) if dua.get('registration_date') else 'Sin fecha'
        
        return ft.Container(
            content=ft.Row([
                ft.Radio(value=str(dua['id'])),
                ft.Text(dua['dua_number'], weight=ft.FontWeight.BOLD, width=120),
                ft.Text(fecha, width=100, color=ImportacionesTheme.TEXT_SECONDARY),
                ft.Text(dua.get('customs_agency') or 'Sin agencia', expand=True),
                ft.Text(f"${fob_value:,.2f}", width=100, weight=ft.FontWeight.BOLD),
            ], spacing=8),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=8,
            on_click=lambda e, dua_id=str(dua['id']): self._seleccionar_dua_por_click(dua_id),
        )
    
    def _seleccionar_dua_por_click(self, dua_id):
        if self.radio_group:
            self.radio_group.value = dua_id
            self.selected_dua_id = int(dua_id)
            if self.btn_guardar_modal:
                self.btn_guardar_modal.disabled = False
            self.page.update()
    
    def on_dua_selected(self, e):
        if e.control.value:
            self.selected_dua_id = int(e.control.value)
            if self.btn_guardar_modal:
                self.btn_guardar_modal.disabled = False
                self.page.update()

    def asignar_dua_a_importacion(self, e):
        if not self.selected_dua_id or not self.current_importacion_id:
            return
        
        try:
            query = "UPDATE dua_documents SET importacion_id = %s WHERE id = %s"
            self.db.execute_query(query, (self.current_importacion_id, self.selected_dua_id), fetch=False)
            self.cerrar_modal(e)
            self.mostrar_mensaje_exito("✅ DUA asignada correctamente")
            self.page.go(f"/importaciones/{self.current_importacion_id}")
        except Exception as ex:
            self.mostrar_mensaje_error(f"Error: {str(ex)}")
    
    def ir_a_crear_dua(self):
        self.cerrar_modal()
        self.page.go(f"/dua/nuevo?importacion_id={self.current_importacion_id}")
    
    def cerrar_modal(self, e=None):
        if self.modal_dialog:
            self.modal_dialog.open = False
            if self.modal_dialog in self.page.overlay:
                self.page.overlay.remove(self.modal_dialog)
            self.page.update()
        self.selected_dua_id = None
        self.current_importacion_id = None
        self.modal_dialog = None

    def mostrar_mensaje_exito(self, mensaje):
        """Mostrar mensaje de éxito"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje, color="white", weight=ft.FontWeight.BOLD),
            bgcolor=ImportacionesTheme.SUCCESS,
            duration=3000,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def mostrar_mensaje_error(self, mensaje):
        """Mostrar mensaje de error"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje, color="white"),
            bgcolor=ImportacionesTheme.ERROR,
            duration=4000,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def eliminar_importacion(self, importacion_id):
        """Método mantenido por compatibilidad - ahora usa modal"""
        # Buscar la importación para mostrar en modal
        query = """
            SELECT i.*, COUNT(ip.po_id) as cantidad_pos
            FROM importaciones i
            LEFT JOIN importacion_pos ip ON i.id = ip.importacion_id
            WHERE i.id = %s
            GROUP BY i.id
        """
        result = self.db.execute_query(query, (importacion_id,))
        
        if result:
            self.mostrar_modal_confirmacion_eliminar(result[0])
        else:
            self.mostrar_mensaje_error("No se encontró la importación")

    
    def mostrar_modal_confirmacion_eliminar(self, importacion):
        self.importacion_a_eliminar = importacion
        
        self.dialog_eliminar_importacion = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING, color=ImportacionesTheme.WARNING),
                ft.Text("Confirmar Eliminación", weight=ft.FontWeight.BOLD),
            ], spacing=12),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("¿Eliminar la importación:", size=14),
                    ft.Container(height=8),
                    ft.Text(f"📦 {importacion['numero_importacion']}", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(f"📝 {importacion.get('descripcion', 'Sin descripción')}", size=13),
                    ft.Container(height=16),
                    ft.Container(
                        content=ft.Text("⚠️ Esta acción eliminará las asociaciones con POs.", 
                            size=12, color=ImportacionesTheme.WARNING, weight=ft.FontWeight.BOLD),
                        bgcolor=f"{ImportacionesTheme.WARNING}20",
                        padding=12,
                        border_radius=8,
                    ),
                ], tight=True, spacing=4),
                width=450,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self.cerrar_modal_eliminar_importacion),
                ft.ElevatedButton("Eliminar", icon=ft.Icons.DELETE_FOREVER,
                    on_click=self.eliminar_importacion_confirmado,
                    style=ft.ButtonStyle(bgcolor=ImportacionesTheme.ERROR, color="white")),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.open(self.dialog_eliminar_importacion)

    def limpiar_estado_eliminar(self):
        """Limpia el estado después de cerrar modal"""
        self.importacion_a_eliminar = None
        self.dialog_eliminar_importacion = None
    

    def eliminar_importacion_confirmado(self, e):
        if not self.importacion_a_eliminar:
            if self.dialog_eliminar_importacion:
                self.page.close(self.dialog_eliminar_importacion)
            return
        
        importacion_id = self.importacion_a_eliminar['id']
        numero = self.importacion_a_eliminar['numero_importacion']
        
        try:
            self.db.execute_query("DELETE FROM importacion_pos WHERE importacion_id = %s", (importacion_id,), fetch=False)
            self.db.execute_query("UPDATE dua_documents SET importacion_id = NULL WHERE importacion_id = %s", (importacion_id,), fetch=False)
            self.db.execute_query("UPDATE shipping_documents SET importacion_id = NULL WHERE importacion_id = %s", (importacion_id,), fetch=False)
            self.db.execute_query("DELETE FROM importaciones WHERE id = %s", (importacion_id,), fetch=False)
            
            if self.dialog_eliminar_importacion:
                self.page.close(self.dialog_eliminar_importacion)
            
            self.importacion_a_eliminar = None
            self.dialog_eliminar_importacion = None
            
            # ⭐ Actualizar datos y refiltrar
            self.todas_importaciones = self.cargar_importaciones()
            self.filtrar_tiempo_real()
            
            self.mostrar_mensaje_exito(f"✅ Importación {numero} eliminada")
            
        except Exception as ex:
            if self.dialog_eliminar_importacion:
                self.page.close(self.dialog_eliminar_importacion)
            self.importacion_a_eliminar = None
            self.dialog_eliminar_importacion = None
            self.mostrar_mensaje_error(f"Error: {str(ex)}")

    def filtrar_tiempo_real(self, e=None):
        """Filtra las importaciones en tiempo real"""
        texto_busqueda = self.txt_busqueda.value.lower().strip() if self.txt_busqueda.value else ""
        estado_filtro = self.dd_estado.value if self.dd_estado.value else "todos"
        
        # Filtrar importaciones
        importaciones_filtradas = []
        for imp in self.todas_importaciones:
            # Filtro por texto (número o descripción)
            coincide_texto = True
            if texto_busqueda:
                numero = (imp.get('numero_importacion') or '').lower()
                descripcion = (imp.get('descripcion') or '').lower()
                coincide_texto = texto_busqueda in numero or texto_busqueda in descripcion
            
            # Filtro por estado
            coincide_estado = True
            if estado_filtro != "todos":
                coincide_estado = imp.get('estado') == estado_filtro
            
            if coincide_texto and coincide_estado:
                importaciones_filtradas.append(imp)
        
        # Actualizar tabla
        self.actualizar_tabla(importaciones_filtradas)

    def cerrar_modal_eliminar_importacion(self, e=None):
        """Cierra el modal de eliminación"""
        if self.dialog_eliminar_importacion:
            self.page.close(self.dialog_eliminar_importacion)
        self.limpiar_estado_eliminar()

    def actualizar_tabla_importaciones(self):
        """Actualiza la tabla de importaciones sin recargar toda la página"""
        try:
            print(f"[DEBUG] Actualizando tabla de importaciones...")
            
            # 1. Recargar importaciones
            nuevas_importaciones = self.cargar_importaciones()
            print(f"[DEBUG] {len(nuevas_importaciones)} importaciones cargadas")
            
            # 2. Buscar el contenedor de la tabla en la página
            main_content = self.page.controls[0].content.content
            
            # Asumiendo que la estructura es: Container > Column > [header, filtros, card]
            # Y dentro del card hay un Column con la tabla
            for control in main_content.controls:
                if isinstance(control, ft.Container) and hasattr(control, 'content'):
                    if isinstance(control.content, ft.Column):
                        # Buscar el DataTable dentro del card
                        for child in control.content.controls:
                            if isinstance(child, ft.DataTable):
                                # Reemplazar filas
                                child.rows = [self.crear_data_row(imp) for imp in nuevas_importaciones]
                                print(f"[DEBUG] Tabla actualizada con {len(child.rows)} filas")
                                break
            
            # 3. Si no hay importaciones, mostrar vista vacía
            if not nuevas_importaciones:
                for control in main_content.controls:
                    if isinstance(control, ft.Container) and hasattr(control, 'content'):
                        if isinstance(control.content, ft.Column):
                            # Buscar el contenedor de la tabla
                            for i, child in enumerate(control.content.controls):
                                if isinstance(child, ft.DataTable):
                                    # Reemplazar DataTable por vista vacía
                                    control.content.controls[i] = self.crear_vista_vacia()
                                    print(f"[DEBUG] Mostrando vista vacía")
                                    break
            
            # 4. Actualizar página
            self.page.update()
            
        except Exception as ex:
            print(f"[ERROR] Error actualizando tabla: {ex}")
            # Fallback: recargar página
            self.page.go("/importaciones")
    def actualizar_tabla(self, importaciones):
        """Actualiza la tabla con las importaciones filtradas"""
        # Actualizar contador
        self.txt_contador.value = f"{len(importaciones)} importaciones encontradas"
        
        # Actualizar contenido de la tabla
        if importaciones:
            self.contenedor_tabla.content = self.crear_data_table(importaciones)
        else:
            self.contenedor_tabla.content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.SEARCH_OFF, size=48, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Container(height=16),
                    ft.Text("No se encontraron importaciones", 
                           size=16, weight=ft.FontWeight.BOLD,
                           color=ImportacionesTheme.TEXT_PRIMARY),
                    ft.Text("Intenta con otros criterios de búsqueda", 
                           size=14, color=ImportacionesTheme.TEXT_SECONDARY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=40,
                alignment=ft.alignment.center
            )
        
        self.page.update()

    def _obtener_color_estado(self, estado):
        """Obtener color según estado (método auxiliar)"""
        colores = {
            'planificada': ImportacionesTheme.STATUS_DRAFT,
            'en_transito': ImportacionesTheme.STATUS_IN_TRANSIT,
            'en_aduana': ImportacionesTheme.STATUS_IN_CUSTOMS,
            'completada': ImportacionesTheme.STATUS_COMPLETED,
            'cancelada': ImportacionesTheme.ERROR,
        }
        return colores.get(estado, ImportacionesTheme.TEXT_SECONDARY)
    