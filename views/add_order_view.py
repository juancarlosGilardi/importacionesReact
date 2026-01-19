# views/agregar_pos_view.py - VERSIÓN LIMPIA (SOLO DISPONIBLES Y SELECCIONADAS)
import flet as ft
from config_importaciones import ImportacionesTheme, format_currency, format_date

class AddOrderView:
    """Vista simplificada para agregar Órdenes de Compra a una importación"""
    
    def __init__(self, page: ft.Page, db, importacion_id: int):
        self.page = page
        self.db = db
        self.importacion_id = importacion_id
        self.importacion_data = {}
        
        # Diccionarios para tracking
        self.pos_disponibles_dict = {}      # POs libres (sin asignar a ninguna importación)
        self.pos_seleccionadas_dict = {}    # POs asignadas a ESTA importación
        
        # Referencias a controles que se actualizarán dinámicamente
        self.tabla_seleccionadas_container = ft.Container()
        self.tabla_disponibles_container = ft.Container()
        
        # Estadísticas
        self.stat_seleccionadas_text = ft.Text("0", size=28, weight=ft.FontWeight.BOLD, 
                                                color=ImportacionesTheme.SUCCESS)
        self.stat_disponibles_text = ft.Text("0", size=28, weight=ft.FontWeight.BOLD, 
                                              color=ImportacionesTheme.INFO)
        self.stat_total_fob_text = ft.Text("$0.00", size=20, weight=ft.FontWeight.BOLD, 
                                            color=ImportacionesTheme.STATUS_COMPLETED)
        
        # Tabs
        self.tabs_control = None
        
        # Footer resumen
        self.resumen_text = ft.Text("", size=14, weight=ft.FontWeight.BOLD, 
                                     color=ImportacionesTheme.TEXT_PRIMARY)
        
        # Botón guardar
        self.btn_guardar = ft.ElevatedButton(
            "💾 Guardar Cambios",
            icon=ft.Icons.SAVE,
            on_click=self.guardar_pos,
            style=ft.ButtonStyle(
                bgcolor=ImportacionesTheme.SUCCESS,
                color="white",
                padding=ft.padding.symmetric(horizontal=20, vertical=12)
            )
        )
        
        # Cargar datos iniciales
        self.cargar_datos()
    
    def cargar_datos(self):
        """Cargar datos de la importación y POs"""
        # Cargar datos de la importación
        query = "SELECT id, numero_importacion, descripcion FROM importaciones WHERE id = %s"
        result = self.db.execute_query(query, (self.importacion_id,))
        if result:
            self.importacion_data = result[0]
        
        # Cargar las POs
        self.cargar_listas_pos()
    
    def cargar_listas_pos(self):
        """Cargar POs seleccionadas y disponibles"""
        # Limpiar diccionarios
        self.pos_disponibles_dict = {}
        self.pos_seleccionadas_dict = {}
        
        # 1. Cargar POs ya seleccionadas para ESTA importación
        query_seleccionadas = """
            SELECT 
                po.id,
                po.po_number,
                po.order_date,
                po.total_fob,
                s.business_name as supplier_name,
                po.status
            FROM purchase_orders po
            LEFT JOIN suppliers s ON po.supplier_id = s.id
            JOIN importacion_pos ip ON po.id = ip.po_id AND ip.importacion_id = %s
            WHERE po.status IN ('confirmada', 'en_transito', 'en_aduana', 'prorrateado', 'en_almacen', 'completada')
            ORDER BY po.order_date DESC
        """
        pos_seleccionadas = self.db.execute_query(query_seleccionadas, (self.importacion_id,)) or []
        
        for po in pos_seleccionadas:
            self.pos_seleccionadas_dict[po['id']] = dict(po)
        
        # 2. Cargar POs disponibles (NO asignadas a NINGUNA importación)
        query_disponibles = """
            SELECT 
                po.id,
                po.po_number,
                po.order_date,
                po.total_fob,
                s.business_name as supplier_name,
                po.status
            FROM purchase_orders po
            LEFT JOIN suppliers s ON po.supplier_id = s.id
            WHERE po.status IN ('confirmada', 'en_transito', 'en_aduana', 'prorrateado', 'en_almacen')
            AND po.id NOT IN (
                SELECT po_id FROM importacion_pos
            )
            ORDER BY po.order_date DESC
        """
        pos_disponibles = self.db.execute_query(query_disponibles, ()) or []
        
        for po in pos_disponibles:
            self.pos_disponibles_dict[po['id']] = dict(po)
    
    def vista_principal(self):
        """Vista principal con dos tablas organizadas"""
        
        # Actualizar contenido inicial de las tablas
        self.actualizar_contenido_tablas()
        self.actualizar_estadisticas()
        
        # Crear tabs (SOLO 2: Seleccionadas y Disponibles)
        self.tabs_control = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text=f"✅ Seleccionadas ({len(self.pos_seleccionadas_dict)})",
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "Estas POs están asignadas a esta importación. Haz clic en ❌ para quitarlas.",
                                size=13,
                                color=ImportacionesTheme.TEXT_SECONDARY,
                                italic=True
                            ),
                            ft.Container(height=12),
                            self.tabla_seleccionadas_container,
                        ], scroll=ft.ScrollMode.AUTO),
                        padding=20,
                    ),
                ),
                ft.Tab(
                    text=f"📦 Disponibles ({len(self.pos_disponibles_dict)})",
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "POs sin asignar. Haz clic en ➕ para agregarlas a esta importación.",
                                size=13,
                                color=ImportacionesTheme.TEXT_SECONDARY,
                                italic=True
                            ),
                            ft.Container(height=12),
                            self.tabla_disponibles_container,
                        ], scroll=ft.ScrollMode.AUTO),
                        padding=20,
                    ),
                ),
            ],
            expand=True,
        )
        
        return ft.Container(
            content=ft.Column([
                # 1. Parte superior con SCROLL
                ft.Column([
                    self._crear_header(),
                    self._crear_panel_estadisticas(),
                    self.tabs_control,
                ], scroll=ft.ScrollMode.AUTO, expand=True), # Solo esto hace scroll
                
                ft.Divider(),
                
                # 2. BOTÓN FIJO (Siempre visible al final)
                self._crear_footer(), # Esto ya no se moverá al hacer scroll
                
            ], expand=True),
            padding=24,
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )
    
    def _crear_header(self):
        """Crear el header de la vista"""
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color=ImportacionesTheme.TEXT_SECONDARY,
                        on_click=lambda e: self.page.go("/importaciones")
                    ),
                    ft.Column([
                        ft.Text("📦 Asignar POs a Importación", size=22, 
                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                        ft.Row([
                            ft.Container(
                                content=ft.Text(
                                    self.importacion_data.get('numero_importacion', ''),
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=ImportacionesTheme.STATUS_CONFIRMED
                                ),
                                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                bgcolor=f"{ImportacionesTheme.STATUS_CONFIRMED}20",
                                border_radius=8,
                            ),
                            ft.Text(
                                self.importacion_data.get('descripcion', ''),
                                size=13, 
                                color=ImportacionesTheme.TEXT_SECONDARY,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS
                            ),
                        ], spacing=8),
                    ], spacing=2)
                ], spacing=8),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(bottom=20)
        )
    
    def _crear_panel_estadisticas(self):
        """Crear panel de estadísticas simplificado"""
        return ft.Container(
            content=ft.ResponsiveRow([
                # Seleccionadas
                ft.Column([
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.CHECK_CIRCLE, size=20, color=ImportacionesTheme.SUCCESS),
                                ft.Text("Seleccionadas", size=14, weight=ft.FontWeight.BOLD),
                            ], spacing=8),
                            ft.Container(height=4),
                            self.stat_seleccionadas_text,
                        ]),
                        padding=16,
                        bgcolor=ImportacionesTheme.BG_SECONDARY,
                        border_radius=12,
                        border=ft.border.all(1, ImportacionesTheme.SUCCESS),
                    )
                ], col={"xs": 12, "md": 4}), # Ajustado ancho
                
                # Disponibles
                ft.Column([
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.INVENTORY_2, size=20, color=ImportacionesTheme.INFO),
                                ft.Text("Disponibles", size=14, weight=ft.FontWeight.BOLD),
                            ], spacing=8),
                            ft.Container(height=4),
                            self.stat_disponibles_text,
                        ]),
                        padding=16,
                        bgcolor=ImportacionesTheme.BG_SECONDARY,
                        border_radius=12,
                        border=ft.border.all(1, ImportacionesTheme.INFO),
                    )
                ], col={"xs": 6, "md": 4}), # Ajustado ancho
                
                # Total FOB
                ft.Column([
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.ATTACH_MONEY, size=20, color=ImportacionesTheme.STATUS_COMPLETED),
                                ft.Text("Total FOB", size=14, weight=ft.FontWeight.BOLD),
                            ], spacing=8),
                            ft.Container(height=4),
                            self.stat_total_fob_text,
                        ]),
                        padding=16,
                        bgcolor=ImportacionesTheme.BG_SECONDARY,
                        border_radius=12,
                        border=ft.border.all(1, ImportacionesTheme.STATUS_COMPLETED),
                    )
                ], col={"xs": 6, "md": 4}), # Ajustado ancho
            ], spacing=12, run_spacing=12),
            padding=ft.padding.only(bottom=20)
        )
    
    def _crear_footer(self):
        """Crear footer con resumen y botones"""
        self.actualizar_resumen_text()
        
        return ft.Container(
            content=ft.Row([
                self.resumen_text,
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Cancelar",
                    icon=ft.Icons.CANCEL,
                    on_click=lambda e: self.page.go("/importaciones"),
                    style=ft.ButtonStyle(
                        bgcolor=ImportacionesTheme.TEXT_SECONDARY,
                        color="white",
                        padding=ft.padding.symmetric(horizontal=16, vertical=10)
                    )
                ),
                self.btn_guardar,
            ]),
            padding=ft.padding.symmetric(vertical=16, horizontal=20),
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
        )
    
    def actualizar_contenido_tablas(self):
        """Actualizar el contenido de las tablas"""
        # Tabla de seleccionadas
        if self.pos_seleccionadas_dict:
            self.tabla_seleccionadas_container.content = self._crear_tabla_seleccionadas()
        else:
            self.tabla_seleccionadas_container.content = self._crear_vista_vacia(
                "No hay POs seleccionadas para esta importación",
                ft.Icons.REMOVE_SHOPPING_CART
            )
        
        # Tabla de disponibles
        if self.pos_disponibles_dict:
            self.tabla_disponibles_container.content = self._crear_tabla_disponibles()
        else:
            self.tabla_disponibles_container.content = self._crear_vista_vacia(
                "No hay más POs disponibles",
                ft.Icons.INVENTORY_2
            )
    
    def actualizar_estadisticas(self):
        """Actualizar las estadísticas mostradas"""
        self.stat_seleccionadas_text.value = str(len(self.pos_seleccionadas_dict))
        self.stat_disponibles_text.value = str(len(self.pos_disponibles_dict))
        self.stat_total_fob_text.value = format_currency(self._calcular_total_fob())
    
    def actualizar_resumen_text(self):
        """Actualizar el texto del resumen"""
        total = len(self.pos_seleccionadas_dict)
        fob = format_currency(self._calcular_total_fob())
        self.resumen_text.value = f"📊 Total: {total} POs seleccionadas • {fob}"
    
    def actualizar_tabs_titles(self):
        """Actualizar los títulos de las pestañas con los contadores"""
        if self.tabs_control and self.tabs_control.tabs:
            self.tabs_control.tabs[0].text = f"✅ Seleccionadas ({len(self.pos_seleccionadas_dict)})"
            self.tabs_control.tabs[1].text = f"📦 Disponibles ({len(self.pos_disponibles_dict)})"
    
    def _calcular_total_fob(self):
        """Calcular el total FOB de las POs seleccionadas"""
        total = 0
        for po_data in self.pos_seleccionadas_dict.values():
            total += float(po_data.get('total_fob', 0) or 0)
        return total
    
    def _crear_tabla_seleccionadas(self):
        """Crear tabla de POs seleccionadas"""
        rows = []
        
        for po_id, po_data in self.pos_seleccionadas_dict.items():
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Row([
                                ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=ImportacionesTheme.SUCCESS),
                                ft.Text(po_data.get('po_number', ''), weight=ft.FontWeight.BOLD),
                            ], spacing=8)
                        ),
                        ft.DataCell(ft.Text(po_data.get('supplier_name', '') or 'Sin proveedor')),
                        ft.DataCell(ft.Text(format_date(po_data.get('order_date')))),
                        ft.DataCell(
                            ft.Text(
                                format_currency(po_data.get('total_fob', 0)),
                                weight=ft.FontWeight.BOLD,
                                color=ImportacionesTheme.SUCCESS
                            )
                        ),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.Icons.REMOVE_CIRCLE,
                                icon_color=ImportacionesTheme.ERROR,
                                icon_size=24,
                                tooltip="Quitar de esta importación",
                                on_click=lambda e, pid=po_id: self.quitar_po_seleccionada(pid)
                            )
                        ),
                    ],
                )
            )
        
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("N° PO", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Proveedor", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Fecha", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Valor FOB", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Acción", weight=ft.FontWeight.BOLD)),
            ],
            rows=rows,
            heading_row_color=ImportacionesTheme.BG_SECONDARY,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
            border_radius=8,
            column_spacing=30,
            heading_row_height=48,
            data_row_max_height=56,
        )
    
    def _crear_tabla_disponibles(self):
        """Crear tabla de POs disponibles"""
        rows = []
        
        for po_id, po_data in self.pos_disponibles_dict.items():
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Text(po_data.get('po_number', ''), weight=ft.FontWeight.BOLD)
                        ),
                        ft.DataCell(ft.Text(po_data.get('supplier_name', '') or 'Sin proveedor')),
                        ft.DataCell(ft.Text(format_date(po_data.get('order_date')))),
                        ft.DataCell(ft.Text(format_currency(po_data.get('total_fob', 0)))),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.Icons.ADD_CIRCLE,
                                icon_color=ImportacionesTheme.SUCCESS,
                                icon_size=24,
                                tooltip="Agregar a esta importación",
                                on_click=lambda e, pid=po_id: self.agregar_po_disponible(pid)
                            )
                        ),
                    ],
                )
            )
        
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("N° PO", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Proveedor", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Fecha", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Valor FOB", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Acción", weight=ft.FontWeight.BOLD)),
            ],
            rows=rows,
            heading_row_color=ImportacionesTheme.BG_SECONDARY,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
            border_radius=8,
            column_spacing=30,
            heading_row_height=48,
            data_row_max_height=56,
        )
    
    def _crear_vista_vacia(self, mensaje, icono):
        """Crear vista cuando no hay datos"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(icono, size=48, color=ImportacionesTheme.TEXT_SECONDARY),
                ft.Container(height=12),
                ft.Text(mensaje, color=ImportacionesTheme.TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=40,
            alignment=ft.alignment.center,
        )
    
    def agregar_po_disponible(self, po_id):
        """Mover una PO de disponibles a seleccionadas"""
        if po_id in self.pos_disponibles_dict:
            # Mover de disponibles a seleccionadas
            po_data = self.pos_disponibles_dict.pop(po_id)
            self.pos_seleccionadas_dict[po_id] = po_data
            
            # Actualizar toda la UI
            self._refrescar_ui_completa()
            
            # Mostrar feedback
            self.mostrar_mensaje(
                f"✅ PO {po_data.get('po_number', '')} agregada",
                ImportacionesTheme.SUCCESS
            )
    
    def quitar_po_seleccionada(self, po_id):
        """Mover una PO de seleccionadas a disponibles"""
        if po_id in self.pos_seleccionadas_dict:
            # Mover de seleccionadas a disponibles
            po_data = self.pos_seleccionadas_dict.pop(po_id)
            self.pos_disponibles_dict[po_id] = po_data
            
            # Actualizar toda la UI
            self._refrescar_ui_completa()
            
            # Mostrar feedback
            self.mostrar_mensaje(
                f"❌ PO {po_data.get('po_number', '')} removida",
                ImportacionesTheme.WARNING
            )
    
    def _refrescar_ui_completa(self):
        """Refrescar todos los elementos de la UI"""
        # Actualizar contenido de las tablas
        self.actualizar_contenido_tablas()
        
        # Actualizar estadísticas
        self.actualizar_estadisticas()
        
        # Actualizar resumen
        self.actualizar_resumen_text()
        
        # Actualizar títulos de tabs
        self.actualizar_tabs_titles()
        
        # Actualizar la página
        self.page.update()
    
    def guardar_pos(self, e):
        self.btn_guardar.disabled = True
        self.btn_guardar.text = "⏳ Guardando..."
        self.page.update()
        
        try:
            # 1. Limpiar asignaciones previas
            delete_query = "DELETE FROM importacion_pos WHERE importacion_id = %s"
            self.db.execute_query(delete_query, (self.importacion_id,), fetch=False)
            
            # 2. Insertar las nuevas POs seleccionadas
            insert_count = 0
            for po_id in self.pos_seleccionadas_dict.keys():
                query = "INSERT INTO importacion_pos (importacion_id, po_id) VALUES (%s, %s)"
                self.db.execute_query(query, (self.importacion_id, po_id), fetch=False)
                insert_count += 1
                print(f"🔗 DEBUG: Vinculando PO ID {po_id} a Importación {self.importacion_id}")

            # 3. Actualizar totales en la tabla de importaciones
            self.actualizar_totales_importacion()

            # 4. ¡LA CLAVE! Confirmar la transacción en la base de datos
            if hasattr(self.db.connection, 'commit'):
                self.db.connection.commit()
                print("✅ COMMIT: Cambios guardados permanentemente en la BD.")

            self.mostrar_mensaje(
                f"✅ {insert_count} POs vinculadas correctamente",
                ImportacionesTheme.SUCCESS
            )
            
            import time
            time.sleep(0.5)
            self.page.go("/importaciones")
            
        except Exception as ex:
            # Si algo falla, deshacemos para no dejar datos corruptos
            if hasattr(self.db.connection, 'rollback'):
                self.db.connection.rollback()
                
            print(f"❌ ERROR al guardar: {str(ex)}")
            self.mostrar_mensaje(f"❌ Error al guardar: {str(ex)}", ImportacionesTheme.ERROR)
            self.btn_guardar.disabled = False
            self.btn_guardar.text = "💾 Guardar Cambios"
            self.page.update()


    def actualizar_totales_importacion(self):
        """Actualizar los totales de la importación"""
        query = """
            UPDATE importaciones i
            SET total_fob_importacion = (
                SELECT COALESCE(SUM(po.total_fob), 0)
                FROM purchase_orders po
                JOIN importacion_pos ip ON po.id = ip.po_id
                WHERE ip.importacion_id = i.id
            )
            WHERE i.id = %s
        """
        self.db.execute_query(query, (self.importacion_id,), fetch=False)
    
    def mostrar_mensaje(self, mensaje, color):
        """Mostrar mensaje de snackbar"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje, color="white", weight=ft.FontWeight.BOLD),
            bgcolor=color,
            show_close_icon=True,
            duration=2000,
        )
        self.page.snack_bar.open = True
        self.page.update()


