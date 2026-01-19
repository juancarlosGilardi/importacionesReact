# views/factura_form_view.py
import flet as ft
from datetime import datetime
from config_importaciones import (
    ImportacionesTheme, ImportacionesConfig,
    format_currency, format_date, get_status_color
)

class FacturaFormView:
    def __init__(self, page: ft.Page, db, factura_id=None, po_id=None):
        self.page = page
        self.db = db
        self.factura_id = factura_id
        self.modo_edicion = factura_id is not None
        self.po_id = po_id
        self.xml_file_path = None
        self.pdf_file_path = None
        self.tipo_archivo_actual = None
        self.file_picker = ft.FilePicker(
            on_result=self.handle_file_upload
        )
        self.page.overlay.append(self.file_picker)
        

        # Campos del formulario
        self.controls = self.crear_controles()
        
        # Cargar datos iniciales
        self.cargar_datos_combos()
        if self.modo_edicion:
            self.cargar_factura()
        elif self.po_id:
            self.cargar_orden_por_defecto()
    
    def crear_controles(self):
        """Crea todos los controles del formulario"""
        return {
            'po_id': ft.Dropdown( 
                label="Orden de Compra *",
                prefix_icon="shopping_cart",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                options=[],

                on_change=self.cargar_items_orden
            ),
            
            'invoice_number': ft.TextField(
                label="Número de Factura *",
                prefix_icon="receipt",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
            ),
            
            'invoice_date': ft.TextField(
                label="Fecha de Factura *",
                prefix_icon="event",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value=datetime.now().strftime("%Y-%m-%d"),
                hint_text="YYYY-MM-DD"
            ),
            
            'supplier_id': ft.Dropdown(
                label="Proveedor *",
                prefix_icon="business",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                options=[],
            ),
            
            'currency_id': ft.Dropdown(
                label="Moneda *",
                prefix_icon="paid",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                options=[],

                value="1"  # USD por defecto
            ),
            
            'exchange_rate': ft.TextField(
                label="Tipo de Cambio *",
                prefix_icon="currency_exchange",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="3.75",
            ),
            
            'subtotal': ft.TextField(
                label="Subtotal (sin IGV) **",
                prefix_icon="attach_money",
                border_color=ImportacionesTheme.BORDER,
                filled=True,

                on_change=self.calcular_total
            ),
            'tax_rate': ft.Dropdown( 
                label="Tasa de IGV (%)",
                prefix_icon="percent",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                options=[
                    ft.dropdown.Option("0", "0% - Exonerado"),
                    ft.dropdown.Option("18", "18% - IGV General"),
                ],
                value="18",
                on_change=self.calcular_impuestos_auto
            ),
            
            'tax_amount': ft.TextField(
                label="IGV *",
                prefix_icon="request_quote",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="0.00",
                read_only=True,
                on_change=self.calcular_total
            ),
            
            'xml_display': ft.TextField(
                label="XML Adjunto",
                prefix_icon="description",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                read_only=True,
                value=""
            ),
            
            'pdf_display': ft.TextField(
                label="PDF Adjunto",
                prefix_icon="picture_as_pdf",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                read_only=True,
                value=""
            ),
            
            'total_amount': ft.TextField(
                label="Total *",
                prefix_icon="summarize",
                border_color=ImportacionesTheme.BORDER,
                filled=True,

                read_only=True
            ),
            
            'xml_file_path': ft.TextField(
                label="Ruta XML",
                prefix_icon="description",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                read_only=True
            ),
            
            'archivo_pdf': ft.TextField(
                label="Archivo PDF",
                prefix_icon="picture_as_pdf",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                read_only=True
            ),
            
            'status': ft.Dropdown(
                label="Estado",
                prefix_icon="status",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                options=[
                    ft.dropdown.Option("pending", "Pendiente"),
                    ft.dropdown.Option("validated", "Validada"),
                    ft.dropdown.Option("paid", "Pagada"),
                    ft.dropdown.Option("cancelled", "Cancelada"),
                ],
                value="pending"
            ),
            
            'notes': ft.TextField(
                label="Notas",
                prefix_icon="notes",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                multiline=True,
                min_lines=3,
                max_lines=5
            ),

            'xml_upload_btn': ft.ElevatedButton(
                "Subir XML",
                icon="upload_file",
                on_click=lambda e: self.subir_xml(e),
            ),
            
            'pdf_upload_btn': ft.ElevatedButton(
                "Subir PDF",
                icon="upload_file",
                on_click=lambda e: self.subir_pdf(e),
            ),
        }
    
    def subir_xml(self, e):
        """Abre diálogo para subir XML"""
        # Guardar tipo de archivo que estamos subiendo
        self.tipo_archivo_actual = "xml"
        self.file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["xml"],
            dialog_title="Seleccionar archivo XML"
        )
    
    def subir_pdf(self, e):
        """Abre diálogo para subir PDF"""
        self.tipo_archivo_actual = "pdf"
        self.file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["pdf"],
            dialog_title="Seleccionar archivo PDF"
        )
    
    def cargar_orden_por_defecto(self):
        """Carga PO si viene de URL"""
        if self.po_id:
            self.controls['po_id'].value = str(self.po_id)
            # Cargar datos automáticos de la PO
            query = """
                SELECT po.*, s.id as supplier_id, s.business_name,
                       (SELECT SUM(fob_value) FROM purchase_order_items WHERE po_id = po.id) as subtotal
                FROM purchase_orders po
                LEFT JOIN suppliers s ON po.supplier_id = s.id
                WHERE po.id = %s
            """
            result = self.db.execute_query(query, (self.po_id,))
            if result:
                data = result[0]
                self.controls['po_id'].value = str(data['id'])
                self.controls['supplier_id'].value = str(data['supplier_id'])
                if data['subtotal']:
                    self.controls['subtotal'].value = str(data['subtotal'])
                    self.calcular_impuestos_auto(None)
    
    def calcular_impuestos_auto(self, e):
        """Calcula IGV automáticamente"""
        try:
            subtotal = float(self.controls['subtotal'].value or 0)
            tax_rate = float(self.controls['tax_rate'].value or 0)
            
            tax_amount = subtotal * (tax_rate / 100)
            total = subtotal + tax_amount
            
            self.controls['tax_amount'].value = f"{tax_amount:.2f}"
            self.controls['total_amount'].value = f"{total:.2f}"
        except ValueError:
            pass
        self.page.update()

    def handle_file_upload(self, e: ft.FilePickerResultEvent):
        """Maneja la subida de archivos"""
        if e.files:
            archivo = e.files[0]
            nombre_archivo = archivo.name
            
            if self.tipo_archivo_actual == "xml":
                self.xml_file_path = nombre_archivo
                self.controls['xml_display'].value = nombre_archivo
                self.mostrar_exito(f"XML cargado: {nombre_archivo}")
            elif self.tipo_archivo_actual == "pdf":
                self.pdf_file_path = nombre_archivo
                self.controls['pdf_display'].value = nombre_archivo
                self.mostrar_exito(f"PDF cargado: {nombre_archivo}")
            
            self.page.update()
    
    def cargar_datos_combos(self):
        """Carga datos para los combos desde la base de datos"""
        # Órdenes de compra
        query = """
            SELECT po.id, po.po_number, s.business_name 
            FROM purchase_orders po
            LEFT JOIN suppliers s ON po.supplier_id = s.id
            WHERE po.status IN ('confirmada', 'en_transito', 'en_aduana')
            ORDER BY po.order_date DESC
        """
        result = self.db.execute_query(query)
        if result:
            options = [ft.dropdown.Option(str(po['id']), f"{po['po_number']} - {po['business_name']}") for po in result]
            self.controls['po_id'].options = options  # ← CORREGIDO: 'po_id' en lugar de 'po'
        
        # Proveedores
        query = "SELECT id, ruc, business_name FROM suppliers WHERE status = 'active' ORDER BY business_name"
        result = self.db.execute_query(query)
        if result:
            options = [ft.dropdown.Option(str(s['id']), f"{s['business_name']} ({s['ruc']})") for s in result]
            self.controls['supplier_id'].options = options
        
        # Monedas
        query = "SELECT id, code, name FROM currencies ORDER BY code"
        result = self.db.execute_query(query)
        if result:
            options = [ft.dropdown.Option(str(c['id']), c['code']) for c in result]
            self.controls['currency_id'].options = options
    
    def cargar_items_orden(self, e):
        """Carga los items de la orden de compra seleccionada"""
        po_id = self.controls['po_id'].value
        if not po_id:
            return
        
        # Cargar items de la orden
        query = """
            SELECT poi.*, p.sku, p.name as product_name
            FROM purchase_order_items poi
            LEFT JOIN products p ON poi.product_id = p.id
            WHERE poi.po_id = %s
        """
        result = self.db.execute_query(query, (po_id,))
        
        # Aquí puedes cargar los items en una tabla o lista
        # Por ahora, solo mostramos mensaje en consola
        print(f"Items cargados para PO #{po_id}: {len(result or [])} items")
        
        # Calcular subtotal automáticamente si no está ingresado
        if not self.controls['subtotal'].value and result:
            subtotal = sum(float(item['fob_value'] or 0) for item in result)
            self.controls['subtotal'].value = str(subtotal)
            self.calcular_total(None)
    
    def calcular_total(self, e):
        """Calcula el total de la factura"""
        self.calcular_impuestos_auto(e)
    
    def cargar_factura(self):
        """Carga los datos de una factura existente"""
        query = """
            SELECT si.*, c.code as currency_code
            FROM supplier_invoices si
            LEFT JOIN currencies c ON si.currency_id = c.id
            WHERE si.id = %s
        """
        result = self.db.execute_query(query, (self.factura_id,))
        if result:
            factura = result[0]
            
            # Campos básicos
            self.controls['po_id'].value = str(factura['po_id'])
            self.controls['invoice_number'].value = factura['invoice_number']
            self.controls['invoice_date'].value =  str(factura['invoice_date'])
            self.controls['supplier_id'].value = str(factura['supplier_id'])
            self.controls['currency_id'].value = str(factura['currency_id'])
            self.controls['exchange_rate'].value = str(factura['exchange_rate'])
            self.controls['subtotal'].value = str(factura['subtotal'])
            self.controls['tax_amount'].value = str(factura['tax_amount'])
            self.controls['total_amount'].value = str(factura['total_amount'])
            self.controls['xml_file_path'].value = factura['xml_file_path'] or ''
            self.controls['archivo_pdf'].value = factura['archivo_pdf'] or ''
            self.controls['status'].value = factura['status']
            self.controls['notes'].value = factura['notes'] or ''
    
    def validar_formulario(self):
        """Valida los datos del formulario"""
        errores = []
        
        if not self.controls['po_id'].value:
            errores.append("Debe seleccionar una orden de compra")
        
        if not self.controls['invoice_number'].value:
            errores.append("Número de factura es requerido")
        
        if not self.controls['invoice_date'].value:
            errores.append("Fecha de factura es requerida")
        
        if not self.controls['supplier_id'].value:
            errores.append("Proveedor es requerido")
        
        if not self.controls['currency_id'].value:
            errores.append("Moneda es requerida")
        
        if not self.controls['subtotal'].value or float(self.controls['subtotal'].value or 0) <= 0:
            errores.append("Subtotal debe ser mayor a 0")
        
        if not self.controls['total_amount'].value or float(self.controls['total_amount'].value or 0) <= 0:
            errores.append("Total debe ser mayor a 0")
        try:
            datetime.strptime(self.controls['invoice_date'].value, "%Y-%m-%d")
        except ValueError:
            errores.append("Formato de fecha inválido. Use YYYY-MM-DD")
        
        # Validar números
        try:
            subtotal = float(self.controls['subtotal'].value or 0)
            if subtotal <= 0:
                errores.append("Subtotal debe ser mayor a 0")
        except ValueError:
            errores.append("Subtotal debe ser un número válido")
        
        return errores
    
    def guardar_factura(self, e):
        """Guarda o actualiza la factura"""
        print(f"\n=== GUARDAR FACTURA ===")
        print(f"Modo edición: {self.modo_edicion}")
        print(f"Factura ID: {self.factura_id}")
        
        # Validar formulario
        errores = self.validar_formulario()
        if errores:
            print(f"❌ Errores de validación: {errores}")
            self.mostrar_error("\n".join(errores))
            return
        
        fecha_str = self.controls['invoice_date'].value
        fecha_mysql = self.convertir_formato_fecha(fecha_str)
        # Obtener rutas de archivos
        xml_path = self.xml_file_path or self.controls['xml_file_path'].value
        pdf_path = self.pdf_file_path or self.controls['archivo_pdf'].value
        

        
        # Preparar datos
        factura_data = {
            'po_id': int(self.controls['po_id'].value),
            'invoice_number': self.controls['invoice_number'].value,
            'invoice_date': self.controls['invoice_date'].value,
            'supplier_id': int(self.controls['supplier_id'].value),
            'currency_id': int(self.controls['currency_id'].value),
            'exchange_rate': float(self.controls['exchange_rate'].value),
            'subtotal': float(self.controls['subtotal'].value),
            'tax_amount': float(self.controls['tax_amount'].value),
            'total_amount': float(self.controls['total_amount'].value),
            'xml_file_path': xml_path,
            'archivo_pdf': pdf_path,
            'status': self.controls['status'].value,
            'notes': self.controls['notes'].value or None,
        }
        
        try:
            if self.modo_edicion:
                print(f"🔄 Actualizando factura #{self.factura_id}...")
                self.actualizar_factura(factura_data)
                mensaje = "Factura actualizada exitosamente"
            else:
                print("➕ Creando nueva factura...")
                self.crear_factura(factura_data)
                mensaje = "Factura guardada exitosamente"
            
            print(f"✅ {mensaje}")
            self.mostrar_exito(mensaje)
            
            # Redirigir después de 1 segundo
            def redirigir():
                print("↪️ Redirigiendo a /facturas")
                self.page.go("/facturas")
            
            import threading
            timer = threading.Timer(1.0, redirigir)
            timer.start()
            
        except Exception as ex:
            print(f"❌ Error: {str(ex)}")
            import traceback
            traceback.print_exc()
            self.mostrar_error(f"Error al guardar: {str(ex)}")

    def crear_factura(self, factura_data):
        """Crea nueva factura"""
        # Intenta con columna notes
        try:
            query = """
                INSERT INTO supplier_invoices 
                (po_id, invoice_number, invoice_date, supplier_id,
                currency_id, exchange_rate, subtotal, tax_amount,
                total_amount, xml_file_path, archivo_pdf, status, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = tuple(factura_data.values())
            self.factura_id = self.db.execute_query(query, params, fetch=False)
            
        except Exception as ex:
            if "notes" in str(ex).lower():
                query = """
                    INSERT INTO supplier_invoices 
                    (po_id, invoice_number, invoice_date, supplier_id,
                    currency_id, exchange_rate, subtotal, tax_amount,
                    total_amount, xml_file_path, archivo_pdf, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = tuple(list(factura_data.values())[:-1])
                self.factura_id = self.db.execute_query(query, params, fetch=False)
            else:
                raise ex

    def actualizar_factura(self, factura_data):
        """Actualiza factura existente"""
        # Intenta con columna notes
        try:
            query = """
                UPDATE supplier_invoices 
                SET po_id = %s, invoice_number = %s, invoice_date = %s,
                    supplier_id = %s, currency_id = %s, exchange_rate = %s,
                    subtotal = %s, tax_amount = %s, total_amount = %s,
                    xml_file_path = %s, archivo_pdf = %s, status = %s,
                    notes = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            params = tuple(factura_data.values()) + (self.factura_id,)
            self.db.execute_query(query, params, fetch=False)
            
        except Exception as ex:
            if "notes" in str(ex).lower():
                query = """
                    UPDATE supplier_invoices 
                    SET po_id = %s, invoice_number = %s, invoice_date = %s,
                        supplier_id = %s, currency_id = %s, exchange_rate = %s,
                        subtotal = %s, tax_amount = %s, total_amount = %s,
                        xml_file_path = %s, archivo_pdf = %s, status = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """
                params = tuple(list(factura_data.values())[:-1]) + (self.factura_id,)
                self.db.execute_query(query, params, fetch=False)
            else:
                raise ex    
    def mostrar_mensaje(self, mensaje, color):
        """Muestra un mensaje en snackbar"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje, color="white"),
            bgcolor=color,
        )
        self.page.snack_bar.open = True
        self.page.update()
    def convertir_formato_fecha(self, fecha_str):
        """
        Convierte cualquier formato de fecha común a YYYY-MM-DD
        Formatos soportados:
        - DD/MM/YYYY (27/12/2024)
        - YYYY-MM-DD (2024-12-27)
        - DD-MM-YYYY (27-12-2024)
        - MM/DD/YYYY (12/27/2024) - estilo americano
        """
        if not fecha_str:
            return None
        
        # Limpiar espacios
        fecha_str = fecha_str.strip()
        
        # Diccionario de formatos comunes
        formatos = {
            '%d/%m/%Y': r'^\d{2}/\d{2}/\d{4}$',  # DD/MM/YYYY
            '%Y-%m-%d': r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            '%d-%m-%Y': r'^\d{2}-\d{2}-\d{4}$',  # DD-MM-YYYY
            '%m/%d/%Y': r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
            '%Y/%m/%d': r'^\d{4}/\d{2}/\d{2}$',  # YYYY/MM/DD
        }
        
        import re
        
        for formato, patron in formatos.items():
            if re.match(patron, fecha_str):
                try:
                    fecha_obj = datetime.strptime(fecha_str, formato)
                    return fecha_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        # Si llega aquí, intentar interpretar sin formato específico
        try:
            # Reemplazar cualquier separador por guión
            fecha_limpia = fecha_str.replace('/', '-').replace('.', '-')
            partes = fecha_limpia.split('-')
            
            if len(partes) == 3:
                # Determinar si es DD-MM-YYYY o YYYY-MM-DD
                if len(partes[0]) == 4:  # Primer parte tiene 4 dígitos = año
                    año, mes, dia = partes[0], partes[1], partes[2]
                else:  # Asumir DD-MM-YYYY
                    dia, mes, año = partes[0], partes[1], partes[2]
                
                # Asegurar 2 dígitos para día y mes
                dia = dia.zfill(2)
                mes = mes.zfill(2)
                
                return f"{año}-{mes}-{dia}"
        except:
            pass
        
        # Si nada funciona, devolver None
        return None
    def mostrar_error(self, mensaje):
        """Muestra un mensaje de error"""
        self.mostrar_mensaje(mensaje, ImportacionesTheme.ERROR)
    
    def mostrar_exito(self, mensaje):
        """Muestra un mensaje de éxito"""
        self.mostrar_mensaje(mensaje, ImportacionesTheme.SUCCESS)
    
    def form_view(self):
        """Retorna la vista completa del formulario"""
        titulo = f"Editar Factura #{self.factura_id}" if self.modo_edicion else "Nueva Factura de Proveedor"
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Row([
                                ft.Icon("receipt_long", size=24, 
                                    color=ImportacionesTheme.INFO if self.modo_edicion else ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text(titulo, size=24, 
                                    weight=ft.FontWeight.BOLD, 
                                    color=ImportacionesTheme.INFO if self.modo_edicion else ImportacionesTheme.TEXT_PRIMARY),
                            ], spacing=12),
                            ft.Row([
                                ft.Text("Registro de facturas de proveedores internacionales", 
                                    size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                                ft.Container(
                                    content=ft.Text("EDITANDO", size=10, color="white"),
                                    bgcolor=ImportacionesTheme.INFO,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                    border_radius=12,
                                    margin=ft.margin.only(left=10)
                                ) if self.modo_edicion else ft.Container()
                            ]),
                        ]),
                        ft.ElevatedButton(
                            "Volver",
                            icon="arrow_back",
                            on_click=lambda e: self.page.go("/facturas"),
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
                                        ft.Icon("info", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Text("Información de la Factura", size=16, 
                                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                    ], spacing=8),
                                    ft.Divider(height=20),
                                    ft.ResponsiveRow([
                                        ft.Column([self.controls['po_id']], col={"md": 6}),
                                        ft.Column([self.controls['invoice_number']], col={"md": 6}),
                                    ], spacing=16, run_spacing=16),
                                    ft.ResponsiveRow([
                                        ft.Column([self.controls['invoice_date']], col={"md": 4}),
                                        ft.Column([self.controls['supplier_id']], col={"md": 4}),
                                        ft.Column([self.controls['status']], col={"md": 4}),
                                    ], spacing=16, run_spacing=16),
                                ]),
                                padding=20,
                                border=ft.border.all(1, ImportacionesTheme.BORDER),
                                border_radius=8,
                                margin=ft.margin.only(bottom=20),
                            ),
                            
                            # Sección 2: Montos
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon("attach_money", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Text("Montos de la Factura", size=16, 
                                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                    ], spacing=8),
                                    ft.Divider(height=20),
                                    ft.ResponsiveRow([
                                        ft.Column([self.controls['currency_id']], col={"md": 4}),
                                        ft.Column([self.controls['exchange_rate']], col={"md": 4}),
                                        ft.Column([self.controls['subtotal']], col={"md": 4}),
                                    ], spacing=16, run_spacing=16),
                                    ft.ResponsiveRow([
                                        ft.Column([self.controls['tax_amount']], col={"md": 6}),
                                        ft.Column([self.controls['total_amount']], col={"md": 6}),
                                    ], spacing=16, run_spacing=16),
                                ]),
                                padding=20,
                                border=ft.border.all(1, ImportacionesTheme.BORDER),
                                border_radius=8,
                                margin=ft.margin.only(bottom=20),
                            ),
                            
                            # Sección 3: Documentos
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon("attach_file", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Text("Documentos Adjuntos", size=16, 
                                            weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                    ], spacing=8),
                                    ft.Divider(height=20),
                                    
                                    # XML
                                    ft.Row([
                                        self.controls['xml_upload_btn'],
                                        self.controls['xml_display'],
                                    ], spacing=16),
                                    
                                    ft.Container(height=10),
                                    
                                    # PDF
                                    ft.Row([
                                        self.controls['pdf_upload_btn'],
                                        self.controls['pdf_display'],
                                    ], spacing=16),
                                ]),
                                padding=20,
                                border=ft.border.all(1, ImportacionesTheme.BORDER),
                                border_radius=8,
                                margin=ft.margin.only(bottom=20),
                            ),
                            
                            # Sección 4: Notas
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon("notes", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Text("Observaciones y Notas", size=16, 
                                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                    ], spacing=8),
                                    ft.Divider(height=20),
                                    self.controls['notes'],
                                ]),
                                padding=20,
                                border=ft.border.all(1, ImportacionesTheme.BORDER),
                                border_radius=8,
                                margin=ft.margin.only(bottom=20),
                            ),
                            
                            # Botones de acción
                            ft.Container(
                                content=ft.Row([
                                    ft.ElevatedButton(
                                        "Cancelar",
                                        icon="cancel",
                                        on_click=lambda e: self.page.go("/facturas"),
                                        style=ft.ButtonStyle(
                                            bgcolor=ImportacionesTheme.BG_SECONDARY,
                                            color=ImportacionesTheme.TEXT_PRIMARY
                                        ),
                                    ),
                                    ft.Container(width=20),
                                    ft.ElevatedButton(
                                        "Guardar Factura",
                                        icon="save",
                                        on_click=self.guardar_factura,
                                        style=ft.ButtonStyle(
                                            bgcolor=ImportacionesTheme.SUCCESS,
                                            color="white"
                                        ),
                                    ),
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


