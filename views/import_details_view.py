# views/import_details_view.py - Vista detallada de importación (CORREGIDO)
import flet as ft
from datetime import datetime
from config_importaciones import ImportacionesTheme, format_currency, format_date
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import tempfile
import os
import threading
import time
import pandas as pd
from io import BytesIO

class ImportDetailsView:
    """Vista detallada de una importación con todas sus POs y documentos asociados"""
    
    def __init__(self, page: ft.Page, db, importacion_id: int):
        self.page = page
        self.db = db
        self.importacion_id = importacion_id
        self.importacion_data = {}
        self.pos_asociadas = []
        self.dua_asociada = None
        self.documentos_transporte = []
        self.error_carga = None  # Para manejar errores de carga
        
        # Cargar datos iniciales
        self._cargar_datos_completos()
    
    # ==================== CARGA DE DATOS ====================
    
    def _cargar_datos_completos(self):
        """Cargar todos los datos de la importación de forma ordenada"""
        try:
            self._cargar_importacion()
            
            if self.importacion_data:
                self._cargar_pos_asociadas()
                self._cargar_dua()
                self._cargar_documentos_transporte()
                
        except Exception as e:
            self.error_carga = str(e)
            print(f"❌ Error cargando datos de importación: {e}")
    
    def _cargar_importacion(self):
        """Cargar datos básicos de la importación"""
        # Query sin la tabla users (la removemos por ahora)
        query = """
            SELECT 
                i.*,
                COUNT(DISTINCT ip.po_id) as cantidad_pos,
                COALESCE(SUM(po.total_fob), 0) as total_fob_importacion
            FROM importaciones i
            LEFT JOIN importacion_pos ip ON i.id = ip.importacion_id
            LEFT JOIN purchase_orders po ON ip.po_id = po.id
            WHERE i.id = %s
            GROUP BY i.id
        """
        result = self.db.execute_query(query, (self.importacion_id,))
        
        if result:
            self.importacion_data = result[0]
            print(f"✅ Importación #{self.importacion_id} cargada")
        else:
            print(f"⚠️ No se encontró importación con ID: {self.importacion_id}")
            self.importacion_data = {}
    
    def _cargar_pos_asociadas(self):
        """Cargar POs asociadas a la importación (CORREGIDO: Sin duplicados)"""
        try:
            # ✅ CORRECCIÓN: Agregado DISTINCT para evitar duplicados
            query = """
                SELECT DISTINCT
                    po.id,
                    po.po_number,
                    po.order_date,
                    po.status,
                    po.total_fob,
                    po.incoterm,
                    po.expected_arrival,
                    po.currency_id,
                    s.business_name as supplier_name,
                    ip.porcentaje_participacion,
                    ip.peso_total,
                    ip.volumen_total
                FROM purchase_orders po
                JOIN importacion_pos ip ON po.id = ip.po_id
                LEFT JOIN suppliers s ON po.supplier_id = s.id
                WHERE ip.importacion_id = %s
                GROUP BY po.id  -- ✅ GROUP BY adicional para garantizar unicidad
                ORDER BY po.order_date DESC
            """
            
            self.pos_asociadas = self.db.execute_query(query, (self.importacion_id,)) or []
            
            # ✅ CORRECCIÓN ADICIONAL: Eliminar duplicados en Python por si acaso
            seen_ids = set()
            pos_unicas = []
            for po in self.pos_asociadas:
                if po['id'] not in seen_ids:
                    seen_ids.add(po['id'])
                    po['supplier_country'] = 'N/A'
                    pos_unicas.append(po)
            
            self.pos_asociadas = pos_unicas
            print(f"✅ {len(self.pos_asociadas)} POs cargadas (sin duplicados)")

        except Exception as e:
            print(f"❌ Error cargando POs: {e}")
            self.pos_asociadas = []
            
            
    def _cargar_pos_simple_emergencia(self):
        """Carga alternativa simple por si falla el JOIN con proveedores"""
        try:
            query = """
                SELECT 
                    po.id,
                    po.po_number,
                    po.order_date,
                    po.status,
                    po.total_fob,
                    'Proveedor Desc.' as supplier_name,
                    '' as supplier_country
                FROM purchase_orders po
                JOIN importacion_pos ip ON po.id = ip.po_id
                WHERE ip.importacion_id = %s
            """
            self.pos_asociadas = self.db.execute_query(query, (self.importacion_id,)) or []
            print(f"✅ POs cargadas en modo emergencia: {len(self.pos_asociadas)}")
        except Exception as ex:
            print(f"❌ Error final cargando POs: {ex}")
            self.pos_asociadas = []        
    def _cargar_dua(self):
        """Cargar DUA asociada si existe"""
        query = """
            SELECT *
            FROM dua_documents
            WHERE importacion_id = %s
            LIMIT 1
        """
        result = self.db.execute_query(query, (self.importacion_id,))
        self.dua_asociada = result[0] if result else None
        
        if self.dua_asociada:
            print(f"✅ DUA {self.dua_asociada.get('dua_number')} cargada")
    
    def _cargar_documentos_transporte(self):
        """Cargar documentos de transporte"""
        query = """
            SELECT 
                sd.*,
                CASE sd.document_type
                    WHEN 'bill_of_lading' THEN 'Bill of Lading'
                    WHEN 'air_waybill' THEN 'Air Waybill'
                    WHEN 'carta_porte' THEN 'Carta Porte'
                    ELSE 'Otro'
                END as document_type_label
            FROM shipping_documents sd
            WHERE sd.importacion_id = %s
            ORDER BY sd.etd_date DESC
        """
        self.documentos_transporte = self.db.execute_query(query, (self.importacion_id,)) or []
        print(f"✅ {len(self.documentos_transporte)} documentos de transporte cargados")

    # ==================== VISTA PRINCIPAL ====================
    
    def vista_detallada(self):
        """Renderizar la vista detallada con tabs organizadas"""
        
        # Si hubo error de carga, mostrar vista de error
        if self.error_carga or not self.importacion_data:
            return self._crear_vista_error()
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    self._crear_header(),
                    self._crear_tarjetas_resumen(),
                    ft.Container(height=16),
                    self._crear_tabs(),
                    ft.Container(height=20),
                    self._crear_botones_accion(),
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True
            ),
            padding=24,
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )
    
    def _crear_vista_error(self):
        """Vista cuando hay error al cargar los datos"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color=ImportacionesTheme.TEXT_SECONDARY,
                        on_click=lambda e: self.page.go("/importaciones")
                    ),
                    ft.Container(height=40),
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color=ImportacionesTheme.ERROR),
                    ft.Container(height=16),
                    ft.Text(
                        "No se pudo cargar la importación",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ImportacionesTheme.TEXT_PRIMARY
                    ),
                    ft.Text(
                        self.error_carga or f"Importación #{self.importacion_id} no encontrada",
                        size=14,
                        color=ImportacionesTheme.TEXT_SECONDARY
                    ),
                    ft.Container(height=24),
                    ft.ElevatedButton(
                        "Volver a importaciones",
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda e: self.page.go("/importaciones"),
                        style=ft.ButtonStyle(
                            bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                            color="white"
                        )
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=40,
            alignment=ft.alignment.center,
            expand=True,
        )
    
    def _crear_tabs(self):
        """Crear las tabs principales"""
        return ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="📋 Resumen",
                    content=self._crear_tab_resumen(),
                ),
                ft.Tab(
                    text=f"📦 POs ({len(self.pos_asociadas)})",
                    content=self._crear_tab_pos(),
                ),
                ft.Tab(
                    text="📄 Documentos",
                    content=self._crear_tab_documentos(),
                ),
                ft.Tab(
                    text="📊 Costos",
                    content=self._crear_tab_costos(),
                ),
            ],
            expand=True,
        )

    # ==================== HEADER ====================
    
    def _crear_header(self):
        """Crear header con navegación e información principal"""
        estado = self.importacion_data.get('estado', 'planificada')
        estado_color = self._obtener_color_estado(estado)
        
        badge_estado = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CIRCLE, size=10, color=estado_color),
                    ft.Text(estado.replace('_', ' ').title(), size=12, color=estado_color),
                ],
                spacing=6
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            bgcolor=f"{estado_color}20",
            border_radius=8,
            border=ft.border.all(1, estado_color)
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                icon_color=ImportacionesTheme.TEXT_SECONDARY,
                                on_click=lambda e: self.page.go("/importaciones")
                            ),
                            ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text(
                                                "📦 Detalles de Importación",
                                                size=22,
                                                weight=ft.FontWeight.BOLD,
                                                color=ImportacionesTheme.TEXT_PRIMARY
                                            ),
                                            badge_estado,
                                        ],
                                        spacing=12
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Container(
                                                content=ft.Text(
                                                    self.importacion_data.get('numero_importacion', 'N/A'),
                                                    size=16,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=ImportacionesTheme.STATUS_CONFIRMED
                                                ),
                                                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                                bgcolor=f"{ImportacionesTheme.STATUS_CONFIRMED}20",
                                                border_radius=8,
                                            ),
                                            ft.Text(
                                                self.importacion_data.get('descripcion', 'Sin descripción'),
                                                size=14,
                                                color=ImportacionesTheme.TEXT_SECONDARY,
                                                max_lines=1,
                                                overflow=ft.TextOverflow.ELLIPSIS
                                            ),
                                        ],
                                        spacing=8
                                    ),
                                ],
                                spacing=4,
                                expand=True
                            ),
                            self._crear_menu_acciones(),
                        ]
                    ),
                ]
            ),
            padding=ft.padding.only(bottom=20)
        )
    
    def _crear_menu_acciones(self):
        """Crear menú de acciones del header"""
        return ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT,
            items=[
                ft.PopupMenuItem(
                    text="Editar",
                    icon=ft.Icons.EDIT,
                    on_click=lambda e: self.page.go(f"/importaciones/{self.importacion_id}/editar")
                ),
                ft.PopupMenuItem(
                    text="Agregar más POs",
                    icon=ft.Icons.ADD_SHOPPING_CART,
                    on_click=lambda e: self.page.go(f"/importaciones/{self.importacion_id}/agregar-pos")
                ),
                ft.PopupMenuItem(),
                ft.PopupMenuItem(text="Exportar PDF", icon=ft.Icons.PICTURE_AS_PDF),
                ft.PopupMenuItem(text="Imprimir", icon=ft.Icons.PRINT),
            ]
        )

    # ==================== TARJETAS RESUMEN ====================
    
    def _crear_tarjetas_resumen(self):
        """Crear tarjetas de resumen rápido"""
        return ft.ResponsiveRow(
            controls=[
                self._tarjeta_resumen_item(
                    "POs Asociadas",
                    str(len(self.pos_asociadas)),
                    ImportacionesTheme.INFO,
                    ft.Icons.INVENTORY_2,
                    col={"xs": 6, "md": 3}
                ),
                self._tarjeta_resumen_item(
                    "Valor FOB Total",
                    format_currency(self.importacion_data.get('total_fob_importacion', 0)),
                    ImportacionesTheme.SUCCESS,
                    ft.Icons.ATTACH_MONEY,
                    col={"xs": 6, "md": 3}
                ),
                self._tarjeta_resumen_item(
                    "Transporte",
                    self.importacion_data.get('via_transporte', 'N/A').replace('_', ' ').title(),
                    ImportacionesTheme.STATUS_IN_TRANSIT,
                    ft.Icons.LOCAL_SHIPPING,
                    col={"xs": 6, "md": 3}
                ),
                self._tarjeta_resumen_item(
                    "DUA",
                    self.dua_asociada['dua_number'] if self.dua_asociada else "Sin asignar",
                    ImportacionesTheme.STATUS_CONFIRMED if self.dua_asociada else ImportacionesTheme.TEXT_SECONDARY,
                    ft.Icons.DESCRIPTION,
                    col={"xs": 6, "md": 3}
                ),
            ],
            spacing=12,
            run_spacing=12
        )
    
    def _tarjeta_resumen_item(self, titulo: str, valor: str, color: str, icono, col: dict):
        """Crear un item de tarjeta de resumen"""
        return ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(icono, size=20, color=color),
                                    ft.Text(titulo, size=14, weight=ft.FontWeight.BOLD),
                                ],
                                spacing=8
                            ),
                            ft.Container(height=4),
                            ft.Text(
                                valor,
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=color
                            ),
                        ]
                    ),
                    padding=16,
                    bgcolor=ImportacionesTheme.BG_SECONDARY,
                    border_radius=12,
                    border=ft.border.all(1, color),
                )
            ],
            col=col
        )

    # ==================== TAB RESUMEN ====================
    
    def _crear_tab_resumen(self):
        """Crear tab de resumen general"""
        controles = [
            ft.Text(
                "Información General",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ImportacionesTheme.TEXT_PRIMARY
            ),
            ft.Container(height=8),
        ]
        
        # Agregar notas si existen
        if self.importacion_data.get('notas'):
            controles.append(self._crear_seccion_notas())
        
        controles.extend([
            ft.Container(height=24),
            ft.ResponsiveRow(
                controls=[
                    ft.Column([self._crear_info_transporte()], col={"md": 4}),
                    ft.Column([self._crear_info_fechas()], col={"md": 4}),
                    ft.Column([self._crear_info_agentes()], col={"md": 4}),
                ],
                spacing=16,
                run_spacing=16
            ),
            ft.Container(height=24),
            self._crear_info_actualizacion(),
        ])
        
        return ft.Container(
            content=ft.Column(controls=controles, scroll=ft.ScrollMode.AUTO),
            padding=20,
        )
    
    def _crear_seccion_notas(self):
        """Crear sección de notas"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("📝 Notas:", size=14, weight=ft.FontWeight.BOLD),
                    ft.Container(height=4),
                    ft.Text(
                        self.importacion_data['notas'],
                        size=13,
                        color=ImportacionesTheme.TEXT_SECONDARY
                    ),
                ]
            ),
            padding=12,
            bgcolor=f"{ImportacionesTheme.INFO}10",
            border_radius=8,
            border=ft.border.all(1, ImportacionesTheme.INFO),
        )
    
    def _crear_info_transporte(self):
        """Crear información de transporte"""
        return ft.Column(
            controls=[
                self._list_tile(
                    ft.Icons.LOCAL_SHIPPING,
                    ImportacionesTheme.STATUS_IN_TRANSIT,
                    "Tipo de Transporte",
                    self.importacion_data.get('via_transporte', 'N/A').replace('_', ' ').title()
                ),
                self._list_tile(
                    ft.Icons.NUMBERS,
                    ImportacionesTheme.TEXT_SECONDARY,
                    "BL Number",
                    self.importacion_data.get('bl_number') or 'No especificado'
                ),
                self._list_tile(
                    ft.Icons.INVENTORY_2,
                    ImportacionesTheme.TEXT_SECONDARY,
                    "Contenedor",
                    self.importacion_data.get('container_number') or 'No especificado'
                ),
            ]
        )
    
    def _crear_info_fechas(self):
        """Crear información de fechas"""
        return ft.Column(
            controls=[
                self._list_tile(
                    ft.Icons.DATE_RANGE,
                    ImportacionesTheme.STATUS_CONFIRMED,
                    "Fecha de Creación",
                    self._formatear_fecha(self.importacion_data.get('fecha_creacion'))
                ),
                self._list_tile(
                    ft.Icons.FLIGHT_TAKEOFF,
                    ImportacionesTheme.STATUS_IN_TRANSIT,
                    "Fecha de Embarque (ETD)",
                    self._formatear_fecha(self.importacion_data.get('fecha_embarque'))
                ),
                self._list_tile(
                    ft.Icons.FLIGHT_LAND,
                    ImportacionesTheme.SUCCESS,
                    "Fecha Estimada Arribo (ETA)",
                    self._formatear_fecha(self.importacion_data.get('fecha_arribo_estimada'))
                ),
            ]
        )
    
    def _crear_info_agentes(self):
        """Crear información de agentes"""
        return ft.Column(
            controls=[
                self._list_tile(
                    ft.Icons.BUSINESS,
                    ImportacionesTheme.INFO,
                    "Agente Aduanero",
                    self.importacion_data.get('agente_aduanero') or 'No especificado'
                ),
                self._list_tile(
                    ft.Icons.LOCAL_SHIPPING,
                    ImportacionesTheme.INFO,
                    "Agente de Carga",
                    self.importacion_data.get('agente_carga') or 'No especificado'
                ),
            ]
        )
    
    def _crear_info_actualizacion(self):
        """Crear información de última actualización"""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.UPDATE, size=16, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Text(
                        f"Última actualización: {self._formatear_fecha(self.importacion_data.get('updated_at'))}",
                        size=12,
                        color=ImportacionesTheme.TEXT_SECONDARY
                    ),
                ],
                spacing=8
            ),
            padding=ft.padding.symmetric(vertical=8),
        )

    # ==================== TAB POs ====================
    
    def _crear_tab_pos(self):
        """Crear tab con la lista de POs asociadas"""
        if not self.pos_asociadas:
            return self._crear_vista_vacia(
                "No hay POs asociadas a esta importación",
                ft.Icons.REMOVE_SHOPPING_CART,
                "Agregar POs",
                lambda e: self.page.go(f"/importaciones/{self.importacion_id}/agregar-pos")
            )
        
        rows = [self._crear_fila_po(po) for po in self.pos_asociadas]
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"{len(self.pos_asociadas)} POs asociadas",
                                size=14,
                                color=ImportacionesTheme.TEXT_SECONDARY
                            ),
                            ft.ElevatedButton(
                                "🔄 Calcular Prorrateo",
                                icon=ft.Icons.CALCULATE,
                                on_click=self._abrir_modal_prorrateo,
                                style=ft.ButtonStyle(bgcolor=ImportacionesTheme.SUCCESS, color="white")
                            ),
                        ], spacing=12
                    ),
                    
                    ft.Container(height=12),
                    ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("N° PO", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("Proveedor", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("Fecha", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("Estado", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("Valor FOB", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("Acciones", weight=ft.FontWeight.BOLD)),
                        ],
                        rows=rows,
                        heading_row_color=ImportacionesTheme.BG_SECONDARY,
                        data_row_color={"hovered": f"0x30{ImportacionesTheme.STATUS_CONFIRMED[1:]}"},
                        border=ft.border.all(1, ImportacionesTheme.BORDER),
                        border_radius=8,
                        column_spacing=20,
                    ),
                ],
                scroll=ft.ScrollMode.AUTO
            ),
            padding=20,
        )
    
    def _crear_fila_po(self, po: dict):
        """Crear fila para una PO (CORREGIDO: 6 celdas para 6 columnas)"""
        estado_color = self._obtener_color_estado_po(po.get('status'))
        po_id = po.get('id')
        estado = po.get('status', 'pendiente')

        # Lógica del botón de almacén/prorrateo
        if estado == 'prorrateado':
            accion_boton = ft.IconButton(
                icon=ft.Icons.INVENTORY,
                icon_color=ImportacionesTheme.SUCCESS,
                tooltip="Ingresar esta orden al Almacén",
                on_click=lambda _: self.page.go(f"/almacen/ingreso/{po['id']}")
            )
        elif estado == 'en_almacen':
            # Acción: Puede estar en transición a 'completed'
            accion_boton = ft.Icon(
                ft.Icons.WAREHOUSE, 
                color=ImportacionesTheme.INFO, 
                tooltip="Ya se encuentra en Almacén"
            )
        else:
            accion_boton = ft.Icon(ft.Icons.LOCK_CLOCK, color=ft.Colors.GREY_400, tooltip="Primero debes aplicar el prorrateo")
            
        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(po.get('po_number', ''), weight=ft.FontWeight.BOLD)),
                ft.DataCell(
                    ft.Column(
                        controls=[
                            ft.Text(po.get('supplier_name', 'Sin proveedor'), size=13),
                            ft.Text(po.get('supplier_country', ''), size=11, color=ImportacionesTheme.TEXT_SECONDARY),
                        ],
                        spacing=2
                    )
                ),
                ft.DataCell(ft.Text(self._formatear_fecha(po.get('order_date')))),
                ft.DataCell(
                    ft.Container(
                        content=ft.Text(
                            (po.get('status') or 'N/A').replace('_', ' ').title(),
                            size=12, color=estado_color, weight=ft.FontWeight.BOLD
                        ),
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        bgcolor=f"{estado_color}15",
                        border_radius=6,
                        border=ft.border.all(1, estado_color),
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        format_currency(po.get('total_fob', 0)),
                        weight=ft.FontWeight.BOLD, color=ImportacionesTheme.SUCCESS
                    )
                ),
                # CELDA 6: Aquí consolidamos todos los botones de acción
                ft.DataCell(
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.VISIBILITY_OUTLINED, 
                            on_click=lambda _: self.page.go(f"/po/{po['id']}")
                        ),
                        accion_boton,
                        ft.IconButton(
                            icon=ft.Icons.OPEN_IN_NEW,
                            icon_size=18,
                            icon_color=ImportacionesTheme.TEXT_SECONDARY,
                            tooltip="Ver detalles de la PO",
                            on_click=lambda e, pid=po_id: self.page.go(f"/ordenes/{pid}")
                        )
                    ], spacing=0)
                ),
            ],
            on_select_changed=lambda e, pid=po_id: self.page.go(f"/ordenes/{pid}")
        )
    # ==================== TAB DOCUMENTOS ====================
    
    def _crear_tab_documentos(self):
        """Crear tab de documentos (DUA, BL, etc.)"""
        controles = []
        
        # DUA
        if self.dua_asociada:
            controles.append(self._crear_tarjeta_dua())
        else:
            controles.append(self._crear_vista_dua_vacia())
        
        # Documentos de transporte
        if self.documentos_transporte:
            controles.append(self._crear_tarjeta_documentos_transporte())
        else:
            controles.append(self._crear_vista_transporte_vacia())
        
        # Documentos adjuntos
        # controles.append(self._crear_tarjeta_documentos_adjuntos())
        
        return ft.Container(
            content=ft.Column(controls=controles, scroll=ft.ScrollMode.AUTO, spacing=16),
            padding=20,
        )

    # ==================== TAB COSTOS (CORREGIDO) ====================
    
    def _crear_tab_costos(self):
        """Crear tab de análisis de costos detallado"""
        total_fob = self._safe_float(self.importacion_data.get('total_fob_importacion', 0))
        
        controles = [
            ft.Text(
                "Resumen de Costos",
                size=18,
                weight=ft.FontWeight.BOLD,
                color=ImportacionesTheme.TEXT_PRIMARY
            ),
            ft.Container(height=16),
        ]
        
        if self.dua_asociada:
            controles.extend(self._crear_contenido_costos_con_dua(total_fob))
        else:
            controles.append(
                self._crear_vista_vacia(
                    "Análisis de costos no disponible",
                    ft.Icons.CALCULATE_OUTLINED,
                    "Asignar DUA",
                    lambda e: self.page.go(f"/importaciones/{self.importacion_id}/asignar-dua")
                )
            )
        
        # Notas de costos
        if self.importacion_data.get('notas'):
            controles.append(self._crear_notas_costos())
        
        return ft.Container(
            content=ft.Column(controls=controles, scroll=ft.ScrollMode.AUTO, spacing=16),
            padding=20,
        )
    
    def _crear_contenido_costos_con_dua(self, total_fob: float) -> list:
        """Crear contenido de costos cuando hay DUA"""
        controles = []
        
        cif_value = self._safe_float(self.dua_asociada.get('cif_value_usd', 0))
        total_taxes = self._safe_float(self.dua_asociada.get('total_taxes', 0))
        total_customs_expenses = self._safe_float(self.dua_asociada.get('total_customs_expenses', 0))
        total_import = cif_value + total_taxes + total_customs_expenses
        
        # Tarjetas de resumen de costos
        controles.append(
            ft.ResponsiveRow(
                controls=[
                    self._crear_tarjeta_costo(
                        "FOB Total", total_fob, 
                        ImportacionesTheme.SUCCESS, ft.Icons.INVENTORY,
                        col={"xs": 6, "md": 3}
                    ),
                    self._crear_tarjeta_costo(
                        "CIF Total", cif_value,
                        ImportacionesTheme.INFO, ft.Icons.LOCAL_SHIPPING,
                        col={"xs": 6, "md": 3}
                    ),
                    self._crear_tarjeta_costo(
                        "Impuestos", total_taxes,
                        ImportacionesTheme.WARNING, ft.Icons.ACCOUNT_BALANCE,
                        col={"xs": 6, "md": 3}
                    ),
                    self._crear_tarjeta_costo(
                        "Gastos Aduaneros", total_customs_expenses,
                        ImportacionesTheme.STATUS_IN_CUSTOMS, ft.Icons.REQUEST_QUOTE,
                        col={"xs": 6, "md": 3}
                    ),
                ],
                spacing=12,
                run_spacing=12
            )
        )
        
        # Costo total destacado
        controles.append(
            ft.ResponsiveRow(
                controls=[
                    self._crear_tarjeta_costo(
                        "Costo Total Importación", total_import,
                        ImportacionesTheme.STATUS_COMPLETED, ft.Icons.CALCULATE,
                        col={"xs": 12, "md": 6},
                        destacado=True
                    ),
                ],
                spacing=12,
                run_spacing=12
            )
        )
        
        # Desglose de impuestos
        desglose_impuestos = self._crear_desglose_impuestos()
        if desglose_impuestos:
            controles.append(desglose_impuestos)
        
        # Desglose de gastos aduaneros
        desglose_gastos = self._crear_desglose_gastos_aduaneros()
        if desglose_gastos:
            controles.append(desglose_gastos)
        
        return controles
    
    def _crear_tarjeta_costo(self, titulo: str, valor: float, color: str, icono, 
                             col: dict, destacado: bool = False):
        """Crear tarjeta individual de costo"""
        return ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(icono, size=20, color=color),
                                    ft.Text(titulo, size=14, weight=ft.FontWeight.BOLD),
                                ],
                                spacing=8
                            ),
                            ft.Container(height=8),
                            ft.Text(
                                format_currency(valor),
                                size=24 if destacado else 20,
                                weight=ft.FontWeight.BOLD,
                                color=color
                            ),
                        ]
                    ),
                    padding=20,
                    bgcolor=ImportacionesTheme.BG_SECONDARY,
                    border_radius=12,
                    border=ft.border.all(2 if destacado else 1, color),
                )
            ],
            col=col
        )
    
    def _crear_desglose_impuestos(self):
        """Crear desglose de impuestos"""
        ad_valorem = self._safe_float(self.dua_asociada.get('ad_valorem_amount', 0))
        igv = self._safe_float(self.dua_asociada.get('igv_amount', 0))
        ipm = self._safe_float(self.dua_asociada.get('ipm_amount', 0))
        
        if ad_valorem <= 0 and igv <= 0 and ipm <= 0:
            return None
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Desglose de Impuestos", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(height=8),
                    ft.ResponsiveRow(
                        controls=[
                            self._crear_item_desglose("Ad Valorem", ad_valorem, ImportacionesTheme.WARNING),
                            self._crear_item_desglose("IGV", igv, ImportacionesTheme.WARNING),
                            self._crear_item_desglose("IPM", ipm, ImportacionesTheme.WARNING),
                        ],
                        spacing=12,
                        run_spacing=12
                    ),
                ]
            ),
            padding=16,
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
        )
    
    def _crear_desglose_gastos_aduaneros(self):
        """Crear desglose de gastos aduaneros"""
        customs_fees = self._safe_float(self.dua_asociada.get('customs_fees', 0))
        agency_fees = self._safe_float(self.dua_asociada.get('agency_fees', 0))
        storage_fees = self._safe_float(self.dua_asociada.get('storage_fees', 0))
        
        if customs_fees <= 0 and agency_fees <= 0 and storage_fees <= 0:
            return None
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Desglose de Gastos Aduaneros", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(height=8),
                    ft.ResponsiveRow(
                        controls=[
                            self._crear_item_desglose(
                                "Derechos Aduaneros", customs_fees, 
                                ImportacionesTheme.STATUS_IN_CUSTOMS
                            ),
                            self._crear_item_desglose(
                                "Honorarios Agente", agency_fees,
                                ImportacionesTheme.STATUS_IN_CUSTOMS
                            ),
                            self._crear_item_desglose(
                                "Almacenaje", storage_fees,
                                ImportacionesTheme.STATUS_IN_CUSTOMS
                            ),
                        ],
                        spacing=12,
                        run_spacing=12
                    ),
                ]
            ),
            padding=16,
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
        )
    
    def _crear_item_desglose(self, titulo: str, valor: float, color: str):
        """Crear item de desglose de costos"""
        return ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(titulo, size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                            ft.Text(
                                format_currency(valor),
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=color
                            ),
                        ]
                    ),
                    padding=12,
                    bgcolor=ImportacionesTheme.BG_SECONDARY,
                    border_radius=8,
                    border=ft.border.all(1, color),
                )
            ],
            col={"xs": 6, "md": 4}
        )
    
    def _crear_notas_costos(self):
        """Crear sección de notas de costos"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("📝 Notas de costos:", size=14, weight=ft.FontWeight.BOLD),
                    ft.Container(height=8),
                    ft.Text(self.importacion_data.get('notas', ''), size=13),
                ]
            ),
            padding=16,
            bgcolor=f"{ImportacionesTheme.INFO}10",
            border_radius=8,
            border=ft.border.all(1, ImportacionesTheme.INFO),
        )

    # ==================== TARJETAS DOCUMENTOS ====================
    
    def _crear_tarjeta_dua(self):
        """Crear tarjeta con información de DUA - Versión profesional"""
        dua = self.dua_asociada
        
        # Valores
        fob = self._safe_float(dua.get('fob_value_usd', 0))
        freight = self._safe_float(dua.get('freight_usd', 0))
        insurance = self._safe_float(dua.get('insurance_usd', 0))
        cif = self._safe_float(dua.get('cif_value_usd', 0))
        total_impuestos = self._safe_float(dua.get('total_taxes', 0))
        total_gastos = self._safe_float(dua.get('total_customs_expenses', 0))
        total_dua = cif + total_impuestos + total_gastos
        
        # Estado
        status = dua.get('status', 'registered')
        status_config = {
            'registered': ('Registrada', ImportacionesTheme.INFO),
            'in_process': ('En Proceso', ImportacionesTheme.WARNING),
            'cleared': ('Despachada', ImportacionesTheme.SUCCESS),
            'cancelled': ('Cancelada', ImportacionesTheme.ERROR),
        }
        status_label, status_color = status_config.get(status, ('--', ImportacionesTheme.TEXT_SECONDARY))
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Header con número y estado
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Icon(ft.Icons.DESCRIPTION, size=24, color="white"),
                                    padding=10,
                                    bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                                    border_radius=8,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text("DUA", size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                                        ft.Text(
                                            dua['dua_number'],
                                            size=18,
                                            weight=ft.FontWeight.BOLD,
                                            color=ImportacionesTheme.TEXT_PRIMARY
                                        ),
                                    ],
                                    spacing=0,
                                    expand=True
                                ),
                                ft.Container(
                                    content=ft.Text(status_label, size=12, color=status_color, weight=ft.FontWeight.BOLD),
                                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                    bgcolor=f"{status_color}15",
                                    border_radius=16,
                                    border=ft.border.all(1, status_color),
                                ),
                            ],
                            spacing=12
                        ),
                        padding=ft.padding.only(bottom=16),
                        border=ft.border.only(bottom=ft.BorderSide(1, ImportacionesTheme.BORDER)),
                    ),
                    
                    ft.Container(height=16),
                    
                    # Información general
                    ft.ResponsiveRow(
                        controls=[
                            ft.Column([
                                ft.Text("Agencia Aduanera", size=11, color=ImportacionesTheme.TEXT_SECONDARY),
                                ft.Text(dua.get('customs_agency') or 'N/A', size=13, weight=ft.FontWeight.W_500),
                            ], col={"xs": 6, "md": 3}, spacing=2),
                            ft.Column([
                                ft.Text("RUC Agente", size=11, color=ImportacionesTheme.TEXT_SECONDARY),
                                ft.Text(dua.get('customs_agent_ruc') or 'N/A', size=13, weight=ft.FontWeight.W_500),
                            ], col={"xs": 6, "md": 3}, spacing=2),
                            ft.Column([
                                ft.Text("Fecha Registro", size=11, color=ImportacionesTheme.TEXT_SECONDARY),
                                ft.Text(self._formatear_fecha(dua.get('registration_date')), size=13, weight=ft.FontWeight.W_500),
                            ], col={"xs": 6, "md": 3}, spacing=2),
                            ft.Column([
                                ft.Text("Fecha Despacho", size=11, color=ImportacionesTheme.TEXT_SECONDARY),
                                ft.Text(
                                    self._formatear_fecha(dua.get('clearance_date')) if dua.get('clearance_date') else 'Pendiente',
                                    size=13,
                                    weight=ft.FontWeight.W_500,
                                    color=ImportacionesTheme.SUCCESS if dua.get('clearance_date') else ImportacionesTheme.WARNING
                                ),
                            ], col={"xs": 6, "md": 3}, spacing=2),
                        ],
                        spacing=16,
                        run_spacing=12
                    ),
                    
                    ft.Container(height=20),
                    
                    # Valores FOB → CIF
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Column([
                                    ft.Text("FOB", size=11, color=ImportacionesTheme.TEXT_SECONDARY),
                                    ft.Text(format_currency(fob), size=14, weight=ft.FontWeight.BOLD),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                                ft.Text("+", color=ImportacionesTheme.TEXT_SECONDARY),
                                ft.Column([
                                    ft.Text("Flete", size=11, color=ImportacionesTheme.TEXT_SECONDARY),
                                    ft.Text(format_currency(freight), size=14, weight=ft.FontWeight.BOLD),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                                ft.Text("+", color=ImportacionesTheme.TEXT_SECONDARY),
                                ft.Column([
                                    ft.Text("Seguro", size=11, color=ImportacionesTheme.TEXT_SECONDARY),
                                    ft.Text(format_currency(insurance), size=14, weight=ft.FontWeight.BOLD),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                                ft.Text("=", color=ImportacionesTheme.TEXT_SECONDARY, weight=ft.FontWeight.BOLD),
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("CIF", size=11, color="white"),
                                        ft.Text(format_currency(cif), size=14, weight=ft.FontWeight.BOLD, color="white"),
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                                    bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                                    border_radius=8,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=16,
                        bgcolor=ImportacionesTheme.BG_PRIMARY,
                        border_radius=8,
                        border=ft.border.all(1, ImportacionesTheme.BORDER),
                    ),
                    
                    ft.Container(height=16),
                    
                    # Resumen de costos
                    ft.ResponsiveRow(
                        controls=[
                            ft.Column([
                                ft.Container(
                                    content=ft.Column([
                                        ft.Row([
                                            ft.Icon(ft.Icons.ACCOUNT_BALANCE, size=16, color=ImportacionesTheme.WARNING),
                                            ft.Text("Tributos", size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                                        ], spacing=6),
                                        ft.Text(format_currency(total_impuestos), size=16, weight=ft.FontWeight.BOLD, color=ImportacionesTheme.WARNING),
                                    ], spacing=4),
                                    padding=12,
                                    bgcolor=f"{ImportacionesTheme.WARNING}10",
                                    border_radius=8,
                                    border=ft.border.all(1, f"{ImportacionesTheme.WARNING}30"),
                                )
                            ], col={"xs": 6, "md": 4}),
                            ft.Column([
                                ft.Container(
                                    content=ft.Column([
                                        ft.Row([
                                            ft.Icon(ft.Icons.REQUEST_QUOTE, size=16, color=ImportacionesTheme.STATUS_IN_CUSTOMS),
                                            ft.Text("Gastos Aduaneros", size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                                        ], spacing=6),
                                        ft.Text(format_currency(total_gastos), size=16, weight=ft.FontWeight.BOLD, color=ImportacionesTheme.STATUS_IN_CUSTOMS),
                                    ], spacing=4),
                                    padding=12,
                                    bgcolor=f"{ImportacionesTheme.STATUS_IN_CUSTOMS}10",
                                    border_radius=8,
                                    border=ft.border.all(1, f"{ImportacionesTheme.STATUS_IN_CUSTOMS}30"),
                                )
                            ], col={"xs": 6, "md": 4}),
                            ft.Column([
                                ft.Container(
                                    content=ft.Column([
                                        ft.Row([
                                            ft.Icon(ft.Icons.CALCULATE, size=16, color="white"),
                                            ft.Text("COSTO TOTAL", size=12, color="white"),
                                        ], spacing=6),
                                        ft.Text(format_currency(total_dua), size=18, weight=ft.FontWeight.BOLD, color="white"),
                                    ], spacing=4),
                                    padding=12,
                                    bgcolor=ImportacionesTheme.STATUS_COMPLETED,
                                    border_radius=8,
                                )
                            ], col={"xs": 12, "md": 4}),
                        ],
                        spacing=12,
                        run_spacing=12
                    ),
                    
                    # Notas (si existen)
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.INFO_OUTLINE, size=14, color=ImportacionesTheme.TEXT_SECONDARY),
                            ft.Text(dua.get('notes', ''), size=12, color=ImportacionesTheme.TEXT_SECONDARY, expand=True),
                        ], spacing=8),
                        padding=ft.padding.only(top=16),
                    ) if dua.get('notes') else ft.Container(),
                    
                    ft.Container(height=16),
                    
                    # Botones
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                "Ver detalles",
                                icon=ft.Icons.OPEN_IN_NEW,
                                on_click=lambda e: self.page.go(f"/dua/{dua['id']}"),
                                style=ft.ButtonStyle(bgcolor=ImportacionesTheme.STATUS_CONFIRMED, color="white")
                            ),
                            ft.ElevatedButton(
                                "Ver PDF",
                                icon=ft.Icons.PICTURE_AS_PDF,
                                on_click=lambda e: self._abrir_pdf_dua(),
                                style=ft.ButtonStyle(bgcolor=ImportacionesTheme.ERROR, color="white")
                            ) if dua.get('archivo_pdf') else ft.Container(),
                        ],
                        spacing=12
                    ),
                ],
            ),
            padding=20,
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
        )
    
    def _crear_tarjeta_documentos_transporte(self):
        """Crear tarjeta con documentos de transporte"""
        rows = [self._crear_fila_documento_transporte(doc) for doc in self.documentos_transporte]
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.LOCAL_SHIPPING, size=24, color=ImportacionesTheme.STATUS_IN_TRANSIT),
                            ft.Text(
                                "Documentos de Transporte",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=ImportacionesTheme.TEXT_PRIMARY
                            ),
                            ft.Container(expand=True),
                            ft.Text(
                                f"{len(self.documentos_transporte)} documentos",
                                size=12,
                                color=ImportacionesTheme.TEXT_SECONDARY
                            ),
                        ],
                        spacing=12
                    ),
                    ft.Container(height=12),
                    ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("Tipo", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("Número", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("Transportista", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("ETD", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("ETA", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("Archivo", weight=ft.FontWeight.BOLD)),
                        ],
                        rows=rows,
                        heading_row_color=ImportacionesTheme.BG_SECONDARY,
                        border=ft.border.all(1, ImportacionesTheme.BORDER),
                        border_radius=8,
                        column_spacing=20,
                    ),
                    ft.Container(height=12),
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                "Agregar documento",
                                icon=ft.Icons.ADD,
                                on_click=lambda e: self.page.go(
                                    f"/transporte"
                                ),
                                style=ft.ButtonStyle(
                                    bgcolor=ImportacionesTheme.STATUS_IN_TRANSIT,
                                    color="white"
                                )
                            ),
                        ]
                    ),
                ]
            ),
            padding=20,
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
        )
    def _crear_fila_documento_transporte(self, doc: dict):
        """Crear fila para documento de transporte"""
        doc_id = doc.get('id')
        tiene_archivo = bool(doc.get('document_file_path'))
        
        archivo_cell = (
            ft.IconButton(
                icon=ft.Icons.VISIBILITY,
                icon_size=18,
                icon_color=ImportacionesTheme.INFO,
                tooltip="Ver documento",
                on_click=lambda e, did=doc_id: self._ver_documento_transporte(did)
            ) if tiene_archivo else ft.Icon(
                ft.Icons.FILE_DOWNLOAD_OFF,
                color=ImportacionesTheme.TEXT_SECONDARY
            )
        )
        
        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(doc.get('document_type_label', 'Documento'))),
                ft.DataCell(ft.Text(doc.get('document_number', 'N/A'))),
                ft.DataCell(ft.Text(doc.get('carrier', 'N/A'))),
                ft.DataCell(ft.Text(self._formatear_fecha(doc.get('etd_date')))),
                ft.DataCell(ft.Text(self._formatear_fecha(doc.get('eta_date')))),
                ft.DataCell(archivo_cell),
            ]
        )
    
    def _crear_tarjeta_documentos_adjuntos(self):
        """Crear tarjeta para documentos adjuntos"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ATTACH_FILE, size=24, color=ImportacionesTheme.TEXT_SECONDARY),
                            ft.Text(
                                "Documentos Adjuntos",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=ImportacionesTheme.TEXT_PRIMARY
                            ),
                        ],
                        spacing=12
                    ),
                    ft.Container(height=12),
                    ft.Text(
                        "Packing list, certificados, facturas comerciales, etc.",
                        size=14,
                        color=ImportacionesTheme.TEXT_SECONDARY
                    ),
                    ft.Container(height=16),
                    ft.ElevatedButton(
                        "Subir documentos",
                        icon=ft.Icons.UPLOAD_FILE,
                        style=ft.ButtonStyle(
                            bgcolor=ImportacionesTheme.BORDER,
                            color=ImportacionesTheme.TEXT_PRIMARY
                        )
                    ),
                ]
            ),
            padding=20,
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
        )

    # ==================== VISTAS VACÍAS ====================
    
    def _crear_vista_vacia(self, mensaje: str, icono, texto_boton: str = None, on_click=None):
        """Crear vista cuando no hay datos"""
        controles = [
            ft.Icon(icono, size=48, color=ImportacionesTheme.TEXT_SECONDARY),
            ft.Container(height=12),
            ft.Text(
                mensaje,
                size=16,
                color=ImportacionesTheme.TEXT_SECONDARY,
                text_align=ft.TextAlign.CENTER
            ),
        ]
        
        if texto_boton and on_click:
            controles.extend([
                ft.Container(height=16),
                ft.ElevatedButton(
                    texto_boton,
                    icon=ft.Icons.ADD,
                    on_click=on_click,
                    style=ft.ButtonStyle(
                        bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                        color="white"
                    )
                )
            ])
        
        return ft.Container(
            content=ft.Column(
                controls=controles,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=60,
            alignment=ft.alignment.center,
        )
    def _crear_vista_dua_vacia(self):
        """Crear vista cuando no hay DUA"""
        return self._crear_vista_vacia(
            "No hay DUA asignada\nAsigna una DUA para llevar el control aduanero",
            ft.Icons.DESCRIPTION_OUTLINED,
            "Asignar DUA",
            lambda e: self.page.go(f"dua")
        )
    def _crear_vista_transporte_vacia(self):
        """Crear vista cuando no hay documentos de transporte"""
        return self._crear_vista_vacia(
            "No hay documentos de transporte\nAgrega documentos para seguimiento",
            ft.Icons.LOCAL_SHIPPING_OUTLINED,
            "Agregar documento",
            lambda e: self.page.go(f"/transporte")
        )

    # ==================== BOTONES DE ACCIÓN ====================
    
    def _crear_botones_accion(self):
        """Crear botones de acción en el footer"""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.ElevatedButton(
                        "📋 Ver reporte",
                        icon=ft.Icons.SUMMARIZE,
                        style=ft.ButtonStyle(
                            bgcolor=ImportacionesTheme.INFO,
                            color="white"
                        )
                    ),
                    ft.ElevatedButton(
                        "📧 Compartir",
                        icon=ft.Icons.SHARE,
                        style=ft.ButtonStyle(
                            bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                            color="white"
                        )
                    ),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "📦 Agregar más POs",
                        icon=ft.Icons.ADD_SHOPPING_CART,
                        on_click=lambda e: self.page.go(f"/importaciones/{self.importacion_id}/agregar-pos"),
                        style=ft.ButtonStyle(
                            bgcolor=ImportacionesTheme.SUCCESS,
                            color="white"
                        )
                    ),
                    ft.ElevatedButton(
                        "📝 Editar",
                        icon=ft.Icons.EDIT,
                        on_click=lambda e: self.page.go(f"/importaciones/{self.importacion_id}/editar"),
                        style=ft.ButtonStyle(
                            bgcolor=ImportacionesTheme.STATUS_IN_CUSTOMS,
                            color="white"
                        )
                    )
                    
                ],
                spacing=12
            ),
            padding=ft.padding.symmetric(vertical=16, horizontal=20),
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
        )

    # ==================== UTILIDADES ====================
    def _abrir_modal_prorrateo(self, e):
        """Abre modal de prorrateo con opciones de cálculo, columnas dinámicas y exportación"""
        
        # ✅ CORRECCIÓN: Usar set() para garantizar IDs únicos
        po_ids = list(set([po['id'] for po in self.pos_asociadas]))
        print(f"🔍 DEBUG: PO IDs únicos para prorrateo: {po_ids}")
        
        if not po_ids:
            self._mostrar_snackbar("No hay POs vinculadas para calcular", ImportacionesTheme.ERROR)
            return

        # 1. Cargar todos los ítems de las POs (con DISTINCT para evitar duplicados)
        format_strings = ','.join(['%s'] * len(po_ids))
        
        # ✅ CORRECCIÓN: Agregado DISTINCT en la consulta de items
        query_items = f"""
            SELECT 
                MAX(poi.id) as id, -- Tomamos el ID más reciente
                poi.po_id,
                poi.product_id,
                SUM(poi.quantity) as quantity, -- SI HAY DUPLICADOS, SUMA LAS CANTIDADES
                poi.unit_price,
                p.sku,
                p.name as product_name,
                po.po_number,
                COALESCE(p.weight_kg, 0) as weight_kg,
                COALESCE(p.volume_m3, 0) as volume_m3
            FROM purchase_order_items poi
            LEFT JOIN products p ON poi.product_id = p.id
            LEFT JOIN purchase_orders po ON poi.po_id = po.id
            WHERE poi.po_id IN ({format_strings})
            GROUP BY poi.po_id, poi.product_id, poi.unit_price -- AGRUPACIÓN CLAVE
            ORDER BY po.po_number, p.name
        """
        items_raw = self.db.execute_query(query_items, tuple(po_ids)) or []
        
        # ✅ CORRECCIÓN ADICIONAL: Eliminar items duplicados por ID
        seen_item_ids = set()
        self.items_consolidados = []
        for item in items_raw:
            if item['id'] not in seen_item_ids:
                seen_item_ids.add(item['id'])
                self.items_consolidados.append(item)
        
        print(f"📦 Items cargados: {len(items_raw)} raw → {len(self.items_consolidados)} únicos")
        
        if not self.items_consolidados:
            self._mostrar_snackbar("No hay items en las POs para prorratear", ImportacionesTheme.WARNING)
            return

        # 2. Calcular totales base para los métodos de prorrateo
        self.total_fob_imp = 0
        self.total_qty_imp = 0
        self.total_weight_imp = 0
        self.total_volume_imp = 0
        
        for item in self.items_consolidados:
            qty = float(item.get('quantity', 0) or 0)
            price = float(item.get('unit_price', 0) or 0)
            weight = float(item.get('weight_kg', 0) or 0) * qty
            volume = float(item.get('volume_m3', 0) or 0) * qty
            
            item['fob_total'] = qty * price
            item['weight_total'] = weight
            item['volume_total'] = volume
            
            self.total_fob_imp += item['fob_total']
            self.total_qty_imp += qty
            self.total_weight_imp += weight
            self.total_volume_imp += volume

        print(f"📊 Totales calculados:")
        print(f"   - FOB Total: S/ {self.total_fob_imp:,.2f}")
        print(f"   - Cantidad Total: {self.total_qty_imp:,.0f}")
        print(f"   - Peso Total: {self.total_weight_imp:,.2f} kg")
        print(f"   - Volumen Total: {self.total_volume_imp:,.4f} m³")

        # 3. Cargar Gastos de la DUA e identificar columnas dinámicas
        query_dua = """
            SELECT freight_usd, insurance_usd, ad_valorem_amount, igv_amount, 
                ipm_amount, customs_fees, agency_fees, storage_fees
            FROM dua_documents WHERE importacion_id = %s LIMIT 1
        """
        res_dua = self.db.execute_query(query_dua, (self.importacion_id,))
        
        tc = float(self.importacion_data.get('exchange_rate') or 
                self.importacion_data.get('tipo_cambio') or 1)
        
        self.gastos_valores = {}
        self.present_expense_types = []

        if res_dua:
            dua = res_dua[0]
            dua_map = {
                'freight_usd': ('freight', True),
                'insurance_usd': ('insurance', True),
                'ad_valorem_amount': ('ad_valorem', False),
                'ipm_amount': ('ipm', False),
                'customs_fees': ('customs_fees', False),
                'agency_fees': ('agency_fees', False),
                'storage_fees': ('storage_fees', False),
            }
            
            for campo, (tipo, es_usd) in dua_map.items():
                monto = float(dua.get(campo) or 0)
                if monto > 0:
                    # Excluir IGV del prorrateo
                    if tipo == 'igv':
                        continue
                    monto_pen = monto * tc if es_usd else monto
                    self.gastos_valores[tipo] = monto_pen
                    self.present_expense_types.append(tipo)

        self.total_gastos_imp = sum(self.gastos_valores.values())
        
        # ✅ VALIDACIÓN: Verificar que los totales sean coherentes
        if self.total_fob_imp <= 0:
            self._mostrar_snackbar("Error: FOB Total es 0 o negativo", ImportacionesTheme.ERROR)
            return

        # 4. Determinar qué métodos están disponibles
        metodos_disponibles = [
            ft.dropdown.Option("fob", "Por Valor FOB"),
            ft.dropdown.Option("quantity", "Por Cantidad"),
        ]
        
        if self.total_weight_imp > 0:
            metodos_disponibles.append(ft.dropdown.Option("weight", "Por Peso (kg)"))
        
        if self.total_volume_imp > 0:
            metodos_disponibles.append(ft.dropdown.Option("volume", "Por Volumen (m³)"))
        
        if self.total_weight_imp > 0:
            metodos_disponibles.append(ft.dropdown.Option("mixed", "Mixto (70% FOB + 30% Peso)"))

        # 5. Controles del Modal
        self.metodo_selector = ft.Dropdown(
            options=metodos_disponibles,
            value="fob",
            label="Método de Distribución",
            width=250,
            on_change=self._actualizar_tabla_prorrateo
        )

        self.tabla_container = ft.Container()
        self._actualizar_tabla_prorrateo()

        # 6. Resumen de totales
        factor_gasto = (self.total_gastos_imp / self.total_fob_imp * 100) if self.total_fob_imp > 0 else 0
        
        resumen_totales = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("FOB Total:", size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Text(f"S/ {self.total_fob_imp:,.2f}", size=16, weight=ft.FontWeight.BOLD, 
                        color=ImportacionesTheme.SUCCESS),
                ], spacing=2),
                ft.Column([
                    ft.Text("Gastos DUA:", size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Text(f"S/ {self.total_gastos_imp:,.2f}", size=16, weight=ft.FontWeight.BOLD,
                        color=ImportacionesTheme.WARNING),
                ], spacing=2),
                ft.Column([
                    ft.Text("Costo Total:", size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Text(f"S/ {self.total_fob_imp + self.total_gastos_imp:,.2f}", 
                        size=16, weight=ft.FontWeight.BOLD, color=ImportacionesTheme.INFO),
                ], spacing=2),
                ft.Column([
                    ft.Text("Items:", size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Text(f"{len(self.items_consolidados)}", size=16, weight=ft.FontWeight.BOLD),
                ], spacing=2),
                ft.Column([
                    ft.Text("POs:", size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Text(f"{len(po_ids)}", size=16, weight=ft.FontWeight.BOLD),
                ], spacing=2),
                ft.Column([
                    ft.Text("Factor:", size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Text(f"+{factor_gasto:.2f}%", 
                        size=16, weight=ft.FontWeight.BOLD, color=ImportacionesTheme.STATUS_IN_CUSTOMS),
                ], spacing=2),
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            padding=15,
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=8,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
        )

        # 7. Advertencias
        advertencias = []
        if self.total_weight_imp == 0:
            advertencias.append(ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.WARNING_AMBER, size=16, color=ImportacionesTheme.WARNING),
                    ft.Text("No hay datos de peso. Métodos por peso no disponibles.", 
                        size=12, color=ImportacionesTheme.WARNING),
                ], spacing=8),
                padding=8,
                bgcolor=f"{ImportacionesTheme.WARNING}15",
                border_radius=6,
            ))

        # 8. Construir el Modal
        self.diag_prorrateo = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.CALCULATE, color=ImportacionesTheme.STATUS_CONFIRMED),
                ft.Text(f"Prorrateo - {self.importacion_data.get('numero_importacion', 'Importación')}",
                    size=18, weight=ft.FontWeight.BOLD),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    resumen_totales,
                    ft.Container(height=10),
                    *advertencias,
                    ft.Row([
                        self.metodo_selector,
                        ft.Container(width=20),
                        ft.Text("Seleccione el método de distribución de costos", 
                            size=12, color=ImportacionesTheme.TEXT_SECONDARY, italic=True),
                    ], alignment=ft.MainAxisAlignment.START),
                    ft.Divider(height=20),
                    ft.Container(
                        content=self.tabla_container,
                        expand=True,
                    ),
                ], 
                scroll=ft.ScrollMode.AUTO,
                spacing=10,
                ),
                width=1400,
                height=700,
                padding=10,
            ),
            actions=[
                ft.TextButton(
                    "Exportar Excel", 
                    icon=ft.Icons.FILE_DOWNLOAD,
                    on_click=lambda _: self._exportar_prorrateo_excel(self.metodo_selector.value)
                ),
                ft.TextButton(
                    "Cerrar", 
                    on_click=lambda _: self.page.close(self.diag_prorrateo)
                ),
                ft.ElevatedButton(
                    "✓ Aplicar Prorrateo", 
                    bgcolor=ImportacionesTheme.SUCCESS, 
                    color="white",
                    on_click=lambda _: self._ejecutar_aplicacion_prorrateo(
                        self.metodo_selector.value, 
                        po_ids  # Ya está limpio de duplicados
                    )
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.open(self.diag_prorrateo)
        

    def _actualizar_tabla_prorrateo(self, e=None):
        """Actualiza el contenido de la tabla según el método seleccionado"""
        metodo = self.metodo_selector.value if self.metodo_selector else "fob"
        tabla = self._crear_tabla_modal_prorrateo_dinamica(metodo)
        self.tabla_container.content = tabla
        
        if self.tabla_container.page:
            self.tabla_container.update()


    def _calcular_participacion_item(self, item: dict, metodo: str) -> float:
        """Calcula la participación de un item según el método seleccionado"""
        
        if metodo == 'fob':
            if self.total_fob_imp > 0:
                return item['fob_total'] / self.total_fob_imp
            return 0
            
        elif metodo == 'quantity':
            if self.total_qty_imp > 0:
                return float(item.get('quantity', 0)) / self.total_qty_imp
            return 0
            
        elif metodo == 'weight':
            if self.total_weight_imp > 0:
                return item.get('weight_total', 0) / self.total_weight_imp
            # Fallback a FOB si no hay peso
            if self.total_fob_imp > 0:
                return item['fob_total'] / self.total_fob_imp
            return 0
            
        elif metodo == 'volume':
            if self.total_volume_imp > 0:
                return item.get('volume_total', 0) / self.total_volume_imp
            # Fallback a FOB si no hay volumen
            if self.total_fob_imp > 0:
                return item['fob_total'] / self.total_fob_imp
            return 0
            
        elif metodo == 'mixed':
            # 70% FOB + 30% Peso
            pct_fob = (item['fob_total'] / self.total_fob_imp) if self.total_fob_imp > 0 else 0
            pct_weight = (item.get('weight_total', 0) / self.total_weight_imp) if self.total_weight_imp > 0 else pct_fob
            return (pct_fob * 0.7) + (pct_weight * 0.3)
        
        return 0


    def _crear_tabla_modal_prorrateo_dinamica(self, metodo: str):
        """Genera la DataTable con columnas dinámicas, separación por PO y fila de totales"""
        
        # Mapeo para títulos de columnas
        col_titles = {
            'freight': 'Flete',
            'insurance': 'Seguro',
            'ad_valorem': 'Ad/Valorem',
            'ipm': 'IPM',
            'customs_fees': 'Gs. Aduana',
            'agency_fees': 'Agencia',
            'storage_fees': 'Almacenaje',
        }

        # Columnas fijas
        columns = [
            ft.DataColumn(ft.Text("PO", size=11, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("SKU", size=11, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Producto", size=11, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Cant.", size=11, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(ft.Text("P.Unit.FOB", size=11, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(ft.Text("FOB Total", size=11, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(ft.Text("% Part.", size=11, weight=ft.FontWeight.BOLD), numeric=True),
        ]
        
        # Columnas dinámicas (solo las que tienen gastos > 0)
        for tipo in self.present_expense_types:
            columns.append(
                ft.DataColumn(
                    ft.Text(col_titles.get(tipo, tipo), size=10, weight=ft.FontWeight.BOLD), 
                    numeric=True
                )
            )
        
        # Columnas finales
        columns.append(ft.DataColumn(ft.Text("Tot.Gastos", size=11, weight=ft.FontWeight.BOLD), numeric=True))
        columns.append(ft.DataColumn(ft.Text("Costo Total", size=11, weight=ft.FontWeight.BOLD), numeric=True))
        columns.append(ft.DataColumn(ft.Text("Cost.Unit.", size=11, weight=ft.FontWeight.BOLD), numeric=True))
        columns.append(ft.DataColumn(ft.Text("+%", size=11, weight=ft.FontWeight.BOLD), numeric=True))

        rows = []
        
        # Variables para totales
        totales = {
            'cantidad': 0,
            'fob_total': 0,
            'gastos_por_tipo': {tipo: 0 for tipo in self.present_expense_types},
            'total_gastos': 0,
            'costo_total': 0,
        }
        
        # Agrupar ítems por Orden de Compra
        items_by_po = {}
        for item in self.items_consolidados:
            po_num = item.get('po_number', 'Sin PO')
            if po_num not in items_by_po:
                items_by_po[po_num] = []
            items_by_po[po_num].append(item)
        
        # Crear filas con separadores por PO
        for po_num, po_items in items_by_po.items():
            # Fila separadora para la PO
            separator_cells = [
                ft.DataCell(
                    ft.Container(
                        content=ft.Text(f"📦 Orden: {po_num}", weight=ft.FontWeight.BOLD, size=12),
                        padding=ft.padding.symmetric(vertical=5),
                    )
                )
            ]
            # Rellenar celdas vacías
            separator_cells.extend([ft.DataCell(ft.Text("")) for _ in range(len(columns) - 1)])
            
            rows.append(ft.DataRow(
                cells=separator_cells,
                color=f"{ImportacionesTheme.INFO}15",
            ))
            
            # Filas de items de esta PO
            for itm in po_items:
                qty = float(itm.get('quantity', 0) or 0)
                unit_price = float(itm.get('unit_price', 0) or 0)
                fob_total = itm.get('fob_total', qty * unit_price)
                
                # Calcular participación según método
                share = self._calcular_participacion_item(itm, metodo)
                
                # Celdas fijas
                cells = [
                    ft.DataCell(ft.Text(po_num, size=10)),
                    ft.DataCell(ft.Text(itm.get('sku', '-')[:15], size=10)),
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(
                                (itm.get('product_name', '') or '')[:25],
                                size=10,
                                no_wrap=True,
                                overflow=ft.TextOverflow.ELLIPSIS
                            ),
                            width=150,
                            tooltip=itm.get('product_name', ''),
                        )
                    ),
                    ft.DataCell(ft.Text(f"{qty:,.0f}", size=10)),
                    ft.DataCell(ft.Text(f"{unit_price:,.4f}", size=10)),
                    ft.DataCell(ft.Text(f"{fob_total:,.2f}", size=10)),
                    ft.DataCell(ft.Text(f"{share*100:.2f}%", size=10, color=ImportacionesTheme.INFO)),
                ]
                
                # Celdas dinámicas de gastos
                item_total_expenses = 0
                for tipo in self.present_expense_types:
                    gasto_asignado = self.gastos_valores.get(tipo, 0) * share
                    item_total_expenses += gasto_asignado
                    totales['gastos_por_tipo'][tipo] += gasto_asignado
                    cells.append(ft.DataCell(ft.Text(f"{gasto_asignado:,.2f}", size=10)))
                
                costo_total_final = fob_total + item_total_expenses
                costo_unitario_final = costo_total_final / qty if qty > 0 else 0
                
                # Calcular incremento porcentual
                incremento = ((costo_unitario_final - unit_price) / unit_price * 100) if unit_price > 0 else 0
                color_incremento = (
                    ImportacionesTheme.SUCCESS if incremento < 15 
                    else ImportacionesTheme.WARNING if incremento < 30 
                    else ImportacionesTheme.ERROR
                )
                
                # Celdas finales
                cells.append(ft.DataCell(ft.Text(f"{item_total_expenses:,.2f}", size=10, color=ImportacionesTheme.WARNING)))
                cells.append(ft.DataCell(ft.Text(f"{costo_total_final:,.2f}", size=10, weight=ft.FontWeight.BOLD)))
                cells.append(ft.DataCell(ft.Text(f"{costo_unitario_final:,.4f}", size=10, weight=ft.FontWeight.BOLD, color=ImportacionesTheme.STATUS_CONFIRMED)))
                cells.append(ft.DataCell(ft.Text(f"+{incremento:.1f}%", size=10, color=color_incremento)))
                
                rows.append(ft.DataRow(cells=cells))
                
                # Acumular totales
                totales['cantidad'] += qty
                totales['fob_total'] += fob_total
                totales['total_gastos'] += item_total_expenses
                totales['costo_total'] += costo_total_final

        # ==================== FILA DE TOTALES ====================
        total_cells = [
            ft.DataCell(ft.Container(
                content=ft.Text("TOTALES", weight=ft.FontWeight.BOLD, size=12),
                padding=ft.padding.symmetric(vertical=8),
            )),
            ft.DataCell(ft.Text("")),  # SKU
            ft.DataCell(ft.Text(f"{len(self.items_consolidados)} items", size=11, weight=ft.FontWeight.BOLD)),
            ft.DataCell(ft.Text(f"{totales['cantidad']:,.0f}", size=11, weight=ft.FontWeight.BOLD)),
            ft.DataCell(ft.Text("")),  # Precio unitario
            ft.DataCell(ft.Text(f"{totales['fob_total']:,.2f}", size=11, weight=ft.FontWeight.BOLD, color=ImportacionesTheme.SUCCESS)),
            ft.DataCell(ft.Text("100%", size=11, weight=ft.FontWeight.BOLD)),
        ]
        
        # Totales por tipo de gasto
        for tipo in self.present_expense_types:
            total_tipo = totales['gastos_por_tipo'][tipo]
            total_cells.append(ft.DataCell(ft.Text(f"{total_tipo:,.2f}", size=11, weight=ft.FontWeight.BOLD)))
        
        # Totales finales
        total_cells.append(ft.DataCell(ft.Text(f"{totales['total_gastos']:,.2f}", size=11, weight=ft.FontWeight.BOLD, color=ImportacionesTheme.WARNING)))
        total_cells.append(ft.DataCell(ft.Text(f"{totales['costo_total']:,.2f}", size=12, weight=ft.FontWeight.BOLD, color=ImportacionesTheme.STATUS_COMPLETED)))
        total_cells.append(ft.DataCell(ft.Text("")))  # Costo unitario promedio no aplica
        
        # Factor de incremento total
        factor_total = ((totales['costo_total'] - totales['fob_total']) / totales['fob_total'] * 100) if totales['fob_total'] > 0 else 0
        total_cells.append(ft.DataCell(ft.Text(f"+{factor_total:.1f}%", size=11, weight=ft.FontWeight.BOLD, color=ImportacionesTheme.STATUS_IN_CUSTOMS)))
        
        rows.append(ft.DataRow(
            cells=total_cells,
            color=f"{ImportacionesTheme.STATUS_COMPLETED}20",
        ))

        # Crear DataTable con scroll
        data_table = ft.DataTable(
            columns=columns,
            rows=rows,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
            heading_row_color=ImportacionesTheme.BG_SECONDARY,
            heading_row_height=40,
            data_row_min_height=35,
            data_row_max_height=45,
            vertical_lines=ft.border.all(0.5, ImportacionesTheme.BORDER),
            horizontal_lines=ft.border.all(0.5, ImportacionesTheme.BORDER),
            column_spacing=12,
        )
        
        # Envolver en contenedor con scroll horizontal y vertical
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[data_table],
                        scroll=ft.ScrollMode.AUTO,  # Scroll horizontal
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,  # Scroll vertical
            ),
            expand=True,
        )


    def _ejecutar_aplicacion_prorrateo(self, metodo: str, po_ids: list):
        """Aplica el prorrateo y prepara los datos para el ingreso a almacén"""
        try:
            print(f"🔄 Aplicando prorrateo con método: {metodo}")
            
            # 1. Guardar registro principal de prorrateo
            query_main = """
                INSERT INTO cost_prorating 
                (importacion_id, prorating_date, prorating_method, total_fob, total_expenses,
                total_landed_cost, status, calculated_by)
                VALUES (%s, CURDATE(), %s, %s, %s, %s, 'applied', 1)
            """
            total_landed = self.total_fob_imp + self.total_gastos_imp
            # Forzamos el ID de prorrateo (si insert_id no funciona, capturamos el error)
            self.db.execute_query(query_main, (self.importacion_id, metodo, self.total_fob_imp, self.total_gastos_imp, total_landed), fetch=False)

            # 2. Actualizar cada ítem con su costo 'Landed' (Costo en Almacén)
            items_actualizados = 0
            for itm in self.items_consolidados:
                qty = float(itm.get('quantity', 0) or 0)
                if qty <= 0: continue
                
                fob_total = itm.get('fob_total', 0)
                share = self._calcular_participacion_item(itm, metodo)
                
                # Distribución detallada de gastos
                g_freight = self.gastos_valores.get('freight', 0) * share
                g_insurance = self.gastos_valores.get('insurance', 0) * share
                g_taxes = (self.gastos_valores.get('ad_valorem', 0) + self.gastos_valores.get('ipm', 0)) * share
                g_expenses = (self.gastos_valores.get('customs_fees', 0) + self.gastos_valores.get('agency_fees', 0) + self.gastos_valores.get('storage_fees', 0)) * share
                
                landed_cost_total = fob_total + g_freight + g_insurance + g_taxes + g_expenses
                costo_unitario_final = landed_cost_total / qty
                
                # Actualizamos unit_landed_cost (la columna que creamos arriba)
                update_query = """
                    UPDATE purchase_order_items 
                    SET prorated_freight = %s, prorated_insurance = %s, 
                        prorated_taxes = %s, prorated_expenses = %s,
                        total_cost = %s, unit_landed_cost = %s
                    WHERE id = %s
                """
                self.db.execute_query(update_query, (g_freight, g_insurance, g_taxes, g_expenses, landed_cost_total, costo_unitario_final, itm['id']), fetch=False)
                items_actualizados += 1
            
            self.db.execute_query(
                "UPDATE importaciones SET estado = 'prorrateado' WHERE id = %s",
                (self.importacion_id,), fetch=False
            )
            # 3. Actualizar estados para habilitar el ingreso a almacén
            format_strings = ','.join(['%s'] * len(po_ids))
            self.db.execute_query(f"UPDATE purchase_orders SET status = 'prorrateado' WHERE id IN ({format_strings})", tuple(po_ids), fetch=False)
            self.db.execute_query("UPDATE importaciones SET estado = 'prorrateado' WHERE id = %s", (self.importacion_id,), fetch=False)
            
            if hasattr(self.db.connection, 'commit'):
                self.db.connection.commit()
                
            self.page.close(self.diag_prorrateo)
            self._mostrar_snackbar(f"✅ Prorrateo aplicado. {items_actualizados} items listos para almacén.", ImportacionesTheme.SUCCESS)
            self._cargar_datos_completos() # Esto refrescará los botones de la interfaz
            
        except Exception as ex:
            if hasattr(self.db.connection, 'rollback'): self.db.connection.rollback()
            print(f"❌ Error crítico: {ex}")
            self._mostrar_snackbar(f"Error: {str(ex)}", ImportacionesTheme.ERROR)
            

    def _exportar_prorrateo_excel(self, metodo: str):
        """Exporta el prorrateo a Excel con formato profesional"""
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter
            from datetime import datetime
            import os
        except ImportError:
            self._mostrar_snackbar("Librería 'openpyxl' no instalada. Ejecute: pip install openpyxl", ImportacionesTheme.ERROR)
            return

        # Mapeo de títulos
        col_titles = {
            'freight': 'Flete', 
            'insurance': 'Seguro', 
            'ad_valorem': 'Ad/Valorem',
            'ipm': 'IPM', 
            'customs_fees': 'Gastos Aduana', 
            'agency_fees': 'Agencia',
            'storage_fees': 'Almacenaje',
        }
        
        metodo_nombres = {
            'fob': 'Valor FOB',
            'quantity': 'Cantidad',
            'weight': 'Peso (kg)',
            'volume': 'Volumen (m³)',
            'mixed': 'Mixto (70% FOB + 30% Peso)',
        }

        wb = openpyxl.Workbook()
        ws = wb.active
        num_imp = self.importacion_data.get('numero_importacion', 'IMP')
        ws.title = f"Prorrateo {num_imp}"[:31]  # Excel limita a 31 caracteres

        # Estilos
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        po_header_fill = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid")
        total_fill = PatternFill(start_color="C5D9F1", end_color="C5D9F1", fill_type="solid")
        thin_border = Border(
            left=Side(style='thin'), right=Side(style='thin'), 
            top=Side(style='thin'), bottom=Side(style='thin')
        )

        # Título principal
        ws.merge_cells('A1:L1')
        title_cell = ws['A1']
        title_cell.value = f"PRORRATEO DE COSTOS DE IMPORTACIÓN - {num_imp}"
        title_cell.font = Font(bold=True, size=16, color="366092")
        title_cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Información de la importación
        info_rows = [
            (3, f"Importación: {num_imp}"),
            (4, f"Fecha de Cálculo: {datetime.now().strftime('%d/%m/%Y %H:%M')}"),
            (5, f"Método de Prorrateo: {metodo_nombres.get(metodo, metodo)}"),
            (6, f"FOB Total: S/ {self.total_fob_imp:,.2f}"),
            (7, f"Gastos Totales: S/ {self.total_gastos_imp:,.2f}"),
            (8, f"Costo Total Importación: S/ {self.total_fob_imp + self.total_gastos_imp:,.2f}"),
        ]
        
        for row_num, value in info_rows:
            cell = ws.cell(row=row_num, column=1, value=value)
            if row_num in [6, 7, 8]:
                cell.font = Font(bold=True)

        # Encabezados de la tabla (fila 10)
        start_row = 10
        headers = ["PO", "SKU", "Producto", "Cantidad", "P. Unit. FOB", "FOB Total", "% Part."]
        headers.extend([col_titles.get(t, t) for t in self.present_expense_types])
        headers.extend(["Total Gastos", "Costo Total", "Costo Unitario", "Incremento %"])
        
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=start_row, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = thin_border

        current_row = start_row + 1
        
        # Agrupar por PO
        items_by_po = {}
        for item in self.items_consolidados:
            po_num = item.get('po_number', 'Sin PO')
            if po_num not in items_by_po:
                items_by_po[po_num] = []
            items_by_po[po_num].append(item)
        
        # Variables para totales
        totales = {
            'cantidad': 0,
            'fob_total': 0,
            'gastos_por_tipo': {tipo: 0 for tipo in self.present_expense_types},
            'total_gastos': 0,
            'costo_total': 0,
        }
        
        for po_num, po_items in items_by_po.items():
            # Fila separadora PO
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=len(headers))
            cell = ws.cell(row=current_row, column=1, value=f"--- Orden de Compra: {po_num} ---")
            cell.font = Font(bold=True)
            cell.fill = po_header_fill
            cell.alignment = Alignment(horizontal='left')
            current_row += 1
            
            for itm in po_items:
                qty = float(itm.get('quantity', 0) or 0)
                unit_price = float(itm.get('unit_price', 0) or 0)
                fob_total = itm.get('fob_total', qty * unit_price)
                
                share = self._calcular_participacion_item(itm, metodo)
                
                # Datos fijos
                row_data = [
                    po_num,
                    itm.get('sku', ''),
                    itm.get('product_name', ''),
                    qty,
                    unit_price,
                    fob_total,
                    share,
                ]
                
                # Datos dinámicos de gastos
                item_total_expenses = 0
                for tipo in self.present_expense_types:
                    gasto_asignado = self.gastos_valores.get(tipo, 0) * share
                    item_total_expenses += gasto_asignado
                    row_data.append(gasto_asignado)
                    totales['gastos_por_tipo'][tipo] += gasto_asignado
                
                costo_total_final = fob_total + item_total_expenses
                costo_unitario_final = costo_total_final / qty if qty > 0 else 0
                incremento = ((costo_unitario_final - unit_price) / unit_price * 100) if unit_price > 0 else 0
                
                row_data.extend([item_total_expenses, costo_total_final, costo_unitario_final, incremento])
                
                # Acumular totales
                totales['cantidad'] += qty
                totales['fob_total'] += fob_total
                totales['total_gastos'] += item_total_expenses
                totales['costo_total'] += costo_total_final

                # Escribir fila
                for col_idx, value in enumerate(row_data, 1):
                    cell = ws.cell(row=current_row, column=col_idx, value=value)
                    cell.border = thin_border
                    
                    # Formatos específicos
                    if col_idx == 4:  # Cantidad
                        cell.number_format = '#,##0.00'
                    elif col_idx in [5, len(row_data)]:  # Unitarios y %
                        if col_idx == 5:
                            cell.number_format = '#,##0.0000'
                        else:
                            cell.number_format = '0.00"%"'
                    elif col_idx == 7:  # % Participación
                        cell.number_format = '0.00%'
                    elif col_idx >= 6:  # Montos
                        cell.number_format = '#,##0.00'
                
                current_row += 1

        # ==================== FILA DE TOTALES ====================
        current_row += 1  # Espacio
        
        total_row_data = [
            "TOTALES",
            "",
            f"{len(self.items_consolidados)} items",
            totales['cantidad'],
            "",
            totales['fob_total'],
            1.0,  # 100%
        ]
        
        for tipo in self.present_expense_types:
            total_row_data.append(totales['gastos_por_tipo'][tipo])
        
        factor_total = ((totales['costo_total'] - totales['fob_total']) / totales['fob_total'] * 100) if totales['fob_total'] > 0 else 0
        total_row_data.extend([totales['total_gastos'], totales['costo_total'], "", factor_total])
        
        for col_idx, value in enumerate(total_row_data, 1):
            cell = ws.cell(row=current_row, column=col_idx, value=value)
            cell.font = Font(bold=True)
            cell.fill = total_fill
            cell.border = thin_border
            
            if col_idx == 4:
                cell.number_format = '#,##0.00'
            elif col_idx == 7:
                cell.number_format = '0.00%'
            elif col_idx == len(total_row_data):
                cell.number_format = '0.00"%"'
            elif col_idx >= 6 and value != "":
                cell.number_format = '#,##0.00'

        # Ajustar ancho de columnas
        for col in ws.columns:
            max_length = 0
            column = get_column_letter(col[0].column)
            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            adjusted_width = min(max(max_length + 2, 10), 40)
            ws.column_dimensions[column].width = adjusted_width

        # Guardar archivo
        try:
            # Crear carpeta exports si no existe
            exports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'exports')
            exports_dir = os.path.abspath(exports_dir)
            os.makedirs(exports_dir, exist_ok=True)
            
            filename = f"Prorrateo_{num_imp}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = os.path.join(exports_dir, filename)
            
            wb.save(filepath)
            
            self._mostrar_snackbar(f"✅ Excel guardado: {filename}", ImportacionesTheme.SUCCESS)
            
            # Intentar abrir el archivo
            try:
                import platform
                if platform.system() == "Windows":
                    os.startfile(filepath)
                elif platform.system() == "Darwin":
                    import subprocess
                    subprocess.run(["open", filepath])
                else:
                    import subprocess
                    subprocess.run(["xdg-open", filepath])
            except Exception as open_error:
                print(f"No se pudo abrir automáticamente: {open_error}")
                
        except Exception as save_error:
            self._mostrar_snackbar(f"Error al guardar: {str(save_error)}", ImportacionesTheme.ERROR)


    def _list_tile(self, icono, color: str, titulo: str, subtitulo: str):
        """Crear un ListTile personalizado"""
        return ft.ListTile(
            leading=ft.Icon(icono, color=color),
            title=ft.Text(titulo, size=14, weight=ft.FontWeight.BOLD),
            subtitle=ft.Text(subtitulo),
        )
    
    def _formatear_fecha(self, fecha) -> str:
        """Formatear fecha de forma segura"""
        if not fecha:
            return 'N/A'
        try:
            return format_date(fecha)
        except Exception:
            return str(fecha)
    
    def _safe_float(self, value) -> float:
        """Convertir a float de forma segura"""
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0
    
    def _obtener_color_estado(self, estado: str) -> str:
        """Obtener color según el estado de la importación"""
        colores = {
            'planificada': ImportacionesTheme.STATUS_DRAFT,
            'en_transito': ImportacionesTheme.STATUS_IN_TRANSIT,
            'en_aduana': ImportacionesTheme.STATUS_IN_CUSTOMS,
            'completada': ImportacionesTheme.STATUS_COMPLETED,
            'cancelada': ImportacionesTheme.ERROR,
        }
        return colores.get(estado, ImportacionesTheme.TEXT_SECONDARY)
    
    def _obtener_color_estado_po(self, estado: str) -> str:
        """Obtener color según el estado de la PO"""
        colores = {
            'confirmada': ImportacionesTheme.STATUS_CONFIRMED,
            'en_transito': ImportacionesTheme.STATUS_IN_TRANSIT,
            'en_aduana': ImportacionesTheme.STATUS_IN_CUSTOMS,
            'prorrateado': ImportacionesTheme.INFO,
            'en_almacen': ImportacionesTheme.STATUS_COMPLETED,
            'cancelada': ImportacionesTheme.ERROR,
        }
        return colores.get(estado, ImportacionesTheme.TEXT_SECONDARY)
    
    def _abrir_pdf_dua(self):
        """Abrir PDF de la DUA si existe"""
        if self.dua_asociada and self.dua_asociada.get('archivo_pdf'):
            import webbrowser
            try:
                webbrowser.open(self.dua_asociada['archivo_pdf'])
            except Exception as e:
                print(f"Error abriendo PDF: {e}")
                self._mostrar_snackbar("Error al abrir el PDF", ImportacionesTheme.ERROR)
    
    def _ver_documento_transporte(self, doc_id: int):
        """Ver documento de transporte"""
        self.page.go(f"/documentos-transporte/{doc_id}")
    
    def _mostrar_snackbar(self, mensaje: str, color: str):
        """Mostrar mensaje snackbar"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje),
            bgcolor=color
        )
        self.page.snack_bar.open = True
        self.page.update()