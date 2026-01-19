# views/facturas_view.py
import flet as ft
from datetime import datetime
from config_importaciones import (
    ImportacionesTheme, format_date
)
from pdf_parser import PDFInvoiceParser
import threading


class FacturasView:
    def __init__(self, page: ft.Page, db, file_picker: ft.FilePicker = None):
        self.page = page
        self.db = db
        self.current_filter = {}
        self.facturas = []
        self.file_picker = file_picker
        self.pdf_parser = None  # Lazy loading
        self._is_loading = False
        self._table_container = None
        
        # Paginación
        self.page_size = 50
        self.current_page = 0
        self.total_count = 0
    
    def _get_pdf_parser(self):
        """Lazy loading del parser"""
        if self.pdf_parser is None:
            self.pdf_parser = PDFInvoiceParser()
        return self.pdf_parser
    
    def load_facturas(self, show_loading=True):
        """Carga facturas con paginación"""
        try:
            # Primero obtener el conteo total (query más ligera)
            count_query = """
                SELECT COUNT(*) as total
                FROM supplier_invoices si
                WHERE 1=1
            """
            count_params = []
            
            if self.current_filter.get("search"):
                count_query += """ AND (si.invoice_number LIKE %s 
                    OR EXISTS (SELECT 1 FROM suppliers s 
                              WHERE s.id = si.supplier_id 
                              AND s.business_name LIKE %s))"""
                count_params.extend([
                    f"%{self.current_filter['search']}%",
                    f"%{self.current_filter['search']}%"
                ])
            
            if self.current_filter.get("status"):
                count_query += " AND si.status = %s"
                count_params.append(self.current_filter["status"])
            
            count_result = self.db.execute_query(
                count_query, 
                tuple(count_params) if count_params else None
            )
            self.total_count = count_result[0]['total'] if count_result else 0
            
            # Query principal con LIMIT y OFFSET
            query = """
                SELECT 
                    si.id,
                    si.invoice_number,
                    si.invoice_date,
                    si.status,
                    si.total_amount,
                    si.po_id,
                    si.supplier_id,
                    si.currency_id,
                    po.po_number,
                    s.business_name as supplier_name,
                    c.code as currency_code
                FROM supplier_invoices si
                LEFT JOIN purchase_orders po ON si.po_id = po.id
                LEFT JOIN suppliers s ON si.supplier_id = s.id
                LEFT JOIN currencies c ON si.currency_id = c.id
                WHERE 1=1
            """
            
            params = []
            
            if self.current_filter.get("search"):
                query += " AND (si.invoice_number LIKE %s OR s.business_name LIKE %s)"
                params.extend([
                    f"%{self.current_filter['search']}%",
                    f"%{self.current_filter['search']}%"
                ])
            
            if self.current_filter.get("status"):
                query += " AND si.status = %s"
                params.append(self.current_filter["status"])
            
            # Añadir paginación
            query += " ORDER BY si.invoice_date DESC, si.id DESC LIMIT %s OFFSET %s"
            params.extend([self.page_size, self.current_page * self.page_size])
            
            result = self.db.execute_query(query, tuple(params))
            self.facturas = result or []
            
        except Exception as e:
            print(f"Error cargando facturas: {e}")
            self.facturas = []
    
    def load_facturas_async(self, callback=None):
        """Carga facturas en background"""
        def _load():
            self._is_loading = True
            self.load_facturas()
            self._is_loading = False
            if callback:
                self.page.run_thread_safe(callback)
        
        thread = threading.Thread(target=_load)
        thread.start()
    
    def list_view(self):
        """Vista de lista de facturas"""
        
        # Cargar datos si no están cargados
        if not self.facturas and not self._is_loading:
            self.load_facturas()
        
        # Crear contenedor de tabla (se actualizará)
        self._table_container = ft.Container(
            content=self._create_table_content(),
            expand=True,
        )
        
        return ft.Container(
            content=ft.Column([
                self._create_header("Facturas de Proveedor", "Gestión de facturas de importación"),
                self._create_toolbar(),
                ft.Container(height=16),
                self._table_container,
                self._create_pagination(),
                ft.Container(height=40),
            ], scroll=ft.ScrollMode.AUTO),
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )
    
    def _create_toolbar(self):
        """Barra de herramientas optimizada"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.TextField(
                        hint_text="Buscar por número, proveedor...",
                        prefix_icon="search",
                        expand=True,
                        border_color=ImportacionesTheme.BORDER,
                        on_submit=self._on_search_submit,  # Buscar solo al presionar Enter
                        text_size=14
                    ),
                    ft.Dropdown(
                        label="Estado",
                        value="",
                        options=[
                            ft.dropdown.Option("", "Todos"),
                            ft.dropdown.Option("pending", "Pendiente"),
                            ft.dropdown.Option("validated", "Validada"),
                            ft.dropdown.Option("paid", "Pagada"),
                            ft.dropdown.Option("cancelled", "Cancelada"),
                        ],
                        width=150,
                        border_color=ImportacionesTheme.BORDER,
                        on_change=self._on_status_filter_change,
                        text_size=14
                    ),
                    ft.IconButton(
                        icon="refresh",
                        tooltip="Actualizar",
                        on_click=self._refresh_list
                    ),
                ], spacing=12),
                ft.Container(height=12),
                ft.Row([
                    ft.ElevatedButton(
                        "Nueva Factura",
                        icon="add",
                        on_click=lambda e: self.page.go("/facturas/nueva"),
                        style=ft.ButtonStyle(
                            bgcolor=ImportacionesTheme.SUCCESS,
                            color="white"
                        )
                    ),
                    ft.ElevatedButton(
                        "Importar XML",
                        icon="upload_file",
                        on_click=self._import_xml,
                        style=ft.ButtonStyle(
                            bgcolor=ImportacionesTheme.INFO,
                            color="white"
                        ),
                        disabled=self.file_picker is None,
                    ),
                    ft.ElevatedButton(
                        "Importar PDF",
                        icon="picture_as_pdf",
                        on_click=self._import_pdf,
                        style=ft.ButtonStyle(
                            bgcolor=ImportacionesTheme.ERROR,
                            color="white"
                        ),
                        disabled=self.file_picker is None,
                    ),
                    ft.Container(expand=True),
                    ft.Text(
                        f"{self.total_count} facturas encontradas",
                        color=ImportacionesTheme.TEXT_SECONDARY
                    ),
                ]),
            ]),
            padding=ft.padding.symmetric(horizontal=24, vertical=16),
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
        )
    
    def _create_table_content(self):
        """Crea el contenido de la tabla"""
        if not self.facturas:
            return self._create_empty_state()
        
        return self._create_facturas_table()
    
    def _create_facturas_table(self):
        """Crea tabla optimizada usando ListView"""
        
        # Usar ListView en lugar de DataTable para mejor rendimiento
        return ft.Container(
            content=ft.Column([
                # Header de la tabla
                self._create_table_header(),
                # Filas con ListView (más eficiente)
                ft.ListView(
                    controls=[
                        self._create_factura_row(factura) 
                        for factura in self.facturas
                    ],
                    spacing=0,
                    height=min(len(self.facturas) * 56, 500),  # Limitar altura
                    auto_scroll=False,
                )
            ]),
            border_radius=12,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            padding=0,
        )
    
    def _create_table_header(self):
        """Header de la tabla"""
        columns = ["Número", "Orden", "Proveedor", "Fecha", "Estado", "Total", ""]
        
        return ft.Container(
            content=ft.Row([
                ft.Text(col, weight=ft.FontWeight.BOLD, size=13, expand=1 if i < 6 else False)
                for i, col in enumerate(columns)
            ] + [ft.Container(width=100)], spacing=8),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ImportacionesTheme.BG_SECONDARY,
            border=ft.border.only(bottom=ft.BorderSide(1, ImportacionesTheme.BORDER)),
        )
    
    def _create_factura_row(self, factura):
        """Crea una fila de factura optimizada"""
        status_config = {
            "pending": (ImportacionesTheme.WARNING, "pending"),
            "validated": (ImportacionesTheme.INFO, "check_circle"),
            "paid": (ImportacionesTheme.SUCCESS, "paid"),
            "cancelled": (ImportacionesTheme.ERROR, "cancel"),
        }
        
        status_color, status_icon = status_config.get(
            factura["status"], 
            (ImportacionesTheme.TEXT_SECONDARY, "pending")
        )
        
        currency = factura.get("currency_code") or "USD"
        total = factura.get("total_amount") or 0
        
        return ft.Container(
            content=ft.Row([
                # Número
                ft.Text(
                    factura["invoice_number"], 
                    weight=ft.FontWeight.BOLD,
                    size=13,
                    expand=True
                ),
                # Orden
                ft.Text(
                    factura.get("po_number") or "-", 
                    size=13,
                    expand=True,
                    color=ImportacionesTheme.TEXT_SECONDARY
                ),
                # Proveedor
                ft.Text(
                    factura.get("supplier_name") or "N/A", 
                    size=13,
                    expand=True,
                    color=ImportacionesTheme.TEXT_SECONDARY
                ),
                # Fecha
                ft.Text(
                    format_date(factura["invoice_date"]), 
                    size=13,
                    expand=True,
                    color=ImportacionesTheme.TEXT_SECONDARY
                ),
                # Estado (simplificado)
                ft.Container(
                    content=ft.Text(
                        factura["status"].title(), 
                        size=11,
                        color=status_color
                    ),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    bgcolor=f"{status_color}20",
                    border_radius=6,
                    expand=True,
                ),
                # Total
                ft.Text(
                    f"{currency} {total:,.2f}", 
                    weight=ft.FontWeight.BOLD,
                    size=13,
                    expand=True
                ),
                # Acciones (reducidas)
                ft.Row([
                    ft.IconButton(
                        icon="visibility",
                        icon_size=18,
                        tooltip="Ver",
                        data=factura["id"],
                        on_click=self._view_factura
                    ),
                    ft.IconButton(
                        icon="edit",
                        icon_size=18,
                        tooltip="Editar",
                        data=factura["id"],
                        on_click=self._edit_factura
                    ),
                ], spacing=0, width=80),
            ], spacing=8),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            border=ft.border.only(bottom=ft.BorderSide(1, ImportacionesTheme.BORDER)),
            on_hover=self._on_row_hover,
            data=factura["id"],
            on_click=self._on_row_click,
        )
    
    def _create_pagination(self):
        """Controles de paginación"""
        total_pages = max(1, (self.total_count + self.page_size - 1) // self.page_size)
        
        return ft.Container(
            content=ft.Row([
                ft.Text(
                    f"Mostrando {len(self.facturas)} de {self.total_count}",
                    color=ImportacionesTheme.TEXT_SECONDARY,
                    size=13
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    icon="chevron_left",
                    disabled=self.current_page == 0,
                    on_click=self._prev_page
                ),
                ft.Text(
                    f"Página {self.current_page + 1} de {total_pages}",
                    size=13
                ),
                ft.IconButton(
                    icon="chevron_right",
                    disabled=(self.current_page + 1) >= total_pages,
                    on_click=self._next_page
                ),
            ]),
            padding=ft.padding.symmetric(horizontal=24, vertical=12),
        )
    
    def _create_empty_state(self):
        """Estado vacío"""
        return ft.Container(
            content=ft.Column([
                ft.Icon("receipt_long", size=64, color=ImportacionesTheme.TEXT_SECONDARY),
                ft.Container(height=20),
                ft.Text("No hay facturas registradas", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=30),
                ft.ElevatedButton(
                    "Crear primera factura",
                    icon="add",
                    on_click=lambda e: self.page.go("/facturas/nueva"),
                    style=ft.ButtonStyle(bgcolor=ImportacionesTheme.SUCCESS, color="white")
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=48,
            alignment=ft.alignment.center,
        )
    
    def _create_header(self, title: str, subtitle: str = None):
        """Header de la página"""
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(title, size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(subtitle, color=ImportacionesTheme.TEXT_SECONDARY) if subtitle else ft.Container(),
                ], spacing=2),
            ]),
            padding=ft.padding.symmetric(horizontal=24, vertical=20),
            bgcolor=ImportacionesTheme.BG_SECONDARY,
        )
    
    # Event Handlers
    def _on_search_submit(self, e):
        """Solo buscar al presionar Enter"""
        self.current_filter["search"] = e.control.value
        self.current_page = 0
        self._reload_data()
    
    def _on_status_filter_change(self, e):
        self.current_filter["status"] = e.control.value if e.control.value else None
        self.current_page = 0
        self._reload_data()
    
    def _refresh_list(self, e=None):
        self._reload_data()
    
    def _reload_data(self):
        """Recarga datos y actualiza UI"""
        self.load_facturas()
        if self._table_container:
            self._table_container.content = self._create_table_content()
            self.page.update()
    
    def _prev_page(self, e):
        if self.current_page > 0:
            self.current_page -= 1
            self._reload_data()
    
    def _next_page(self, e):
        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        if self.current_page + 1 < total_pages:
            self.current_page += 1
            self._reload_data()
    
    def _view_factura(self, e):
        factura_id = e.control.data
        self.page.go(f"/facturas/{factura_id}")
    
    def _edit_factura(self, e):
        factura_id = e.control.data
        self.page.go(f"/facturas/{factura_id}/editar")
    
    def _on_row_hover(self, e):
        e.control.bgcolor = ImportacionesTheme.BG_SECONDARY if e.data == "true" else None
        e.control.update()
    
    def _on_row_click(self, e):
        factura_id = e.control.data
        self.page.go(f"/facturas/{factura_id}")
    
    def _import_xml(self, e):
        if self.file_picker:
            self.file_picker.pick_files(
                allowed_extensions=["xml"],
                allow_multiple=True,
                dialog_title="Seleccionar facturas XML"
            )
    
    def _import_pdf(self, e):
        if self.file_picker:
            self.file_picker.pick_files(
                allowed_extensions=["pdf"],
                allow_multiple=True,
                dialog_title="Seleccionar facturas PDF"
            )

    