# views/prorrateo_view.py
import flet as ft
from config_importaciones import (
    ImportacionesTheme, ImportacionesConfig,
    format_currency, format_date, get_status_color
)
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import tempfile
import os
import threading
import time
from datetime import datetime
import pandas as pd
from io import BytesIO

class CalculoAduanero:
    """Clase para cálculos aduaneros"""
    
    def __init__(self, tipo_cambio=1):
        self.tipo_cambio = tipo_cambio
    
    def calcular_todos_impuestos(self, fob_total_pen, flete_usd, seguro_usd, 
                               tasa_ad_valorem=0.06, tasa_isc=0.10, 
                               tasa_igv=0.18, tasa_percepcion=0.035):
        """Calcula todos los impuestos en secuencia"""
        
        # 1. Convertir a PEN
        flete_pen = flete_usd * self.tipo_cambio
        seguro_pen = seguro_usd * self.tipo_cambio
        
        # 2. CIF
        cif_pen = fob_total_pen + flete_pen + seguro_pen
        
        # 3. Derechos Aduaneros
        derechos_pen = cif_pen * tasa_ad_valorem
        
        # 4. Subtotal sin IGV
        subtotal_sin_igv = cif_pen + derechos_pen
        
        # 5. ISC
        isc_pen = subtotal_sin_igv * tasa_isc
        
        # 6. Subtotal con ISC
        subtotal_con_isc = subtotal_sin_igv + isc_pen
        
        # 7. IGV (NO se incluye en costos)
        igv_pen = subtotal_con_isc * tasa_igv
        
        # 8. Total con IGV
        total_con_igv = subtotal_con_isc + igv_pen
        
        # 9. Percepción
        percepcion_pen = total_con_igv * tasa_percepcion
        
        return {
            'fob_total': fob_total_pen,
            'flete': flete_pen,
            'seguro': seguro_pen,
            'cif': cif_pen,
            'derechos': derechos_pen,
            'isc': isc_pen,
            'igv': igv_pen,
            'percepcion': percepcion_pen,
            'subtotal_sin_igv': subtotal_sin_igv,
            'tasas': {
                'isc': tasa_isc,
                'igv': tasa_igv,
                'percepcion': tasa_percepcion
            }
        }

class ProrrateoView:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.po_id = self.obtener_po_id_url()
        self.orden = None
        self.items = []
        self.gastos = []
        self.costos_prorrateados = []
        self.prorrateo_calculado = {}  # Guardar el prorrateo calculado
        self.metodo_seleccionado = "value"  # Método por defecto
        self.historial_container = None


        if self.po_id:
            self.cargar_datos()
    

            
    def obtener_po_id_url(self):
        """Obtiene el po_id de los parámetros de la URL"""
        if self.page and hasattr(self.page, 'route'):
            try:
                import urllib.parse
                route_parts = self.page.route.split('?')
                if len(route_parts) > 1:
                    query_params = urllib.parse.parse_qs(route_parts[1])
                    if 'po_id' in query_params:
                        print(f"✅ PO_ID encontrado: {query_params['po_id'][0]}")
                        return int(query_params['po_id'][0])
            except Exception as e:
                print(f"Error obteniendo po_id: {e}")
        print(f"❌ No se encontró po_id en la ruta: {self.page.route}")
        return None
    
    def cargar_datos(self):
        # Cargar orden
        query = """
            SELECT po.*, s.business_name as supplier_name,
                c.code as currency_code, c.name as currency_name
            FROM purchase_orders po
            LEFT JOIN suppliers s ON po.supplier_id = s.id
            LEFT JOIN currencies c ON po.currency_id = c.id
            WHERE po.id = %s
        """
        result = self.db.execute_query(query, (self.po_id,))
        if result:
            self.orden = result[0]
            print(f"✅ Orden cargada: {self.orden['po_number']}")
        
        # Cargar items
        query = """
            SELECT poi.*, p.sku, p.name as product_name
            FROM purchase_order_items poi
            LEFT JOIN products p ON poi.product_id = p.id
            WHERE poi.po_id = %s
        """
        result = self.db.execute_query(query, (self.po_id,))
        if result:
            self.items = result
            print(f"✅ Items cargados: {len(self.items)}")
            # Calcular fob_value SIEMPRE, asegurando que sea correcto
            for item in self.items:
                quantity = self.convertir_a_float(item.get('quantity', 0))
                unit_price = self.convertir_a_float(item.get('unit_price', 0))
                item['fob_value'] = quantity * unit_price
        
        # Cargar gastos de import_expenses EXCLUYENDO IGV
        self.gastos = []
    
        # 4. Cargar gastos de import_expenses EXCLUYENDO IGV
        query = """
            SELECT ie.*, etu.nombre_ui as expense_type_name
            FROM import_expenses ie
            LEFT JOIN expense_types_ui etu ON ie.expense_type = etu.tipo_gasto
            WHERE ie.po_id = %s AND ie.status = 'paid'
            AND ie.expense_type != 'igv'  -- EXCLUIR IGV
        """
        result = self.db.execute_query(query, (self.po_id,))
        if result:
            # AGREGAR (no sobrescribir) los gastos importados
            self.gastos.extend(result)
            print(f"✅ Gastos cargados desde import_expenses (sin IGV): {len(result)}")
        
        # 5. Cargar facturas de proveedores nacionales
        query_invoices = """
            SELECT 
                si.*,
                'supplier_invoice' as source,
                CONCAT('Factura Prov. Nacional: ', si.invoice_number) as expense_type_name,
                'supplier_national' as expense_type,
                sp.business_name as supplier_name
            FROM supplier_invoices si
            LEFT JOIN suppliers sp ON si.supplier_id = sp.id
            WHERE si.po_id = %s 
            AND si.status = 'pending'
            ORDER BY si.invoice_date ASC
        """
        
        result_invoices = self.db.execute_query(query_invoices, (self.po_id,))
        if result_invoices:
            print(f"✅ Facturas de proveedores nacionales cargadas: {len(result_invoices)}")
            tipo_cambio_orden = float(self.orden.get('exchange_rate', 1)) if self.orden else 1
            
            for invoice in result_invoices:
                total_amount = self.convertir_a_float(invoice.get('total_amount', 0))
                currency_id = invoice.get('currency_id')
                
                # Convertir a moneda base (PEN)
                if currency_id == 1:  # USD
                    total_pen = total_amount * tipo_cambio_orden
                    total_usd = total_amount
                else:  # PEN
                    total_pen = total_amount
                    total_usd = total_amount / tipo_cambio_orden if tipo_cambio_orden > 0 else 0
                
                total_con_igv = total_pen
                total_sin_igv = total_con_igv / 1.18
                igv_factura = total_con_igv - total_sin_igv
                # Crear objeto de gasto para la factura
                invoice_gasto = {
                    'expense_type': f"factura_{invoice['invoice_number']}",  # ÚNICO por factura
                    'expense_type_name': f"Factura {invoice['invoice_number']}",
                    'amount_usd': total_usd,
                    'amount_pen': total_sin_igv,  # *** SIN IGV ***
                    'amount_pen_con_igv': total_con_igv,  # Guardar con IGV para referencia
                    'igv_amount': igv_factura,  # Guardar IGV quitado
                    'description': f"Factura proveedor nacional: {invoice['invoice_number']}",
                    'source': 'supplier_invoice',
                    'invoice_id': invoice['id'],
                    'invoice_number': invoice['invoice_number'],
                    'invoice_date': invoice['invoice_date'],
                    'supplier_name': invoice.get('supplier_name', '')
                }
                
                self.gastos.append(invoice_gasto)
                print(f"  - Factura {invoice['invoice_number']}: S/ {total_con_igv:,.2f} (SIN IGV: {total_sin_igv:,.2f})")
        # 6. CARGAR GASTOS DEL DUA (excluyendo IGV)
        query = """
            SELECT * FROM dua_documents 
            WHERE po_id = %s AND status = 'registered'
            ORDER BY id DESC
            LIMIT 1
        """
        result = self.db.execute_query(query, (self.po_id,))
        if result:
            dua = result[0]
            print(f"✅ DUA encontrado: {dua['dua_number']}")
            
            tipo_cambio = float(self.orden.get('exchange_rate',1)) if self.orden else 1
            gastos_dua = []
            
            # Flete internacional
            if dua.get('freight_usd') and float(dua['freight_usd'] or 0) > 0:
                freight_usd = float(dua['freight_usd'] or 0)
                gastos_dua.append({
                    'expense_type': 'freight',
                    'expense_type_name': 'Flete Internacional',
                    'amount_usd': freight_usd,
                    'amount_pen': freight_usd ,
                    'description': f"Flete DUA {dua['dua_number']}",
                    'source': 'dua'
                })
            
            # Seguro internacional
            if dua.get('insurance_usd') and float(dua['insurance_usd'] or 0) > 0:
                gastos_dua.append({
                    'expense_type': 'insurance',
                    'expense_type_name': 'Seguro Internacional',
                    'amount_usd': float(dua['insurance_usd'] or 0),
                    'amount_pen': float(dua['insurance_usd'] or 0),
                    'description': f"Seguro DUA {dua['dua_number']}",
                    'source': 'dua'
                })
            
            # Impuestos NO RECUPERABLES (Ad Valorem, IPM) - IGV se excluye
            # if dua.get('ad_valorem_amount') and float(dua['ad_valorem_amount'] or 0) > 0:
            #     gastos_dua.append({
            #         'expense_type': 'ad_valorem',
            #         'expense_type_name': 'Impuesto Ad-Valorem',
            #         'amount_usd': float(dua['ad_valorem_amount'] or 0),
            #         'amount_pen': float(dua['ad_valorem_amount'] or 0),
            #         'description': f"Ad-Valorem DUA {dua['dua_number']}",
            #         'source': 'dua'
            #     })
            
            if dua.get('ipm_amount') and float(dua['ipm_amount'] or 0) > 0:
                gastos_dua.append({
                    'expense_type': 'ipm',
                    'expense_type_name': 'IPM',
                    'amount_usd': float(dua['ipm_amount'] or 0),
                    'amount_pen': float(dua['ipm_amount'] or 0) ,
                    'description': f"IPM DUA {dua['dua_number']}",
                    'source': 'dua'
                })
            
            # Gastos aduaneros varios
            if dua.get('customs_fees') and float(dua['customs_fees'] or 0) > 0:
                gastos_dua.append({
                    'expense_type': 'customs_fees',
                    'expense_type_name': 'Gastos de Aduana',
                    'amount_usd': float(dua['customs_fees'] or 0),
                    'amount_pen': float(dua['customs_fees'] or 0),
                    'description': f"Gastos Aduana DUA {dua['dua_number']}",
                    'source': 'dua'
                })
            
            if dua.get('agency_fees') and float(dua['agency_fees'] or 0) > 0:
                gastos_dua.append({
                    'expense_type': 'agency_fees',
                    'expense_type_name': 'Honorarios de Agencia',
                    'amount_usd': float(dua['agency_fees'] or 0),
                    'amount_pen': float(dua['agency_fees'] or 0) ,
                    'description': f"Honorarios DUA {dua['dua_number']}",
                    'source': 'dua'
                })
            
            # Agregar gastos del DUA a la lista general
            self.gastos.extend(gastos_dua)
            print(f"✅ Gastos del DUA agregados (sin IGV): {len(gastos_dua)}")
            
        # Cargar prorrateos previos
        query = """
            SELECT * FROM cost_prorating 
            WHERE po_id = %s AND status = 'applied'
            ORDER BY prorating_date DESC
            LIMIT 1
        """
        result = self.db.execute_query(query, (self.po_id,))
        if result:
            self.costos_prorrateados = result
            print(f"✅ Prorrateos previos cargados: {len(self.costos_prorrateados)}")

        total_gastos = sum(self.convertir_a_float(gasto.get('amount_pen', 0)) for gasto in self.gastos)
        print(f"💰 TOTAL GASTOS CARGADOS: S/ {total_gastos:,.2f} ({len(self.gastos)} registros)")
    
    # Agrega este método auxiliar en la clase ProrrateoView
    def convertir_a_float(self, valor):
        """Convierte cualquier valor a float de manera segura"""
        if valor is None:
            return 0.0
        if isinstance(valor, (int, float)):
            return float(valor)
        if isinstance(valor, str):
            try:
                return float(valor)
            except ValueError:
                return 0.0
        # Para decimal.Decimal
        try:
            return float(valor)
        except:
            return 0.0
    def consolidar_facturas_proveedor(self, invoices):
        """Consolida facturas por proveedor para mejor presentación"""
        proveedores = {}
        
        for invoice in invoices:
            supplier_id = invoice.get('supplier_id')
            supplier_name = invoice.get('supplier_name', f"Proveedor {supplier_id}")
            
            if supplier_id not in proveedores:
                proveedores[supplier_id] = {
                    'supplier_name': supplier_name,
                    'total_pen': 0,
                    'total_usd': 0,
                    'invoices': []
                }
            
            # Convertir montos
            total_amount = self.convertir_a_float(invoice.get('total_amount', 0))
            tipo_cambio = float(self.orden.get('exchange_rate', 1)) if self.orden else 1
            
            if invoice.get('currency_id') == 1:  # USD
                total_pen = total_amount * tipo_cambio
                total_usd = total_amount
            else:  # PEN
                total_pen = total_amount
                total_usd = total_amount / tipo_cambio if tipo_cambio > 0 else 0
            
            proveedores[supplier_id]['total_pen'] += total_pen
            proveedores[supplier_id]['total_usd'] += total_usd
            proveedores[supplier_id]['invoices'].append({
                'number': invoice['invoice_number'],
                'amount': total_pen,
                'date': invoice.get('invoice_date')
            })
        
        # Convertir a lista de gastos consolidados
        gastos_consolidados = []
        for supplier_id, datos in proveedores.items():
            if datos['total_pen'] > 0:
                gastos_consolidados.append({
                    'expense_type': 'supplier_national',
                    'expense_type_name': f"Proveedor Nacional: {datos['supplier_name']}",
                    'amount_usd': datos['total_usd'],
                    'amount_pen': datos['total_pen'],
                    'description': f"Facturas proveedor nacional: {', '.join([inv['number'] for inv in datos['invoices']])}",
                    'source': 'supplier_invoice_consolidated',
                    'supplier_id': supplier_id,
                    'supplier_name': datos['supplier_name'],
                    'invoice_count': len(datos['invoices'])
                })
        
        return gastos_consolidados
    def calcular_prorrateo(self, metodo=None):
        """Calcula el prorrateo según el método seleccionado"""
        metodo = metodo or self.metodo_seleccionado

        print(f"\n=== DEBUG: INICIANDO CÁLCULO DE PRORRATEO (Método: {metodo}) ===")
        
        if not self.items or not self.gastos:
            print("❌ ERROR: No hay items o gastos para calcular")
            return {}
        
        # DEBUG: Mostrar todos los gastos cargados
        print(f"\n📊 GASTOS CARGADOS ({len(self.gastos)} registros):")
        for i, gasto in enumerate(self.gastos):
            print(f"  {i+1}. {gasto['expense_type']}: {gasto.get('amount_usd', 0):,.2f} USD | {gasto.get('amount_pen', 0):,.2f} PEN")
        
        # 1. Separar tipos de gastos
        gastos_impuestos = []      # Flete, seguro, derechos, etc.
        gastos_facturas = []       # Facturas proveedor
        gastos_varios = []
        gastos_excluidos = []         # Otros gastos
        
        for gasto in self.gastos:
            tipo = gasto['expense_type']
            
            if 'supplier_national' in tipo or 'factura_' in tipo:
                gastos_facturas.append(gasto)
            elif tipo in ['freight', 'insurance', 'ipm']:
                gastos_impuestos.append(gasto)
            elif tipo == 'ad_valorem':
            # EXCLUIR Ad-Valorem del prorrateo
                gastos_excluidos.append(gasto)
            else:
                gastos_varios.append(gasto)
        
        print(f"\n📦 GASTOS SEPARADOS:")
        print(f"  - Impuestos/Importación: {len(gastos_impuestos)}")
        print(f"  - Facturas proveedor: {len(gastos_facturas)}")
        print(f"  - Varios: {len(gastos_varios)}")
        
        # 2. Calcular FOB total
        total_fob = 0
        print(f"\n📊 ITEMS FOB:")
        for item in self.items:
            quantity = self.convertir_a_float(item.get('quantity', 0))
            unit_price = self.convertir_a_float(item.get('unit_price', 0))
            fob_item = quantity * unit_price
            item['fob_value'] = fob_item
            total_fob += fob_item
            print(f"  - {item.get('sku', 'N/A')}: {quantity} x {unit_price:,.2f} = {fob_item:,.2f}")
        
        print(f"✅ TOTAL FOB: {total_fob:,.2f}")

          
        # 3. Obtener flete y seguro para cálculos aduaneros
        flete_usd = 0
        seguro_usd = 0
        for gasto in gastos_impuestos:
            if gasto['expense_type'] == 'freight':
                flete_usd = self.convertir_a_float(gasto.get('amount_usd', 0))
            elif gasto['expense_type'] == 'insurance':
                seguro_usd = self.convertir_a_float(gasto.get('amount_usd', 0))
        
        print(f"\n🚢 DATOS PARA CÁLCULOS ADUANEROS:")
        print(f"  - Flete USD: {flete_usd:,.2f}")
        print(f"  - Seguro USD: {seguro_usd:,.2f}")
        
        # 4. Calcular impuestos aduaneros (SOLO PARA REFERENCIA - NO USAR)
        tipo_cambio = float(self.orden.get('exchange_rate', 3.75)) if self.orden else 3.75
        print(f"  - Tipo cambio: {tipo_cambio}")
        
        # DEBUG: Mostrar qué impuestos YA tenemos del DUA
        print(f"\n💰 IMPUESTOS DEL DUA (YA CARGADOS):")
        for gasto in gastos_impuestos:
            print(f"  - {gasto['expense_type']}: {gasto.get('amount_pen', 0):,.2f} PEN")
        
        # 5. CALCULAR GASTOS SIN IGV (CORREGIDO - SIN DUPLICAR)
        total_gastos_sin_igv = 0
        
        print(f"\n🧮 CÁLCULO DE TOTAL GASTOS (sin IGV):")
        
        # Gastos de impuestos (Flete, Seguro, Ad-Valorem, IPM) - DEL DUA
        subtotal_impuestos = 0
        for gasto in gastos_impuestos:
            monto = self.convertir_a_float(gasto.get('amount_pen', 0))
            subtotal_impuestos += monto
            print(f"  - {gasto['expense_type']}: {monto:,.2f} PEN")
        print(f"  → Subtotal impuestos DUA: {subtotal_impuestos:,.2f} PEN")
        
        # Facturas (ya sin IGV) - NO TOCAR, FUNCIONAN BIEN
        subtotal_facturas = 0
        for factura in gastos_facturas:
            monto = self.convertir_a_float(factura.get('amount_pen', 0))
            subtotal_facturas += monto
            print(f"  - {factura['expense_type']}: {monto:,.2f} PEN")
        print(f"  → Subtotal facturas: {subtotal_facturas:,.2f} PEN")
        
        # Gastos varios
        subtotal_varios = 0
        for gasto in gastos_varios:
            monto = self.convertir_a_float(gasto.get('amount_pen', 0))
            subtotal_varios += monto
            print(f"  - {gasto['expense_type']}: {monto:,.2f} PEN")
        print(f"  → Subtotal varios: {subtotal_varios:,.2f} PEN")
        
        total_gastos_sin_igv = subtotal_impuestos + subtotal_facturas + subtotal_varios
        print(f"✅ TOTAL GASTOS SIN IGV: {total_gastos_sin_igv:,.2f} PEN")
        
        base_prorrateo = total_fob + total_gastos_sin_igv
        print(f"✅ BASE PARA PRORRATEO (FOB + Gastos): {base_prorrateo:,.2f} PEN")
        
        # 6. Calcular proporciones según método
        if metodo == 'value':
            print(f"\n📈 PRORRATEO POR VALOR:")
            
            resultado = {}
            for item in self.items:
                item_id = item['id']
                fob_item = self.convertir_a_float(item.get('fob_value', 0))
                proporcion = fob_item / total_fob if total_fob > 0 else 0
                
                print(f"\n  🏷️  Producto: {item.get('sku', 'N/A')} ({item.get('product_name', 'N/A')})")
                print(f"    - FOB: {fob_item:,.2f}")
                print(f"    - Proporción: {proporcion:.4f} ({proporcion*100:.2f}%)")
                
                resultado[item_id] = {
                    'item': item,
                    'proporcion': proporcion,
                    'costos': {}
                }
                
                # Distribuir FOB
                resultado[item_id]['costos']['fob'] = fob_item
                
                # Distribuir gastos de impuestos (DEL DUA - NO RECALCULAR)
                for gasto in gastos_impuestos:
                    monto = self.convertir_a_float(gasto.get('amount_pen', 0))
                    monto_prorrateado = monto * proporcion
                    resultado[item_id]['costos'][gasto['expense_type']] = monto_prorrateado
                    print(f"    - {gasto['expense_type']}: {monto:,.2f} x {proporcion:.4f} = {monto_prorrateado:,.2f}")
                
                # Distribuir facturas (NO TOCAR)
                for factura in gastos_facturas:
                    monto = self.convertir_a_float(factura.get('amount_pen', 0))
                    monto_prorrateado = monto * proporcion
                    clave = f"factura_{factura['invoice_number']}"
                    resultado[item_id]['costos'][clave] = monto_prorrateado
                    print(f"    - Factura {factura['invoice_number']}: {monto:,.2f} x {proporcion:.4f} = {monto_prorrateado:,.2f}")
                
                # Distribuir gastos varios
                for gasto in gastos_varios:
                    monto = self.convertir_a_float(gasto.get('amount_pen', 0))
                    monto_prorrateado = monto * proporcion
                    resultado[item_id]['costos'][gasto['expense_type']] = monto_prorrateado
                    print(f"    - {gasto['expense_type']}: {monto:,.2f} x {proporcion:.4f} = {monto_prorrateado:,.2f}")
                
                # Calcular totales
                total_item = sum(resultado[item_id]['costos'].values())
                resultado[item_id]['total_sin_igv'] = total_item
                
                # Calcular costo unitario
                cantidad = self.convertir_a_float(item.get('quantity', 1))
                resultado[item_id]['costo_unitario'] = total_item / cantidad if cantidad > 0 else 0
                
                print(f"    → TOTAL ITEM: {total_item:,.2f} PEN")
                print(f"    → COSTO UNITARIO: {resultado[item_id]['costo_unitario']:,.2f} PEN")
            
            # Verificar totales
            print(f"\n✅ VERIFICACIÓN DE TOTALES:")
            total_calculado = 0
            for item_id, datos in resultado.items():
                total_calculado += datos['total_sin_igv']
            
            print(f"  - Total FOB: {total_fob:,.2f}")
            print(f"  - Total Gastos: {total_gastos_sin_igv:,.2f}")
            print(f"  - Total Calculado: {total_calculado:,.2f}")
            print(f"  - Base Prorrateo: {base_prorrateo:,.2f}")
            print(f"  - Diferencia: {abs(total_calculado - base_prorrateo):,.2f}")
            
            return resultado
            
        elif metodo == 'weight':
            # Prorrateo por peso
            total_peso = sum(float(item.get('weight_kg', 0) or 0) for item in self.items)
            if total_peso == 0:
                print("❌ Total peso es 0, no se puede calcular prorrateo por peso")
                return {}
            
            resultado = {}
            for gasto in self.gastos:
                monto_pen = float(gasto.get('amount_pen', 0) or 0)
                for item in self.items:
                    item_id = item['id']
                    peso = float(item.get('weight_kg', 0) or 0)
                    
                    if item_id not in resultado:
                        resultado[item_id] = {
                            'item': item,
                            'peso_proporcion': peso / total_peso if total_peso > 0 else 0,
                            'costos': {}
                        }
                    
                    costo_prorrateado = monto_pen * (peso / total_peso)
                    resultado[item_id]['costos'][gasto['expense_type']] = costo_prorrateado
            
            return resultado
        
        elif metodo == 'volume':
            # Prorrateo por volumen
            total_volumen = sum(float(item.get('volume_m3', 0) or 0) for item in self.items)
            if total_volumen == 0:
                print("❌ Total volumen es 0, no se puede calcular prorrateo por volumen")
                return {}
            
            resultado = {}
            for gasto in self.gastos:
                monto_pen = float(gasto.get('amount_pen', 0) or 0)
                for item in self.items:
                    item_id = item['id']
                    volumen = float(item.get('volume_m3', 0) or 0)
                    
                    if item_id not in resultado:
                        resultado[item_id] = {
                            'item': item,
                            'volumen_proporcion': volumen / total_volumen if total_volumen > 0 else 0,
                            'costos': {}
                        }
                    
                    costo_prorrateado = monto_pen * (volumen / total_volumen)
                    resultado[item_id]['costos'][gasto['expense_type']] = costo_prorrateado
            
            return resultado
        
        print(f"❌ Método no soportado: {metodo}")
        return {}
    
    def calcular_datos_prorrateo(self, prorrateo_calculado):
        """
        Calcula los datos estructurados del prorrateo para usar en UI o Excel.
        Retorna un diccionario con:
        - items: lista de items con sus costos
        - totales: totales generales
        - columnas: información de las columnas
        - gastos: información de los gastos
        """
        # Inicializar estructuras
        datos = {
            'items': [],
            'totales': {},
            'columnas': [],
            'gastos': {}
        }
        
        # Calcular totales globales
        total_fob = sum(self.convertir_a_float(item.get('fob_value', 0)) for item in self.items)
        total_gastos = sum(self.convertir_a_float(gasto.get('amount_pen', 0)) for gasto in self.gastos)
        total_general = total_fob + total_gastos
        total_cantidad = sum(self.convertir_a_float(item.get('quantity', 0)) for item in self.items)
        
        factor = total_general / total_fob if total_fob > 0 else 0
        
        # Mapear gastos para tener nombres consistentes
        tipos_gasto = {}
        for gasto in self.gastos:
            tipo_key = gasto['expense_type']
            if tipo_key not in tipos_gasto:
                tipos_gasto[tipo_key] = {
                    'nombre_largo': gasto.get('expense_type_name', tipo_key),
                    'nombre_corto': self.acortar_nombre_gasto(gasto.get('expense_type_name', tipo_key))
                }
        
        # Procesar cada item
        items_calculados = []
        for item_id, datos_item in prorrateo_calculado.items():
            item = datos_item['item']
            costos_item = datos_item['costos']
            
            cantidad = self.convertir_a_float(item.get('quantity', 1))
            precio_unitario_original = self.convertir_a_float(item.get('unit_price', 0))
            fob_value = self.convertir_a_float(item.get('fob_value', 0))
            
            # Calcular FOB total si es necesario
            if fob_value == 0 and precio_unitario_original > 0 and cantidad > 0:
                fob_value = precio_unitario_original * cantidad
            
            # Inicializar costo total con FOB
            costo_total = fob_value
            
            # Acumular costos por tipo de gasto
            costos_por_tipo = {}
            for tipo in tipos_gasto.keys():
                costo_tipo = costos_item.get(tipo, 0)
                costos_por_tipo[tipo] = costo_tipo
                costo_total += costo_tipo
            
            # Calcular costo unitario final y aumento porcentual
            costo_unitario_final = precio_unitario_original * factor
            
            if precio_unitario_original > 0:
                incremento_porcentual = ((costo_unitario_final - precio_unitario_original) / precio_unitario_original) * 100
            else:
                incremento_porcentual = 0
            
            # Estructura del item calculado
            item_calculado = {
                'sku': item.get('sku', ''),
                'nombre': item.get('product_name', ''),
                'cantidad': cantidad,
                'precio_unitario_original': precio_unitario_original,
                'fob_value': fob_value,
                'costos_por_tipo': costos_por_tipo,
                'costo_total': costo_total,
                'costo_unitario_final': costo_unitario_final,
                'incremento_porcentual': incremento_porcentual
            }
            
            items_calculados.append(item_calculado)
        
        # Calcular totales por tipo de gasto
        totales_por_tipo = {}
        for tipo in tipos_gasto.keys():
            total_tipo = sum(self.convertir_a_float(gasto.get('amount_pen', 0)) for gasto in self.gastos if gasto['expense_type'] == tipo)
            totales_por_tipo[tipo] = total_tipo
        
        # Calcular costo unitario promedio
        costo_unitario_promedio = total_general / total_cantidad if total_cantidad > 0 else 0
        
        # Construir resultado final
        datos['items'] = items_calculados
        datos['totales'] = {
            'total_fob': total_fob,
            'total_gastos': total_gastos,
            'total_general': total_general,
            'total_cantidad': total_cantidad,
            'costo_unitario_promedio': costo_unitario_promedio,
            'factor': factor,
            'totales_por_tipo': totales_por_tipo
        }
        datos['columnas'] = list(tipos_gasto.keys())
        datos['gastos'] = tipos_gasto
        
        return datos

    
    def crear_resumen_costos(self, prorrateo_calculado):
        """Crea el resumen de costos prorrateados con scroll horizontal"""
        print(f"Creando resumen para {len(prorrateo_calculado)} items...")
        
        if not prorrateo_calculado:
            return ft.Container(
                content=ft.Text("No hay datos para calcular el prorrateo", 
                            color=ImportacionesTheme.TEXT_SECONDARY),
                padding=20,
                alignment=ft.alignment.center
            )
        
        # Obtener datos calculados
        datos = self.calcular_datos_prorrateo(prorrateo_calculado)
        
        # Crear columnas para la tabla
        columns = [
            # Columna Producto
            ft.DataColumn(
                ft.Text("Producto", size=12, weight=ft.FontWeight.BOLD),
                numeric=False
            ),
            # Columna Cantidad
            ft.DataColumn(
                ft.Text("Cant", size=12, weight=ft.FontWeight.BOLD),
                numeric=True
            ),
            # Columna Precio Unitario Original
            ft.DataColumn(
                ft.Text("Precio U.", size=12, weight=ft.FontWeight.BOLD),
                numeric=True,
                tooltip="Precio unitario original (FOB)"
            ),
            # Columna FOB Total
            ft.DataColumn(
                ft.Text("FOB Total", size=12, weight=ft.FontWeight.BOLD),
                numeric=True
            ),
        ]
        
        # Columnas para cada tipo de gasto (con nombres cortos)
        for tipo_key in datos['columnas']:
            tipo_info = datos['gastos'][tipo_key]
            columns.append(
                ft.DataColumn(
                    ft.Text(tipo_info['nombre_corto'], size=10, weight=ft.FontWeight.BOLD),
                    numeric=True,
                    tooltip=tipo_info['nombre_largo']
                )
            )
        
        # Columnas finales: Total, Unit., +%
        columns.extend([
            ft.DataColumn(
                ft.Text("Total Costo", size=12, weight=ft.FontWeight.BOLD),
                numeric=True
            ),
            ft.DataColumn(
                ft.Text("Costo Unit.", size=12, weight=ft.FontWeight.BOLD),
                numeric=True
            ),
            ft.DataColumn(
                ft.Text("Incremento %", size=12, weight=ft.FontWeight.BOLD),
                numeric=True
            ),
        ])
        
        # Crear filas de datos
        rows = []
        
        for item in datos['items']:
            # Formatear SKU y nombre
            sku = item['sku'][:10] if item['sku'] else ''
            nombre = item['nombre'][:20] if item['nombre'] else ''
            if len(item['nombre']) > 20:
                nombre = nombre + "..."
            
            # Celdas para este item
            cells = [
                # Producto (con SKU y nombre)
                ft.DataCell(
                    ft.Column([
                        ft.Text(sku, size=10, color=ImportacionesTheme.TEXT_SECONDARY),
                        ft.Text(nombre, size=11, color=ImportacionesTheme.TEXT_PRIMARY),
                    ], spacing=1)
                ),
                # Cantidad
                ft.DataCell(
                    ft.Text(str(int(item['cantidad'])), 
                        size=11,
                        text_align=ft.TextAlign.RIGHT)
                ),
                # Precio Unitario Original
                ft.DataCell(
                    ft.Text(f"S/ {item['precio_unitario_original']:,.2f}", 
                        size=11,
                        text_align=ft.TextAlign.RIGHT)
                ),
                # FOB Total
                ft.DataCell(
                    ft.Text(f"S/ {item['fob_value']:,.2f}", 
                        size=11,
                        text_align=ft.TextAlign.RIGHT)
                ),
            ]
            
            # Celdas para cada tipo de gasto
            for tipo_key in datos['columnas']:
                costo_tipo = item['costos_por_tipo'].get(tipo_key, 0)
                cells.append(
                    ft.DataCell(
                        ft.Text(f"S/ {costo_tipo:,.2f}", 
                            size=10,
                            text_align=ft.TextAlign.RIGHT)
                    )
                )
            
            # Color para el incremento %
            incremento = item['incremento_porcentual']
            color_incremento = ImportacionesTheme.SUCCESS if incremento < 10 else ImportacionesTheme.WARNING if incremento < 25 else ImportacionesTheme.ERROR
            
            # Celdas finales: Total Costo, Costo Unit., Incremento %
            cells.extend([
                ft.DataCell(
                    ft.Text(f"S/ {item['costo_total']:,.2f}", 
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.RIGHT)
                ),
                ft.DataCell(
                    ft.Text(f"S/ {item['costo_unitario_final']:,.2f}", 
                        size=11,
                        text_align=ft.TextAlign.RIGHT)
                ),
                ft.DataCell(
                    ft.Text(f"{incremento:.1f}%", 
                        size=11,
                        color=color_incremento,
                        text_align=ft.TextAlign.RIGHT)
                ),
            ])
            
            rows.append(ft.DataRow(cells=cells))
        
        # Fila de totales
        total_cells = [
            ft.DataCell(ft.Text("TOTALES", size=12, weight=ft.FontWeight.BOLD)),
            ft.DataCell(
                ft.Text(str(int(datos['totales']['total_cantidad'])), 
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.RIGHT)
            ),
            ft.DataCell(ft.Text("")),  # Precio unitario promedio
            ft.DataCell(
                ft.Text(f"S/ {datos['totales']['total_fob']:,.2f}", 
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.RIGHT)
            ),
        ]
        
        for tipo_key in datos['columnas']:
            total_tipo = datos['totales']['totales_por_tipo'].get(tipo_key, 0)
            total_cells.append(
                ft.DataCell(
                    ft.Text(f"S/ {total_tipo:,.2f}", 
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.RIGHT)
                )
            )
        total_cells.extend([
            ft.DataCell(
                ft.Text(f"S/ {datos['totales']['total_general']:,.2f}", 
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=ImportacionesTheme.SUCCESS,
                    text_align=ft.TextAlign.RIGHT)
            ),
            ft.DataCell(
                ft.Text("", 
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.RIGHT)
            ),
            ft.DataCell(ft.Text("")),  # Incremento % promedio
        ])
        
        rows.append(ft.DataRow(cells=total_cells))
        
        # Crear el DataTable
        datatable = ft.DataTable(
            columns=columns,
            rows=rows,
            heading_row_color=ImportacionesTheme.BG_SECONDARY,
            heading_row_height=35,
            data_row_min_height=32,
            column_spacing=10,
            horizontal_lines=ft.border.BorderSide(0.5, ImportacionesTheme.BORDER),
            vertical_lines=ft.border.BorderSide(0.5, ImportacionesTheme.BORDER),
        )
        
        # Calcular ancho aproximado
        ancho_aproximado = 200 + 80 + 100 + 120 + (len(datos['columnas']) * 100) + 120 + 100 + 80
        
        # Limitar ancho máximo
        if ancho_aproximado > 1400:
            ancho_aproximado = 1400
        
        # Contenedor para la tabla
        table_container = ft.Container(
            content=datatable,
            width=ancho_aproximado,
            padding=10,
            border=ft.border.all(1, ImportacionesTheme.BORDER),
            border_radius=8,
        )
        
        # Envolver en un Column con scroll horizontal
        return ft.Container(
            content=ft.Column(
                controls=[table_container],
                scroll=ft.ScrollMode.AUTO,
            ),
            height=450,
            padding=ft.padding.all(5),
        )
    
    def exportar_prorrateo_excel(self, e):
        """Exporta el prorrateo a Excel - Guarda en carpeta del proyecto"""
        print(f"\n=== Exportando prorrateo a Excel ===")
        
        if not self.prorrateo_calculado:
            self.mostrar_error("No hay prorrateo calculado para exportar")
            return
        
        try:
            from datetime import datetime
            import pandas as pd
            from io import BytesIO
            import os
            import platform
            from openpyxl.utils import get_column_letter
            
            # Obtener datos calculados (reutilizando la misma lógica)
            datos = self.calcular_datos_prorrateo(self.prorrateo_calculado)
            
            # **1. Crear carpeta 'exports' dentro del proyecto si no existe**
            current_dir = os.path.dirname(os.path.abspath(__file__))
            exports_dir = os.path.join(current_dir, '..', 'exports')
            exports_dir = os.path.abspath(exports_dir)
            os.makedirs(exports_dir, exist_ok=True)
            print(f"✅ Carpeta de exportaciones: {exports_dir}")
            
            # **2. Preparar datos para Excel usando los datos calculados**
            datos_items = []
            
            for item in datos['items']:
                # Crear diccionario con datos base
                item_data = {
                    'SKU': item['sku'],
                    'Producto': item['nombre'],
                    'Cantidad': item['cantidad'],
                    'Precio Unit. FOB': item['precio_unitario_original'],
                    'FOB Total': item['fob_value'],
                }
                
                # Agregar costos por tipo de gasto
                for tipo_key in datos['columnas']:
                    costo_tipo = item['costos_por_tipo'].get(tipo_key, 0)
                    # Usar el nombre corto para la columna
                    nombre_columna = datos['gastos'][tipo_key]['nombre_corto']
                    item_data[nombre_columna] = costo_tipo
                
                # Agregar cálculos finales
                item_data['Costo Total'] = item['costo_total']
                item_data['Costo Unit. Final'] = item['costo_unitario_final']
                item_data['Incremento %'] = item['incremento_porcentual']
                
                datos_items.append(item_data)
            
            # **3. Crear DataFrame**
            df = pd.DataFrame(datos_items)
            
            # **4. Crear Excel en memoria**
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # **HOJA PRINCIPAL - Escribir los datos**
                # Empezar en fila 8 para dejar espacio para encabezados (1-7)
                start_row = 8
                df.to_excel(writer, sheet_name='Prorrateo', index=False, startrow=start_row-1)
                
                # Obtener workbook y worksheet
                workbook = writer.book
                worksheet = writer.sheets['Prorrateo']
                
                # **AGREGAR ENCABEZADOS CON FORMATO**
                from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
                
                # Título principal (fila 1, columnas A-K)
                worksheet.merge_cells(f'A1:{get_column_letter(len(df.columns))}1')
                cell_a1 = worksheet['A1']
                cell_a1.value = f"PRORRATEO DE COSTOS DE IMPORTACIÓN"
                cell_a1.font = Font(bold=True, size=16, color="366092")
                cell_a1.alignment = Alignment(horizontal='center', vertical='center')
                
                # Información de la orden
                info_rows = [
                    (2, f"Orden de Compra: {self.orden.get('po_number', 'N/A')}"),
                    (3, f"Proveedor: {self.orden.get('supplier_name', 'N/A')}"),
                    (4, f"Fecha de Exportación: {datetime.now().strftime('%d/%m/%Y %H:%M')}"),
                    (5, f"Método de Prorrateo: {self.metodo_seleccionado.title()}"),
                    (6, f"NOTA: El IGV no se incluye en el costeo por ser impuesto recuperable"),
                ]
                
                for row_num, value in info_rows:
                    cell = worksheet[f'A{row_num}']
                    cell.value = value
                    if row_num == 6:  # Fila de nota
                        cell.font = Font(italic=True, color="808080")
                    elif row_num == 2:  # Fila de orden
                        cell.font = Font(bold=True)
                
                # **FORMATEAR ENCABEZADOS DE COLUMNAS (fila start_row)**
                header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                header_font = Font(color="FFFFFF", bold=True)
                header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                thin_border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
                
                # Aplicar formato a los encabezados
                for col in range(1, len(df.columns) + 1):
                    cell = worksheet.cell(row=start_row, column=col)
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = header_alignment
                    cell.border = thin_border
                
                # **FORMATEAR COLUMNAS NUMÉRICAS**
                from openpyxl.styles import numbers
                
                # Identificar columnas que son moneda
                currency_columns = []
                for col_name in df.columns:
                    if any(keyword in col_name for keyword in ['Precio', 'FOB', 'Costo', 'Total', 'Unit.', 'Final']):
                        if col_name != 'Cantidad' and col_name != 'Incremento %':
                            currency_columns.append(col_name)
                    # También incluir nombres de gastos (nombres cortos)
                    elif any(tipo_info['nombre_corto'] == col_name for tipo_info in datos['gastos'].values()):
                        currency_columns.append(col_name)
                
                # Aplicar formatos
                for col_num, col_name in enumerate(df.columns, 1):
                    # Aplicar formato según tipo de columna
                    if col_name in currency_columns:
                        # Formato moneda S/
                        
                        for row in range(start_row + 1, start_row + len(df) + 1):
                            cell = worksheet.cell(row=row, column=col_num)
                            cell.number_format = '"S/"#,##0.00'
                            cell.border = thin_border
                    
                    elif col_name == 'Incremento %':
                        # Formato porcentaje
                        for row in range(start_row + 1, start_row + len(df) + 1):
                            cell = worksheet.cell(row=row, column=col_num)
                            cell.number_format = '0.0"%"'
                            cell.border = thin_border
                            
                            # Color según porcentaje
                            if cell.value is not None:
                                try:
                                    porcentaje = float(cell.value)
                                    if porcentaje < 10:
                                        cell.font = Font(color="00B050")  # Verde
                                    elif porcentaje < 25:
                                        cell.font = Font(color="FFC000")  # Naranja
                                    else:
                                        cell.font = Font(color="FF0000")  # Rojo
                                except:
                                    pass
                    
                    elif col_name == 'Cantidad':
                        # Formato número entero
                        for row in range(start_row + 1, start_row + len(df) + 1):
                            cell = worksheet.cell(row=row, column=col_num)
                            cell.number_format = '0'
                            cell.alignment = Alignment(horizontal='center')
                            cell.border = thin_border
                    
                    else:
                        # Formato texto
                        for row in range(start_row + 1, start_row + len(df) + 1):
                            worksheet.cell(row=row, column=col_num).border = thin_border
                
                # **AJUSTAR ANCHO DE COLUMNAS**
                for col_num in range(1, len(df.columns) + 1):
                    max_length = 0
                    col_letter = get_column_letter(col_num)
                    
                    # Verificar celdas en esta columna
                    for row in range(start_row, start_row + len(df) + 2):
                        cell = worksheet.cell(row=row, column=col_num)
                        if cell.value:
                            try:
                                cell_length = len(str(cell.value))
                                if cell_length > max_length:
                                    max_length = cell_length
                            except:
                                pass
                    
                    # Ajustar ancho (mínimo 10, máximo 30)
                    adjusted_width = min(max(max_length + 2, 10), 30)
                    worksheet.column_dimensions[col_letter].width = adjusted_width
                
               # **5. AGREGAR FILA DE TOTALES**
                total_row = start_row + len(df) + 1

                # Celda "TOTALES"
                total_cell = worksheet.cell(row=total_row, column=1)
                total_cell.value = "TOTALES"
                total_cell.font = Font(bold=True)
                total_cell.fill = PatternFill(start_color="C5D9F1", end_color="C5D9F1", fill_type="solid")
                total_cell.border = thin_border
                total_cell.alignment = Alignment(horizontal='right')

                # Llenar los totales columna por columna
                for col_num, col_name in enumerate(df.columns, 1):
                    if col_num == 1:  # SKU ya está
                        continue
                    
                    # Obtener la celda
                    cell = worksheet.cell(row=total_row, column=col_num)
                    
                    # Aplicar formato básico a todas las celdas de totales
                    cell.fill = PatternFill(start_color="C5D9F1", end_color="C5D9F1", fill_type="solid")
                    cell.border = thin_border
                    cell.font = Font(bold=True)
                    
                    # Poner el valor según el tipo de columna
                    if col_name == 'Cantidad':
                        cell.value = datos['totales']['total_cantidad']
                        cell.number_format = '0'
                        cell.alignment = Alignment(horizontal='center')
                    
                    elif col_name == 'Precio Unit. FOB':
                        cell.value = ''
                        cell.alignment = Alignment(horizontal='center')
                    
                    elif col_name == 'FOB Total':
                        cell.value = datos['totales']['total_fob']
                        cell.number_format = '"S/"#,##0.00'
                        cell.alignment = Alignment(horizontal='right')
                    
                    elif col_name == 'Costo Total':
                        cell.value = datos['totales']['total_general']
                        cell.number_format = '"S/"#,##0.00'
                        cell.alignment = Alignment(horizontal='right')
                    
                    elif col_name == 'Costo Unit. Final':
                        # Dejar vacío - no tiene sentido sumar costos unitarios
                        cell.value = ''
                        cell.alignment = Alignment(horizontal='center')
                    
                    elif col_name == 'Incremento %':
                        # Dejar vacío o calcular promedio
                        cell.value = ''  # O puedes poner: datos['totales']['total_general'] / datos['totales']['total_fob'] * 100
                        cell.number_format = '0.0"%"'
                        cell.alignment = Alignment(horizontal='right')
                    
                    else:
                        # Verificar si es una columna de gasto
                        es_gasto = False
                        for tipo_key in datos['columnas']:
                            tipo_info = datos['gastos'][tipo_key]
                            if tipo_info['nombre_corto'] == col_name:
                                # Es un gasto - usar el total de ese gasto
                                cell.value = datos['totales']['totales_por_tipo'].get(tipo_key, 0)
                                cell.number_format = '"S/"#,##0.00'
                                cell.alignment = Alignment(horizontal='right')
                                es_gasto = True
                                break
                        
                        # Si no es un gasto y es otra columna de moneda
                        if not es_gasto and col_name in currency_columns:
                            cell.value = df[col_name].sum()
                            cell.number_format = '"S/"#,##0.00'
                            cell.alignment = Alignment(horizontal='right')
                
                # **6. HOJA DE RESUMEN DE GASTOS**
                if self.gastos:
                    # Resumen de gastos
                    resumen_data = []
                    for tipo_key in datos['columnas']:
                        tipo_info = datos['gastos'][tipo_key]
                        total_tipo = datos['totales']['totales_por_tipo'].get(tipo_key, 0)
                        porcentaje = (total_tipo / datos['totales']['total_gastos'] * 100) if datos['totales']['total_gastos'] > 0 else 0
                        
                        resumen_data.append({
                            'Tipo de Gasto': tipo_info['nombre_largo'],
                            'Monto (S/)': total_tipo,
                            'Porcentaje': porcentaje
                        })
                    
                    # Agregar total
                    resumen_data.append({
                        'Tipo de Gasto': 'TOTAL GASTOS',
                        'Monto (S/)': datos['totales']['total_gastos'],
                        'Porcentaje': 100.0
                    })
                    
                    resumen_df = pd.DataFrame(resumen_data)
                    resumen_df.to_excel(writer, sheet_name='Resumen Gastos', index=False)
                    
                    # Formatear hoja de resumen
                    resumen_ws = writer.sheets['Resumen Gastos']
                    
                    # Título
                    resumen_ws.merge_cells('A1:C1')
                    cell_a1 = resumen_ws['A1']
                    cell_a1.value = "RESUMEN DE GASTOS DE IMPORTACIÓN"
                    cell_a1.font = Font(bold=True, size=14, color="366092")
                    cell_a1.alignment = Alignment(horizontal='center')
                    
                    # Formatear encabezados
                    for col in range(1, 4):
                        cell = resumen_ws.cell(row=2, column=col)
                        cell.fill = header_fill
                        cell.font = header_font
                        cell.alignment = header_alignment
                        cell.border = thin_border
                    
                    # Formatear datos
                    for row in range(3, len(resumen_df) + 3):
                        # Formato moneda para columna B
                        cell_b = resumen_ws.cell(row=row, column=2)
                        cell_b.number_format = '"S/"#,##0.00'
                        cell_b.border = thin_border
                        
                        # Formato porcentaje para columna C
                        cell_c = resumen_ws.cell(row=row, column=3)
                        cell_c.number_format = '0.0"%"'
                        cell_c.border = thin_border
                    
                    # Resaltar fila de total
                    total_resumen_row = len(resumen_df) + 2
                    for col in range(1, 4):
                        cell = resumen_ws.cell(row=total_resumen_row, column=col)
                        cell.font = Font(bold=True)
                        cell.fill = PatternFill(start_color="C5D9F1", end_color="C5D9F1", fill_type="solid")
                        cell.border = thin_border
                    
                    # Ajustar anchos
                    resumen_ws.column_dimensions['A'].width = 35
                    resumen_ws.column_dimensions['B'].width = 20
                    resumen_ws.column_dimensions['C'].width = 15
            
            output.seek(0)
            excel_bytes = output.getvalue()
            
            # **7. Guardar archivo**
            filename = f"prorrateo_PO_{self.orden.get('po_number', 'N/A')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            file_path = os.path.join(exports_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(excel_bytes)
            
            print(f"✅ Archivo guardado en: {file_path}")
            
            # **8. Abrir archivo y mostrar mensaje**
            try:
                sistema = platform.system()
                if sistema == "Windows":
                    os.startfile(file_path)
                    mensaje = f"✅ Excel generado exitosamente!\n📂 Guardado en: {exports_dir}\n📄 Archivo: {filename}"
                elif sistema == "Darwin":
                    import subprocess
                    subprocess.run(["open", file_path])
                    mensaje = f"✅ Excel generado exitosamente!\n📂 Guardado en: {exports_dir}\n📄 Archivo: {filename}"
                elif sistema == "Linux":
                    import subprocess
                    subprocess.run(["xdg-open", file_path])
                    mensaje = f"✅ Excel generado exitosamente!\n📂 Guardado en: {exports_dir}\n📄 Archivo: {filename}"
                else:
                    mensaje = f"✅ Excel generado en: {file_path}"
                
                self.mostrar_exito(mensaje)
                
            except Exception as open_error:
                print(f"⚠️ No se pudo abrir automáticamente: {open_error}")
                mensaje = f"✅ Excel generado!\n📂 Guardado en: {exports_dir}\n📄 Archivo: {filename}"
                self.mostrar_exito(mensaje)
            
            print("=== Exportación completada ===\n")
            
        except ImportError as ie:
            print(f"❌ Error de importación: {ie}")
            self.mostrar_error("Instala: pip install pandas openpyxl")
        except Exception as ex:
            print(f"❌ Error al exportar: {ex}")
            import traceback
            traceback.print_exc()
            self.mostrar_error(f"Error: {str(ex)}")
    
    def acortar_nombre_gasto(self, nombre_largo):
        """Acorta el nombre del gasto para la tabla"""
        abreviaciones = {
            'Flete Internacional': 'Flete',
            'Seguro Internacional': 'Seguro',
            'Impuesto Ad-Valorem': 'Ad-Valorem',
            'Gastos de Aduana': 'Aduana',
            'Honorarios de Agencia': 'Honorarios',
            'Almacenaje': 'Almacén',
            'Transporte Nacional': 'Transp. Nac',
            'Proveedor Nacional': 'Prov. Nac',
        }
        
        # Verificar si es una factura de proveedor
        if 'Factura Prov. Nacional:' in nombre_largo:
            # Extraer número de factura
            import re
            match = re.search(r'Factura (\S+)', nombre_largo)
            if match:
                return f"Fact. {match.group(1)}"
            return "Fact. Prov."
        
        for largo, corto in abreviaciones.items():
            if largo in nombre_largo:
                return corto
        
        palabras = nombre_largo.split()
        if len(palabras) > 2:
            return ' '.join(palabras[:2])
        return nombre_largo[:12]

    def aplicar_prorrateo(self, e, metodo):
        """Versión corregida para guardar prorrateo y actualizar la vista"""
        prorrateo_calculado = self.calcular_prorrateo(metodo)
        if not prorrateo_calculado:
            self.mostrar_error("No se pudo calcular el prorrateo")
            return
        
        try:
            total_fob = sum(self.convertir_a_float(item.get('fob_value', 0)) for item in self.items)
            total_gastos = sum(self.convertir_a_float(gasto.get('amount_pen', 0)) for gasto in self.gastos)
            total_landed_cost = total_fob + total_gastos
            
            # 1. Guardar registro principal en cost_prorating
            query = """
                INSERT INTO cost_prorating 
                (po_id, prorating_date, prorating_method, total_fob, total_expenses,
                total_landed_cost, status, calculated_by)
                VALUES (%s, CURDATE(), %s, %s, %s, %s, 'applied', 1)
            """
            params = (self.po_id, metodo, total_fob, total_gastos, total_landed_cost)
            prorrateo_id = self.db.execute_query(query, params, fetch=False)
            
            if not prorrateo_id:
                self.mostrar_error("Error al guardar prorrateo")
                return
            
            print(f"✅ Prorrateo guardado con ID: {prorrateo_id}")
            
            # 2. Actualizar cada item con costos prorrateados
            for item_id, datos in prorrateo_calculado.items():
                item = datos['item']
                
                # Inicializar categorías
                prorated_freight = 0
                prorated_insurance = 0
                prorated_taxes = 0
                prorated_expenses = 0
                prorated_supplier = 0
                
                # Distribuir los costos según el tipo
                for tipo_gasto, monto in datos['costos'].items():
                    if tipo_gasto == 'freight':
                        prorated_freight += monto
                    elif tipo_gasto == 'insurance':
                        prorated_insurance += monto
                    elif tipo_gasto in ['igv', 'ipm']:
                        prorated_taxes += monto
                    elif tipo_gasto == 'ad_valorem':
                        continue
                    elif tipo_gasto == 'supplier_national':  # NUEVO: Facturas de proveedores
                        prorated_supplier += monto
                    else:  # customs_fees, agency_fees, etc.
                        prorated_expenses += monto
                
                # Calcular costo total
                fob_value = self.convertir_a_float(item.get('fob_value', 0))
                total_cost = fob_value + prorated_freight + prorated_insurance + prorated_taxes + prorated_expenses + prorated_supplier
                # IMPORTANTE: Usar las columnas que EXISTEN en tu esquema
                update_query = """
                    UPDATE purchase_order_items 
                    SET prorated_freight = %s,
                        prorated_insurance = %s,
                        prorated_taxes = %s,
                        prorated_expenses = %s,
                        prorated_supplier_invoices = %s,  -- NUEVA COLUMNA
                        total_cost = %s
                    WHERE id = %s
                """
                update_params = (prorated_freight, prorated_insurance, prorated_taxes, 
                                prorated_expenses, prorated_supplier, total_cost, item_id)
                self.db.execute_query(update_query, update_params, fetch=False)
            # 3. Actualizar la orden de compra
            order_update = """
                UPDATE purchase_orders 
                SET total_import_cost = %s,
                    status = 'prorrateado'
                WHERE id = %s
            """
            self.db.execute_query(order_update, (total_landed_cost, self.po_id), fetch=False)
            # 4. RECARGAR LOS DATOS para que aparezca en el historial
            self.actualizar_historial()
            # 5. Mostrar mensaje de éxito y actualizar la vista
            self.mostrar_exito(f"Prorrateo aplicado exitosamente (ID: {prorrateo_id})")
            
            # 6. Actualizar la vista actual para mostrar el nuevo historial
            self.page.update()
            

        except Exception as ex:
            print(f"❌ Error en aplicar_prorrateo: {str(ex)}")
            self.mostrar_error(f"Error: {str(ex)}")
    
    def crear_historial_view(self):
        """Crea la vista del historial de prorrateos que se puede actualizar"""
        if not self.costos_prorrateados:
            return ft.Container(
                content=ft.Text("No hay prorrateos previos", 
                            color=ImportacionesTheme.TEXT_SECONDARY),
                padding=20,
                alignment=ft.alignment.center
            )
        
        items_historial = []
        for pr in self.costos_prorrateados:
            # Formatear la fecha
            fecha = pr['prorating_date']
            if isinstance(fecha, str):
                fecha_str = fecha
            else:
                fecha_str = fecha.strftime('%d/%m/%Y') if hasattr(fecha, 'strftime') else str(fecha)
            
            # Crear tarjeta para cada prorrateo
            card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon("date_range", size=16, color=ImportacionesTheme.INFO),
                            ft.Text(f"Fecha: {fecha_str}", 
                                size=12, color=ImportacionesTheme.TEXT_PRIMARY),
                        ]),
                        ft.Row([
                            ft.Icon("settings", size=16, color=ImportacionesTheme.INFO),
                            ft.Text(f"Método: {pr.get('prorating_method', 'N/A')}", 
                                size=12, color=ImportacionesTheme.TEXT_PRIMARY),
                        ]),
                        ft.Row([
                            ft.Icon("attach_money", size=16, color=ImportacionesTheme.INFO),
                            ft.Text(f"FOB: S/ {float(pr.get('total_fob', 0) or 0):,.0f}", 
                                size=12, color=ImportacionesTheme.TEXT_PRIMARY),
                        ]),
                        ft.Row([
                            ft.Icon("receipt", size=16, color=ImportacionesTheme.INFO),
                            ft.Text(f"Gastos: S/ {float(pr.get('total_expenses', 0) or 0):,.0f}", 
                                size=12, color=ImportacionesTheme.WARNING),
                        ]),
                        ft.Row([
                            ft.Icon("summarize", size=16, color=ImportacionesTheme.INFO),
                            ft.Text(f"Total: S/ {float(pr.get('total_landed_cost', 0) or 0):,.0f}", 
                                size=12, weight=ft.FontWeight.BOLD, 
                                color=ImportacionesTheme.SUCCESS),
                        ]),
                    ], spacing=5),
                    padding=12,
                ),
                elevation=1,
            )
            items_historial.append(card)
        
        return ft.Column(items_historial, spacing=8)

    def actualizar_historial(self):
        """Recarga el historial y actualiza la vista"""
        print("Actualizando historial...")
        
        # Recargar prorrateos previos
        query = """
            SELECT * FROM cost_prorating 
            WHERE po_id = %s 
            ORDER BY prorating_date DESC
        """
        result = self.db.execute_query(query, (self.po_id,))
        self.costos_prorrateados = result or []
        print(f"✅ Historial actualizado: {len(self.costos_prorrateados)} registros")
        
        # Actualizar el contenedor del historial
        if self.historial_container and self.historial_container.current:
            self.historial_container.current.content = self.crear_historial_view()
            self.historial_container.current.update()
        
        self.mostrar_exito("Historial actualizado")


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
    
    def prorrateo_view(self):
        """Retorna la vista de prorrateo"""
        if not self.po_id or not self.orden:
            return ft.Container(
                content=ft.Column([
                    ft.Icon("error", size=64, color=ImportacionesTheme.ERROR),
                    ft.Text("Orden no especificada", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(f"PO_ID: {self.po_id}", color=ImportacionesTheme.TEXT_SECONDARY),
                    ft.ElevatedButton(
                        "Volver a la lista",
                        on_click=lambda e: self.page.go("/ordenes"),
                        style=ft.ButtonStyle(
                            bgcolor=ImportacionesTheme.STATUS_CONFIRMED,
                            color="white"
                        )
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
                padding=100,
                alignment=ft.alignment.center
            )
        
        # Calcular totales
        total_fob = sum(float(item.get('fob_value', 0) or 0) for item in self.items)
        total_gastos = sum(float(gasto.get('amount_pen', 0) or 0) for gasto in self.gastos)
        
        # Crear elementos reactivos
        resultados_container = ft.Ref[ft.Container]()
        metodo_dropdown = ft.Dropdown(
            label="Método de Prorrateo",
            options=[
                ft.dropdown.Option("value", "Por Valor (FOB)"),
                ft.dropdown.Option("weight", "Por Peso"),
                ft.dropdown.Option("volume", "Por Volumen"),
                ft.dropdown.Option("manual", "Manual"),
            ],
            value=self.metodo_seleccionado,
            width=200,
            on_change=lambda e: setattr(self, 'metodo_seleccionado', e.control.value)
        )
        
        def calcular(e):
            """Función para calcular el prorrateo"""
            metodo = metodo_dropdown.value
            print(f"Calculando prorrateo con método: {metodo}")
            
            # Calcular prorrateo
            prorrateo_calculado = self.calcular_prorrateo(metodo)
            self.prorrateo_calculado = prorrateo_calculado
            
            # Actualizar contenedor de resultados
            if resultados_container.current:
                if prorrateo_calculado:
                    # Crear tabla de resultados
                    tabla = self.crear_resumen_costos(prorrateo_calculado)
                    resultados_container.current.content = tabla
                else:
                    # Mostrar mensaje de error
                    resultados_container.current.content = ft.Container(
                        content=ft.Column([
                            ft.Icon("error", size=48, color=ImportacionesTheme.ERROR),
                            ft.Text("No se pudo calcular el prorrateo", 
                                   color=ImportacionesTheme.ERROR),
                            ft.Text("Verifique que haya gastos registrados y valores válidos", 
                                   size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=40,
                        alignment=ft.alignment.center
                    )
                
                # Actualizar el texto del método en la tarjeta
                metodo_text.current.value = f"Método: {metodo_dropdown.value.title()}"
                
                # Forzar actualización de la página
                resultados_container.current.update()
                metodo_text.current.update()      

        # Texto del método (para actualizar dinámicamente)
        metodo_text = ft.Ref[ft.Text]()
        
        self.historial_container = ft.Ref[ft.Container]()
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Row([
                                ft.Icon("calculate", size=24, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text(f"Prorrateo de Costos - PO: {self.orden['po_number']}", 
                                       size=24, weight=ft.FontWeight.BOLD, 
                                       color=ImportacionesTheme.TEXT_PRIMARY),
                            ], spacing=12),
                            ft.Text("Distribución de costos de importación a los productos", 
                                   size=13, color=ImportacionesTheme.TEXT_SECONDARY),
                        ]),
                        ft.ElevatedButton(
                            "Volver a Orden",
                            icon="arrow_back",
                            on_click=lambda e: self.page.go(f"/ordenes/{self.po_id}"),
                            style=ft.ButtonStyle(
                                bgcolor=ImportacionesTheme.BG_SECONDARY,
                                color=ImportacionesTheme.TEXT_PRIMARY
                            ),
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.symmetric(vertical=16),
                ),
                
                # Resumen de datos
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon("assessment", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text("Resumen de Datos", size=16, 
                                       weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                            ], spacing=8),
                            ft.Divider(height=20),
                            ft.ResponsiveRow([
                                ft.Column([
                                    ft.Text("Total FOB:", size=14, color=ImportacionesTheme.TEXT_SECONDARY),
                                    ft.Text(format_currency(total_fob), 
                                           size=18, weight=ft.FontWeight.BOLD,
                                           color=ImportacionesTheme.TEXT_PRIMARY),
                                ], col={"md": 3}),
                                ft.Column([
                                    ft.Text("Total Gastos:", size=14, color=ImportacionesTheme.TEXT_SECONDARY),
                                    ft.Text(format_currency(total_gastos), 
                                           size=18, weight=ft.FontWeight.BOLD,
                                           color=ImportacionesTheme.WARNING),
                                ], col={"md": 3}),
                                ft.Column([
                                    ft.Text("Costo Total:", size=14, color=ImportacionesTheme.TEXT_SECONDARY),
                                    ft.Text(format_currency(total_fob + total_gastos), 
                                           size=18, weight=ft.FontWeight.BOLD,
                                           color=ImportacionesTheme.SUCCESS),
                                ], col={"md": 3}),
                                ft.Column([
                                    ft.Text("Items:", size=14, color=ImportacionesTheme.TEXT_SECONDARY),
                                    ft.Text(str(len(self.items)), 
                                           size=18, weight=ft.FontWeight.BOLD,
                                           color=ImportacionesTheme.TEXT_PRIMARY),
                                ], col={"md": 3}),
                            ], spacing=16, run_spacing=16),
                        ]),
                        padding=20,
                    ),
                    elevation=1,
                ),
                
                # Controles de prorrateo
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon("settings", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text("Configuración de Prorrateo", size=16, 
                                       weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                            ], spacing=8),
                            ft.Divider(height=20),
                            ft.Row([
                                metodo_dropdown,
                                ft.Container(width=20),
                                ft.ElevatedButton(
                                    "Calcular",
                                    icon="calculate",
                                    on_click=calcular,
                                    style=ft.ButtonStyle(
                                        bgcolor=ImportacionesTheme.INFO,
                                        color="white"
                                    ),
                                ),
                                ft.Container(width=20),
                                ft.ElevatedButton(
                                    "Aplicar Prorrateo",
                                    icon="check_circle",
                                    on_click=lambda e: self.aplicar_prorrateo(e, metodo_dropdown.value),
                                    style=ft.ButtonStyle(
                                        bgcolor=ImportacionesTheme.SUCCESS,
                                        color="white"
                                    ),
                                ),
                                ft.Container(width=20),
                                ft.ElevatedButton(
                                "Exportar a Excel",
                                icon="download",
                                on_click=self.exportar_prorrateo_excel,  # Cambia aquí
                                style=ft.ButtonStyle(
                                    bgcolor=ImportacionesTheme.SUCCESS,
                                    color="black"
                                ),
                            )
                            ], spacing=12),
                            ft.Container(height=20),
                            ft.Text("Nota: El prorrateo distribuirá los costos de importación entre los productos según el método seleccionado.", 
                                   size=12, color=ImportacionesTheme.TEXT_SECONDARY),
                        ]),
                        padding=20,
                    ),
                    elevation=1,
                ),
                
                # Resultados del prorrateo
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon("table_chart", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text("Resultados del Prorrateo", size=16, 
                                       weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Container(expand=True),
                                ft.Text(ref=metodo_text, value=f"Método: {metodo_dropdown.value.title()}", 
                                       color=ImportacionesTheme.TEXT_SECONDARY),
                            ], spacing=8),
                            ft.Divider(height=20),
                            ft.Container(
                                ref=resultados_container,
                                content=ft.Column([
                                    ft.Icon("calculate", size=48, color=ImportacionesTheme.TEXT_SECONDARY),
                                    ft.Container(height=16),
                                    ft.Text("Calcule el prorrateo para ver los resultados", 
                                           color=ImportacionesTheme.TEXT_SECONDARY),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=40,
                                alignment=ft.alignment.center
                            ),
                        ]),
                        padding=20,
                    ),
                    elevation=1,
                ),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon("history", size=20, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Text("Historial de Prorrateos", size=16, 
                                    weight=ft.FontWeight.BOLD, color=ImportacionesTheme.TEXT_PRIMARY),
                                ft.Container(expand=True),
                                ft.IconButton(
                                    icon="refresh",
                                    icon_size=20,
                                    on_click=lambda e: self.actualizar_historial(),
                                    tooltip="Actualizar historial"
                                )
                            ], spacing=8),
                            ft.Divider(height=20),
                            ft.Container(
                                ref=self.historial_container,
                                content=self.crear_historial_view(),
                            ),
                        ]),
                        padding=20,
                    ),
                    elevation=1,
                    visible=bool(self.costos_prorrateados)
                ),
            
            ], scroll=ft.ScrollMode.AUTO),
            padding=24,
            expand=True,
            bgcolor=ImportacionesTheme.BG_PRIMARY,
        )
 