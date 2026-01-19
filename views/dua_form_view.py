import flet as ft
from datetime import datetime
from config_importaciones import (
    ImportacionesTheme, ImportacionesConfig,
    format_currency, format_date, get_status_color
)

class DUAFormView:
    def __init__(self, page: ft.Page, db, dua_id=None):
        self.page = page
        self.db = db
        self.dua_id = dua_id
        self.modo_edicion = dua_id is not None
        self.importacion_id = self.obtener_importacion_id_url()
        
        # Datos para combos
        self.importaciones = []
        
        # Campos del formulario principal
        self.controls = self.crear_controles()
        
        # Cargar datos iniciales
        self.cargar_datos_combos()
        if self.modo_edicion:
            self.cargar_dua()
        elif self.importacion_id:
            self.cargar_importacion_por_defecto()
    
    def obtener_importacion_id_url(self):
        """Obtiene el importacion_id de los parámetros de la URL"""
        if hasattr(self.page, 'route') and 'importacion_id=' in self.page.route:
            try:
                import urllib.parse
                # Obtener ruta actual
                route = self.page.route
                if '?' in route:
                    query_string = route.split('?')[1]
                    params = urllib.parse.parse_qs(query_string)
                    return int(params.get('importacion_id', [0])[0])
            except:
                return None
        return None
    
    def cargar_importacion_por_defecto(self):
        """Carga la importación por defecto si viene en la URL"""
        if self.importacion_id:
            self.controls['importacion'].value = str(self.importacion_id)
            self.calcular_valores_importacion(None)
    
    def crear_controles(self):
        """Crea todos los controles del formulario - AHORA PARA IMPORTACIÓN"""
        return {
            'dua_number': ft.TextField(
                label="Número de DUA *",
                prefix_icon="numbers",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
            ),
            
            'importacion': ft.Dropdown(
                label="Importación (Folder Manila) *",
                prefix_icon="folder",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                options=[],
                on_change=self.calcular_valores_importacion
            ),
            
            'registration_date': ft.TextField(
                label="Fecha de Registro *",
                prefix_icon="event",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value=datetime.now().strftime("%Y-%m-%d"),
                hint_text="YYYY-MM-DD"
            ),
            
            'clearance_date': ft.TextField(
                label="Fecha de Despacho",
                prefix_icon="event_available",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value=datetime.now().strftime("%Y-%m-%d"),
                hint_text="YYYY-MM-DD"
            ),
            
            'customs_agency': ft.TextField(
                label="Agencia de Aduanas",
                prefix_icon="gavel",
                border_color=ImportacionesTheme.BORDER,
                filled=True
            ),
            
            'customs_agent_ruc': ft.TextField(
                label="RUC Agente Aduanal",
                prefix_icon="badge",
                border_color=ImportacionesTheme.BORDER,
                filled=True
            ),
            
            'numero_operacion': ft.TextField(
                label="Número de Operación",
                prefix_icon="receipt_long",
                border_color=ImportacionesTheme.BORDER,
                filled=True
            ),
            
            # Valores en USD
            'fob_value_usd': ft.TextField(
                label="Valor FOB (USD)",
                prefix_icon="attach_money",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="0.00",
                on_change=self.calcular_impuestos
            ),
            
            'freight_usd': ft.TextField(
                label="Flete (USD)",
                prefix_icon="flight",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="0.00",
                on_change=self.calcular_impuestos
            ),
            
            'insurance_usd': ft.TextField(
                label="Seguro (USD)",
                prefix_icon="security",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="0.00",
                on_change=self.calcular_impuestos
            ),
            
            'cif_value_usd': ft.TextField(
                label="Valor CIF (USD)",
                prefix_icon="paid",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="0.00",
                read_only=True
            ),
            
            # Tasas de impuestos
            'ad_valorem_rate': ft.TextField(
                label="Tasa Ad-Valorem (%)",
                prefix_icon="percent",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="6.00",
                on_change=self.calcular_impuestos
            ),
            
            'ad_valorem_amount': ft.TextField(
                label="Ad-Valorem (USD)",
                prefix_icon="receipt",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="0.00",
                on_change=self.calcular_totales
            ),
            
            'igv_rate': ft.TextField(
                label="Tasa IGV (%)",
                prefix_icon="percent",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="18.00",
                on_change=self.calcular_impuestos
            ),
            
            'igv_amount': ft.TextField(
                label="IGV (USD)",
                prefix_icon="receipt",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="0.00",
                read_only=True
            ),
            
            'ipm_rate': ft.TextField(
                label="Tasa IPM (%)",
                prefix_icon="percent",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="0.00",
                on_change=self.calcular_impuestos
            ),
            
            'ipm_amount': ft.TextField(
                label="IPM (USD)",
                prefix_icon="receipt",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="0.00",
                read_only=True
            ),
            
            # Otros impuestos
            'selective_consumption': ft.TextField(
                label="Consumo Selectivo (USD)",
                prefix_icon="receipt",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="0.00",
                on_change=self.calcular_totales
            ),
            
            'antidumping': ft.TextField(
                label="Antidumping (USD)",
                prefix_icon="receipt",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="0.00",
                on_change=self.calcular_totales
            ),
            
            # Gastos aduaneros
            'customs_fees': ft.TextField(
                label="Derechos Aduaneros (USD)",
                prefix_icon="receipt",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="0.00",
                on_change=self.calcular_totales
            ),
            
            'agency_fees': ft.TextField(
                label="Honorarios Agente (USD)",
                prefix_icon="badge",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="0.00",
                on_change=self.calcular_totales
            ),
            
            'storage_fees': ft.TextField(
                label="Almacenaje (USD)",
                prefix_icon="warehouse",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="0.00",
                on_change=self.calcular_totales
            ),
            
            'other_customs_expenses': ft.TextField(
                label="Otros Gastos (USD)",
                prefix_icon="payments",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="0.00",
                on_change=self.calcular_totales
            ),
            
            # Totales
            'total_taxes': ft.TextField(
                label="Total Impuestos (USD)",
                prefix_icon="summarize",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="0.00",
                read_only=True
            ),
            
            'total_customs_expenses': ft.TextField(
                label="Total Gastos Aduaneros (USD)",
                prefix_icon="summarize",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                value="0.00",
                read_only=True
            ),
            
            'status': ft.Dropdown(
                label="Estado",
                prefix_icon="status",
                border_color=ImportacionesTheme.BORDER,
                filled=True,
                options=[
                    ft.dropdown.Option("registered", "Registrado"),
                    ft.dropdown.Option("in_process", "En Proceso"),
                    ft.dropdown.Option("cleared", "Despachado"),
                    ft.dropdown.Option("cancelled", "Cancelado"),
                ],
                value="registered"
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
        """Carga datos para los combos desde la base de datos - CORREGIDO"""
        
        if self.modo_edicion:
            query = """
                SELECT 
                    i.id,
                    i.numero_importacion,
                    i.descripcion,
                    i.estado,
                    i.total_fob_importacion,
                    COUNT(DISTINCT ip.po_id) as cantidad_pos
                FROM importaciones i
                LEFT JOIN importacion_pos ip ON i.id = ip.importacion_id
                LEFT JOIN dua_documents d ON i.id = d.importacion_id
                WHERE d.id IS NULL 
                OR d.id = %s
                GROUP BY i.id, i.numero_importacion, i.descripcion, i.estado, 
                        i.total_fob_importacion
                ORDER BY i.numero_importacion DESC
            """
            result = self.db.execute_query(query, (self.dua_id,))
        else:
            query = """
                SELECT 
                    i.id,
                    i.numero_importacion,
                    i.descripcion,
                    i.estado,
                    i.total_fob_importacion,
                    COUNT(DISTINCT ip.po_id) as cantidad_pos
                FROM importaciones i
                LEFT JOIN importacion_pos ip ON i.id = ip.importacion_id
                LEFT JOIN dua_documents d ON i.id = d.importacion_id
                WHERE d.id IS NULL
                GROUP BY i.id, i.numero_importacion, i.descripcion, i.estado, 
                        i.total_fob_importacion
                ORDER BY i.numero_importacion DESC
            """
            result = self.db.execute_query(query)
        
        if result:
            self.importaciones = result
            options = []
            for imp in result:
                fob_value = float(imp['total_fob_importacion'] or 0)
                descripcion = imp['descripcion'][:40] if imp['descripcion'] else 'Sin descripción'
                label = f"{imp['numero_importacion']} - {descripcion} - {imp['cantidad_pos']} POs - ${fob_value:,.2f}"
                options.append(ft.dropdown.Option(str(imp['id']), label))
            
            self.controls['importacion'].options = options
            print(f"[DEBUG] Se cargaron {len(options)} importaciones disponibles")
        else:
            print("[DEBUG] No se encontraron importaciones disponibles")
            self.controls['importacion'].options = []
                
    def calcular_valores_importacion(self, e):
        """Calcula los valores de aduana basados en la importación seleccionada"""
        if not self.controls['importacion'].value:
            return
        
        importacion_id = int(self.controls['importacion'].value)
        
        # Obtener valores totales de la importación (suma de todas las POs)
        query = """
            SELECT 
                i.total_fob_importacion as fob_total,
                i.total_cif_importacion as cif_total,
                COALESCE(SUM(
                    CASE WHEN ie.expense_type = 'international_freight' THEN ie.amount ELSE 0 END
                ), 0) as freight_total,
                COALESCE(SUM(
                    CASE WHEN ie.expense_type = 'insurance' THEN ie.amount ELSE 0 END
                ), 0) as insurance_total
            FROM importaciones i
            LEFT JOIN importacion_pos ip ON i.id = ip.importacion_id
            LEFT JOIN import_expenses ie ON ip.po_id = ie.po_id
            WHERE i.id = %s
        """
        result = self.db.execute_query(query, (importacion_id,))
        
        if result:
            data = result[0]
            
            # Usar total_fob_importacion si está definido, sino calcular de POs
            fob_total = data['fob_total'] or 0
            freight_total = data['freight_total'] or 0
            insurance_total = data['insurance_total'] or 0
            
            # Si no hay total FOB, calcular de las POs
            if not fob_total:
                query_fob = """
                    SELECT COALESCE(SUM(po.total_fob), 0) as fob_sum
                    FROM importacion_pos ip
                    LEFT JOIN purchase_orders po ON ip.po_id = po.id
                    WHERE ip.importacion_id = %s
                """
                result_fob = self.db.execute_query(query_fob, (importacion_id,))
                if result_fob:
                    fob_total = result_fob[0]['fob_sum']
            
            self.controls['fob_value_usd'].value = f"{float(fob_total):.2f}"
            self.controls['freight_usd'].value = f"{float(freight_total):.2f}"
            self.controls['insurance_usd'].value = f"{float(insurance_total):.2f}"
            
            # Calcular CIF
            self.calcular_impuestos(None)
    
    def calcular_impuestos(self, e):
        """Calcula los impuestos basados en los valores ingresados"""
        try:
            fob = float(self.controls['fob_value_usd'].value or 0)
            freight = float(self.controls['freight_usd'].value or 0)
            insurance = float(self.controls['insurance_usd'].value or 0)
            ad_valorem_rate = float(self.controls['ad_valorem_rate'].value or 0)
            igv_rate = float(self.controls['igv_rate'].value or 0)
            ipm_rate = float(self.controls['ipm_rate'].value or 0)
            
            # Calcular CIF
            cif = fob + freight + insurance
            self.controls['cif_value_usd'].value = f"{cif:.2f}"
            
            # Calcular Ad-Valorem
            ad_valorem_sugerido = cif * (ad_valorem_rate / 100)
            ad_valorem = float(self.controls['ad_valorem_amount'].value or 0)
            if ad_valorem == 0:
                # Mostrar sugerencia
                self.controls['ad_valorem_amount'].value = f"{ad_valorem_sugerido:.2f}"
                ad_valorem_usar = ad_valorem_sugerido
            else:
                # Usar el valor que ya ingresó el usuario
                ad_valorem_usar = ad_valorem
            
            # Calcular IGV (sobre CIF + Ad-Valorem)
            igv = (cif + ad_valorem_usar) * (igv_rate / 100)
            self.controls['igv_amount'].value = f"{igv:.2f}"
            
            # Calcular IPM (si aplica)
            ipm = cif * (ipm_rate / 100)
            self.controls['ipm_amount'].value = f"{ipm:.2f}"
            
            # Calcular totales
            self.calcular_totales(None)
            
        except ValueError:
            pass
    
    def calcular_totales(self, e):
        """Calcula los totales de impuestos y gastos"""
        try:
            ad_valorem = float(self.controls['ad_valorem_amount'].value or 0)
            igv = float(self.controls['igv_amount'].value or 0)
            ipm = float(self.controls['ipm_amount'].value or 0)
            selective_consumption = float(self.controls['selective_consumption'].value or 0)
            antidumping = float(self.controls['antidumping'].value or 0)
            customs_fees = float(self.controls['customs_fees'].value or 0)
            agency_fees = float(self.controls['agency_fees'].value or 0)
            storage_fees = float(self.controls['storage_fees'].value or 0)
            other_customs_expenses = float(self.controls['other_customs_expenses'].value or 0)
            
            # Total impuestos
            total_taxes = ad_valorem + igv + ipm + selective_consumption + antidumping
            self.controls['total_taxes'].value = f"{total_taxes:.2f}"
            
            # Total gastos aduaneros
            total_customs_expenses = customs_fees + agency_fees + storage_fees + other_customs_expenses
            self.controls['total_customs_expenses'].value = f"{total_customs_expenses:.2f}"
            
        except ValueError:
            pass
    
    def cargar_dua(self):
        """Carga los datos de un DUA existente - AHORA CON IMPORTACIÓN"""
        query = """
            SELECT dd.*, i.numero_importacion 
            FROM dua_documents dd
            LEFT JOIN importaciones i ON dd.importacion_id = i.id
            WHERE dd.id = %s
        """
        result = self.db.execute_query(query, (self.dua_id,))
        if result:
            dua = result[0]
            
            # Campos básicos
            self.controls['dua_number'].value = dua['dua_number']
            if dua['importacion_id']:
                self.controls['importacion'].value = str(dua['importacion_id'])
            
            self.controls['registration_date'].value = format_date(dua['registration_date'])
            
            if dua['clearance_date']:
                self.controls['clearance_date'].value = format_date(dua['clearance_date'])
            
            self.controls['customs_agency'].value = dua['customs_agency'] or ''
            self.controls['customs_agent_ruc'].value = dua['customs_agent_ruc'] or ''
            self.controls['numero_operacion'].value = dua['numero_operacion'] or ''
            
            # Valores en USD
            self.controls['fob_value_usd'].value = str(dua['fob_value_usd'] or 0)
            self.controls['freight_usd'].value = str(dua['freight_usd'] or 0)
            self.controls['insurance_usd'].value = str(dua['insurance_usd'] or 0)
            self.controls['cif_value_usd'].value = str(dua['cif_value_usd'] or 0)
            
            # Tasas e impuestos
            self.controls['ad_valorem_rate'].value = str(dua['ad_valorem_rate'] or 0)
            self.controls['ad_valorem_amount'].value = str(dua['ad_valorem_amount'] or 0)
            self.controls['igv_rate'].value = str(dua['igv_rate'] or 0)
            self.controls['igv_amount'].value = str(dua['igv_amount'] or 0)
            self.controls['ipm_rate'].value = str(dua['ipm_rate'] or 0)
            self.controls['ipm_amount'].value = str(dua['ipm_amount'] or 0)
            self.controls['selective_consumption'].value = str(dua['selective_consumption'] or 0)
            self.controls['antidumping'].value = str(dua['antidumping'] or 0)
            
            # Gastos aduaneros
            self.controls['customs_fees'].value = str(dua['customs_fees'] or 0)
            self.controls['agency_fees'].value = str(dua['agency_fees'] or 0)
            self.controls['storage_fees'].value = str(dua['storage_fees'] or 0)
            self.controls['other_customs_expenses'].value = str(dua['other_customs_expenses'] or 0)
            
            # Totales
            self.controls['total_taxes'].value = str(dua['total_taxes'] or 0)
            self.controls['total_customs_expenses'].value = str(dua['total_customs_expenses'] or 0)
            
            # Estado y notas
            self.controls['status'].value = dua['status']
            self.controls['notes'].value = dua['notes'] or ''
            
            # Recalcular para asegurar consistencia
            self.calcular_impuestos(None)
    
    def validar_formulario(self):
        """Valida los datos del formulario"""
        errores = []
        
        if not self.controls['dua_number'].value:
            errores.append("El número de DUA es requerido")
        
        if not self.controls['importacion'].value:
            errores.append("Debe seleccionar una importación (folder Manila)")
        
        if not self.controls['registration_date'].value:
            errores.append("La fecha de registro es requerida")
        
        return errores
    
    def guardar_dua(self, e):
        """Guarda el DUA en la base de datos - AHORA ASOCIADO A IMPORTACIÓN"""
        # Validar formulario
        errores = self.validar_formulario()
        if errores:
            self.mostrar_error("\n".join(errores))
            return
        
        date_register = self.controls['registration_date'].value
        date_clear = self.controls['clearance_date'].value
        try:
            # Intentar parsear diferentes formatos
            if '/' in date_register:
                fecha_obj = datetime.strptime(date_register, '%d/%m/%Y')
                fecha_mysql = fecha_obj.strftime('%Y-%m-%d')
            else:
                fecha_mysql = date_register
                
            if date_clear and '/' in date_clear:
                fecha_obj_clear = datetime.strptime(date_clear, '%d/%m/%Y')
                fecha_mysql_clear = fecha_obj_clear.strftime('%Y-%m-%d')
            else:
                fecha_mysql_clear = date_clear
            
        except:
            fecha_mysql = datetime.now().strftime('%Y-%m-%d')
            fecha_mysql_clear = datetime.now().strftime('%Y-%m-%d') if date_clear else None
        
        # Preparar datos del DUA
        dua_data = {
            'dua_number': self.controls['dua_number'].value,
            'importacion_id': int(self.controls['importacion'].value),
            'registration_date': fecha_mysql,
            'clearance_date': fecha_mysql_clear or None,
            'customs_agency': self.controls['customs_agency'].value or None,
            'customs_agent_ruc': self.controls['customs_agent_ruc'].value or None,
            'numero_operacion': self.controls['numero_operacion'].value or None,
            'fob_value_usd': float(self.controls['fob_value_usd'].value or 0),
            'freight_usd': float(self.controls['freight_usd'].value or 0),
            'insurance_usd': float(self.controls['insurance_usd'].value or 0),
            'cif_value_usd': float(self.controls['cif_value_usd'].value or 0),
            'ad_valorem_rate': float(self.controls['ad_valorem_rate'].value or 0),
            'ad_valorem_amount': float(self.controls['ad_valorem_amount'].value or 0),
            'igv_rate': float(self.controls['igv_rate'].value or 0),
            'igv_amount': float(self.controls['igv_amount'].value or 0),
            'ipm_rate': float(self.controls['ipm_rate'].value or 0),
            'ipm_amount': float(self.controls['ipm_amount'].value or 0),
            'selective_consumption': float(self.controls['selective_consumption'].value or 0),
            'antidumping': float(self.controls['antidumping'].value or 0),
            'customs_fees': float(self.controls['customs_fees'].value or 0),
            'agency_fees': float(self.controls['agency_fees'].value or 0),
            'storage_fees': float(self.controls['storage_fees'].value or 0),
            'other_customs_expenses': float(self.controls['other_customs_expenses'].value or 0),
            'total_taxes': float(self.controls['total_taxes'].value or 0),
            'total_customs_expenses': float(self.controls['total_customs_expenses'].value or 0),
            'status': self.controls['status'].value,
            'notes': self.controls['notes'].value or None,
        }
        
        try:
            if self.modo_edicion:
                # Actualizar DUA existente
                query = """
                    UPDATE dua_documents 
                    SET dua_number = %s, importacion_id = %s, registration_date = %s,
                        clearance_date = %s, customs_agency = %s, customs_agent_ruc = %s,
                        numero_operacion = %s, fob_value_usd = %s, freight_usd = %s,
                        insurance_usd = %s, cif_value_usd = %s, ad_valorem_rate = %s,
                        ad_valorem_amount = %s, igv_rate = %s, igv_amount = %s,
                        ipm_rate = %s, ipm_amount = %s, selective_consumption = %s,
                        antidumping = %s, customs_fees = %s, agency_fees = %s,
                        storage_fees = %s, other_customs_expenses = %s,
                        total_taxes = %s, total_customs_expenses = %s,
                        status = %s, notes = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """
                params = (
                    dua_data['dua_number'], dua_data['importacion_id'], dua_data['registration_date'],
                    dua_data['clearance_date'], dua_data['customs_agency'], dua_data['customs_agent_ruc'],
                    dua_data['numero_operacion'], dua_data['fob_value_usd'], dua_data['freight_usd'],
                    dua_data['insurance_usd'], dua_data['cif_value_usd'], dua_data['ad_valorem_rate'],
                    dua_data['ad_valorem_amount'], dua_data['igv_rate'], dua_data['igv_amount'],
                    dua_data['ipm_rate'], dua_data['ipm_amount'], dua_data['selective_consumption'],
                    dua_data['antidumping'], dua_data['customs_fees'], dua_data['agency_fees'],
                    dua_data['storage_fees'], dua_data['other_customs_expenses'],
                    dua_data['total_taxes'], dua_data['total_customs_expenses'],
                    dua_data['status'], dua_data['notes'], self.dua_id
                )
                
                self.db.execute_query(query, params, fetch=False)
                
            else:
                # Crear nuevo DUA
                query = """
                    INSERT INTO dua_documents 
                    (dua_number, importacion_id, registration_date, clearance_date,
                     customs_agency, customs_agent_ruc, numero_operacion,
                     fob_value_usd, freight_usd, insurance_usd, cif_value_usd,
                     ad_valorem_rate, ad_valorem_amount, igv_rate, igv_amount,
                     ipm_rate, ipm_amount, selective_consumption, antidumping,
                     customs_fees, agency_fees, storage_fees, other_customs_expenses,
                     total_taxes, total_customs_expenses, status, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = tuple(dua_data.values())
                
                self.dua_id = self.db.execute_query(query, params, fetch=False)
                
                # Actualizar la importación con el ID de la DUA
                update_importacion_query = """
                    UPDATE importaciones 
                    SET dua_id = %s, estado = 'en_aduana'
                    WHERE id = %s
                """
                self.db.execute_query(update_importacion_query, (self.dua_id, dua_data['importacion_id']), fetch=False)
                
                # Actualizar el estado de todas las POs de esta importación
                update_pos_query = """
                    UPDATE purchase_orders po
                    JOIN importacion_pos ip ON po.id = ip.po_id
                    SET po.status = 'en_aduana'
                    WHERE ip.importacion_id = %s 
                      AND po.status IN ('confirmada', 'en_transito')
                """
                self.db.execute_query(update_pos_query, (dua_data['importacion_id'],), fetch=False)
            
            self.mostrar_exito("DUA guardado exitosamente")
            
            # Redirigir a la vista de importación
            def redirigir():
                self.page.go(f"/dua")
            
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
        titulo = f"Editar DUA #{self.dua_id}" if self.modo_edicion else "Nuevo DUA"
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Row([
                                ft.Icon("description", size=24, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text(titulo, size=24, 
                                       weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                            ], spacing=12),
                            ft.Text("Documento Único de Aduana - Asignado a Importación", 
                                   size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                        ]),
                        ft.ElevatedButton(
                            "Volver a dua",
                            icon="arrow_back",
                            on_click=lambda e: self.page.go("/dua"),
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
                                        ft.Icon("folder", size=20, color=ImportacionesTheme.STATUS_CONFIRMED),
                                        ft.Text("Información del DUA e Importación", size=16, 
                                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                    ], spacing=8),
                                    ft.Divider(height=20),
                                    ft.ResponsiveRow([
                                        ft.Column([self.controls['dua_number']], col={"md": 6}),
                                        ft.Column([self.controls['importacion']], col={"md": 6}),
                                    ], spacing=16, run_spacing=16),
                                    ft.ResponsiveRow([
                                        ft.Column([self.controls['registration_date']], col={"md": 4}),
                                        ft.Column([self.controls['clearance_date']], col={"md": 4}),
                                        ft.Column([self.controls['status']], col={"md": 4}),
                                    ], spacing=16, run_spacing=16),
                                    ft.ResponsiveRow([
                                        ft.Column([self.controls['customs_agency']], col={"md": 6}),
                                        ft.Column([self.controls['customs_agent_ruc']], col={"md": 6}),
                                    ], spacing=16, run_spacing=16),
                                    ft.ResponsiveRow([
                                        ft.Column([self.controls['numero_operacion']], col={"md": 12}),
                                    ], spacing=16, run_spacing=16),
                                ]),
                                padding=20,
                                border=ft.border.all(1, ImportacionesTheme.BORDER),
                                border_radius=8,
                                margin=ft.margin.only(bottom=20),
                            ),
                            
                            # Sección 2: Valores en USD
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon("attach_money", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Text("Valores de la Importación (USD)", size=16, 
                                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                    ], spacing=8),
                                    ft.Divider(height=20),
                                    ft.Text("Los valores se calculan automáticamente de todas las POs de la importación", 
                                           size=12, color=ImportacionesTheme.TEXT_SECONDARY, italic=True),
                                    ft.Container(height=12),
                                    ft.ResponsiveRow([
                                        ft.Column([self.controls['fob_value_usd']], col={"md": 3}),
                                        ft.Column([self.controls['freight_usd']], col={"md": 3}),
                                        ft.Column([self.controls['insurance_usd']], col={"md": 3}),
                                        ft.Column([self.controls['cif_value_usd']], col={"md": 3}),
                                    ], spacing=16, run_spacing=16),
                                ]),
                                padding=20,
                                border=ft.border.all(1, ImportacionesTheme.BORDER),
                                border_radius=8,
                                margin=ft.margin.only(bottom=20),
                            ),
                            
                            # Sección 3: Cálculo de impuestos
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon("calculate", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Text("Cálculo de Impuestos (Aduanas)", size=16, 
                                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                    ], spacing=8),
                                    ft.Divider(height=20),
                                    ft.Text("Tasas e Impuestos", size=14, weight=ft.FontWeight.BOLD),
                                    ft.Container(height=12),
                                    ft.ResponsiveRow([
                                        ft.Column([self.controls['ad_valorem_rate']], col={"md": 3}),
                                        ft.Column([self.controls['ad_valorem_amount']], col={"md": 3}),
                                        ft.Column([self.controls['igv_rate']], col={"md": 3}),
                                        ft.Column([self.controls['igv_amount']], col={"md": 3}),
                                    ], spacing=16, run_spacing=16),
                                    ft.ResponsiveRow([
                                        ft.Column([self.controls['ipm_rate']], col={"md": 3}),
                                        ft.Column([self.controls['ipm_amount']], col={"md": 3}),
                                        ft.Column([self.controls['selective_consumption']], col={"md": 3}),
                                        ft.Column([self.controls['antidumping']], col={"md": 3}),
                                    ], spacing=16, run_spacing=16),
                                    ft.Divider(height=20),
                                    ft.ResponsiveRow([
                                        ft.Column([self.controls['total_taxes']], col={"md": 6}),
                                        ft.Column([self.controls['total_customs_expenses']], col={"md": 6}),
                                    ], spacing=16, run_spacing=16),
                                ]),
                                padding=20,
                                border=ft.border.all(1, ImportacionesTheme.BORDER),
                                border_radius=8,
                                margin=ft.margin.only(bottom=20),
                            ),
                            
                            # Sección 4: Gastos aduaneros
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon("payments", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                        ft.Text("Gastos Aduaneros Adicionales", size=16, 
                                               weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                    ], spacing=8),
                                    ft.Divider(height=20),
                                    ft.ResponsiveRow([
                                        ft.Column([self.controls['customs_fees']], col={"md": 3}),
                                        ft.Column([self.controls['agency_fees']], col={"md": 3}),
                                        ft.Column([self.controls['storage_fees']], col={"md": 3}),
                                        ft.Column([self.controls['other_customs_expenses']], col={"md": 3}),
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
                                        on_click=lambda e: self.page.go("/dua"),
                                        style=ft.ButtonStyle(
                                            bgcolor=ImportacionesTheme.BG_SECONDARY,
                                            color=ImportacionesTheme.TEXT_PRIMARY
                                        ),
                                    ),
                                    ft.Container(width=20),
                                    ft.ElevatedButton(
                                        "Recalcular Valores",
                                        icon="refresh",
                                        on_click=lambda e: self.calcular_valores_importacion(e),
                                        style=ft.ButtonStyle(
                                            bgcolor=ImportacionesTheme.INFO,
                                            color="white"
                                        ),
                                    ),
                                    ft.Container(width=20),
                                    ft.ElevatedButton(
                                        "Calcular Impuestos",
                                        icon="calculate",
                                        on_click=self.calcular_impuestos,
                                        style=ft.ButtonStyle(
                                            bgcolor=ImportacionesTheme.WARNING,
                                            color="white"
                                        ),
                                    ),
                                    ft.Container(width=20),
                                    ft.ElevatedButton(
                                        "Guardar DUA",
                                        icon="save",
                                        on_click=self.guardar_dua,
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

