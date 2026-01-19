# pdf_utils.py
import re
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

def get_or_create_supplier(db, ruc: str, name: str, invoice_data: Dict[str, Any]) -> Optional[int]:
    """Buscar o crear proveedor - Función independiente"""
    supplier_id = None
    
    # Primero por RUC
    if ruc:
        supplier_query = "SELECT id FROM suppliers WHERE ruc = %s"
        supplier_result = db.execute_query(supplier_query, (ruc,))
        if supplier_result:
            supplier_id = supplier_result[0]['id']
    
    # Si no encontró por RUC, buscar por nombre
    if not supplier_id and name:
        supplier_query = "SELECT id FROM suppliers WHERE business_name LIKE %s"
        supplier_result = db.execute_query(supplier_query, (f"%{name}%",))
        if supplier_result:
            supplier_id = supplier_result[0]['id']
    
    # Crear proveedor si no existe
    if not supplier_id:
        insert_supplier = """
            INSERT INTO suppliers (ruc, business_name, trade_name, 
                                country_id, currency_id, is_foreign, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'active')
        """
        
        # Si no hay RUC, generar uno provisional
        if not ruc:
            ruc = f"PDF-{name[:10]}-{datetime.now().strftime('%Y%m%d')}"
        
        # Determinar país (2=USA por defecto para PDFs internacionales)
        country_id = 2  # USA por defecto
        logistics = invoice_data.get('logistics', {})
        origin = logistics.get('country_origin', '').upper()
        
        if 'PERU' in origin or 'PE' in origin:
            country_id = 1
        elif 'CHINA' in origin or 'CN' in origin:
            country_id = 3
        elif 'GERMANY' in origin or 'DE' in origin:
            country_id = 4
        
        supplier_id = db.execute_query(
            insert_supplier, 
            (
                ruc[:11],  # Limitar a 11 caracteres
                name[:200],
                name[:200],
                country_id,
                1,  # USD por defecto
                1   # Extranjero
            ), 
            fetch=False
        )
    
    return supplier_id


def process_invoice_item(db, invoice_id: int, item: Dict[str, Any], invoice_number: str) -> bool:
    """Procesar item de factura - Función independiente"""
    try:
        description = item.get('description', '')
        if not description:
            return False
        
        # Buscar producto por descripción o SKU
        product_query = """
            SELECT id FROM products 
            WHERE name LIKE %s OR sku LIKE %s 
            LIMIT 1
        """
        product_result = db.execute_query(
            product_query, 
            (f"%{description[:50]}%", f"%{description[:20]}%")
        )
        
        product_id = None
        if product_result:
            product_id = product_result[0]['id']
        else:
            # Crear producto básico
            create_product = """
                INSERT INTO products (sku, name, description, hs_code, 
                                    unit_measure, weight_kg, volume_m3, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'active')
            """
            
            # Generar SKU único
            sku = f"PDF-{invoice_number}-{hash(description) % 10000:04d}"
            
            product_id = db.execute_query(
                create_product,
                (
                    sku,
                    description[:100],
                    description[:500],
                    '99999999',  # HS Code genérico
                    item.get('unit', 'NIU'),
                    item.get('weight_kg', 0.1),
                    item.get('volume_m3', 0.001),
                ),
                fetch=False
            )
        
        # Insertar item de factura
        if product_id:
            insert_item_query = """
                INSERT INTO invoice_items (invoice_id, product_id, quantity, 
                                        unit_price, total_price, created_by)
                VALUES (%s, %s, %s, %s, %s, 1)
            """
            db.execute_query(
                insert_item_query,
                (
                    invoice_id,
                    product_id,
                    item.get('quantity', 1),
                    item.get('unit_price', 0),
                    item.get('total_price', 0),
                ),
                fetch=False
            )
            return True
        
        return False
    
    except Exception as e:
        print(f"  ⚠️ Error procesando item: {e}")
        return False


def get_currency_id(currency_code: str) -> int:
    """Obtener ID de moneda basado en código"""
    if currency_code == 'PEN':
        return 4
    elif currency_code == 'EUR':
        return 2
    elif currency_code == 'CNY':
        return 3
    else:
        return 1  # USD por defecto