# imports/excel_kardex_processor.py - VERSIÓN CORREGIDA CON DEBUG
import pandas as pd
import io
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re

class ExcelKardexProcessor:
    """
    Procesa las hojas de KARDEX del Excel para extraer productos.
    VERSIÓN CON DEBUG COMPLETO para diagnosticar problemas.
    """
    
    def __init__(self, db):
        self.db = db
        self.products_cache = {}
        self.po_cache = {}
        self.stats = {
            'hojas_procesadas': 0,
            'movimientos_encontrados': 0,
            'movimientos_guardados': 0,
            'productos_creados': 0,
            'pos_no_encontradas': [],
            'pos_encontradas': [],
            'errores': []
        }
    
    def load_kardex_sheets(self, excel_content: bytes) -> Dict[str, pd.DataFrame]:
        """Carga hojas que contengan 'KARDEX' en el nombre"""
        try:
            excel_file = pd.ExcelFile(io.BytesIO(excel_content))
            sheets_data = {}
            
            print(f"\n   📂 Todas las hojas en el archivo:")
            for i, name in enumerate(excel_file.sheet_names):
                has_kardex = "KARDEX" in name.upper()
                print(f"      {i+1}. '{name}' {'✅ KARDEX' if has_kardex else ''}")
            
            for sheet_name in excel_file.sheet_names:
                if "KARDEX" in sheet_name.upper():
                    df = excel_file.parse(sheet_name, header=None)
                    sheets_data[sheet_name] = df
                    print(f"\n   ✅ Cargada: '{sheet_name}' ({len(df)} filas, {len(df.columns)} columnas)")
            
            if not sheets_data:
                print("\n   ⚠️ NO se encontraron hojas con 'KARDEX' en el nombre")
                print("   💡 Verifica que el archivo tenga hojas como 'KARDEX MOTOR', 'KARDEX RELE', etc.")
            
            return sheets_data
            
        except Exception as e:
            print(f"❌ Error leyendo Excel: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def _safe_float(self, val) -> float:
        """Convierte a float de forma segura"""
        if pd.isna(val) or str(val).strip() == '':
            return 0.0
        try:
            # Limpiar caracteres comunes
            clean = str(val).replace(',', '').replace('$', '').replace(' ', '').strip()
            return float(clean)
        except:
            return 0.0

    def _clean_po_number(self, text) -> Optional[str]:
        """Extrae y normaliza el número de PO - VERSIÓN MEJORADA"""
        if pd.isna(text):
            return None
        
        text = str(text).upper().strip()
        
        # Patrones más flexibles
        patterns = [
            r'PO\s*(\d{4,})(?:/\d{2})?',      # PO2754, PO 2754, PO2754/25
            r'PO-?(\d{4,})(?:-\d{2})?',        # PO-2754, PO2754-25
            r'P\.?O\.?\s*(\d{4,})',             # P.O.2754, P.O 2754
            r'(\d{4,})/(\d{2})',                # 2754/25
            r'\b(\d{4,})\b',                    # Solo números de 4+ dígitos
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Extraer solo los dígitos principales
                numero = match.group(1)
                if len(numero) >= 4:
                    return f"PO{numero}"
        
        return None

    def _extract_product_name(self, df: pd.DataFrame, sheet_name: str) -> str:
        """Extrae el nombre del producto"""
        print(f"\n      🔍 Buscando nombre del producto...")
        
        # Buscar en primeras 20 filas
        for idx in range(min(20, len(df))):
            row = df.iloc[idx]
            for col_idx, val in enumerate(row.values):
                if pd.notna(val):
                    val_str = str(val).strip()
                    val_upper = val_str.upper()
                    
                    # Buscar patrones de descripción
                    if any(x in val_upper for x in ["DESCRIPCION", "DESCRIPCIÓN", "PRODUCTO"]):
                        if ":" in val_str:
                            parts = val_str.split(":", 1)
                            if len(parts) > 1 and parts[1].strip():
                                nombre = parts[1].strip()[:200]
                                print(f"         ✅ Encontrado en fila {idx}, col {col_idx}: '{nombre[:50]}...'")
                                return nombre
                        # Buscar en la siguiente celda
                        if col_idx + 1 < len(row) and pd.notna(row.iloc[col_idx + 1]):
                            nombre = str(row.iloc[col_idx + 1]).strip()[:200]
                            print(f"         ✅ Encontrado en celda siguiente: '{nombre[:50]}...'")
                            return nombre
        
        # Usar nombre de la hoja
        nombre = sheet_name.upper().replace("KARDEX", "").strip()
        nombre = nombre if nombre else "PRODUCTO KARDEX"
        print(f"         ⚠️ Usando nombre de hoja: '{nombre}'")
        return nombre

    def _find_header_and_columns(self, df: pd.DataFrame) -> Tuple[int, Dict]:
        """
        Encuentra encabezados buscando en un BLOQUE de filas.
        Maneja el caso donde ENTRADAS, FECHA y CANTIDAD están en filas distintas.
        """
        header_row_idx = -1
        col_map = {}
        
        print(f"\n      🔍 Buscando estructura de columnas...")
        
        # 1. Buscar la fila principal que define las secciones (ENTRADAS / SALIDAS)
        # Limitamos la búsqueda a las primeras 30 filas
        for idx in range(min(30, len(df))):
            # Convertimos la fila a string mayúsculas para buscar palabras clave
            row_str = " ".join([str(x).upper() for x in df.iloc[idx].values if pd.notna(x)])
            
            # La fila clave debe tener "ENTRADA" (o ENTRADAS) y "SALIDA" (o SALIDAS)
            if "ENTRADA" in row_str and "SALIDA" in row_str:
                header_row_idx = idx
                print(f"         ✅ Fila Principal encontrada en índice {idx}")
                
                # A. Buscar columna ORDEN / PO en esta misma fila principal
                for c, val in enumerate(df.iloc[idx].values):
                    if pd.notna(val):
                        val_str = str(val).upper().strip()
                        if "ORDEN" in val_str or "IMPORTAC" in val_str:
                            col_map['po'] = c
                            print(f"            - PO/ORDEN en columna {c}")

                # B. Explorar las siguientes 3 filas hacia abajo para encontrar FECHA, CANTIDAD, etc.
                # Esto es crucial porque en tu Excel 'CANTIDAD' y 'FECHA' están más abajo.
                for offset in range(1, 4): 
                    if idx + offset >= len(df): break
                    
                    sub_row = df.iloc[idx + offset].values
                    sub_str = " ".join([str(x).upper() for x in sub_row if pd.notna(x)])
                    
                    # Buscar columna FECHA
                    if 'fecha' not in col_map:
                        for c, val in enumerate(sub_row):
                            if pd.notna(val) and "FECHA" in str(val).upper():
                                col_map['fecha'] = c
                                print(f"            - FECHA en columna {c} (fila +{offset})")
                    
                    # Buscar columna DESCRIPCION
                    if 'desc' not in col_map:
                        for c, val in enumerate(sub_row):
                            val_str = str(val).upper()
                            if pd.notna(val) and ("DESCRIPCI" in val_str or "DETALLE" in val_str):
                                col_map['desc'] = c
                                print(f"            - DESCRIPCION en columna {c} (fila +{offset})")

                    # Buscar CANTIDAD (Solo la primera aparición, que corresponde a ENTRADAS)
                    if 'qty' not in col_map:
                        for c, val in enumerate(sub_row):
                            if pd.notna(val) and "CANTIDAD" in str(val).upper():
                                col_map['qty'] = c
                                # Asumimos estructura estándar: Cantidad | Costo Unit | Costo Total
                                col_map['unit_cost'] = c + 1
                                col_map['total_cost'] = c + 2
                                print(f"            - CANTIDAD (Entrada) en columna {c} (fila +{offset})")
                                break # ¡Importante! Paramos aquí para no tomar la cantidad de Salidas
                
                break # Salimos del bucle principal una vez encontrada la cabecera
        
        # Validación final y Defaults
        if header_row_idx != -1 and 'qty' in col_map:
            # Si no encontramos fecha explícita, asumimos columna 0 (estándar en tus archivos)
            if 'fecha' not in col_map: 
                col_map['fecha'] = 0
                print(f"            ⚠️ FECHA no detectada explícitamente, usando columna 0")
            
            # Si no encontramos descripción, asumimos columna 1
            if 'desc' not in col_map:
                col_map['desc'] = 1
            
            return header_row_idx, col_map
            
        print("         ❌ No se pudo determinar la estructura del Kardex (No se hallaron 'ENTRADAS' y 'SALIDAS')")
        return -1, {}
    
    def _generate_sku(self, name: str) -> str:
        """Genera SKU a partir del nombre"""
        clean = re.sub(r'[^A-Za-z0-9\s]', '', name.upper())
        words = clean.split()[:3]
        sku = "-".join([w[:4] for w in words if w])
        return sku[:20] if sku else "PROD"

    def process_and_save_to_db(self, excel_content: bytes, file_name: str) -> Dict:
        """Procesa hojas KARDEX y guarda productos/movimientos"""
        
        print(f"\n{'='*70}")
        print(f"📦 PROCESANDO KARDEX DE PRODUCTOS: {file_name}")
        print(f"{'='*70}")
        
        # Reset stats
        self.stats = {
            'hojas_procesadas': 0,
            'movimientos_encontrados': 0,
            'movimientos_guardados': 0,
            'productos_creados': 0,
            'pos_no_encontradas': [],
            'pos_encontradas': [],
            'errores': []
        }
        
        # Cargar hojas KARDEX
        sheets = self.load_kardex_sheets(excel_content)
        
        if not sheets:
            return {
                'success': False,
                'message': "No se encontraron hojas KARDEX en el archivo."
            }
        
        # Conectar a BD
        print(f"\n[PASO 1] Conectando a BD...")
        try:
            if hasattr(self.db, 'connection'):
                conn = self.db.connection
            else:
                conn = self.db
            
            if hasattr(conn, 'is_connected') and not conn.is_connected():
                print("   🔄 Reconectando...")
                conn.reconnect(attempts=3, delay=2)
            
            cursor = conn.cursor()
            print("   ✅ Conexión establecida")
            
            # Verificar POs existentes
            cursor.execute("SELECT COUNT(*) FROM purchase_orders")
            po_count = cursor.fetchone()[0]
            print(f"   📊 POs en BD: {po_count}")
            
            if po_count == 0:
                print("   ⚠️ ¡NO hay POs en la base de datos!")
                print("   💡 Primero debes importar las importaciones con el otro procesador")
            else:
                # Mostrar algunas POs de ejemplo
                cursor.execute("SELECT po_number FROM purchase_orders LIMIT 5")
                ejemplos = [row[0] for row in cursor.fetchall()]
                print(f"   📋 Ejemplos de POs: {ejemplos}")
                
        except Exception as e:
            import traceback
            print(f"   ❌ Error BD: {e}")
            traceback.print_exc()
            return {'success': False, 'message': f"Error BD: {str(e)}"}
        
        # Procesar cada hoja
        print(f"\n[PASO 2] Procesando {len(sheets)} hojas de KARDEX...")
        
        for sheet_name, df in sheets.items():
            print(f"\n{'='*50}")
            print(f"   📄 HOJA: {sheet_name}")
            print(f"{'='*50}")
            self.stats['hojas_procesadas'] += 1
            
            # Obtener nombre del producto
            producto_nombre = self._extract_product_name(df, sheet_name)
            
            # Extraer movimientos
            movimientos = self._extract_movements(df, producto_nombre)
            self.stats['movimientos_encontrados'] += len(movimientos)
            
            if movimientos:
                print(f"\n      💾 Guardando {len(movimientos)} movimientos...")
                guardados = self._save_movements(movimientos, cursor)
                self.stats['movimientos_guardados'] += guardados
                print(f"      ✅ Guardados: {guardados}")
            else:
                print(f"\n      ⚠️ No se encontraron movimientos válidos en esta hoja")
        
        # Commit
        print(f"\n[PASO 3] Guardando cambios en BD...")
        conn.commit()
        cursor.close()
        print("   ✅ Commit realizado")
        
        # Resumen
        print(f"\n{'='*70}")
        print(f"📊 RESUMEN FINAL KARDEX:")
        print(f"   - Hojas procesadas: {self.stats['hojas_procesadas']}")
        print(f"   - Movimientos encontrados: {self.stats['movimientos_encontrados']}")
        print(f"   - Movimientos guardados: {self.stats['movimientos_guardados']}")
        print(f"   - Productos creados: {self.stats['productos_creados']}")
        
        if self.stats['pos_encontradas']:
            print(f"   - POs vinculadas: {self.stats['pos_encontradas'][:10]}...")
        
        if self.stats['pos_no_encontradas']:
            print(f"\n   ⚠️ POs NO encontradas en BD ({len(self.stats['pos_no_encontradas'])}):")
            for po in self.stats['pos_no_encontradas'][:10]:
                print(f"      - {po}")
            print(f"   💡 Estas POs existen en el Kardex pero no en tu tabla purchase_orders")
        
        if self.stats['errores']:
            print(f"\n   ❌ Errores ({len(self.stats['errores'])}):")
            for err in self.stats['errores'][:5]:
                print(f"      - {err}")
        
        print(f"{'='*70}\n")
        
        return {
            'success': True,
            'message': f"Procesadas {self.stats['hojas_procesadas']} hojas. {self.stats['movimientos_guardados']} ingresos guardados.",
            'stats': self.stats
        }

    def _extract_movements(self, df: pd.DataFrame, producto_nombre: str) -> List[Dict]:
        """Extrae movimientos de ENTRADA - CON DEBUG COMPLETO"""
        movements = []
        
        # Encontrar encabezados
        header_row, col_map = self._find_header_and_columns(df)
        
        if header_row == -1:
            return []
        
        if 'qty' not in col_map:
            print(f"\n      ❌ No se encontró columna de CANTIDAD")
            print(f"      💡 El código busca una celda con 'CANTIDAD' en los sub-encabezados")
            return []
        
        # Procesar filas de datos
        start_row = header_row + 2
        filas_con_po = 0
        filas_con_cantidad = 0
        filas_validas = 0
        
        print(f"\n      📊 Procesando filas desde {start_row} hasta {len(df)}...")
        
        for idx in range(start_row, len(df)):
            row = df.iloc[idx]
            
            try:
                # === OBTENER PO ===
                po_number = None
                
                # Primero buscar en columna específica
                if 'po' in col_map and col_map['po'] < len(row):
                    po_raw = row.iloc[col_map['po']]
                    po_number = self._clean_po_number(po_raw)
                    if po_number and filas_con_po < 3:
                        print(f"         Fila {idx}: PO '{po_raw}' -> '{po_number}'")
                
                # Si no encontró, buscar en toda la fila
                if not po_number:
                    for val in row.values:
                        if pd.notna(val):
                            po_number = self._clean_po_number(val)
                            if po_number:
                                break
                
                if not po_number:
                    continue
                
                filas_con_po += 1
                
                # === OBTENER FECHA ===
                fecha = None
                if 'fecha' in col_map and col_map['fecha'] < len(row):
                    fecha_raw = row.iloc[col_map['fecha']]
                    if isinstance(fecha_raw, datetime):
                        fecha = fecha_raw
                    elif pd.notna(fecha_raw):
                        try:
                            fecha = pd.to_datetime(fecha_raw, errors='coerce')
                        except:
                            pass
                
                if pd.isna(fecha) or fecha is None:
                    continue
                
                # === OBTENER CANTIDAD ===
                qty = 0
                if col_map['qty'] < len(row):
                    qty = self._safe_float(row.iloc[col_map['qty']])
                
                if qty <= 0:
                    continue
                
                filas_con_cantidad += 1
                
                # === OBTENER COSTOS ===
                unit_cost = 0
                total_cost = 0
                
                if 'unit_cost' in col_map and col_map['unit_cost'] < len(row):
                    unit_cost = self._safe_float(row.iloc[col_map['unit_cost']])
                if 'total_cost' in col_map and col_map['total_cost'] < len(row):
                    total_cost = self._safe_float(row.iloc[col_map['total_cost']])
                
                if total_cost == 0 and unit_cost > 0:
                    total_cost = unit_cost * qty
                
                # Agregar movimiento
                movements.append({
                    'fecha': fecha,
                    'producto': producto_nombre,
                    'sku': self._generate_sku(producto_nombre),
                    'cantidad': qty,
                    'costo_unitario': unit_cost,
                    'costo_total': total_cost,
                    'po_number': po_number
                })
                filas_validas += 1
                
                # Debug primeros movimientos
                if filas_validas <= 3:
                    print(f"         ✅ Movimiento {filas_validas}: {po_number}, Qty: {qty}, Cost: ${total_cost:.2f}")
                
            except Exception as e:
                if len(self.stats['errores']) < 5:
                    self.stats['errores'].append(f"Fila {idx}: {str(e)[:50]}")
                continue
        
        print(f"\n      📊 Estadísticas de extracción:")
        print(f"         - Filas con PO detectada: {filas_con_po}")
        print(f"         - Filas con cantidad > 0: {filas_con_cantidad}")
        print(f"         - Movimientos válidos: {filas_validas}")
        
        return movements

    def _get_po_id(self, po_number: str, cursor) -> Optional[int]:
        """Obtiene ID de PO con búsqueda flexible"""
        if po_number in self.po_cache:
            return self.po_cache[po_number]
        
        # Búsqueda exacta
        cursor.execute("SELECT id FROM purchase_orders WHERE po_number = %s", (po_number,))
        result = cursor.fetchone()
        
        if result:
            self.po_cache[po_number] = result[0]
            if po_number not in self.stats['pos_encontradas']:
                self.stats['pos_encontradas'].append(po_number)
            return result[0]
        
        # Búsqueda parcial (sin el /XX del final)
        po_base = re.sub(r'/\d{2}$', '', po_number)
        cursor.execute("SELECT id, po_number FROM purchase_orders WHERE po_number LIKE %s LIMIT 1", (f"%{po_base}%",))
        result = cursor.fetchone()
        
        if result:
            self.po_cache[po_number] = result[0]
            if po_number not in self.stats['pos_encontradas']:
                self.stats['pos_encontradas'].append(f"{po_number}={result[1]}")
            return result[0]
        
        # Búsqueda solo por número
        solo_numeros = re.sub(r'[^0-9]', '', po_number)
        if len(solo_numeros) >= 4:
            cursor.execute("SELECT id, po_number FROM purchase_orders WHERE po_number LIKE %s LIMIT 1", (f"%{solo_numeros}%",))
            result = cursor.fetchone()
            
            if result:
                self.po_cache[po_number] = result[0]
                if po_number not in self.stats['pos_encontradas']:
                    self.stats['pos_encontradas'].append(f"{po_number}={result[1]}")
                return result[0]
        
        return None

    def _get_or_create_product(self, name: str, sku: str, cursor) -> int:
        """Obtiene o crea producto"""
        cache_key = f"{sku}_{name[:30]}"
        if cache_key in self.products_cache:
            return self.products_cache[cache_key]
        
        # Buscar existente por nombre
        cursor.execute("SELECT id FROM products WHERE name LIKE %s LIMIT 1", (f"%{name[:50]}%",))
        result = cursor.fetchone()
        
        if result:
            self.products_cache[cache_key] = result[0]
            return result[0]
        
        # Buscar por SKU
        cursor.execute("SELECT id FROM products WHERE sku = %s LIMIT 1", (sku,))
        result = cursor.fetchone()
        
        if result:
            self.products_cache[cache_key] = result[0]
            return result[0]
        
        # Crear nuevo producto
        sku_final = sku
        counter = 1
        while True:
            cursor.execute("SELECT id FROM products WHERE sku = %s", (sku_final,))
            if not cursor.fetchone():
                break
            sku_final = f"{sku[:15]}-{counter}"
            counter += 1
        
        cursor.execute("""
            INSERT INTO products (sku, name, description, status, created_by, created_at)
            VALUES (%s, %s, %s, 'active', 1, NOW())
        """, (sku_final, name[:200], name[:500]))
        
        product_id = cursor.lastrowid
        self.products_cache[cache_key] = product_id
        self.stats['productos_creados'] += 1
        print(f"            ➕ Producto creado: {sku_final}")
        
        return product_id

    def _save_movements(self, movements: List[Dict], cursor) -> int:
        """Guarda movimientos en BD (Corregido: po_item_id y duplicados)"""
        count = 0
        
        for mov in movements:
            try:
                # 1. Obtener PO
                po_id = self._get_po_id(mov['po_number'], cursor)
                
                if not po_id:
                    if mov['po_number'] not in self.stats['pos_no_encontradas']:
                        self.stats['pos_no_encontradas'].append(mov['po_number'])
                    continue
                
                # 2. Obtener/crear producto
                product_id = self._get_or_create_product(mov['producto'], mov['sku'], cursor)
                
                # 3. GESTIÓN DE PO_ITEM (Corrección del error 1364)
                # Buscamos si ya existe el ítem en la orden de compra
                cursor.execute("""
                    SELECT id FROM purchase_order_items 
                    WHERE po_id = %s AND product_id = %s
                """, (po_id, product_id))
                
                result_item = cursor.fetchone()
                
                if result_item:
                    po_item_id = result_item[0]
                else:
                    # Si no existe, lo creamos y capturamos su ID
                    cursor.execute("""
                        INSERT INTO purchase_order_items 
                        (po_id, product_id, quantity, unit_price, unit_measure, total_cost, created_by)
                        VALUES (%s, %s, %s, %s, 'UNI', %s, 1)
                    """, (po_id, product_id, mov['cantidad'], mov['costo_unitario'], mov['costo_total']))
                    po_item_id = cursor.lastrowid
                
                # 4. Crear movimiento almacén (Corrección del error 1062 - Duplicados)
                mov_ref = f"ING-{mov['po_number']}"
                
                cursor.execute("""
                    SELECT id FROM warehouse_movements 
                    WHERE reference_document = %s AND DATE(movement_date) = DATE(%s)
                """, (mov_ref, mov['fecha']))
                
                res_mov = cursor.fetchone()
                
                if res_mov:
                    mov_id = res_mov[0]
                else:
                    # Usamos PO_ID y un contador global para asegurar unicidad
                    import time
                    unique_suffix = f"{int(time.time())}-{po_id}-{count}"
                    mov_num = f"MOV-{unique_suffix}"
                    
                    cursor.execute("""
                        INSERT INTO warehouse_movements 
                        (movement_number, po_id, movement_type, movement_date, 
                         reference_document, status, created_by)
                        VALUES (%s, %s, 'receipt', %s, %s, 'completed', 1)
                    """, (mov_num, po_id, mov['fecha'], mov_ref))
                    mov_id = cursor.lastrowid
                
                # 5. Detalle del movimiento (Ahora enviamos po_item_id)
                cursor.execute("""
                    SELECT id FROM movement_details 
                    WHERE movement_id = %s AND product_id = %s
                """, (mov_id, product_id))
                
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO movement_details
                        (movement_id, product_id, quantity, unit_cost, total_cost, po_item_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (mov_id, product_id, mov['cantidad'], mov['costo_unitario'], mov['costo_total'], po_item_id))
                
                count += 1
                
            except Exception as e:
                if len(self.stats['errores']) < 10:
                    self.stats['errores'].append(f"{mov['po_number']}: {str(e)[:100]}")
                continue
        
        return count

