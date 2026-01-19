import flet as ft
from config_importaciones import (
    ImportacionesTheme, format_date, get_status_color, get_status_icon
)

class MovimientosView:
    def __init__(self, page: ft.Page, db, tipo_movimiento=None):
        self.page = page
        self.db = db
        self.tipo_movimiento = tipo_movimiento
        
        # Configuración "Camaleónica"
        self.config = {
            'receipt': {
                'titulo': 'Ingresos a Almacén',
                'icono': ft.Icons.INBOX_ROUNDED,
                'desc': 'Historial de recepciones de importación y compras locales',
                'btn_text': 'Nuevo Ingreso',
                'btn_icon': ft.Icons.ADD,
            },
            'output': {
                'titulo': 'Salidas de Almacén',
                'icono': ft.Icons.OUTBOX_ROUNDED,
                'desc': 'Despachos, ventas y consumos internos',
                'btn_text': 'Nueva Salida',
                'btn_icon': ft.Icons.REMOVE,
            },
            'transfer': {
                'titulo': 'Transferencias',
                'icono': ft.Icons.SWAP_HORIZ_ROUNDED,
                'desc': 'Movimientos entre ubicaciones o almacenes',
                'btn_text': 'Nueva Transferencia',
                'btn_icon': ft.Icons.SWAP_HORIZ,
            },
            None: { 
                'titulo': 'Kardex General',
                'icono': ft.Icons.HISTORY_ROUNDED,
                'desc': 'Historial completo de movimientos de inventario',
                'btn_text': 'Registrar Movimiento',
                'btn_icon': ft.Icons.ADD_CIRCLE,
            }
        }
        self.current_config = self.config.get(tipo_movimiento, self.config[None])

    def procesar_accion_nuevo(self, e):
        """Redirige al formulario correcto según la pestaña actual"""
        if self.tipo_movimiento == 'receipt':
            self.page.go("/ordenes") 
        elif self.tipo_movimiento == 'transfer':
            self.page.go("/transferencia/nueva") 
        elif self.tipo_movimiento == 'output':
            self.page.go("/salida/nueva")
        else:
            # Si estamos en "Todos" o "Salidas"
            self.page.snack_bar = ft.SnackBar(ft.Text("Seleccione una pestaña específica (Ingresos o Transferencias) para crear."))
            self.page.snack_bar.open = True
            self.page.update()

    def obtener_movimientos(self):
        query = """
            SELECT wm.id, wm.movement_number, wm.movement_type, wm.movement_date,
                wm.status, wm.reference_document, wm.total_products,
                po.po_number, s.business_name as supplier
            FROM warehouse_movements wm
            LEFT JOIN purchase_orders po ON wm.po_id = po.id
            LEFT JOIN suppliers s ON po.supplier_id = s.id
        """
        params = []
        if self.tipo_movimiento:
            query += " WHERE wm.movement_type = %s"
            params.append(self.tipo_movimiento)
        
        query += " ORDER BY wm.movement_date DESC, wm.created_at DESC"
        return self.db.execute_query(query, tuple(params))

    def get_type_label(self, type_code):
        types = {
            'receipt': ('Recepción', 'arrow_downward', ImportacionesTheme.SUCCESS),
            'transfer': ('Transferencia', 'compare_arrows', ImportacionesTheme.INFO),
            'adjustment': ('Ajuste', 'tune', ImportacionesTheme.WARNING),
            'output': ('Salida', 'arrow_upward', ImportacionesTheme.ERROR),
        }
        return types.get(type_code, ('Otro', 'help', ImportacionesTheme.TEXT_SECONDARY))

    def create_table_rows(self, movimientos):
        rows = []
        if not movimientos:
            return []
            
        for mov in movimientos:
            label, icon, color = self.get_type_label(mov['movement_type'])
            
            # Construimos la lista de celdas dinámicamente
            cells = [
                # Columna 1: ID/Número
                ft.DataCell(ft.Container(
                    content=ft.Row([
                        ft.Icon(icon, size=16, color=color),
                        ft.Text(mov['movement_number'], weight=ft.FontWeight.BOLD)
                    ], spacing=8),
                    on_click=lambda e, m=mov: self.page.go(f"/movimientos/{m['id']}/editar")
                )),
                # Columna 2: Fecha
                ft.DataCell(ft.Text(format_date(mov['movement_date']))),
            ]

            # SOLO agregamos la celda de Tipo si NO estamos filtrando (Vista "Todos")
            if not self.tipo_movimiento:
                cells.append(
                    ft.DataCell(ft.Container(
                        content=ft.Text(label, size=12, color=color),
                        bgcolor=f"{color}15",
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=4
                    ))
                )
            
            # Agregamos el resto de celdas comunes
            cells.extend([
                # Columna Referencia
                ft.DataCell(ft.Column([
                    ft.Text(mov['po_number'] or mov['reference_document'] or "Sin Ref", weight=ft.FontWeight.BOLD, size=12),
                    ft.Text(mov['supplier'] or "", size=10, color=ImportacionesTheme.TEXT_SECONDARY)
                ], spacing=2, alignment=ft.MainAxisAlignment.CENTER)),
                # Columna Estado
                ft.DataCell(ft.Container(
                    content=ft.Row([
                        ft.Icon(get_status_icon(mov['status']), size=14, 
                               color=get_status_color(mov['status'])),
                        ft.Text(mov['status'].upper(), size=11, 
                               color=get_status_color(mov['status']))
                    ], spacing=4),
                )),
                # Columna Acciones
                ft.DataCell(ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.VISIBILITY,
                        icon_color=ImportacionesTheme.TEXT_SECONDARY,
                        tooltip="Ver Detalle",
                        on_click=lambda e, m=mov: self.page.go(f"/movimientos/{m['id']}/editar")
                    )
                ]))
            ])
            
            rows.append(ft.DataRow(cells=cells))
        return rows
    
    # --- LÓGICA DE PESTAÑAS ---
    def cambiar_tab(self, e):
        """Navega a la ruta correspondiente según la pestaña seleccionada"""
        rutas = ["/movimientos", "/movimientos/ingresos", "/movimientos/salidas", "/movimientos/transferencias"]
        try:
            self.page.go(rutas[e.control.selected_index])
        except: pass

    def get_tab_index(self):
        """Determina qué pestaña activar"""
        if self.tipo_movimiento == 'receipt': return 1
        if self.tipo_movimiento == 'output': return 2
        if self.tipo_movimiento == 'transfer': return 3
        return 0

    def list_view(self):
        datos = self.obtener_movimientos()
        
        columnas = [
            ft.DataColumn(ft.Text("Movimiento")),
            ft.DataColumn(ft.Text("Fecha")),
        ]
        if not self.tipo_movimiento: 
            columnas.append(ft.DataColumn(ft.Text("Tipo")))
        columnas.extend([
            ft.DataColumn(ft.Text("Referencia")),
            ft.DataColumn(ft.Text("Estado")),
            ft.DataColumn(ft.Text("Acciones")),
        ])
        # Header con Pestañas
        return ft.Container(
            content=ft.Column([
                # 1. Título y Botón
                ft.Container(
                    content=ft.Row([
                        ft.Row([
                            ft.Icon(self.current_config['icono'], size=32, color=ImportacionesTheme.STATUS_CONFIRMED),
                            ft.Column([
                                ft.Text(self.current_config['titulo'], size=24, weight="bold", color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text(self.current_config['desc'], size=14, color=ImportacionesTheme.TEXT_SECONDARY),
                            ], spacing=2)
                        ]),
                        ft.ElevatedButton(
                            self.current_config['btn_text'],
                            icon=self.current_config['btn_icon'],
                            bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                            color="white",
                            on_click=self.procesar_accion_nuevo
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.only(bottom=10)
                ),
                
                # 2. Pestañas de Navegación (NUEVO)
                ft.Tabs(
                    selected_index=self.get_tab_index(),
                    animation_duration=300,
                    on_change=self.cambiar_tab,
                    tabs=[
                        ft.Tab(text="Todos", icon=ft.Icons.HISTORY),
                        ft.Tab(text="Ingresos", icon=ft.Icons.INBOX),
                        ft.Tab(text="Salidas", icon=ft.Icons.OUTBOX),
                        ft.Tab(text="Transferencias", icon=ft.Icons.SWAP_HORIZ),
                    ],
                ),
                
                ft.Divider(height=1, color="transparent"), # Espaciador

                # 3. Tabla
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.DataTable(
                                columns=columnas,
                                rows=self.create_table_rows(datos),
                                border=ft.border.all(1, ImportacionesTheme.BORDER),
                                heading_row_color=ImportacionesTheme.BG_SECONDARY,
                                heading_row_height=40,
                                data_row_min_height=60,
                                expand=True 
                            ) if datos else ft.Container(
                                content=ft.Text("No hay movimientos registrados", color=ImportacionesTheme.TEXT_SECONDARY),
                                padding=40, alignment=ft.alignment.center
                            )
                        ], scroll=ft.ScrollMode.AUTO),
                        padding=0
                    ),
                    elevation=0,
                    variant=ft.CardVariant.OUTLINED,
                    expand=True
                )
            ], expand=True),
            padding=24,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
            expand=True
        )