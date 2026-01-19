# views/gasto_form_view.py
import flet as ft
from datetime import datetime
from config_importaciones import (
    ImportacionesTheme, ImportacionesConfig,
    format_currency, format_date, get_status_color
)

class GastoFormView:
    def __init__(self, page: ft.Page, db, gasto_id=None):
        self.page = page
        self.db = db
        self.gasto_id = gasto_id
        self.modo_edicion = gasto_id is not None
        self.po_id = self.obtener_po_id_url()
        
        # Datos para combos
        self.ordenes = []
        self.monedas = []
        self.tipos_gasto = []
        
        # Campos del formulario principal
        self.controls = self.crear_controles()
        
        # Cargar datos iniciales
        self.cargar_datos_combos()
        if self.modo_edicion:
            self.cargar_gasto()
        elif self.po_id:
            self.cargar_orden_por_defecto()
    
    def obtener_po_id_url(self):
        """Obtiene el po_id de los parámetros de la URL"""
        if hasattr(self.page, 'route') and 'po_id=' in self.page.route:
            try:
                import urllib.parse
                parsed = urllib.parse.urlparse(self.page.route)
                query_params = urllib.parse.parse_qs(parsed.query)
                return int(query_params.get('po_id', [0])[0])
            except:
                return None
        return None
    
    def cargar_orden_por_defecto(self):
        """Carga la orden de compra por defecto si viene en la URL"""
        if self.po_id:
            self.controls['po'].value = str(self.po_id)
    
    def crear_controles(self):
        """Crea todos los controles del formulario"""
        return {
            'po': ft.Dropdown(
                label="Orden de Compra *",
                prefix_icon="shopping_cart",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                options=[]
            ),
            
            'expense_type': ft.Dropdown(
                label="Tipo de Gasto *",
                prefix_icon="category",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                options=[],
                on_change=self.actualizar_tipo_gasto
            ),
            
            'description': ft.TextField(
                label="Descripción",
                prefix_icon="description",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                multiline=True,
                min_lines=2,
                max_lines=3
            ),
            
            'supplier_ruc': ft.TextField(
                label="RUC Proveedor",
                prefix_icon="badge",
                border_color=ImportacionesTheme.BORDER,
                filled=True
            ),
            
            'supplier_name': ft.TextField(
                label="Nombre Proveedor",
                prefix_icon="business",
                border_color=ImportacionesTheme.BORDER,
                filled=True
            ),
            
            'currency': ft.Dropdown(
                label="Moneda *",
                prefix_icon="paid",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                options=[],
                on_change=self.actualizar_tipo_cambio
            ),
            
            'amount': ft.TextField(
                label="Monto *",
                prefix_icon="attach_money",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                on_change=self.calcular_equivalente
            ),
            
            'exchange_rate': ft.TextField(
                label="Tipo de Cambio *",
                prefix_icon="currency_exchange",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="1.0000",
                on_change=self.calcular_equivalente
            ),
            
            'amount_pen': ft.TextField(
                label="Equivalente PEN",
                prefix_icon="money",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                read_only=True,
                value="0.00"
            ),
            
            'invoice_number': ft.TextField(
                label="Número de Factura",
                prefix_icon="receipt",
                border_color=ImportacionesTheme.BORDER,
                filled=True
            ),
            
            'expense_date': ft.TextField(
                label="Fecha del Gasto",
                prefix_icon="event",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value=datetime.now().strftime("%Y-%m-%d")
            ),
            
            'status': ft.Dropdown(
                label="Estado",
                prefix_icon="status",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                options=[
                    ft.dropdown.Option("pending", "Pendiente"),
                    ft.dropdown.Option("approved", "Aprobado"),
                    ft.dropdown.Option("paid", "Pagado"),
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
            )
        }
    
    def cargar_datos_combos(self):
        """Carga datos para los combos desde la base de datos"""
        # Órdenes de compra
        query = """
            SELECT po.id, po.po_number, s.business_name 
            FROM purchase_orders po
            LEFT JOIN suppliers s ON po.supplier_id = s.id
            WHERE po.status NOT IN ('cancelada', 'completada')
            ORDER BY po.order_date DESC
        """
        result = self.db.execute_query(query)
        if result:
            self.ordenes = result
            options = [ft.dropdown.Option(str(po['id']), f"{po['po_number']} - {po['business_name']}") for po in result]
            self.controls['po'].options = options
        
        # Tipos de gasto
        query = "SELECT tipo_gasto, nombre_ui, color_ui, icono_ui, requiere_proveedor FROM expense_types_ui ORDER BY orden"
        result = self.db.execute_query(query)
        if result:
            self.tipos_gasto = result
            options = [ft.dropdown.Option(tipo['tipo_gasto'], tipo['nombre_ui']) for tipo in result]
            self.controls['expense_type'].options = options
        
        # Monedas
        query = "SELECT id, code, symbol, exchange_rate FROM currencies ORDER BY code"
        result = self.db.execute_query(query)
        if result:
            self.monedas = result
            options = [ft.dropdown.Option(str(m['id']), f"{m['code']} ({m['symbol']})") for m in result]
            self.controls['currency'].options = options
            
            # Seleccionar USD por defecto
            for moneda in result:
                if moneda['code'] == 'USD':
                    self.controls['currency'].value = str(moneda['id'])
                    self.controls['exchange_rate'].value = str(moneda['exchange_rate'])
                    break
    
    def actualizar_tipo_gasto(self, e):
        """Actualiza campos según el tipo de gasto seleccionado"""
        expense_type = self.controls['expense_type'].value
        if not expense_type:
            return
        
        # Buscar el tipo de gasto seleccionado
        tipo_seleccionado = next((t for t in self.tipos_gasto if t['tipo_gasto'] == expense_type), None)
        
        if tipo_seleccionado:
            # Habilitar/deshabilitar campos según requiere_proveedor
            requiere_proveedor = tipo_seleccionado.get('requiere_proveedor', 1)
            self.controls['supplier_ruc'].disabled = not requiere_proveedor
            self.controls['supplier_name'].disabled = not requiere_proveedor
            self.controls['supplier_ruc'].value = '' if not requiere_proveedor else self.controls['supplier_ruc'].value
            self.controls['supplier_name'].value = '' if not requiere_proveedor else self.controls['supplier_name'].value
        
        self.page.update()
    
    def actualizar_tipo_cambio(self, e):
        """Actualiza el tipo de cambio según la moneda seleccionada"""
        currency_id = self.controls['currency'].value
        if currency_id:
            for moneda in self.monedas:
                if str(moneda['id']) == currency_id:
                    self.controls['exchange_rate'].value = str(moneda['exchange_rate'])
                    break
        self.calcular_equivalente(None)
    
    def calcular_equivalente(self, e):
        """Calcula el equivalente en PEN del monto"""
        try:
            amount = float(self.controls['amount'].value or 0)
            exchange_rate = float(self.controls['exchange_rate'].value or 1)
            amount_pen = amount * exchange_rate
            self.controls['amount_pen'].value = f"{amount_pen:.2f}"
        except ValueError:
            self.controls['amount_pen'].value = "0.00"
        self.page.update()
    
    def cargar_gasto(self):
        """Carga los datos de un gasto existente"""
        query = """
            SELECT ie.*, c.code as currency_code
            FROM import_expenses ie
            LEFT JOIN currencies c ON ie.currency_id = c.id
            WHERE ie.id = %s
        """
        result = self.db.execute_query(query, (self.gasto_id,))
        if result:
            gasto = result[0]
            
            # Campos básicos
            self.controls['po'].value = str(gasto['po_id'])
            self.controls['expense_type'].value = gasto['expense_type']
            self.controls['description'].value = gasto['description'] or ''
            self.controls['supplier_ruc'].value = gasto['supplier_ruc'] or ''
            self.controls['supplier_name'].value = gasto['supplier_name'] or ''
            self.controls['currency'].value = str(gasto['currency_id'])
            self.controls['amount'].value = str(gasto['amount'])
            self.controls['exchange_rate'].value = str(gasto['exchange_rate'])
            self.controls['amount_pen'].value = str(gasto.get('amount_pen', 0))
            self.controls['invoice_number'].value = gasto['invoice_number'] or ''
            self.controls['expense_date'].value = format_date(gasto['expense_date']) if gasto['expense_date'] else ''
            self.controls['status'].value = gasto['status']
            self.controls['notes'].value = gasto['notes'] or ''
            
            # Actualizar campos según tipo de gasto
            self.actualizar_tipo_gasto(None)
    
    def validar_formulario(self):
        """Valida los datos del formulario"""
        errores = []
        
        if not self.controls['po'].value:
            errores.append("Debe seleccionar una orden de compra")
        
        if not self.controls['expense_type'].value:
            errores.append("Debe seleccionar un tipo de gasto")
        
        if not self.controls['amount'].value or float(self.controls['amount'].value or 0) <= 0:
            errores.append("El monto debe ser mayor a 0")
        
        if not self.controls['currency'].value:
            errores.append("Debe seleccionar una moneda")
        
        try:
            float(self.controls['exchange_rate'].value or 0)
        except ValueError:
            errores.append("El tipo de cambio debe ser un número válido")
        
        return errores
    
    def guardar_gasto(self, e):
        """Guarda el gasto en la base de datos"""
        # Validar formulario
        errores = self.validar_formulario()
        if errores:
            self.mostrar_error("\n".join(errores))
            return
        
        # Preparar datos del gasto
        gasto_data = {
            'po_id': int(self.controls['po'].value),
            'expense_type': self.controls['expense_type'].value,
            'description': self.controls['description'].value or None,
            'supplier_ruc': self.controls['supplier_ruc'].value or None,
            'supplier_name': self.controls['supplier_name'].value or None,
            'currency_id': int(self.controls['currency'].value),
            'amount': float(self.controls['amount'].value),
            'exchange_rate': float(self.controls['exchange_rate'].value),
            'invoice_number': self.controls['invoice_number'].value or None,
            'expense_date': self.controls['expense_date'].value if self.controls['expense_date'].value else None,
            'status': self.controls['status'].value,
            'notes': self.controls['notes'].value or None,
        }
        
        try:
            if self.modo_edicion:
                # Actualizar gasto existente
                query = """
                    UPDATE import_expenses 
                    SET po_id = %s, expense_type = %s, description = %s,
                        supplier_ruc = %s, supplier_name = %s, currency_id = %s,
                        amount = %s, exchange_rate = %s, invoice_number = %s,
                        expense_date = %s, status = %s, notes = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """
                params = (
                    gasto_data['po_id'], gasto_data['expense_type'], gasto_data['description'],
                    gasto_data['supplier_ruc'], gasto_data['supplier_name'], gasto_data['currency_id'],
                    gasto_data['amount'], gasto_data['exchange_rate'], gasto_data['invoice_number'],
                    gasto_data['expense_date'], gasto_data['status'], gasto_data['notes'],
                    self.gasto_id
                )
                
                self.db.execute_query(query, params, fetch=False)
                
            else:
                # Crear nuevo gasto
                query = """
                    INSERT INTO import_expenses 
                    (po_id, expense_type, description, supplier_ruc, supplier_name,
                     currency_id, amount, exchange_rate, invoice_number,
                     expense_date, status, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    gasto_data['po_id'], gasto_data['expense_type'], gasto_data['description'],
                    gasto_data['supplier_ruc'], gasto_data['supplier_name'], gasto_data['currency_id'],
                    gasto_data['amount'], gasto_data['exchange_rate'], gasto_data['invoice_number'],
                    gasto_data['expense_date'], gasto_data['status'], gasto_data['notes']
                )
                
                self.gasto_id = self.db.execute_query(query, params, fetch=False)
            
            self.mostrar_exito("Gasto guardado exitosamente")
            
            # Redirigir después de 1 segundo
            def redirigir():
                self.page.go(f"/ordenes/{gasto_data['po_id']}")
            
            import threading
            timer = threading.Timer(1.0, redirigir)
            timer.start()
            
        except Exception as ex:
            self.mostrar_error(f"Error al guardar: {str(ex)}")
    
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
        titulo = f"Editar Gasto #{self.gasto_id}" if self.modo_edicion else "Nuevo Gasto de Importación"
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Row([
                                ft.Icon("account_balance_wallet", size=24, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text(titulo, size=24, 
                                       weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                            ], spacing=12),
                            ft.Text("Registro de gastos asociados a la importación", 
                                   size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                        ]),
                        ft.ElevatedButton(
                            "Volver",
                            icon="arrow_back",
                            on_click=lambda e: self.page.go("/ordenes"),
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
                                        ft.Text("Información del Gasto", size=16, 
                                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                    ], spacing=8),
                                    ft.Divider(height=20),
                                    ft.ResponsiveRow([
                                        ft.Column([self.controls['po']], col={"md": 6}),
                                        ft.Column([self.controls['expense_type']], col={"md": 6}),
                                    ], spacing=16, run_spacing=16),
                                    ft.ResponsiveRow([
                                        ft.Column([self.controls['expense_date']], col={"md": 4}),
                                        ft.Column([self.controls['invoice_number']], col={"md": 4}),
                                        ft.Column([self.controls['status']], col={"md": 4}),
                                    ], spacing=16, run_spacing=16),
                                    ft.Column([self.controls['description']], col=12),
                                ]),
                                padding=20,
                                border=ft.border.all(1, ImportacionesTheme.BORDER),
                                border_radius=8,
                                margin=ft.margin.only(bottom=20),
                            ),
                            
                            # Sección 2: Proveedor
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon("business", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Text("Información del Proveedor", size=16, 
                                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                    ], spacing=8),
                                    ft.Divider(height=20),
                                    ft.ResponsiveRow([
                                        ft.Column([self.controls['supplier_ruc']], col={"md": 6}),
                                        ft.Column([self.controls['supplier_name']], col={"md": 6}),
                                    ], spacing=16, run_spacing=16),
                                ]),
                                padding=20,
                                border=ft.border.all(1, ImportacionesTheme.BORDER),
                                border_radius=8,
                                margin=ft.margin.only(bottom=20),
                            ),
                            
                            # Sección 3: Montos
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon("attach_money", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Text("Monto del Gasto", size=16, 
                                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                    ], spacing=8),
                                    ft.Divider(height=20),
                                    ft.ResponsiveRow([
                                        ft.Column([self.controls['currency']], col={"md": 4}),
                                        ft.Column([self.controls['amount']], col={"md": 4}),
                                        ft.Column([self.controls['exchange_rate']], col={"md": 4}),
                                    ], spacing=16, run_spacing=16),
                                    ft.ResponsiveRow([
                                        ft.Column([self.controls['amount_pen']], col={"md": 12}),
                                    ], spacing=16, run_spacing=16),
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
                                        on_click=lambda e: self.page.go("/ordenes"),
                                        style=ft.ButtonStyle(
                                            bgcolor=ImportacionesTheme.BG_SECONDARY,
                                            color=ImportacionesTheme.TEXT_PRIMARY
                                        ),
                                    ),
                                    ft.Container(width=20),
                                    ft.ElevatedButton(
                                        "Guardar Gasto",
                                        icon="save",
                                        on_click=self.guardar_gasto,
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