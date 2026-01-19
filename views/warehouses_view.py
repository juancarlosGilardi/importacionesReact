# views/warehouses_view.py - Gestión de Almacenes
import flet as ft
import threading
from config_importaciones import ImportacionesTheme

class WarehousesView:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.warehouses = []
        self.table_container = None
        self.loading = True
    
    def list_view(self):
        """Vista de lista de almacenes"""
        
        # Contenedor de tabla
        self.table_container = ft.Container(
            content=ft.Column([
                ft.ProgressRing(width=40, height=40),
                ft.Text("Cargando almacenes...", color=ImportacionesTheme.TEXT_SECONDARY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               alignment=ft.MainAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            height=300,
        )
        
        # Cargar datos
        threading.Thread(target=self._load_warehouses_async, daemon=True).start()
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.WAREHOUSE, size=28, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text("Gestión de Almacenes", size=26, weight=ft.FontWeight.BOLD,
                                       color=ImportacionesTheme.TEXT_PRIMARY),
                            ], spacing=12),
                            ft.Text("Administre sus ubicaciones de almacenamiento",
                                   size=14, color=ImportacionesTheme.TEXT_SECONDARY),
                        ]),
                        ft.Row([
                            ft.ElevatedButton(
                                "Volver a Inventario",
                                icon=ft.Icons.ARROW_BACK,
                                on_click=lambda _: self.page.go("/inventario"),
                            ),
                            ft.ElevatedButton(
                                "Nuevo Almacén",
                                icon=ft.Icons.ADD,
                                on_click=lambda _: self._show_warehouse_dialog(),
                                style=ft.ButtonStyle(
                                    bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                                    color="white"
                                )
                            ),
                        ], spacing=12),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.symmetric(horizontal=24, vertical=20),
                    bgcolor=ImportacionesTheme.BG_SECONDARY,
                    border=ft.border.only(bottom=ft.BorderSide(1, ImportacionesTheme.BORDER)),
                ),
                
                # Contenido
                ft.Container(
                    content=ft.Column([
                        self.table_container,
                    ], scroll=ft.ScrollMode.AUTO),
                    padding=24,
                    expand=True,
                ),
            ]),
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )
    
    def _load_warehouses_async(self):
        """Carga almacenes en background"""
        try:
            query = """
                SELECT 
                    w.*,
                    (SELECT COUNT(DISTINCT i.product_id) FROM inventory i WHERE i.warehouse_id = w.id AND i.quantity > 0) as product_count,
                    (SELECT COALESCE(SUM(i.quantity * i.unit_cost), 0) FROM inventory i WHERE i.warehouse_id = w.id) as total_value
                FROM warehouses w
                ORDER BY w.name
            """
            self.warehouses = self.db.execute_query(query) or []
            
            self._update_table()
            self.page.update()
            
        except Exception as e:
            print(f"Error cargando almacenes: {e}")
            self.table_container.content = ft.Text(f"Error: {str(e)}", color=ImportacionesTheme.ERROR)
            self.page.update()
    
    def _update_table(self):
        """Actualiza la tabla de almacenes"""
        if not self.warehouses:
            self.table_container.content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.WAREHOUSE, size=64, color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Container(height=16),
                    ft.Text("No hay almacenes registrados", size=18,
                           color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.Container(height=16),
                    ft.ElevatedButton(
                        "Crear Primer Almacén",
                        icon=ft.Icons.ADD,
                        on_click=lambda _: self._show_warehouse_dialog(),
                        style=ft.ButtonStyle(
                            bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                            color="white"
                        )
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=60,
                alignment=ft.alignment.center,
            )
            return
        
        rows = []
        for w in self.warehouses:
            status_color = ImportacionesTheme.SUCCESS if w['status'] == 'active' else ImportacionesTheme.TEXT_SECONDARY
            
            rows.append(ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(w['code'], weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(w['name'])),
                    ft.DataCell(ft.Text(w.get('address', '-') or '-', 
                                       color=ImportacionesTheme.TEXT_SECONDARY)),
                    ft.DataCell(ft.Container(
                        content=ft.Text(w['status'].upper(), size=11, color="white"),
                        bgcolor=status_color,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=4,
                    )),
                    ft.DataCell(ft.Text(str(w.get('product_count', 0)),
                                       weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(f"${float(w.get('total_value', 0)):,.2f}",
                                       weight=ft.FontWeight.BOLD,
                                       color=ImportacionesTheme.STATUS_CONFIRMED)),
                    ft.DataCell(ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.VISIBILITY,
                            icon_size=18,
                            tooltip="Ver detalle",
                            on_click=lambda e, wid=w['id']: self.page.go(f"/almacenes/{wid}"),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_size=18,
                            tooltip="Editar",
                            on_click=lambda e, wh=w: self._show_warehouse_dialog(wh),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_size=18,
                            icon_color=ImportacionesTheme.ERROR,
                            tooltip="Eliminar",
                            on_click=lambda e, wh=w: self._confirm_delete(wh),
                        ),
                    ], spacing=0)),
                ],
                on_select_changed=lambda e, wid=w['id']: self.page.go(f"/almacenes/{wid}"),
            ))
        
        self.table_container.content = ft.Container(
            content=ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Código", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Nombre", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Dirección", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Estado", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Productos", weight=ft.FontWeight.BOLD), numeric=True),
                    ft.DataColumn(ft.Text("Valor Total", weight=ft.FontWeight.BOLD), numeric=True),
                    ft.DataColumn(ft.Text("Acciones", weight=ft.FontWeight.BOLD)),
                ],
                rows=rows,
                heading_row_color=ImportacionesTheme.BG_SECONDARY,
                border=ft.border.all(1, ImportacionesTheme.BORDER),
            ),
            border_radius=12,
            bgcolor=ImportacionesTheme.BG_SECONDARY,
        )
    
    def _show_warehouse_dialog(self, warehouse=None):
        """Muestra diálogo para crear/editar almacén"""
        is_edit = warehouse is not None
        
        code_field = ft.TextField(
            label="Código *",
            value=warehouse['code'] if is_edit else "",
            width=150,
            autofocus=True,
        )
        
        name_field = ft.TextField(
            label="Nombre del Almacén *",
            value=warehouse['name'] if is_edit else "",
            expand=True,
        )
        
        address_field = ft.TextField(
            label="Dirección",
            value=warehouse.get('address', '') if is_edit else "",
            expand=True,
        )
        
        manager_field = ft.TextField(
            label="Responsable",
            value=warehouse.get('manager_name', '') if is_edit else "",
            width=200,
        )
        
        status_dropdown = ft.Dropdown(
            label="Estado",
            value=warehouse['status'] if is_edit else "active",
            width=150,
            options=[
                ft.dropdown.Option("active", "Activo"),
                ft.dropdown.Option("inactive", "Inactivo"),
            ],
        )
        
        notes_field = ft.TextField(
            label="Notas",
            value=warehouse.get('notes', '') if is_edit else "",
            multiline=True,
            min_lines=2,
            max_lines=4,
        )
        
        def save_warehouse(e):
            if not code_field.value or not name_field.value:
                self._show_snackbar("Código y Nombre son obligatorios", "error")
                return
            
            try:
                if is_edit:
                    query = """
                        UPDATE warehouses 
                        SET code = %s, name = %s, address = %s, 
                            manager_name = %s, status = %s, notes = %s
                        WHERE id = %s
                    """
                    params = (
                        code_field.value, name_field.value, address_field.value,
                        manager_field.value, status_dropdown.value, notes_field.value,
                        warehouse['id']
                    )
                else:
                    query = """
                        INSERT INTO warehouses (code, name, address, manager_name, status, notes)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    params = (
                        code_field.value, name_field.value, address_field.value,
                        manager_field.value, status_dropdown.value, notes_field.value
                    )
                
                self.db.execute_query(query, params, fetch=False)
                self.page.close(dialog)
                self._show_snackbar(f"Almacén {'actualizado' if is_edit else 'creado'} correctamente", "success")
                
                # Recargar datos
                threading.Thread(target=self._load_warehouses_async, daemon=True).start()
                
            except Exception as ex:
                self._show_snackbar(f"Error: {str(ex)}", "error")
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"{'Editar' if is_edit else 'Nuevo'} Almacén"),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([code_field, name_field], spacing=16),
                    address_field,
                    ft.Row([manager_field, status_dropdown], spacing=16),
                    notes_field,
                ], spacing=16, tight=True),
                width=500,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton(
                    "Guardar",
                    on_click=save_warehouse,
                    style=ft.ButtonStyle(
                        bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                        color="white"
                    )
                ),
            ],
        )
        
        self.page.open(dialog)
    
    def _confirm_delete(self, warehouse):
        """Confirma eliminación de almacén"""
        def do_delete(e):
            try:
                # Verificar si tiene inventario
                check = self.db.execute_query(
                    "SELECT COUNT(*) as count FROM inventory WHERE warehouse_id = %s AND quantity > 0",
                    (warehouse['id'],)
                )
                
                if check and check[0]['count'] > 0:
                    self._show_snackbar("No se puede eliminar: el almacén tiene inventario", "error")
                    self.page.close(dialog)
                    return
                
                self.db.execute_query(
                    "DELETE FROM warehouses WHERE id = %s",
                    (warehouse['id'],),
                    fetch=False
                )
                
                self.page.close(dialog)
                self._show_snackbar("Almacén eliminado", "success")
                threading.Thread(target=self._load_warehouses_async, daemon=True).start()
                
            except Exception as ex:
                self._show_snackbar(f"Error: {str(ex)}", "error")
        
        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Eliminación"),
            content=ft.Text(f"¿Está seguro de eliminar el almacén '{warehouse['name']}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dialog)),
                ft.TextButton(
                    "Eliminar",
                    on_click=do_delete,
                    style=ft.ButtonStyle(color=ImportacionesTheme.ERROR)
                ),
            ],
        )
        
        self.page.open(dialog)
    
    def _show_snackbar(self, message, tipo="info"):
        colors = {
            "success": ImportacionesTheme.SUCCESS,
            "error": ImportacionesTheme.ERROR,
            "info": ImportacionesTheme.INFO,
        }
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="white"),
            bgcolor=colors.get(tipo, ImportacionesTheme.INFO),
        )
        self.page.snack_bar.open = True
        self.page.update()