# views/reporte_facturas_view.py
import flet as ft
from config_importaciones import (
    ImportacionesTheme, ImportacionesConfig,
    format_currency, format_date
)

class ReporteFacturasView:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.facturas = []
        self.cargar_facturas()
    
    def cargar_facturas(self):
        """Carga las facturas para el reporte"""
        query = """
            SELECT si.*, po.po_number, s.business_name as supplier_name,
                   c.code as currency_code
            FROM supplier_invoices si
            LEFT JOIN purchase_orders po ON si.po_id = po.id
            LEFT JOIN suppliers s ON si.supplier_id = s.id
            LEFT JOIN currencies c ON si.currency_id = c.id
            ORDER BY si.invoice_date DESC
        """
        result = self.db.execute_query(query)
        if result:
            self.facturas = result
    
    def crear_resumen(self):
        """Crea el resumen del reporte"""
        total_facturas = len(self.facturas)
        total_monto = sum(float(f['total_amount']) for f in self.facturas)
        total_pendientes = sum(1 for f in self.facturas if f['status'] == 'pending')
        total_pagadas = sum(1 for f in self.facturas if f['status'] == 'paid')
        
        return ft.ResponsiveRow([
            ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Total Facturas", size=14, 
                               color=ImportacionesTheme.TEXT_SECONDARY),
                        ft.Text(str(total_facturas), size=24, 
                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                    ]),
                    padding=20,
                    bgcolor=ImportacionesTheme.BG_SECONDARY,
                    border_radius=8,
                    border=ft.border.all(1, ImportacionesTheme.BORDER),
                )
            ], col={"md": 3}),
            
            ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Monto Total", size=14, 
                               color=ImportacionesTheme.TEXT_SECONDARY),
                        ft.Text(format_currency(total_monto), size=24, 
                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                    ]),
                    padding=20,
                    bgcolor=ImportacionesTheme.BG_SECONDARY,
                    border_radius=8,
                    border=ft.border.all(1, ImportacionesTheme.BORDER),
                )
            ], col={"md": 3}),
            
            ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Pendientes", size=14, 
                               color=ImportacionesTheme.TEXT_SECONDARY),
                        ft.Text(str(total_pendientes), size=24, 
                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.WARNING),
                    ]),
                    padding=20,
                    bgcolor=ImportacionesTheme.BG_SECONDARY,
                    border_radius=8,
                    border=ft.border.all(1, ImportacionesTheme.BORDER),
                )
            ], col={"md": 3}),
            
            ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Pagadas", size=14, 
                               color=ImportacionesTheme.TEXT_SECONDARY),
                        ft.Text(str(total_pagadas), size=24, 
                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.SUCCESS),
                    ]),
                    padding=20,
                    bgcolor=ImportacionesTheme.BG_SECONDARY,
                    border_radius=8,
                    border=ft.border.all(1, ImportacionesTheme.BORDER),
                )
            ], col={"md": 3}),
        ], spacing=16, run_spacing=16)
    
    def reporte_view(self):
        """Retorna la vista del reporte de facturas"""
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Row([
                                ft.Icon("receipt", size=24, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text("Reporte de Facturas", size=24, 
                                       weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                            ], spacing=12),
                            ft.Text("Análisis detallado de facturas de proveedores", 
                                   size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                        ]),
                        ft.ElevatedButton(
                            "Volver a Dashboard",
                            icon="arrow_back",
                            on_click=lambda e: self.page.go("/reportes"),
                            style=ft.ButtonStyle(
                                bgcolor=ImportacionesTheme.BG_SECONDARY,
                                color=ImportacionesTheme.TEXT_PRIMARY
                            ),
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.symmetric(vertical=16),
                ),
                
                # Resumen
                self.crear_resumen(),
                ft.Container(height=24),
                
                # Tabla de facturas
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon("table_chart", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text("Detalle de Facturas", size=16, 
                                       weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Container(expand=True),
                                ft.Text(f"{len(self.facturas)} facturas", 
                                       color=ImportacionesTheme.TEXT_SECONDARY),
                            ], spacing=8),
                            ft.Divider(height=20),
                            
                            ft.DataTable(
                                columns=[
                                    ft.DataColumn(ft.Text("N° Factura")),
                                    ft.DataColumn(ft.Text("PO")),
                                    ft.DataColumn(ft.Text("Proveedor")),
                                    ft.DataColumn(ft.Text("Fecha")),
                                    ft.DataColumn(ft.Text("Moneda")),
                                    ft.DataColumn(ft.Text("Subtotal", text_align=ft.TextAlign.RIGHT)),
                                    ft.DataColumn(ft.Text("IGV", text_align=ft.TextAlign.RIGHT)),
                                    ft.DataColumn(ft.Text("Total", text_align=ft.TextAlign.RIGHT)),
                                    ft.DataColumn(ft.Text("Estado")),
                                ],
                                rows=self.crear_filas_facturas(),
                                heading_row_color=ImportacionesTheme.BG_SECONDARY,
                            ),
                        ]),
                        padding=20,
                    ),
                    elevation=1,
                ),
                
                ft.Container(height=40),
            ], scroll=ft.ScrollMode.AUTO),
            padding=24,
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )
    
    def crear_filas_facturas(self):
        """Crea las filas de la tabla de facturas"""
        rows = []
        for factura in self.facturas:
            # Badge de estado
            status_color = ImportacionesTheme.SUCCESS if factura['status'] == 'paid' else \
                          ImportacionesTheme.WARNING if factura['status'] == 'validated' else \
                          ImportacionesTheme.ERROR if factura['status'] == 'cancelled' else \
                          ImportacionesTheme.TEXT_SECONDARY
            
            status_badge = ft.Container(
                content=ft.Text(
                    factura['status'].title(),
                    size=12,
                    color="white",
                    weight=ft.FontWeight.BOLD
                ),
                bgcolor=status_color,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=8,
            )
            
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(factura['invoice_number'], 
                                           color=ImportacionesTheme.TEXT_PRIMARY)),
                        ft.DataCell(ft.Text(factura['po_number'], 
                                           color=ImportacionesTheme.TEXT_SECONDARY)),
                        ft.DataCell(ft.Text(factura['supplier_name'] or "N/A", 
                                           color=ImportacionesTheme.TEXT_SECONDARY)),
                        ft.DataCell(ft.Text(format_date(factura['invoice_date']), 
                                           color=ImportacionesTheme.TEXT_SECONDARY)),
                        ft.DataCell(ft.Text(factura['currency_code'], 
                                           color=ImportacionesTheme.TEXT_SECONDARY)),
                        ft.DataCell(ft.Text(format_currency(factura['subtotal']), 
                                           color=ImportacionesTheme.TEXT_SECONDARY,
                                           text_align=ft.TextAlign.RIGHT)),
                        ft.DataCell(ft.Text(format_currency(factura['tax_amount']), 
                                           color=ImportacionesTheme.TEXT_SECONDARY,
                                           text_align=ft.TextAlign.RIGHT)),
                        ft.DataCell(ft.Text(format_currency(factura['total_amount']), 
                                           color=ImportacionesTheme.TEXT_PRIMARY,
                                           weight=ft.FontWeight.BOLD,
                                           text_align=ft.TextAlign.RIGHT)),
                        ft.DataCell(status_badge),
                    ]
                )
            )
        
        return rows