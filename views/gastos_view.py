# views/gastos_view.py
import flet as ft
from config_importaciones import (
    ImportacionesTheme, ImportacionesConfig,
    format_currency, format_date, create_status_badge
)

class GastosView:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.gastos = []
        self.cargar_gastos()
    
    def cargar_gastos(self):
        """Carga los gastos desde la base de datos"""
        query = """
            SELECT ie.*, po.po_number, s.business_name as supplier_po,
                   c.code as currency_code, c.symbol as currency_symbol,
                   etu.nombre_ui as expense_type_name, etu.color_ui as expense_type_color
            FROM import_expenses ie
            LEFT JOIN purchase_orders po ON ie.po_id = po.id
            LEFT JOIN suppliers s ON po.supplier_id = s.id
            LEFT JOIN currencies c ON ie.currency_id = c.id
            LEFT JOIN expense_types_ui etu ON ie.expense_type = etu.tipo_gasto
            ORDER BY ie.expense_date DESC, ie.created_at DESC
            LIMIT 50
        """
        result = self.db.execute_query(query)
        if result:
            self.gastos = result
    
    def crear_fila_gasto(self, gasto):
        """Crea una fila para la tabla de gastos"""
        # Badge de tipo de gasto
        tipo_badge = ft.Container(
            content=ft.Row([
                ft.Container(
                    width=8,
                    height=8,
                    bgcolor=gasto['expense_type_color'],
                    border_radius=4,
                ),
                ft.Text(gasto['expense_type_name'], size=12, 
                       color=ImportacionesTheme.TEXT_SECONDARY),
            ], spacing=6),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            bgcolor=f"{gasto['expense_type_color']}15",
            border_radius=8,
        )
        
        # Badge de estado
        status_color = ImportacionesTheme.SUCCESS if gasto['status'] == 'paid' else \
                      ImportacionesTheme.WARNING if gasto['status'] == 'approved' else \
                      ImportacionesTheme.ERROR if gasto['status'] == 'pending' else \
                      ImportacionesTheme.TEXT_SECONDARY
        
        status_badge = ft.Container(
            content=ft.Text(
                gasto['status'].title(),
                size=12,
                color="white",
                weight=ft.FontWeight.BOLD
            ),
            bgcolor=status_color,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=8,
        )
        
        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(gasto['po_number'], 
                                   color=ImportacionesTheme.TEXT_PRIMARY,
                                   weight=ft.FontWeight.BOLD)),
                ft.DataCell(tipo_badge),
                ft.DataCell(ft.Text(gasto['supplier_name'] or gasto['supplier_po'] or "N/A", 
                                   color=ImportacionesTheme.TEXT_SECONDARY)),
                ft.DataCell(ft.Text(format_date(gasto['expense_date']) if gasto['expense_date'] else "", 
                                   color=ImportacionesTheme.TEXT_SECONDARY)),
                ft.DataCell(status_badge),
                ft.DataCell(ft.Row([
                    ft.Text(f"{gasto['currency_code']} ", 
                           size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Text(format_currency(gasto['amount']), 
                           color=ImportacionesTheme.TEXT_PRIMARY,
                           weight=ft.FontWeight.BOLD),
                ])),
                ft.DataCell(ft.Row([
                    ft.Text(f"PEN ", 
                           size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Text(format_currency(gasto.get('amount_pen', 0)), 
                           color=ImportacionesTheme.TEXT_PRIMARY),
                ])),
                ft.DataCell(ft.Row([
                    ft.IconButton(
                        icon="visibility",
                        icon_size=18,
                        icon_color=ImportacionesTheme.TEXT_SECONDARY,
                        on_click=lambda e, g=gasto: self.page.go(f"/ordenes/{g['po_id']}")
                    ),
                    ft.IconButton(
                        icon="edit",
                        icon_size=18,
                        icon_color=ImportacionesTheme.TEXT_SECONDARY,
                        on_click=lambda e, g=gasto: self.page.go(f"/gastos/{g['id']}/editar")
                    ),
                ], spacing=4)),
            ]
        )
    
    def list_view(self):
        """Retorna la vista de lista de gastos"""
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Row([
                                ft.Icon("account_balance_wallet", size=24, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text("Gastos de Importación", size=24, 
                                       weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                            ], spacing=12),
                            ft.Text("Gestión de costos asociados a las importaciones", 
                                   size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                        ]),
                        ft.ElevatedButton(
                            "Nuevo Gasto",
                            icon="add",
                            on_click=lambda e: self.page.go("/gastos/nuevo"),
                            style=ft.ButtonStyle(
                                bgcolor=ImportacionesTheme.SUCCESS,
                                color="white"
                            ),
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.symmetric(vertical=16),
                ),
                
                # Resumen por tipo de gasto
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon("assessment", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text("Resumen por Tipo de Gasto", size=16, 
                                       weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                            ], spacing=8),
                            ft.Divider(height=20),
                            self.crear_resumen_tipos(),
                        ]),
                        padding=20,
                    ),
                    elevation=1,
                ),
                
                # Tabla de gastos
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.DataTable(
                                columns=[
                                    ft.DataColumn(ft.Text("PO")),
                                    ft.DataColumn(ft.Text("Tipo")),
                                    ft.DataColumn(ft.Text("Proveedor")),
                                    ft.DataColumn(ft.Text("Fecha")),
                                    ft.DataColumn(ft.Text("Estado")),
                                    ft.DataColumn(ft.Text("Monto")),
                                    ft.DataColumn(ft.Text("PEN")),
                                    ft.DataColumn(ft.Text("Acciones")),
                                ],
                                rows=[self.crear_fila_gasto(g) for g in self.gastos],
                                heading_row_color=ImportacionesTheme.BG_SECONDARY,
                            ) if self.gastos else ft.Container(
                                content=ft.Column([
                                    ft.Icon("payments", size=48, color=ImportacionesTheme.TEXT_SECONDARY),
                                    ft.Container(height=16),
                                    ft.Text("No hay gastos registrados", 
                                           color=ImportacionesTheme.TEXT_SECONDARY),
                                    ft.ElevatedButton(
                                        "Registrar Primer Gasto",
                                        icon="add",
                                        on_click=lambda e: self.page.go("/gastos/nuevo"),
                                        height=36,
                                    ),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=40,
                                alignment=ft.alignment.center
                            ),
                        ]),
                        padding=20,
                    ),
                    elevation=1,
                ),
            ], scroll=ft.ScrollMode.AUTO),
            padding=24,
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )
    
    def crear_resumen_tipos(self):
        """Crea el resumen por tipo de gasto"""
        # Agrupar gastos por tipo
        resumen = {}
        for gasto in self.gastos:
            tipo = gasto['expense_type_name']
            monto_pen = float(gasto.get('amount_pen', 0))
            
            if tipo not in resumen:
                resumen[tipo] = {
                    'monto': 0,
                    'color': gasto['expense_type_color'],
                    'count': 0
                }
            
            resumen[tipo]['monto'] += monto_pen
            resumen[tipo]['count'] += 1
        
        # Calcular total
        total = sum(info['monto'] for info in resumen.values())
        
        # Crear filas de resumen
        filas = []
        for tipo, info in resumen.items():
            porcentaje = (info['monto'] / total * 100) if total > 0 else 0
            
            filas.append(
                ft.Row([
                    ft.Container(
                        width=8,
                        height=8,
                        bgcolor=info['color'],
                        border_radius=4,
                    ),
                    ft.Text(tipo, size=13, color=ImportacionesTheme.TEXT_PRIMARY, width=200),
                    ft.Text(f"{info['count']} gastos", size=13, color=ImportacionesTheme.TEXT_SECONDARY, width=100),
                    ft.Container(
                        content=ft.Container(
                            width=f"{porcentaje}%",
                            height=8,
                            bgcolor=info['color'],
                            border_radius=4,
                        ),
                        width=200,
                        height=8,
                        bgcolor=ImportacionesTheme.BORDER,
                        border_radius=4,
                        padding=0,
                    ),
                    ft.Text(f"{porcentaje:.1f}%", size=13, color=ImportacionesTheme.TEXT_SECONDARY, width=80),
                    ft.Text(format_currency(info['monto']), size=13, 
                           color=ImportacionesTheme.TEXT_PRIMARY,
                           weight=ft.FontWeight.BOLD),
                ], spacing=12)
            )
        
        return ft.Column([
            *filas,
            ft.Divider(height=20),
            ft.Row([
                ft.Text("TOTAL", size=14, color=ImportacionesTheme.TEXT_PRIMARY, 
                       weight=ft.FontWeight.BOLD, width=308),
                ft.Text(format_currency(total), size=14, 
                       color=ImportacionesTheme.TEXT_PRIMARY,
                       weight=ft.FontWeight.BOLD),
            ], spacing=12)
        ], spacing=12)