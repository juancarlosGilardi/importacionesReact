import flet as ft
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime

class SunatKardexReport:
    def __init__(self, db):
        self.db = db
        self.styles = getSampleStyleSheet()
        # Estilos personalizados para coincidir con el modelo SUNAT
        self.styles.add(ParagraphStyle(name='TituloBold', fontSize=10, fontName='Helvetica-Bold', alignment=TA_CENTER))
        self.styles.add(ParagraphStyle(name='InfoSmall', fontSize=7, alignment=TA_LEFT))
        self.styles.add(ParagraphStyle(name='HeaderTabla', fontSize=6, fontName='Helvetica-Bold', alignment=TA_CENTER))

    def _fmt(self, val, decimals=2):
        if val is None or val == "": return ""
        # Eliminamos 'or float(val) == 0' para que el PDF te muestre si algo está en 0.00
        return f"{float(val):,.{decimals}f}"
    def generar_reporte_mensual(self, anio, mes, producto_id=None, filename="kardex_completo.pdf"):
        """
        Genera el reporte para uno o todos los productos, filtrado por año y mes.
        """
        # 1. Obtener lista de productos a procesar
        if producto_id and str(producto_id).strip() != "" and str(producto_id) != "None":
           print(f"DEBUG: Filtrando por producto único ID: {producto_id}")
           productos = self.db.execute_query("SELECT * FROM products WHERE id = %s", (producto_id,))
        else:
            # Seleccionamos solo productos que tuvieron movimientos en ese periodo o antes
            query_p = """
                SELECT DISTINCT p.* FROM products p
                INNER JOIN movement_details md ON p.id = md.product_id
                INNER JOIN warehouse_movements wm ON md.movement_id = wm.id
                WHERE YEAR(wm.movement_date) <= %s
            """
            productos = self.db.execute_query(query_p, (anio,))

        if not productos:
            return False, "No se encontraron productos con movimientos."

        elements = []
        doc = SimpleDocTemplate(filename, pagesize=landscape(A4), margin=1*cm)

        for prod in productos:
            # 2. Obtener movimientos previos (para Saldo Inicial Op 16)
            sql_prev = """
                SELECT md.quantity, md.unit_cost, wm.movement_type
                FROM warehouse_movements wm
                JOIN movement_details md ON wm.id = md.movement_id
                WHERE md.product_id = %s AND wm.movement_date < %s
            """
            fecha_inicio_mes = f"{anio}-{mes:02d}-01"
            movs_previos = self.db.execute_query(sql_prev, (prod['id'], fecha_inicio_mes))
            
            saldo_inicial_qty, saldo_inicial_val = self._calcular_acumulado(movs_previos)

            # 3. Obtener movimientos del mes actual
            sql_mes = """
                SELECT 
                    wm.movement_date AS fecha,
                    IF(LOCATE('-', wm.reference_document) > 0, SUBSTRING_INDEX(wm.reference_document, '-', 1), '001') AS doc_serie,
                    IF(LOCATE('-', wm.reference_document) > 0, SUBSTRING_INDEX(wm.reference_document, '-', -1), wm.reference_document) AS doc_numero,
                    wm.movement_type,
                    md.quantity AS cantidad,
                    md.unit_cost AS costo_unitario,
                    md.total_cost AS costo_total,  -- ¡AQUÍ FALTABA LA COMA!
                    '01' as doc_tipo -- Guía/Factura (ajustar según tu lógica)
                FROM warehouse_movements wm
                JOIN movement_details md ON wm.id = md.movement_id
                WHERE md.product_id = %s AND YEAR(wm.movement_date) = %s AND MONTH(wm.movement_date) = %s
                ORDER BY wm.movement_date ASC, wm.created_at ASC
            """
            movs_mes = self.db.execute_query(sql_mes, (prod['id'], anio, mes))

            # Solo generar página si hay saldo inicial o movimientos en el mes
            if movs_mes or saldo_inicial_qty > 0:
                self._agregar_pagina_producto(elements, prod, anio, mes, saldo_inicial_qty, saldo_inicial_val, movs_mes)
                elements.append(PageBreak())

        if not elements:
            return False, "No hay datos para mostrar en este periodo."

        doc.build(elements)
        return True, filename

    def _calcular_acumulado(self, movimientos):
        qty = 0.0
        val = 0.0
        if movimientos:
            for m in movimientos:
                if m['movement_type'] == 'receipt':
                    qty += float(m['quantity'])
                    val += float(m['quantity']) * float(m['unit_cost'])
                else:
                    # Costo promedio para salidas previas
                    cp = val / qty if qty > 0 else 0
                    qty -= float(m['quantity'])
                    val -= float(m['quantity']) * cp
        return qty, val

    def _agregar_pagina_producto(self, elements, prod, anio, mes, s_qty, s_val, movimientos):
        # Encabezado (Igual al modelo 13.1)
        periodo = f"{mes:02d}-{anio}"
        elements.append(Paragraph("FORMATO 13.1: REGISTRO DE INVENTARIO PERMANENTE VALORIZADO", self.styles['TituloBold']))
        elements.append(Spacer(1, 0.3*cm))
        
        info = [
            [f"PERÍODO: {periodo}", f"RUC: {"12345"}", f"MÉTODO VALUACIÓN: COSTO PROMEDIO"],
            [f"RAZÓN SOCIAL: {"TEC"}", "", ""],
            [f"CÓDIGO: {prod['sku']}", f"DESCRIPCIÓN: {prod['name']}", f"UNIDAD: {prod['unit_measure']}"]
        ]
        t_info = Table(info, colWidths=[8*cm, 10*cm, 8*cm])
        t_info.setStyle(TableStyle([('FONTSIZE', (0,0), (-1,-1), 8), ('LEFTPADDING', (0,0), (-1,-1), 0)]))
        elements.append(t_info)
        elements.append(Spacer(1, 0.3*cm))

        # Estructura de Tabla SUNAT
        headers = [
            ['DOCUMENTO DE TRASLADO...', '', '', '', 'TIPO DE', 'ENTRADAS', '', '', 'SALIDAS', '', '', 'SALDO FINAL', '', ''],
            ['FECHA', 'TIPO', 'SERIE', 'NÚMERO', 'OPER.', 'CANT.', 'COSTO U.', 'COSTO T.', 'CANT.', 'COSTO U.', 'COSTO T.', 'CANT.', 'COSTO U.', 'COSTO T.']
        ]
        
        data_rows = []
        # Fila de Saldo Inicial (Op 16)
        c_p = s_val / s_qty if s_qty > 0 else 0
        data_rows.append([f"01/{mes:02d}/{anio}", "", "", "", "16", "", "", "", "", "", "", self._fmt(s_qty), self._fmt(c_p, 4), self._fmt(s_val)])

        curr_qty, curr_val = s_qty, s_val
        for m in movimientos:
            q = float(m['cantidad'])
            u = float(m['costo_unitario'])
            
            if m['movement_type'] == 'receipt':
                curr_qty += q
                curr_val += (q * u)
                c_p = curr_val / curr_qty if curr_qty > 0 else 0
                row = [m['fecha'].strftime("%d/%m/%Y"), m['doc_tipo'], m['doc_serie'], m['doc_numero'], "02", self._fmt(q), self._fmt(u, 4), self._fmt(q*u), "", "", "", self._fmt(curr_qty), self._fmt(c_p, 4), self._fmt(curr_val)]
            else:
                c_p = curr_val / curr_qty if curr_qty > 0 else 0
                costo_s = q * c_p
                curr_qty -= q
                curr_val -= costo_s
                row = [m['fecha'].strftime("%d/%m/%Y"), m['doc_tipo'], m['doc_serie'], m['doc_numero'], "01", "", "", "", self._fmt(q), self._fmt(c_p, 4), self._fmt(costo_s), self._fmt(curr_qty), self._fmt(c_p, 4), self._fmt(curr_val)]
            data_rows.append(row)

        # Crear Tabla Final
        col_w = [1.8*cm, 0.8*cm, 1.2*cm, 2.2*cm, 1*cm] + [1.8*cm]*9
        t = Table(headers + data_rows, colWidths=col_w, repeatRows=2)
        t.setStyle(TableStyle([
            ('SPAN', (0,0), (3,0)), ('SPAN', (5,0), (7,0)), ('SPAN', (8,0), (10,0)), ('SPAN', (11,0), (13,0)),
            ('FONTSIZE', (0,0), (-1,-1), 6), ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('BACKGROUND', (0,0), (-1,1), colors.lightgrey)
        ]))
        elements.append(t)