# views/orden_form_view.py - VERSIÓN OPTIMIZADA con caché y carga asíncrona
import flet as ft
from datetime import datetime, timedelta
from decimal import Decimal
from config_importaciones import (
    ImportacionesTheme, ImportacionesConfig, 
    format_currency, format_date, get_status_color
)
import threading

class OrdenFormView:
    def __init__(self, page: ft.Page, db, orden_id=None):
        self.page = page
        self.db = db
        self.orden_id = orden_id
        self.is_edit = orden_id is not None
        self.items = []
        self.total_fob = 0
        
        # Campos del formulario
        self.fields = {}
        self.form_data = {}
        
        # ========== CACHÉ DE DATOS (evita múltiples consultas) ==========
        self._suppliers_cache = None
        self._products_cache = None
        self._currencies_cache = None
        
        # ========== CONTENEDORES PARA ACTUALIZACIÓN DINÁMICA ==========
        self.main_content = None
        self.loading_container = None
        self.form_container = None
    
    def form_view(self):
        """Vista del formulario - MUESTRA SPINNER INMEDIATAMENTE"""
        
        # Crear contenedor de carga
        self.loading_container = ft.Container(
            content=ft.Column([
                ft.ProgressRing(width=50, height=50),
                ft.Container(height=20),
                ft.Text("Cargando formulario...", 
                       color=ImportacionesTheme.TEXT_SECONDARY,
                       size=16),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               alignment=ft.MainAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True,
        )
        
        # Contenedor del formulario (inicialmente vacío)
        self.form_container = ft.Container(
            content=None,
            expand=True,
            visible=False,
        )
        
        # Iniciar carga en background
        threading.Thread(target=self._load_form_async, daemon=True).start()
        
        # Retornar inmediatamente con spinner
        return ft.Container(
            content=ft.Stack([
                self.form_container,
                self.loading_container,
            ]),
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )
    
    def _load_form_async(self):
        """Carga todos los datos en background"""
        try:
            # 1. Cargar datos de referencia (UNA SOLA VEZ)
            self._load_reference_data()
            
            # 2. Cargar datos iniciales del formulario
            self._load_initial_data()
            
            # 3. Crear controles del formulario
            self._create_form_controls()
            
            # 4. Construir el formulario completo
            form_content = ft.Column([
                self._create_header(),
                self._create_basic_info_section(),
                ft.Container(height=24),
                self._create_items_section(),
                ft.Container(height=24),
                self._create_footer_section(),
                ft.Container(height=40),
            ], scroll=ft.ScrollMode.AUTO)
            
            # 5. Actualizar UI
            self.form_container.content = form_content
            self.form_container.visible = True
            self.loading_container.visible = False
            
            self.page.update()
            
        except Exception as e:
            print(f"Error cargando formulario: {e}")
            import traceback
            traceback.print_exc()
            
            # Mostrar error
            self.loading_container.content = ft.Column([
                ft.Icon("error", size=50, color=ImportacionesTheme.ERROR),
                ft.Container(height=20),
                ft.Text("Error cargando formulario", 
                       color=ImportacionesTheme.ERROR, size=16),
                ft.Text(str(e), color=ImportacionesTheme.TEXT_SECONDARY, size=12),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Volver",
                    on_click=lambda e: self.page.go("/ordenes")
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               alignment=ft.MainAxisAlignment.CENTER)
            self.page.update()
    
    def _load_reference_data(self):
        """Carga datos de referencia UNA SOLA VEZ (proveedores, productos, monedas)"""
        
        # Proveedores
        try:
            query = """
                SELECT id, ruc, business_name, country_id, currency_id
                FROM suppliers 
                WHERE status = 'active' 
                ORDER BY business_name
            """
            self._suppliers_cache = self.db.execute_query(query) or []
        except Exception as e:
            print(f"Error cargando proveedores: {e}")
            self._suppliers_cache = []
        
        # Productos
        try:
            query = """
                SELECT id, sku, name, description, unit_measure, 
                       weight_kg, volume_m3, hs_code
                FROM products 
                WHERE status = 'active' 
                ORDER BY sku
                LIMIT 500
            """
            self._products_cache = self.db.execute_query(query) or []
        except Exception as e:
            print(f"Error cargando productos: {e}")
            self._products_cache = []
        
        # Monedas
        try:
            query = "SELECT id, code, name FROM currencies ORDER BY code"
            self._currencies_cache = self.db.execute_query(query) or []
        except Exception as e:
            print(f"Error cargando monedas: {e}")
            self._currencies_cache = [{"id": 1, "code": "USD", "name": "Dólares"}]
    
    def _load_initial_data(self):
        """Carga datos iniciales del formulario"""
        if self.is_edit:
            self._load_orden_data()
        else:
            self.form_data = {
                "po_number": self._generate_po_number(),
                "order_date": datetime.now().strftime("%Y-%m-%d"),
                "expected_arrival": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "incoterm": "FOB",
                "currency_id": "1",
                "exchange_rate": "3.75",
                "status": "borrador"
            }
    
    def _load_orden_data(self):
        """Carga datos de la orden si es edición - CORREGIDO"""
        try:
            # 1. Cargar datos de la cabecera (Fecha, proveedor, etc.)
            query = """
                SELECT po.*, s.business_name as supplier_name
                FROM purchase_orders po
                LEFT JOIN suppliers s ON po.supplier_id = s.id
                WHERE po.id = %s
            """
            result = self.db.execute_query(query, (self.orden_id,))
            
            if result:
                self.form_data = result[0]
                # Convertir Decimales para Flet
                for key in self.form_data:
                    if isinstance(self.form_data[key], Decimal):
                        self.form_data[key] = float(self.form_data[key])
                
                # 2. Cargar items (SIN EL JOIN DE CATEGORIES QUE DABA ERROR)
                items_query = """
                    SELECT poi.*, p.sku, p.name as product_name
                    FROM purchase_order_items poi
                    LEFT JOIN products p ON poi.product_id = p.id
                    WHERE poi.po_id = %s
                    ORDER BY poi.id
                """
                items_result = self.db.execute_query(items_query, (self.orden_id,))
                
                self.items = [] # Limpiar lista
                if items_result:
                    for item in items_result:
                        item_dict = {}
                        for key in item:
                            if isinstance(item[key], Decimal):
                                item_dict[key] = float(item[key])
                            else:
                                item_dict[key] = item[key]
                        
                        # CLAVE: Mapear el nombre del producto a 'description'
                        item_dict["description"] = item.get("product_name", "Sin nombre")
                        self.items.append(item_dict)
                    
                    self._calculate_total_fob()
        except Exception as e:
            print(f"Error cargando orden: {e}")
            
    def _create_form_controls(self):
        """Crea todos los controles del formulario"""
        
        # Número de orden
        self.fields["po_number"] = ft.TextField(
            label="Número de Orden*",
            value=self.form_data.get("po_number", ""),
            width=200,
            border_color=ImportacionesTheme.BORDER,
            read_only=self.is_edit,
            text_size=14
        )
        
        # Fecha de orden
        self.fields["order_date"] = ft.TextField(
            label="Fecha de Orden*",
            value=str(self.form_data.get("order_date", datetime.now().date())),
            width=150,
            border_color=ImportacionesTheme.BORDER,
            text_size=14
        )
        
        # Fecha estimada de llegada
        self.fields["expected_arrival"] = ft.TextField(
            label="Fecha Llegada Estimada",
            value=str(self.form_data.get("expected_arrival", 
                                        (datetime.now() + timedelta(days=30)).date())),
            width=150,
            border_color=ImportacionesTheme.BORDER,
            text_size=14
        )
        
        # Proveedor (USA CACHÉ)
        self.fields["supplier_id"] = ft.Dropdown(
            label="Proveedor*",
            options=[ft.dropdown.Option("", "Seleccionar proveedor")] + [
                ft.dropdown.Option(str(s["id"]), f"{s['business_name']} ({s.get('ruc', 'N/A')})")
                for s in self._suppliers_cache
            ],
            value=str(self.form_data.get("supplier_id", "")),
            width=300,
            border_color=ImportacionesTheme.BORDER,
            text_size=14
        )
        
        # Incoterm
        self.fields["incoterm"] = ft.Dropdown(
            label="Incoterm*",
            options=[
                ft.dropdown.Option("EXW", "EXW - En fábrica"),
                ft.dropdown.Option("FOB", "FOB - Libre a bordo"),
                ft.dropdown.Option("CFR", "CFR - Costo y flete"),
                ft.dropdown.Option("CIF", "CIF - Costo, seguro y flete"),
                ft.dropdown.Option("DAP", "DAP - Entregado en lugar"),
                ft.dropdown.Option("DDP", "DDP - Entregado derechos pagados"),
            ],
            value=self.form_data.get("incoterm", "FOB"),
            width=200,
            border_color=ImportacionesTheme.BORDER,
            text_size=14
        )
        
        # Moneda (USA CACHÉ)
        self.fields["currency_id"] = ft.Dropdown(
            label="Moneda*",
            options=[
                ft.dropdown.Option(str(c["id"]), c["code"]) 
                for c in self._currencies_cache
            ] if self._currencies_cache else [ft.dropdown.Option("1", "USD")],
            value=str(self.form_data.get("currency_id", "1")),
            width=120,
            border_color=ImportacionesTheme.BORDER,
            text_size=14
        )
        
        # Tipo de cambio
        self.fields["exchange_rate"] = ft.TextField(
            label="Tipo de Cambio*",
            value=str(self.form_data.get("exchange_rate", "3.75")),
            width=120,
            border_color=ImportacionesTheme.BORDER,
            prefix_text="S/ ",
            text_size=14
        )
        
        # Puerto de embarque
        self.fields["port_loading"] = ft.TextField(
            label="Puerto de Embarque",
            value=self.form_data.get("port_loading", "") or "",
            width=250,
            border_color=ImportacionesTheme.BORDER,
            text_size=14
        )
        
        # Puerto de descarga
        self.fields["port_discharge"] = ft.TextField(
            label="Puerto de Descarga",
            value=self.form_data.get("port_discharge", "Callao") or "Callao",
            width=250,
            border_color=ImportacionesTheme.BORDER,
            text_size=14
        )
        
        # Agente de aduanas
        self.fields["customs_agent"] = ft.TextField(
            label="Agente de Aduanas",
            value=self.form_data.get("customs_agent", "") or "",
            width=250,
            border_color=ImportacionesTheme.BORDER,
            text_size=14
        )
        
        # Agente de carga
        self.fields["freight_forwarder"] = ft.TextField(
            label="Agente de Carga",
            value=self.form_data.get("freight_forwarder", "") or "",
            width=250,
            border_color=ImportacionesTheme.BORDER,
            text_size=14
        )
        
        # Observaciones
        self.fields["notes"] = ft.TextField(
            label="Observaciones",
            value=self.form_data.get("notes", "") or "",
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_color=ImportacionesTheme.BORDER,
            text_size=14
        )
        
        # Total FOB display
        self.fields["total_fob_display"] = ft.Text(
            f"$ {self.total_fob:,.2f}", 
            size=24, 
            weight=ft.FontWeight.BOLD, 
            color=ImportacionesTheme.STATUS_CONFIRMED
        )
    
    def _create_header(self):
        """Crea el header de la página"""
        titulo = f"Editar Orden #{self.orden_id}" if self.is_edit else "Nueva Orden de Compra"
        subtitulo = "Modifique los datos de la orden" if self.is_edit else "Complete los datos de la nueva orden"
        
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(titulo, size=24, weight=ft.FontWeight.BOLD,
                           color=ImportacionesTheme.TEXT_PRIMARY),
                    ft.Text(subtitulo, color=ImportacionesTheme.TEXT_SECONDARY),
                ], spacing=2),
                ft.TextButton(
                    "← Volver a la lista",
                    icon="arrow_back",
                    on_click=lambda e: self.page.go("/ordenes")
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=24, vertical=20),
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border=ft.border.only(bottom=ft.BorderSide(1, ImportacionesTheme.BORDER)),
        )
    
    def _create_basic_info_section(self):
        """Crea la sección de información básica"""
        return ft.Container(
            content=ft.Column([
                ft.Text("Información Básica", size=16, weight=ft.FontWeight.BOLD,
                       color=ImportacionesTheme.TEXT_PRIMARY),
                ft.Container(height=16),
                ft.ResponsiveRow([
                    ft.Column([self.fields["po_number"]], col={"md": 4}),
                    ft.Column([self.fields["order_date"]], col={"md": 4}),
                    ft.Column([self.fields["expected_arrival"]], col={"md": 4}),
                ], spacing=16, run_spacing=16),
                ft.Container(height=16),
                ft.ResponsiveRow([
                    ft.Column([self.fields["supplier_id"]], col={"md": 6}),
                    ft.Column([self.fields["incoterm"]], col={"md": 6}),
                ], spacing=16, run_spacing=16),
                ft.Container(height=16),
                ft.ResponsiveRow([
                    ft.Column([self.fields["currency_id"]], col={"md": 3}),
                    ft.Column([self.fields["exchange_rate"]], col={"md": 3}),
                    ft.Column([self.fields["port_loading"]], col={"md": 3}),
                    ft.Column([self.fields["port_discharge"]], col={"md": 3}),
                ], spacing=16, run_spacing=16),
                ft.Container(height=16),
                ft.ResponsiveRow([
                    ft.Column([self.fields["customs_agent"]], col={"md": 6}),
                    ft.Column([self.fields["freight_forwarder"]], col={"md": 6}),
                ], spacing=16, run_spacing=16),
                ft.Container(height=16),
                ft.Column([self.fields["notes"]]),
            ]),
            padding=24,
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
        )
    
    def _create_items_section(self):
        """Crea la sección de items/productos"""
        
        # ListView para items dinámicos
        self.items_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=20,
            auto_scroll=True
        )
        
        # Cargar items existentes
        self._load_items_to_list()
        
        # Botón para agregar item
        add_item_btn = ft.ElevatedButton(
            "Agregar Producto",
            icon="add",
            on_click=self._add_item_to_list,
            style=ft.ButtonStyle(
                bgcolor=ImportacionesTheme.BG_SECONDARY,
                color=ImportacionesTheme.TEXT_PRIMARY
            )
        )
        
        # Contador de items
        self.items_count_text = ft.Text(
            str(len(self.items)), 
            weight=ft.FontWeight.BOLD,
            color=ImportacionesTheme.TEXT_PRIMARY
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Productos / Items", size=16, weight=ft.FontWeight.BOLD,
                           color=ImportacionesTheme.TEXT_PRIMARY),
                    add_item_btn,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=16),
                ft.Container(
                    content=self.items_list,
                    height=300,
                    border=ft.border.all(1, ImportacionesTheme.BORDER),
                    border_radius=8,
                ),
                ft.Container(height=16),
                ft.Row([
                    ft.Text("Total Items:", color=ImportacionesTheme.TEXT_SECONDARY),
                    self.items_count_text,
                    ft.Container(width=20),
                    ft.Text("Total FOB:", color=ImportacionesTheme.TEXT_SECONDARY),
                    self.fields["total_fob_display"],
                ], spacing=8),
            ]),
            padding=24,
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
        )
    
    def _load_items_to_list(self):
        """Carga los items a la lista"""
        self.items_list.controls.clear()
        
        if not self.items:
            self.items_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon("inventory", size=48, color=ImportacionesTheme.TEXT_SECONDARY),
                        ft.Text("No hay productos agregados", 
                               color=ImportacionesTheme.TEXT_SECONDARY),
                        ft.Text("Haga clic en 'Agregar Producto' para comenzar", 
                               size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=40,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for i, item in enumerate(self.items):
                self.items_list.controls.append(self._create_item_card(i, item))
    
    def _create_item_card(self, index, item):
        """Crea una tarjeta para un item - USA CACHÉ DE PRODUCTOS"""
        
        # Crear controles (USA CACHÉ, no consulta BD)
        product_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option("", "Seleccionar producto")] + [
                ft.dropdown.Option(str(p["id"]), f"{p['sku']} - {p['name'][:30]}")
                for p in self._products_cache[:100]  # Limitar opciones visibles
            ],
            value=str(item.get("product_id", "")) if item.get("product_id") else "",
            width=250,
            border_color=ImportacionesTheme.BORDER,
            text_size=12,
            on_change=lambda e, idx=index: self._on_product_change(idx, e)
        )
        
        quantity_field = ft.TextField(
            value=str(item.get("quantity", 1)),
            width=80,
            border_color=ImportacionesTheme.BORDER,
            text_align=ft.TextAlign.RIGHT,
            text_size=12,
            on_change=lambda e, idx=index: self._on_quantity_change(idx, e)
        )
        
        price_field = ft.TextField(
            value=str(item.get("unit_price", 0)),
            width=100,
            border_color=ImportacionesTheme.BORDER,
            prefix_text="$ ",
            text_align=ft.TextAlign.RIGHT,
            text_size=12,
            on_change=lambda e, idx=index: self._on_price_change(idx, e)
        )
        
        total_text = ft.Text(
            f"${item.get('total', 0):,.2f}",
            width=100,
            color=ImportacionesTheme.TEXT_PRIMARY,
            weight=ft.FontWeight.BOLD,
            size=12
        )
        description_text = ft.Text(
            value=item.get("description", "Cargando..."),
            size=11,
            color=ImportacionesTheme.TEXT_SECONDARY,
            width=200,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS
        )
        
        # Guardar referencia al texto de total para actualizarlo
        item['_total_text'] = total_text
        
        delete_btn = ft.IconButton(
            icon="delete",
            icon_size=18,
            icon_color=ImportacionesTheme.ERROR,
            tooltip="Eliminar producto",
            on_click=lambda e, idx=index: self._remove_item_from_list(idx)
        )
        
        return ft.Container(
            content=ft.Column([ # Cambiamos Row por Column para meter la descripción
            ft.Row([
                product_dropdown,
                quantity_field,
                price_field,
                total_text,
                delete_btn,
            ], spacing=10, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            description_text, # <--- Ahora el nombre es visible debajo de los controles
           ]),
            padding=10,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
            border_radius=8,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
        )
    
    def _add_item_to_list(self, e):
        """Agrega un nuevo item a la lista"""
        self.items.append({
            "product_id": None,
            "sku": "",
            "description": "",
            "quantity": 1,
            "unit_price": 0,
            "unit_measure": "NIU",
            "weight_kg": 0,
            "volume_m3": 0,
            "total": 0,
            "fob_value": 0
        })
        
        self._load_items_to_list()
        self._calculate_total_fob()
        self._update_items_count()
        self.page.update()
    
    def _remove_item_from_list(self, index):
        """Elimina un item de la lista"""
        if 0 <= index < len(self.items):
            self.items.pop(index)
            self._load_items_to_list()
            self._calculate_total_fob()
            self._update_items_count()
            self.page.update()
    
    def _on_product_change(self, index, e):
        """Manejador de cambio de producto - USA CACHÉ"""
        if e.control.value and index < len(self.items):
            try:
                product_id = int(e.control.value)
                # Buscar en caché (NO en BD)
                product = next((p for p in self._products_cache if p["id"] == product_id), None)
                
                if product:
                    self.items[index]["product_id"] = product_id
                    self.items[index]["sku"] = product["sku"]
                    self.items[index]["description"] = product["name"]
                    self.items[index]["unit_measure"] = product.get("unit_measure", "NIU")
                    self.items[index]["weight_kg"] = float(product.get("weight_kg") or 0)
                    self.items[index]["volume_m3"] = float(product.get("volume_m3") or 0)
                    
                    self._calculate_item_total(index)
                    
            except Exception as ex:
                print(f"Error cambiando producto: {ex}")
    
    def _on_quantity_change(self, index, e):
        """Manejador de cambio de cantidad"""
        try:
            quantity = float(e.control.value) if e.control.value else 0
            if index < len(self.items):
                self.items[index]["quantity"] = quantity
                self._calculate_item_total(index)
        except ValueError:
            pass
    
    def _on_price_change(self, index, e):
        """Manejador de cambio de precio"""
        try:
            price = float(e.control.value) if e.control.value else 0
            if index < len(self.items):
                self.items[index]["unit_price"] = price
                self._calculate_item_total(index)
        except ValueError:
            pass
    
    def _calculate_item_total(self, index):
        """Calcula el total de un item"""
        if index < len(self.items):
            item = self.items[index]
            quantity = item.get("quantity", 0)
            price = item.get("unit_price", 0)
            item["total"] = quantity * price
            item["fob_value"] = quantity * price
            
            # Actualizar texto del total en la UI
            if '_total_text' in item:
                item['_total_text'].value = f"${item['total']:,.2f}"
                item['_total_text'].update()
            
            self._calculate_total_fob()
    
    def _calculate_total_fob(self):
        """Calcula el total FOB de todos los items"""
        self.total_fob = sum(item.get("total", 0) for item in self.items)
        
        if "total_fob_display" in self.fields:
            currency_symbol = "$" if str(self.form_data.get("currency_id")) == "1" else "S/"
            self.fields["total_fob_display"].value = f"{currency_symbol} {self.total_fob:,.2f}"
            try:
                self.fields["total_fob_display"].update()
            except:
                pass
    
    def _update_items_count(self):
        """Actualiza el contador de items"""
        if hasattr(self, 'items_count_text'):
            self.items_count_text.value = str(len(self.items))
            try:
                self.items_count_text.update()
            except:
                pass
    
    def _create_footer_section(self):
        """Crea la sección de pie con botones de acción"""
        
        save_btn = ft.ElevatedButton(
            "Guardar Borrador" if not self.is_edit else "Guardar Cambios",
            icon="save",
            on_click=self._save_order,
            style=ft.ButtonStyle(
                bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                color="white",
                padding=ft.padding.symmetric(horizontal=24, vertical=12)
            )
        )
        
        confirm_btn = ft.ElevatedButton(
            "Confirmar Orden",
            icon="check_circle",
            on_click=self._confirm_order,
            style=ft.ButtonStyle(
                bgcolor=ImportacionesTheme.SUCCESS,
                color="white",
                padding=ft.padding.symmetric(horizontal=24, vertical=12)
            )
        )
        
        cancel_btn = ft.TextButton(
            "Cancelar",
            icon="cancel",
            on_click=lambda e: self.page.go("/ordenes"),
        )
        
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("Total FOB:", size=16, color=ImportacionesTheme.TEXT_SECONDARY),
                    self.fields["total_fob_display"],
                ], spacing=4),
                ft.Row([cancel_btn, save_btn, confirm_btn], spacing=12),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=24,
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
        )
    
    # ========== MÉTODOS AUXILIARES ==========
    
    def _generate_po_number(self):
        """Genera un número de orden automático"""
        try:
            year = datetime.now().year
            query = "SELECT COUNT(*) as count FROM purchase_orders WHERE YEAR(order_date) = %s"
            result = self.db.execute_query(query, (year,))
            count = result[0]["count"] if result else 0
            return f"PO-{year}-{count + 1:04d}"
        except:
            return f"PO-{datetime.now().year}-0001"
    
    def _validate_form(self):
        """Valida el formulario antes de guardar"""
        errors = []
        
        if not self.fields["po_number"].value:
            errors.append("Número de orden es requerido")
        
        if not self.fields["supplier_id"].value:
            errors.append("Proveedor es requerido")
        
        if not self.fields["order_date"].value:
            errors.append("Fecha de orden es requerida")
        
        if not self.items:
            errors.append("Debe agregar al menos un producto")
        else:
            for i, item in enumerate(self.items):
                if not item.get("product_id"):
                    errors.append(f"Producto en línea {i+1} no seleccionado")
                if not item.get("quantity") or item["quantity"] <= 0:
                    errors.append(f"Cantidad en línea {i+1} debe ser mayor a 0")
        
        return errors
    
    def _save_order(self, e, status="borrador"):
        """Guarda la orden en la base de datos"""
        
        errors = self._validate_form()
        if errors:
            self._show_snackbar(f"Errores: {'; '.join(errors[:3])}", "error")
            return
        
        # Mostrar indicador de guardado
        self._show_snackbar("Guardando...", "info")
        
        def save_background():
            try:
                order_data = {
                    "po_number": self.fields["po_number"].value,
                    "order_date": self.fields["order_date"].value,
                    "expected_arrival": self.fields["expected_arrival"].value,
                    "supplier_id": int(self.fields["supplier_id"].value),
                    "incoterm": self.fields["incoterm"].value,
                    "currency_id": int(self.fields["currency_id"].value),
                    "exchange_rate": float(self.fields["exchange_rate"].value or 1),
                    "port_loading": self.fields["port_loading"].value,
                    "port_discharge": self.fields["port_discharge"].value,
                    "customs_agent": self.fields["customs_agent"].value,
                    "freight_forwarder": self.fields["freight_forwarder"].value,
                    "total_fob": self.total_fob,
                    "status": status,
                    "notes": self.fields["notes"].value,
                }
                
                if self.is_edit:
                    order_data["id"] = self.orden_id
                    success = self._update_order(order_data)
                    action = "actualizada"
                else:
                    success = self._create_order(order_data)
                    action = "creada"
                
                if success:
                    self._show_snackbar(f"Orden {action} exitosamente", "success")
                    self.page.go("/ordenes")
                else:
                    self._show_snackbar("Error guardando la orden", "error")
                    
            except Exception as ex:
                print(f"Error guardando orden: {ex}")
                self._show_snackbar(f"Error: {str(ex)}", "error")
        
        threading.Thread(target=save_background, daemon=True).start()
    
    def _confirm_order(self, e):
        """Confirma la orden"""
        self._save_order(e, "confirmada")
    
    def _create_order(self, order_data):
        """Crea una nueva orden en la base de datos"""
        try:
            query = """
                INSERT INTO purchase_orders (
                    po_number, supplier_id, order_date, expected_arrival,
                    incoterm, currency_id, exchange_rate, port_loading,
                    port_discharge, customs_agent, freight_forwarder,
                    total_fob, status, notes, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                order_data["po_number"],
                order_data["supplier_id"],
                order_data["order_date"],
                order_data["expected_arrival"],
                order_data["incoterm"],
                order_data["currency_id"],
                order_data["exchange_rate"],
                order_data["port_loading"],
                order_data["port_discharge"],
                order_data["customs_agent"],
                order_data["freight_forwarder"],
                order_data["total_fob"],
                order_data["status"],
                order_data["notes"],
                1
            )
            
            order_id = self.db.execute_query(query, params, fetch=False)
            
            if order_id:
                for item in self.items:
                    if item.get("product_id"):
                        item_query = """
                            INSERT INTO purchase_order_items (
                                po_id, product_id, quantity, unit_price,
                                unit_measure, weight_kg, volume_m3,
                                total_cost, created_by
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        item_params = (
                            order_id,
                            item["product_id"],
                            item["quantity"],
                            item["unit_price"],
                            item.get("unit_measure", "NIU"),
                            item.get("weight_kg", 0),
                            item.get("volume_m3", 0),
                            item["total"],
                            1
                        )
                        self.db.execute_query(item_query, item_params, fetch=False)
                
                return True
            return False
            
        except Exception as e:
            print(f"Error creando orden: {e}")
            return False
    
    def _update_order(self, order_data):
        """Actualiza una orden existente"""
        try:
            query = """
                UPDATE purchase_orders SET
                    expected_arrival = %s, incoterm = %s, currency_id = %s,
                    exchange_rate = %s, port_loading = %s, port_discharge = %s,
                    customs_agent = %s, freight_forwarder = %s, total_fob = %s,
                    status = %s, notes = %s, updated_by = %s
                WHERE id = %s
            """
            
            params = (
                order_data["expected_arrival"],
                order_data["incoterm"],
                order_data["currency_id"],
                order_data["exchange_rate"],
                order_data["port_loading"],
                order_data["port_discharge"],
                order_data["customs_agent"],
                order_data["freight_forwarder"],
                order_data["total_fob"],
                order_data["status"],
                order_data["notes"],
                1,
                order_data["id"]
            )
            
            self.db.execute_query(query, params, fetch=False)
            
            # Eliminar items antiguos
            self.db.execute_query(
                "DELETE FROM purchase_order_items WHERE po_id = %s", 
                (order_data["id"],), 
                fetch=False
            )
            
            # Insertar nuevos items
            for item in self.items:
                if item.get("product_id"):
                    item_query = """
                        INSERT INTO purchase_order_items (
                            po_id, product_id, quantity, unit_price,
                            unit_measure, weight_kg, volume_m3,
                            total_cost, created_by
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    item_params = (
                        order_data["id"],
                        item["product_id"],
                        item["quantity"],
                        item["unit_price"],
                        item.get("unit_measure", "NIU"),
                        item.get("weight_kg", 0),
                        item.get("volume_m3", 0),
                        item["total"],
                        1
                    )
                    self.db.execute_query(item_query, item_params, fetch=False)
            
            return True
            
        except Exception as e:
            print(f"Error actualizando orden: {e}")
            return False
    
    def _show_snackbar(self, message: str, tipo: str = "info"):
        """Muestra un mensaje snackbar"""
        colors = {
            "success": ImportacionesTheme.SUCCESS,
            "error": ImportacionesTheme.ERROR,
            "warning": "#F59E0B",
            "info": ImportacionesTheme.STATUS_CONFIRMED
        }
        
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="white"),
            bgcolor=colors.get(tipo, ImportacionesTheme.STATUS_CONFIRMED)
        )
        self.page.snack_bar.open = True
        self.page.update()