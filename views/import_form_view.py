# views/importacion_form_view.py - VERSIÓN MEJORADA
import flet as ft
from datetime import datetime
from config_importaciones import ImportacionesTheme, format_date

class ImportacionFormView:
    """Formulario para crear/editar importaciones (folders Manila)"""
    
    def __init__(self, page: ft.Page, db, importacion_id=None):
        self.page = page
        self.db = db
        self.importacion_id = importacion_id
        self.importacion_data = {}
        
        # Cargar datos si es edición
        if importacion_id:
            self.load_importacion_data()
    
    def form_view(self):
        """Renderizar el formulario con scroll"""
        
        # Crear los campos (igual que antes)
        self.descripcion_field = ft.TextField(
            label="Descripción de la importación *",
            hint_text="Ej: Importación Miami - Componentes Electrónicos",
            expand=True,
            filled=True,
            border_radius=8
        )
        
        self.bl_number_field = ft.TextField(
            label="Número de Bill of Lading (BL)",
            hint_text="BL-123456",
            expand=True,
            filled=True,
            border_radius=8
        )
        
        self.container_number_field = ft.TextField(
            label="Número de Contenedor",
            hint_text="CONT-789012",
            expand=True,
            filled=True,
            border_radius=8
        )
        
        self.via_transporte_dropdown = ft.Dropdown(
            label="Vía de Transporte *",
            options=[
                ft.dropdown.Option("maritimo", "Marítimo"),
                ft.dropdown.Option("aereo", "Aéreo"),
                ft.dropdown.Option("terrestre", "Terrestre"),
                ft.dropdown.Option("multimodal", "Multimodal"),
            ],
            value="maritimo",
            filled=True,
            border_radius=8,
            expand=True
        )
        
        self.nombre_nave_field = ft.TextField(
            label="Nombre de la Nave/Barco",
            hint_text="Ej: MSC GINA",
            filled=True,
            border_radius=8,
            visible=False  # Solo visible si es marítimo
        )
        
        self.numero_viaje_field = ft.TextField(
            label="Número de Viaje",
            hint_text="Voyage Number",
            filled=True,
            border_radius=8,
            visible=False
        )
        
        self.fecha_embarque_field = ft.TextField(
            label="Fecha de Embarque (ETD)",
            hint_text="YYYY-MM-DD",
            filled=True,
            border_radius=8,
            suffix_icon="calendar_today",
            on_focus=lambda e: self.mostrar_date_picker("embarque")
        )
        
        self.fecha_arribo_field = ft.TextField(
            label="Fecha Estimada de Arribo (ETA)",
            hint_text="YYYY-MM-DD",
            filled=True,
            border_radius=8,
            suffix_icon="calendar_today",
            on_focus=lambda e: self.mostrar_date_picker("arribo")
        )
        
        self.agente_aduanero_field = ft.TextField(
            label="Agente Aduanero",
            hint_text="Nombre del agente de aduanas",
            filled=True,
            border_radius=8
        )
        
        self.agente_carga_field = ft.TextField(
            label="Agente de Carga",
            hint_text="Nombre del freight forwarder",
            filled=True,
            border_radius=8
        )
        
        self.estado_dropdown = ft.Dropdown(
            label="Estado *",
            options=[
                ft.dropdown.Option("planificada", "Planificada"),
                ft.dropdown.Option("en_transito", "En Tránsito"),
                ft.dropdown.Option("en_aduana", "En Aduana"),
                ft.dropdown.Option("completada", "Completada"),
                ft.dropdown.Option("cancelada", "Cancelada"),
            ],
            value="planificada",
            filled=True,
            border_radius=8
        )
        
        self.notas_field = ft.TextField(
            label="Notas",
            multiline=True,
            min_lines=3,
            max_lines=6,
            filled=True,
            border_radius=8,
            expand=True
        )
        
        # Mostrar/ocultar campos según tipo de transporte
        def on_transporte_change(e):
            es_maritimo = self.via_transporte_dropdown.value == "maritimo"
            self.nombre_nave_field.visible = es_maritimo
            self.numero_viaje_field.visible = es_maritimo
            self.page.update()
        
        self.via_transporte_dropdown.on_change = on_transporte_change
        
        # Llenar campos si es edición
        if self.importacion_data:
            self.fill_form_fields()
        
        # Crear el DatePicker
        self.date_picker = ft.DatePicker(
            on_change=self.on_date_pick,
            first_date=datetime(2020, 1, 1),
            last_date=datetime(2030, 12, 31),
        )
        self.page.overlay.append(self.date_picker)
        self.date_picker_target = None  # Para saber qué campo estamos llenando
        
        # Layout principal con SCROLL
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Row([
                            ft.IconButton(
                                icon="arrow_back",
                                on_click=lambda e: self.page.go("/importaciones")
                            ),
                            ft.Column([
                                ft.Text(self.get_titulo(), size=20, 
                                       weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text("Crea un nuevo folder Manila para agrupar POs y documentos", 
                                       size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                            ], spacing=2)
                        ]),
                        
                        # Mostrar número de importación si ya existe
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Número de Importación", 
                                       size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                                ft.Text(self.importacion_data.get('numero_importacion', 'Auto-generado al guardar'), 
                                       size=14, weight=ft.FontWeight.BOLD, 
                                       color=ImportacionesTheme.STATUS_CONFIRMED),
                            ], horizontal_alignment=ft.CrossAxisAlignment.END),
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.only(bottom=20)
                ),
                
                # FORMULARIO CON SCROLL
                ft.Container(
                    content=ft.Column([
                        # Sección 1: Información básica
                        self.crear_seccion(
                            "info",
                            "Información Básica",
                            ft.ResponsiveRow([
                                ft.Column([self.descripcion_field], col={"md": 12}),
                            ], spacing=12),
                            icon="info"
                        ),
                        
                        ft.Container(height=16),
                        
                        # Sección 2: Transporte
                        self.crear_seccion(
                            "transporte",
                            "Información de Transporte",
                            ft.Column([
                                ft.ResponsiveRow([
                                    ft.Column([self.via_transporte_dropdown], col={"md": 6}),
                                    ft.Column([self.bl_number_field], col={"md": 6}),
                                ], spacing=12, run_spacing=12),
                                ft.Container(height=12),
                                ft.ResponsiveRow([
                                    ft.Column([self.container_number_field], col={"md": 6}),
                                    ft.Column([self.nombre_nave_field], col={"md": 6}),
                                ], spacing=12, run_spacing=12),
                                ft.Container(height=12),
                                ft.ResponsiveRow([
                                    ft.Column([self.numero_viaje_field], col={"md": 6}),
                                    ft.Column([ft.Container()], col={"md": 6}),
                                ], spacing=12, run_spacing=12),
                            ]),
                            icon="local_shipping"
                        ),
                        
                        ft.Container(height=16),
                        
                        # Sección 3: Fechas y agentes
                        self.crear_seccion(
                            "fechas",
                            "Fechas y Agentes",
                            ft.Column([
                                ft.ResponsiveRow([
                                    ft.Column([self.fecha_embarque_field], col={"md": 6}),
                                    ft.Column([self.fecha_arribo_field], col={"md": 6}),
                                ], spacing=12, run_spacing=12),
                                ft.Container(height=12),
                                ft.ResponsiveRow([
                                    ft.Column([self.agente_aduanero_field], col={"md": 6}),
                                    ft.Column([self.agente_carga_field], col={"md": 6}),
                                ], spacing=12, run_spacing=12),
                            ]),
                            icon="calendar_today"
                        ),
                        
                        ft.Container(height=16),
                        
                        # Sección 4: Estado y notas
                        self.crear_seccion(
                            "estado",
                            "Estado y Notas",
                            ft.ResponsiveRow([
                                ft.Column([self.estado_dropdown], col={"md": 4}),
                                ft.Column([self.notas_field], col={"md": 8}),
                            ], spacing=12, run_spacing=12),
                            icon="flag"
                        ),
                        
                        ft.Container(height=32),
                        
                        # Botones de acción
                        ft.Container(
                            content=ft.Row([
                                ft.ElevatedButton(
                                    "Cancelar",
                                    icon="arrow_back",
                                    on_click=lambda e: self.page.go("/importaciones"),
                                    style=ft.ButtonStyle(
                                        bgcolor=ImportacionesTheme.TEXT_SECONDARY,
                                        color="white"
                                    )
                                ),
                                ft.Container(expand=True),
                                ft.ElevatedButton(
                                    "Guardar Borrador",
                                    icon="save",
                                    on_click=lambda e: self.save_importacion(guardar_como="planificada"),
                                    style=ft.ButtonStyle(
                                        bgcolor=ImportacionesTheme.BORDER,
                                        color=ImportacionesTheme.TEXT_PRIMARY
                                    )
                                ),
                                ft.ElevatedButton(
                                    "Guardar y Activar",
                                    icon="check_circle",
                                    on_click=lambda e: self.save_importacion(guardar_como="en_transito"),
                                    style=ft.ButtonStyle(
                                        bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                                        color="white"
                                    )
                                ),
                            ], spacing=12),
                            padding=ft.padding.symmetric(vertical=16),
                            border=ft.border.only(top=ft.BorderSide(1, ImportacionesTheme.BORDER))
                        ),
                    ]),
                    expand=True,
                )
            ],scroll=ft.ScrollMode.AUTO),
            padding=24,
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )
    
    def get_titulo(self):
        """Obtener título según si es edición o nuevo"""
        if self.importacion_data:
            return f"📦 Editar Importación: {self.importacion_data.get('numero_importacion', '')}"
        else:
            return "📦 Nueva Importación (Folder Manila)"
    
    def crear_seccion(self, key, titulo, contenido, icon="info"):
        """Crear una sección del formulario"""
        return ft.Container(
            key=key,
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, size=20, color=ImportacionesTheme.STATUS_CONFIRMED),
                    ft.Text(titulo, size=16, 
                           weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                ], spacing=8),
                ft.Container(height=16),
                contenido,
            ]),
            padding=20,
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
        )
    
    def load_importacion_data(self):
        """Cargar datos de la importación si es edición"""
        query = "SELECT * FROM importaciones WHERE id = %s"
        result = self.db.execute_query(query, (self.importacion_id,))
        if result:
            self.importacion_data = result[0]
    
    def fill_form_fields(self):
        """Llenar campos del formulario con datos existentes"""
        data = self.importacion_data
        
        if data.get('descripcion'):
            self.descripcion_field.value = data['descripcion']
        
        if data.get('bl_number'):
            self.bl_number_field.value = data['bl_number']
        
        if data.get('container_number'):
            self.container_number_field.value = data['container_number']
        
        if data.get('via_transporte'):
            self.via_transporte_dropdown.value = data['via_transporte']
        
        if data.get('nombre_nave'):
            self.nombre_nave_field.value = data['nombre_nave']
            self.nombre_nave_field.visible = True
        
        if data.get('numero_viaje'):
            self.numero_viaje_field.value = data['numero_viaje']
            self.numero_viaje_field.visible = True
        
        if data.get('fecha_embarque'):
            self.fecha_embarque_field.value = str(data['fecha_embarque'])
        
        if data.get('fecha_arribo_estimada'):
            self.fecha_arribo_field.value = str(data['fecha_arribo_estimada'])
        
        if data.get('agente_aduanero'):
            self.agente_aduanero_field.value = data['agente_aduanero']
        
        if data.get('agente_carga'):
            self.agente_carga_field.value = data['agente_carga']
        
        if data.get('estado'):
            self.estado_dropdown.value = data['estado']
        
        if data.get('notas'):
            self.notas_field.value = data['notas']
    
    def mostrar_date_picker(self, target):
        """Mostrar el date picker"""
        self.date_picker_target = target
        self.date_picker.pick_date()
    
    def on_date_pick(self, e):
        """Manejador cuando se selecciona una fecha"""
        if self.date_picker_target and e.control.value:
            fecha_str = e.control.value.strftime("%Y-%m-%d")
            if self.date_picker_target == "embarque":
                self.fecha_embarque_field.value = fecha_str
            elif self.date_picker_target == "arribo":
                self.fecha_arribo_field.value = fecha_str
            self.page.update()
    
    def save_importacion(self, guardar_como=None):
        """Guardar importación en la base de datos"""
        
        # Validar campos obligatorios
        if not self.descripcion_field.value:
            self.show_error("La descripción es obligatoria")
            return
        
        if not self.via_transporte_dropdown.value:
            self.show_error("La vía de transporte es obligatoria")
            return
        
        # Preparar datos
        importacion_data = {
            'descripcion': self.descripcion_field.value,
            'bl_number': self.bl_number_field.value or None,
            'container_number': self.container_number_field.value or None,
            'via_transporte': self.via_transporte_dropdown.value,
            'nombre_nave': self.nombre_nave_field.value if self.via_transporte_dropdown.value == "maritimo" else None,
            'numero_viaje': self.numero_viaje_field.value if self.via_transporte_dropdown.value == "maritimo" else None,
            'fecha_embarque': self.parse_date(self.fecha_embarque_field.value),
            'fecha_arribo_estimada': self.parse_date(self.fecha_arribo_field.value),
            'agente_aduanero': self.agente_aduanero_field.value or None,
            'agente_carga': self.agente_carga_field.value or None,
            'estado': guardar_como or self.estado_dropdown.value,
            'notas': self.notas_field.value or None,
        }
        
        try:
            if self.importacion_id:
                # Actualizar existente
                update_query = """
                    UPDATE importaciones 
                    SET descripcion = %s, bl_number = %s, container_number = %s,
                        via_transporte = %s, nombre_nave = %s, numero_viaje = %s,
                        fecha_embarque = %s, fecha_arribo_estimada = %s,
                        agente_aduanero = %s, agente_carga = %s, estado = %s,
                        notas = %s, updated_at = NOW()
                    WHERE id = %s
                """
                params = tuple(importacion_data.values()) + (self.importacion_id,)
                result = self.db.execute_query(update_query, params, fetch=False)
                message = "✅ Importación actualizada correctamente"
                
                # Si el trigger no generó número, generarlo manualmente
                if not self.importacion_data.get('numero_importacion'):
                    self.generar_numero_manual(self.importacion_id)
                
            else:
                # Crear nueva (el trigger generará el número automáticamente)
                insert_query = """
                    INSERT INTO importaciones 
                    (descripcion, bl_number, container_number, via_transporte,
                     nombre_nave, numero_viaje, fecha_embarque, fecha_arribo_estimada,
                     agente_aduanero, agente_carga, estado, notas, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
                """
                importacion_id = self.db.execute_query(insert_query, tuple(importacion_data.values()), fetch=False)
                
                # Si el trigger falló, generar número manualmente
                if importacion_id:
                    self.generar_numero_manual(importacion_id)
                
                message = "✅ Importación creada correctamente"
            
            # Mostrar mensaje de éxito
            self.show_success(message)
            
            # Redirigir a la lista
            self.page.go("/importaciones")
            
        except Exception as e:
            self.show_error(f"Error al guardar: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def generar_numero_manual(self, importacion_id):
        """Generar número de importación manualmente si el trigger falló"""
        try:
            año_actual = datetime.now().year
            
            # Buscar el último número del año actual
            query = """
                SELECT COALESCE(MAX(CAST(SUBSTRING(numero_importacion, 6) AS UNSIGNED)), 0) as max_num
                FROM importaciones 
                WHERE numero_importacion LIKE %s AND id != %s
            """
            result = self.db.execute_query(query, (f"{año_actual}-%", importacion_id))
            
            siguiente_numero = 1
            if result and result[0]['max_num']:
                siguiente_numero = result[0]['max_num'] + 1
            
            numero = f"{año_actual}-{str(siguiente_numero).zfill(3)}"
            
            # Actualizar el registro
            update_query = "UPDATE importaciones SET numero_importacion = %s WHERE id = %s"
            self.db.execute_query(update_query, (numero, importacion_id), fetch=False)
            
            print(f"✅ Número generado manualmente: {numero}")
            
        except Exception as e:
            print(f"⚠️ Error generando número manual: {e}")
    
    def parse_date(self, date_str):
        """Parsear fecha de string a objeto Date"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            # Intentar otros formatos
            try:
                return datetime.strptime(date_str, "%d/%m/%Y").date()
            except:
                return None
    
    def show_error(self, message):
        """Mostrar mensaje de error"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="white"),
            bgcolor=ImportacionesTheme.ERROR,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def show_success(self, message):
        """Mostrar mensaje de éxito"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="white"),
            bgcolor=ImportacionesTheme.SUCCESS,
        )
        self.page.snack_bar.open = True
        self.page.update()

