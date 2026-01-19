# views/transporte_form_view.py - VERSIÓN CORREGIDA
import flet as ft
from datetime import datetime
from config_importaciones import (
    ImportacionesTheme, ImportacionesConfig,
    format_currency, format_date
)

class TransporteFormView:
    def __init__(self, page: ft.Page, db, documento_id=None):
        self.page = page
        self.db = db
        self.documento_id = documento_id
        self.modo_edicion = documento_id is not None
        
        # FilePicker debe agregarse al overlay de la página
        self.file_picker = ft.FilePicker(on_result=self.subir_documento)
        page.overlay.append(self.file_picker)
        
        # Datos para combos
        self.importaciones = []
        
        # Crear controles
        self.crear_controles()
        
        # Cargar datos iniciales
        self.cargar_datos_combos()
        if self.modo_edicion:
            self.cargar_documento()
    
    def crear_controles(self):
        """Crea todos los controles del formulario"""
        # Cambio principal: Importación en lugar de PO
        self.importacion = ft.Dropdown(
            label="Importación (Folder Manila) *",
            prefix_icon=ft.Icons.FOLDER,
            border_color=ImportacionesTheme.BORDER,
            filled=True,
            options=[]
        )
        
        self.document_type = ft.Dropdown(
            label="Tipo de Documento *",
            prefix_icon=ft.Icons.DESCRIPTION,
            border_color=ImportacionesTheme.BORDER,
            filled=True,
            options=[
                ft.dropdown.Option("bill_of_lading", "Conocimiento de Embarque (BL)"),
                ft.dropdown.Option("air_waybill", "Guía Aérea (AWB)"),
                ft.dropdown.Option("carta_porte", "Carta de Porte"),
                ft.dropdown.Option("other", "Otro Documento"),
            ]
        )
        
        self.document_number = ft.TextField(
            label="Número de Documento *",
            prefix_icon=ft.Icons.NUMBERS,
            border_color=ImportacionesTheme.BORDER,
            filled=True,
        )
        
        self.carrier = ft.TextField(
            label="Transportista / Naviera",
            prefix_icon=ft.Icons.FLIGHT,
            border_color=ImportacionesTheme.BORDER,
            filled=True
        )
        
        self.vessel_name = ft.TextField(
            label="Nombre de la Nave / Vuelo",
            prefix_icon=ft.Icons.DIRECTIONS_BOAT,
            border_color=ImportacionesTheme.BORDER,
            filled=True
        )
        
        self.voyage_number = ft.TextField(
            label="Número de Viaje / Vuelo",
            prefix_icon=ft.Icons.CONFIRMATION_NUMBER,
            border_color=ImportacionesTheme.BORDER,
            filled=True
        )
        
        self.etd_date = ft.TextField(
            label="Fecha ETD (Salida)",
            prefix_icon=ft.Icons.FLIGHT_TAKEOFF,
            border_color=ImportacionesTheme.BORDER,
            filled=True,
            hint_text="YYYY-MM-DD"
        )
        
        self.eta_date = ft.TextField(
            label="Fecha ETA (Llegada)",
            prefix_icon=ft.Icons.FLIGHT_LAND,
            border_color=ImportacionesTheme.BORDER,
            filled=True,
            hint_text="YYYY-MM-DD"
        )
        
        self.actual_arrival = ft.TextField(
            label="Fecha Real de Llegada",
            prefix_icon=ft.Icons.EVENT_AVAILABLE,
            border_color=ImportacionesTheme.BORDER,
            filled=True,
            hint_text="YYYY-MM-DD"
        )
        
        self.total_packages = ft.TextField(
            label="Total de Bultos",
            prefix_icon=ft.Icons.INVENTORY_2,
            border_color=ImportacionesTheme.BORDER,
            filled=True,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        self.gross_weight = ft.TextField(
            label="Peso Bruto (kg)",
            prefix_icon=ft.Icons.SCALE,
            border_color=ImportacionesTheme.BORDER,
            filled=True,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        self.volume = ft.TextField(
            label="Volumen (m³)",
            prefix_icon=ft.Icons.VIEW_IN_AR,
            border_color=ImportacionesTheme.BORDER,
            filled=True,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        self.tracking_url = ft.TextField(
            label="URL de Seguimiento",
            prefix_icon=ft.Icons.TRACK_CHANGES,
            border_color=ImportacionesTheme.BORDER,
            filled=True
        )
        
        self.notes = ft.TextField(
            label="Notas",
            prefix_icon=ft.Icons.NOTES,
            border_color=ImportacionesTheme.BORDER,
            filled=True,
            multiline=True,
            min_lines=3,
            max_lines=5
        )
        
        # Botón para subir archivo
        self.upload_button = ft.ElevatedButton(
            "Subir Documento",
            icon=ft.Icons.UPLOAD_FILE,
            on_click=lambda e: self.file_picker.pick_files(
                allow_multiple=False,
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'],
                file_type=ft.FilePickerFileType.CUSTOM,
            ),
            style=ft.ButtonStyle(
                bgcolor=ImportacionesTheme.INFO,
                color="white"
            )
        )
        
        # Botones de acción
        self.cancel_button = ft.ElevatedButton(
            "Cancelar",
            icon=ft.Icons.CANCEL,
            on_click=lambda e: self.page.go("/transporte"),
            style=ft.ButtonStyle(
                bgcolor=ImportacionesTheme.BG_SECONDARY,
                color=ImportacionesTheme.TEXT_PRIMARY
            ),
        )
        
        self.save_button = ft.ElevatedButton(
            "Guardar Documento",
            icon=ft.Icons.SAVE,
            on_click=self.guardar_documento,
            style=ft.ButtonStyle(
                bgcolor=ImportacionesTheme.SUCCESS,
                color="white"
            ),
        )
    
    def cargar_datos_combos(self):
        """Carga datos para los combos desde la base de datos - IMPORTACIONES"""
        try:
            query = """
                SELECT 
                    i.id,
                    i.numero_importacion,
                    i.descripcion,
                    i.estado,
                    COUNT(DISTINCT ip.po_id) as cantidad_pos
                FROM importaciones i
                LEFT JOIN importacion_pos ip ON i.id = ip.importacion_id
                WHERE i.estado NOT IN ('cancelada', 'completada')
                GROUP BY i.id, i.numero_importacion, i.descripcion, i.estado
                ORDER BY i.numero_importacion DESC
            """
            result = self.db.execute_query(query)
            
            if result:
                self.importaciones = result
                options = []
                for imp in result:
                    descripcion = imp.get('descripcion', '')[:30] if imp.get('descripcion') else 'Sin descripción'
                    cantidad_pos = imp.get('cantidad_pos', 0)
                    label = f"{imp['numero_importacion']} - {descripcion} ({cantidad_pos} POs)"
                    options.append(ft.dropdown.Option(str(imp['id']), label))
                
                self.importacion.options = options
                print(f"[DEBUG] Importaciones cargadas: {len(options)}")
            else:
                print("[DEBUG] No se encontraron importaciones")
                self.importacion.options = []
                
        except Exception as ex:
            print(f"[ERROR] Error cargando importaciones: {ex}")
            self.importacion.options = []
    
    def cargar_documento(self):
        """Carga los datos de un documento existente"""
        try:
            query = """
                SELECT sd.*
                FROM shipping_documents sd
                WHERE sd.id = %s
            """
            result = self.db.execute_query(query, (self.documento_id,))
            
            if result:
                doc = result[0]
                
                # Campos básicos - Usar importacion_id
                if doc.get('importacion_id'):
                    self.importacion.value = str(doc['importacion_id'])
                
                self.document_type.value = doc.get('document_type')
                self.document_number.value = doc.get('document_number') or ''
                self.carrier.value = doc.get('carrier') or ''
                self.vessel_name.value = doc.get('vessel_name') or ''
                self.voyage_number.value = doc.get('voyage_number') or ''
                self.etd_date.value = format_date(doc.get('etd_date')) if doc.get('etd_date') else ''
                self.eta_date.value = format_date(doc.get('eta_date')) if doc.get('eta_date') else ''
                self.actual_arrival.value = format_date(doc.get('actual_arrival')) if doc.get('actual_arrival') else ''
                self.total_packages.value = str(doc.get('total_packages')) if doc.get('total_packages') else ''
                self.gross_weight.value = str(doc.get('gross_weight')) if doc.get('gross_weight') else ''
                self.volume.value = str(doc.get('volume')) if doc.get('volume') else ''
                self.tracking_url.value = doc.get('tracking_url') or ''
                self.notes.value = doc.get('notes') or ''
                
                print(f"[DEBUG] Documento cargado: {doc.get('document_number')}")
        except Exception as ex:
            print(f"[ERROR] Error cargando documento: {ex}")
    
    def subir_documento(self, e: ft.FilePickerResultEvent):
        """Procesa la subida de un archivo de documento"""
        if e.files:
            file_name = e.files[0].name
            self.mostrar_mensaje(f"✅ Documento {file_name} seleccionado", ImportacionesTheme.SUCCESS)
    
    def validar_formulario(self):
        """Valida los datos del formulario"""
        errores = []
        
        if not self.importacion.value:
            errores.append("Debe seleccionar una importación")
        
        if not self.document_type.value:
            errores.append("Debe seleccionar un tipo de documento")
        
        if not self.document_number.value or not self.document_number.value.strip():
            errores.append("El número de documento es requerido")
        
        return errores
    
    def parse_date(self, date_str):
        """Función para convertir fechas a formato MySQL"""
        if not date_str:
            return None
        
        date_str = date_str.strip()
        if not date_str:
            return None
        
        # Si ya está en formato YYYY-MM-DD
        if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
            try:
                year, month, day = map(int, date_str.split('-'))
                if 1 <= month <= 12 and 1 <= day <= 31:
                    return date_str
            except:
                pass
        
        # Intentar diferentes formatos
        try:
            # Formato DD/MM/YYYY
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3 and len(parts[2]) == 4:
                    day, month, year = map(int, parts)
                    return f"{year:04d}-{month:02d}-{day:02d}"
            
            # Formato DD-MM-YYYY
            elif '-' in date_str:
                parts = date_str.split('-')
                if len(parts) == 3 and len(parts[0]) == 2:
                    day, month, year = map(int, parts)
                    return f"{year:04d}-{month:02d}-{day:02d}"
            
            # Formato DD.MM.YYYY
            elif '.' in date_str:
                parts = date_str.split('.')
                if len(parts) == 3 and len(parts[2]) == 4:
                    day, month, year = map(int, parts)
                    return f"{year:04d}-{month:02d}-{day:02d}"
                    
        except Exception as e:
            print(f"[WARNING] Error al parsear fecha '{date_str}': {e}")
        
        return None
    
    def guardar_documento(self, e):
        """Guarda el documento en la base de datos"""
        print("=== GUARDANDO DOCUMENTO DE TRANSPORTE ===")
        
        # Validar formulario
        errores = self.validar_formulario()
        if errores:
            self.mostrar_error("\n".join(errores))
            return
        
        # Deshabilitar botón mientras guarda
        self.save_button.disabled = True
        self.save_button.text = "Guardando..."
        self.page.update()
        
        try:
            # Preparar datos
            importacion_id = int(self.importacion.value)
            
            # Parsear fechas
            etd_date = self.parse_date(self.etd_date.value)
            eta_date = self.parse_date(self.eta_date.value)
            actual_arrival = self.parse_date(self.actual_arrival.value)
            
            # Convertir valores numéricos
            total_packages = None
            if self.total_packages.value and self.total_packages.value.strip():
                try:
                    total_packages = int(self.total_packages.value.strip())
                except ValueError:
                    pass
            
            gross_weight = None
            if self.gross_weight.value and self.gross_weight.value.strip():
                try:
                    gross_weight = float(self.gross_weight.value.strip())
                except ValueError:
                    pass
            
            volume = None
            if self.volume.value and self.volume.value.strip():
                try:
                    volume = float(self.volume.value.strip())
                except ValueError:
                    pass
            
            # Usuario (por ahora hardcodeado)
            created_by = 1
            
            if self.modo_edicion:
                # Actualizar documento existente
                query = """
                    UPDATE shipping_documents 
                    SET importacion_id = %s, document_type = %s, document_number = %s,
                        carrier = %s, vessel_name = %s, voyage_number = %s,
                        etd_date = %s, eta_date = %s, actual_arrival = %s,
                        total_packages = %s, gross_weight = %s, volume = %s,
                        tracking_url = %s, notes = %s, updated_by = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """
                params = (
                    importacion_id, 
                    self.document_type.value, 
                    self.document_number.value.strip(),
                    self.carrier.value.strip() if self.carrier.value else None,
                    self.vessel_name.value.strip() if self.vessel_name.value else None,
                    self.voyage_number.value.strip() if self.voyage_number.value else None,
                    etd_date, eta_date, actual_arrival,
                    total_packages, gross_weight, volume,
                    self.tracking_url.value.strip() if self.tracking_url.value else None,
                    self.notes.value.strip() if self.notes.value else None,
                    created_by,
                    self.documento_id
                )
            else:
                # Crear nuevo documento
                query = """
                    INSERT INTO shipping_documents
                    (importacion_id, document_type, document_number, carrier, vessel_name,
                    voyage_number, etd_date, eta_date, actual_arrival,
                    total_packages, gross_weight, volume, tracking_url, notes,
                    created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    importacion_id, 
                    self.document_type.value, 
                    self.document_number.value.strip(),
                    self.carrier.value.strip() if self.carrier.value else None,
                    self.vessel_name.value.strip() if self.vessel_name.value else None,
                    self.voyage_number.value.strip() if self.voyage_number.value else None,
                    etd_date, eta_date, actual_arrival,
                    total_packages, gross_weight, volume,
                    self.tracking_url.value.strip() if self.tracking_url.value else None,
                    self.notes.value.strip() if self.notes.value else None,
                    created_by
                )
            
            print(f"[DEBUG] Query: {query}")
            print(f"[DEBUG] Params: {params}")
            
            # Ejecutar consulta
            self.db.execute_query(query, params, fetch=False)
            
            self.mostrar_exito("✅ Documento guardado exitosamente")
            
            # Redirigir
            import threading
            def redirigir():
                self.page.go("/transporte")
            
            timer = threading.Timer(1.0, redirigir)
            timer.start()
            
        except Exception as ex:
            print(f"[ERROR] Error al guardar: {ex}")
            import traceback
            traceback.print_exc()
            self.mostrar_error(f"Error al guardar: {str(ex)}")
            
            # Rehabilitar botón
            self.save_button.disabled = False
            self.save_button.text = "Guardar Documento"
            self.page.update()
    
    def mostrar_mensaje(self, mensaje, color):
        """Muestra un mensaje en snackbar"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje, color="white"),
            bgcolor=color,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def mostrar_error(self, mensaje):
        """Muestra un mensaje de error"""
        self.mostrar_mensaje(mensaje, ImportacionesTheme.ERROR)
    
    def mostrar_exito(self, mensaje):
        """Muestra un mensaje de éxito"""
        self.mostrar_mensaje(mensaje, ImportacionesTheme.SUCCESS)
    
    def form_view(self):
        """Retorna la vista completa del formulario"""
        titulo = f"Editar Documento #{self.documento_id}" if self.modo_edicion else "Nuevo Documento de Transporte"
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.LOCAL_SHIPPING, size=24, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text(titulo, size=24, 
                                       weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                            ], spacing=12),
                            ft.Text("Registro de documentos de transporte internacional", 
                                   size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                        ]),
                        ft.ElevatedButton(
                            "Volver a la lista",
                            icon=ft.Icons.ARROW_BACK,
                            on_click=lambda e: self.page.go("/transporte"),
                            style=ft.ButtonStyle(
                                bgcolor=ImportacionesTheme.BG_SECONDARY,
                                color=ImportacionesTheme.TEXT_PRIMARY
                            ),
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.symmetric(vertical=16),
                ),
                
                # Formulario principal
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            # Sección 1: Información básica
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.Icons.INFO, size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Text("Información del Documento", size=16, 
                                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                    ], spacing=8),
                                    ft.Divider(height=20),
                                    ft.ResponsiveRow([
                                        ft.Column([self.importacion], col={"md": 6}),
                                        ft.Column([self.document_type], col={"md": 6}),
                                    ], spacing=16, run_spacing=16),
                                    ft.ResponsiveRow([
                                        ft.Column([self.document_number], col={"md": 6}),
                                        ft.Column([self.upload_button], col={"md": 6}),
                                    ], spacing=16, run_spacing=16),
                                ]),
                                padding=20,
                                border=ft.border.all(1, ImportacionesTheme.BORDER),
                                border_radius=8,
                                margin=ft.margin.only(bottom=20),
                            ),
                            
                            # Sección 2: Información del transporte
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.Icons.FLIGHT, size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Text("Información del Transporte", size=16, 
                                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                    ], spacing=8),
                                    ft.Divider(height=20),
                                    ft.ResponsiveRow([
                                        ft.Column([self.carrier], col={"md": 6}),
                                        ft.Column([self.vessel_name], col={"md": 6}),
                                    ], spacing=16, run_spacing=16),
                                    ft.ResponsiveRow([
                                        ft.Column([self.voyage_number], col={"md": 4}),
                                        ft.Column([self.tracking_url], col={"md": 8}),
                                    ], spacing=16, run_spacing=16),
                                ]),
                                padding=20,
                                border=ft.border.all(1, ImportacionesTheme.BORDER),
                                border_radius=8,
                                margin=ft.margin.only(bottom=20),
                            ),
                            
                            # Sección 3: Fechas
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.Icons.EVENT, size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Text("Fechas Importantes", size=16, 
                                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                    ], spacing=8),
                                    ft.Divider(height=20),
                                    ft.ResponsiveRow([
                                        ft.Column([self.etd_date], col={"md": 4}),
                                        ft.Column([self.eta_date], col={"md": 4}),
                                        ft.Column([self.actual_arrival], col={"md": 4}),
                                    ], spacing=16, run_spacing=16),
                                ]),
                                padding=20,
                                border=ft.border.all(1, ImportacionesTheme.BORDER),
                                border_radius=8,
                                margin=ft.margin.only(bottom=20),
                            ),
                            
                            # Sección 4: Detalles de la carga
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.Icons.INVENTORY_2, size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Text("Detalles de la Carga", size=16, 
                                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                    ], spacing=8),
                                    ft.Divider(height=20),
                                    ft.ResponsiveRow([
                                        ft.Column([self.total_packages], col={"md": 4}),
                                        ft.Column([self.gross_weight], col={"md": 4}),
                                        ft.Column([self.volume], col={"md": 4}),
                                    ], spacing=16, run_spacing=16),
                                ]),
                                padding=20,
                                border=ft.border.all(1, ImportacionesTheme.BORDER),
                                border_radius=8,
                                margin=ft.margin.only(bottom=20),
                            ),
                            
                            # Sección 5: Notas
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.Icons.NOTES, size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Text("Observaciones y Notas", size=16, 
                                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                    ], spacing=8),
                                    ft.Divider(height=20),
                                    self.notes,
                                ]),
                                padding=20,
                                border=ft.border.all(1, ImportacionesTheme.BORDER),
                                border_radius=8,
                                margin=ft.margin.only(bottom=20),
                            ),
                            
                            # Botones de acción
                            ft.Container(
                                content=ft.Row([
                                    self.cancel_button,
                                    ft.Container(width=20),
                                    self.save_button,
                                ], alignment=ft.MainAxisAlignment.END),
                                padding=ft.padding.only(top=10),
                            ),
                        ]),
                        padding=20,
                    ),
                    elevation=2,
                ),
            ], scroll=ft.ScrollMode.AUTO),
            padding=24,
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )  






