# excel_importaciones_processor.py
import pandas as pd
import io
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re

class ExcelImportacionesProcessor:
    def __init__(self, db):
        """
        Inicializa el procesador de Excel para Importaciones desde Kardex.
        """
        self.db = db
        self.importaciones = []
        self.pos_por_importacion = {}
        
        
    def load_file(self, file_content: bytes, filename: str) -> Dict[str, pd.DataFrame]:
        """
        Carga INTELIGENTE: Solo carga la hoja 'DETALLE DE COSTO' si es Excel.
        """
        try:
            print(f"   📂 Cargando archivo: {filename}")
            
            if filename.lower().endswith('.csv'):
                try:
                    df = pd.read_csv(io.BytesIO(file_content), header=None)
                except:
                    df = pd.read_csv(io.BytesIO(file_content), header=None, encoding='latin-1')
                print(f"   ✅ CSV cargado: {len(df)} filas")
                return {'HojaCSV': df}
            else:
                excel_file = pd.ExcelFile(io.BytesIO(file_content))
                sheet_names = excel_file.sheet_names
                
                print(f"   - Hojas encontradas en el Excel: {sheet_names}")
                
                target_sheet = None
                for sheet in sheet_names:
                    if "DETALLE DE COSTO" in sheet.upper():
                        target_sheet = sheet
                        break
                
                if target_sheet:
                    print(f"   ✅ Cargando únicamente: '{target_sheet}'...")
                    result = pd.read_excel(excel_file, sheet_name=[target_sheet], header=None)
                    print(f"   ✅ Hoja cargada: {len(result[target_sheet])} filas")
                    return result
                else:
                    print("   ⚠️ No encontré 'DETALLE DE COSTO'. Cargando solo la primera hoja.")
                    result = pd.read_excel(excel_file, sheet_name=[sheet_names[0]], header=None)
                    return result
                
        except Exception as e:
            print(f"❌ Error cargando archivo: {e}")
            return {}
    
    def _safe_float(self, val):
        """Convierte texto a decimal de forma segura"""
        if pd.isna(val) or str(val).strip() == '': 
            return 0.0
        try:
            return float(str(val).replace(',', '').strip())
        except:
            return 0.0

    def extract_po_from_text(self, text: str) -> List[str]:
        """
        Extrae números de PO de un texto con múltiples patrones.
        MEJORADO: Más patrones y mejor manejo de casos especiales.
        """
        if not text or pd.isna(text):
            return []
        
        text = str(text).strip().upper()
        pos = []
        
        # Patrones mejorados para capturar más formatos
        po_patterns = [
            r'PO\s*(\d{4,})',           # PO2754, PO 2754
            r'PO(\d{4,})[/,\s]',        # PO2754/20, PO2754,56
            r'PO(\d{4,})$',             # PO2754 al final
            r'P\.O\.?\s*(\d{4,})',      # P.O.2754, P.O 2754
            r'\bO(\d{4,})[/,\s]',       # O2754/20 (sin P)
            r'\bO(\d{4,})$',            # O2754 al final
            r'ORD[EN]*\s*(\d{4,})',     # ORDEN 2754
            r'OC\s*(\d{4,})',           # OC2754 (Orden de Compra)
        ]
        
        for pattern in po_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Normalizar a formato PO####
                po_number = f"PO{match}"
                if po_number not in pos and len(match) >= 4:
                    pos.append(po_number)
        
        # Caso especial: PO con múltiples números separados por comas
        # Ej: "PO2754,55,56/20" -> PO2754, PO2755, PO2756
        multi_match = re.search(r'PO(\d{4,}),(\d{1,3})(?:,(\d{1,3}))?', text)
        if multi_match:
            base = multi_match.group(1)
            for i, suffix in enumerate([multi_match.group(2), multi_match.group(3)]):
                if suffix:
                    # Si el sufijo es corto, asumimos que comparte el prefijo
                    if len(suffix) <= 2:
                        new_po = f"PO{base[:-len(suffix)]}{suffix}"
                    else:
                        new_po = f"PO{suffix}"
                    if new_po not in pos:
                        pos.append(new_po)
        
        return pos
    
    def _buscar_pos_en_rango(self, df: pd.DataFrame, inicio: int, fin: int) -> List[str]:
        """
        Busca POs en un rango de filas del DataFrame.
        Útil para buscar hacia arriba y abajo de una fecha.
        """
        pos_encontradas = []
        
        for idx in range(max(0, inicio), min(len(df), fin)):
            try:
                row = df.iloc[idx]
                row_text = " ".join([str(x) for x in row.values if pd.notna(x)])
                pos = self.extract_po_from_text(row_text)
                pos_encontradas.extend(pos)
            except:
                continue
        
        return list(set(pos_encontradas))  # Eliminar duplicados
    
    def extract_importacion_info(self, df: pd.DataFrame) -> Tuple[List[Dict], Dict]:
        """
        Extrae información de importaciones del Excel.
        MEJORADO: Busca POs tanto hacia arriba como hacia abajo de cada factura.
        """
        importaciones = []
        pos_por_importacion = {}
        df = df.dropna(how='all')
        
        es_seccion_flete = False 
        
        # Variables de "Memoria"
        imp_pendiente = None
        pos_acumuladas = []
        base_costos_pendiente = -1
        fila_inicio_bloque = 0  # Para buscar POs hacia arriba

        print(f"\n   🔍 Analizando {len(df)} filas...")
        print(f"   {'='*50}")
        
        # FASE 1: Primero, encontrar TODAS las POs en todo el documento
        todas_las_pos = []
        for idx, row in df.iterrows():
            row_text = " ".join([str(x) for x in row.values if pd.notna(x)])
            pos = self.extract_po_from_text(row_text)
            if pos:
                todas_las_pos.extend(pos)
                print(f"      📦 Fila {idx}: Encontradas POs: {pos}")
        
        todas_las_pos = list(set(todas_las_pos))
        print(f"\n   📊 Total POs encontradas en documento: {len(todas_las_pos)}")
        if todas_las_pos:
            print(f"      {todas_las_pos[:10]}{'...' if len(todas_las_pos) > 10 else ''}")
        print(f"   {'='*50}\n")

        # FASE 2: Procesar fila por fila buscando facturas
        for idx, row in df.iterrows():
            row_list = [str(x).strip() if pd.notna(x) else '' for x in row.values]
            fila_texto = " ".join(row_list).upper()
            
            # 1. DETECCIÓN DE ENCABEZADOS
            if "AGENCIA" in fila_texto and "ADUANA" in fila_texto:
                if "FLETE" in fila_texto:
                    es_seccion_flete = True
                    print(f"      📋 Fila {idx}: Modo FLETE activado")
                elif "SEGURO" in fila_texto:
                    es_seccion_flete = False
                    print(f"      📋 Fila {idx}: Modo SEGURO activado")
                continue

            # 2. DETECCIÓN DE NUEVA IMPORTACIÓN (Busca fecha 'YYYY-MM-DD')
            fecha_idx = -1
            fecha_obj = None
            
            for i in range(min(5, len(row_list))): 
                val = row_list[i]
                if len(val) >= 10 and re.match(r'20\d{2}-\d{2}-\d{2}', val):
                    fecha_idx = i
                    try: 
                        fecha_obj = datetime.strptime(val[:10], '%Y-%m-%d')
                    except: 
                        continue
                    break
            
            # SI ENCONTRAMOS FECHA -> NUEVA FACTURA
            if fecha_idx != -1:
                # Si había una factura pendiente sin cerrar, la cerramos primero
                if imp_pendiente and pos_acumuladas:
                    print(f"      ⚠️ Cerrando factura anterior sin totales: {imp_pendiente['numero_importacion']}")
                
                # Buscar POs en las filas ANTERIORES (hacia arriba)
                pos_arriba = self._buscar_pos_en_rango(df, fila_inicio_bloque, idx)
                
                # Obtener datos de la factura
                col_A = row_list[fecha_idx + 1] if fecha_idx + 1 < len(row_list) else ""
                col_B = row_list[fecha_idx + 2] if fecha_idx + 2 < len(row_list) else ""
                
                # Distinguir proveedor y factura
                has_digit_A = any(c.isdigit() for c in col_A)
                if len(col_A) < 25 and has_digit_A and ("-" in col_A or len(col_A) > 3):
                    proveedor = "GENERICO"
                    factura = col_A
                    desc_idx = fecha_idx + 2
                else:
                    proveedor = col_A if col_A else "GENERICO"
                    factura = col_B
                    desc_idx = fecha_idx + 3
                
                if not factura or len(factura) < 2:
                    continue
                
                # Iniciar nueva factura
                imp_pendiente = {
                    'numero_importacion': factura[:40],
                    'fecha_creacion': fecha_obj,
                    'proveedor': proveedor,
                    'descripcion': row_list[desc_idx] if desc_idx < len(row_list) else "",
                    'key': factura.replace(" ", ""),
                    'fila_inicio': idx
                }
                base_costos_pendiente = desc_idx + 1
                
                # Inicializar POs con las encontradas arriba
                pos_acumuladas = pos_arriba.copy()
                
                # También buscar POs en la misma fila de la fecha
                pos_fila_actual = self.extract_po_from_text(fila_texto)
                pos_acumuladas.extend(pos_fila_actual)
                
                print(f"\n   📄 Nueva factura detectada en fila {idx}:")
                print(f"      - Número: {factura[:40]}")
                print(f"      - Proveedor: {proveedor}")
                print(f"      - POs encontradas (arriba + actual): {list(set(pos_acumuladas))}")
                
                fila_inicio_bloque = idx + 1  # Para la próxima factura

            # 3. SI ESTAMOS DENTRO DE UNA FACTURA
            if imp_pendiente:
                # Buscar POs en esta fila
                pos_fila = self.extract_po_from_text(fila_texto)
                if pos_fila:
                    pos_acumuladas.extend(pos_fila)
                    print(f"      + Fila {idx}: Agregadas POs: {pos_fila}")

                # BUSCAR FILA DE TOTALES
                if "OK" not in fila_texto and "TOTAL" not in fila_texto.upper():
                    base = base_costos_pendiente
                    fob = self._safe_float(row_list[base]) if base < len(row_list) else 0.0
                    
                    # Si hay FOB > 0 y no es una fila de item (sin OK)
                    if fob > 0:
                        def get_val(offset):
                            if base + offset < len(row_list):
                                return self._safe_float(row_list[base + offset])
                            return 0.0

                        otros_v = get_val(1)
                        agencia = get_val(2)
                        locales = get_val(3)
                        col_var = get_val(4)
                        aduana  = get_val(5)

                        f_val = col_var if es_seccion_flete else 0.0
                        s_val = 0.0 if es_seccion_flete else col_var

                        # Eliminar duplicados de POs
                        pos_unicas = list(set(pos_acumuladas))
                        
                        # Si no encontramos POs específicas, buscar en todo el bloque
                        if not pos_unicas:
                            print(f"      ⚠️ Sin POs específicas, buscando en rango amplio...")
                            pos_unicas = self._buscar_pos_en_rango(
                                df, 
                                imp_pendiente.get('fila_inicio', idx) - 10, 
                                idx + 5
                            )
                        
                        nueva_imp = {
                            'key': imp_pendiente['key'],
                            'numero_importacion': imp_pendiente['numero_importacion'],
                            'fecha_creacion': imp_pendiente['fecha_creacion'],
                            'descripcion': f"Importación {imp_pendiente['proveedor']} - {imp_pendiente['numero_importacion']}",
                            'notas': f"Prov: {imp_pendiente['proveedor']}. Desc: {imp_pendiente['descripcion'][:50]}...",
                            'pos_found': pos_unicas,
                            'created_by': 1,
                            'costos': {
                                'fob': fob,
                                'insurance': s_val,
                                'freight': f_val,
                                'cif': fob + s_val + f_val,
                                'customs': aduana,
                                'agency': agencia,
                                'other': otros_v + locales,
                                'storage': 0.0,
                                'total_taxes': aduana,
                                'total_customs_expenses': agencia + otros_v + locales
                            }
                        }
                        
                        importaciones.append(nueva_imp)
                        pos_por_importacion[imp_pendiente['key']] = pos_unicas
                        
                        print(f"\n   ✅ Factura cerrada: {imp_pendiente['numero_importacion']}")
                        print(f"      - FOB: ${fob:,.2f}")
                        print(f"      - POs vinculadas: {pos_unicas}")
                        
                        imp_pendiente = None
                        pos_acumuladas = []
        
        # Resumen final
        print(f"\n   {'='*50}")
        print(f"   📊 RESUMEN DE EXTRACCIÓN:")
        print(f"      - Importaciones encontradas: {len(importaciones)}")
        total_pos = sum(len(imp['pos_found']) for imp in importaciones)
        print(f"      - Total POs vinculadas: {total_pos}")
        
        if importaciones:
            print(f"\n   📋 Detalle:")
            for imp in importaciones[:5]:  # Mostrar primeras 5
                print(f"      - {imp['numero_importacion']}: {len(imp['pos_found'])} POs -> {imp['pos_found'][:3]}...")
        print(f"   {'='*50}\n")
        
        return importaciones, pos_por_importacion
    
    def process_and_save_to_db(self, excel_content: bytes, file_name: str) -> Dict:
        """Procesa el archivo y guarda en la base de datos."""
        try:
            print(f"\n{'='*60}")
            print(f"📚 INICIANDO PROCESAMIENTO: {file_name}")
            print(f"{'='*60}")
            
            # Paso 1: Cargar archivo
            print("\n[PASO 1] Cargando archivo...")
            sheets_data = self.load_file(excel_content, file_name)
            
            if not sheets_data: 
                return {'success': False, 'message': "No se pudo leer el archivo Excel."}
            
            # Paso 2: Obtener la primera hoja
            first_sheet_name = list(sheets_data.keys())[0]
            df = sheets_data[first_sheet_name]
            print(f"   📊 Hoja seleccionada: '{first_sheet_name}' con {len(df)} filas")
            
            # Paso 3: Extraer información
            print("\n[PASO 2] Extrayendo información de importaciones...")
            importaciones, pos_por_importacion = self.extract_importacion_info(df)
            
            if not importaciones:
                return {'success': False, 'message': "No se encontraron importaciones válidas."}
            
            print(f"   ✅ Se encontraron {len(importaciones)} importaciones")
            
            # Paso 4: Conectar a BD
            print("\n[PASO 3] Conectando a base de datos...")
            try:
                if hasattr(self.db, 'connection'): 
                    conn = self.db.connection
                else: 
                    conn = self.db
                    
                if hasattr(conn, 'is_connected'):
                    if not conn.is_connected(): 
                        print("   🔄 Reconectando...")
                        conn.reconnect(attempts=3, delay=2)
                        
                cursor = conn.cursor()
                print("   ✅ Conexión establecida")
            except Exception as e:
                return {'success': False, 'message': f"Error conectando a BD: {str(e)}"}

            # Paso 5: Insertar datos
            print(f"\n[PASO 4] Insertando {len(importaciones)} registros...")
            inserted = 0
            pos_creadas = 0
            pos_vinculadas = 0
            errors = []
            
            for i, imp in enumerate(importaciones):
                if i % 10 == 0:
                    print(f"   Procesando {i+1}/{len(importaciones)}...")
                    
                try:
                    # 1. GESTIÓN DE LA IMPORTACIÓN
                    cursor.execute(
                        "SELECT id FROM importaciones WHERE numero_importacion = %s", 
                        (imp['numero_importacion'],)
                    )
                    exist = cursor.fetchone()
                    
                    if exist:
                        imp_id = exist[0]
                        print(f"      ℹ️ Importación {imp['numero_importacion']} ya existe (ID: {imp_id})")
                        self.guardar_costos_en_bd(imp)
                    else:
                        costs = imp['costos']
                        total_gastos = costs['customs'] + costs['agency'] + costs['other'] + costs['insurance']
                        total_costo = costs['fob'] + total_gastos
                        
                        sql_imp = """
                            INSERT INTO importaciones 
                            (numero_importacion, descripcion, fecha_creacion, estado, notas, created_by,
                             total_fob_importacion, total_gastos_importacion, total_costo_importacion) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(sql_imp, (
                            imp['numero_importacion'], imp['descripcion'], imp['fecha_creacion'], 
                            'completada', imp['notas'], 1,
                            costs['fob'], total_gastos, total_costo
                        ))
                        imp_id = cursor.lastrowid
                        inserted += 1

                        # Crear DUA
                        dua_num = f"{imp['numero_importacion']}"[:50]
                        sql_dua = """
                            INSERT INTO dua_documents 
                            (importacion_id, dua_number, registration_date, 
                             fob_value_usd, insurance_usd, freight_usd, cif_value_usd,
                             customs_fees, agency_fees, other_customs_expenses,
                             total_taxes, total_customs_expenses,
                             status, created_by)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'registered', 1)
                        """
                        cursor.execute(sql_dua, (
                            imp_id, dua_num, imp['fecha_creacion'],
                            costs['fob'], costs['insurance'], costs['freight'], costs['cif'],
                            costs['customs'], costs['agency'], costs['other'],
                            costs['total_taxes'], costs['total_customs_expenses']
                        ))

                    # 2. GESTIÓN DE POs
                    # Limpiar vínculos previos
                    cursor.execute("DELETE FROM importacion_pos WHERE importacion_id = %s", (imp_id,))
                    
                    if imp['pos_found']:
                        print(f"      🔗 Procesando {len(imp['pos_found'])} POs para {imp['numero_importacion']}...")
                        
                        for po_number in imp['pos_found']:
                            cursor.execute("SELECT id FROM purchase_orders WHERE po_number = %s", (po_number,))
                            po_exist = cursor.fetchone()
                            
                            if po_exist:
                                po_id = po_exist[0]
                            else:
                                # Crear PO nueva
                                sql_po = """
                                    INSERT INTO purchase_orders 
                                    (po_number, supplier_id, order_date, incoterm, currency_id, 
                                     status, created_by, exchange_rate, total_fob) 
                                    VALUES (%s, 1, %s, 'CIF', 1, 'confirmada', 1, 3.75, 0.00)
                                """
                                cursor.execute(sql_po, (po_number, imp['fecha_creacion']))
                                po_id = cursor.lastrowid
                                pos_creadas += 1
                                print(f"         ➕ PO creada: {po_number} (ID: {po_id})")
                            
                            # Vincular
                            cursor.execute(
                                "INSERT INTO importacion_pos (importacion_id, po_id) VALUES (%s, %s)", 
                                (imp_id, po_id)
                            )
                            pos_vinculadas += 1
                    else:
                        print(f"      ⚠️ Sin POs para {imp['numero_importacion']}")
                            
                except Exception as e:
                    error_msg = f"Error en {imp.get('numero_importacion', 'Desc')}: {str(e)}"
                    errors.append(error_msg)
                    print(f"      ❌ {error_msg}")
                    continue
            
            # Commit
            print("\n[PASO 5] Guardando cambios...")
            conn.commit()
            cursor.close()
            
            print(f"\n{'='*60}")
            print(f"✅ PROCESO COMPLETADO")
            print(f"   - Importaciones insertadas: {inserted}")
            print(f"   - POs creadas: {pos_creadas}")
            print(f"   - POs vinculadas: {pos_vinculadas}")
            print(f"   - Errores: {len(errors)}")
            print(f"{'='*60}\n")

            return {
                'success': True, 
                'message': f"Procesadas {len(importaciones)} importaciones, {pos_vinculadas} POs vinculadas.",
                'importaciones_insertadas': inserted,
                'pos_creadas': pos_creadas,
                'pos_vinculadas': pos_vinculadas,
                'errors': errors
            }

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"\n❌ ERROR CRÍTICO:\n{error_detail}")
            return {'success': False, 'message': f"Error crítico: {str(e)}"}
        
    def process_details_phase(self, excel_content: bytes, conn) -> int:
        """Fase 2: Procesar detalles de productos."""
        print("   ⚠️ process_details_phase no implementado aún")
        return 0

    def guardar_costos_en_bd(self, datos_importacion):
        """Escribe los costos extraídos en la base de datos"""
        try:
            numero_importacion = datos_importacion.get('numero_importacion')
            costos = datos_importacion.get('costos', {})
            
            if not numero_importacion: 
                return False

            query = """
                UPDATE dua_documents d
                JOIN importaciones i ON d.importacion_id = i.id
                SET 
                    d.freight_usd = %s,
                    d.insurance_usd = %s,
                    d.customs_fees = %s,
                    d.agency_fees = %s,
                    d.other_customs_expenses = %s,
                    d.updated_at = NOW()
                WHERE i.numero_importacion = %s
            """
            
            params = (
                costos.get('freight', 0),
                costos.get('insurance', 0),
                costos.get('customs', 0),
                costos.get('agency', 0),
                costos.get('other', 0),
                numero_importacion
            )
            
            self.db.execute_query(query, params, fetch=False)
            return True
        except Exception as e:
            print(f"❌ Error guardando {datos_importacion.get('numero_importacion')}: {e}")
            return False

    def process_all_sheets(self, excel_content: bytes, file_name: str) -> Tuple[List[Dict], Dict]:
        """Procesa todas las hojas del archivo."""
        try:
            sheets_data = self.load_file(excel_content, file_name)
            
            all_importaciones = []
            all_pos_por_importacion = {}
            
            for sheet_name, df in sheets_data.items():
                print(f"   - Analizando hoja: {sheet_name}")
                importaciones, pos_por_importacion = self.extract_importacion_info(df)
                
                for imp in importaciones:
                    key = imp['key']
                    if key not in [i['key'] for i in all_importaciones]:
                        all_importaciones.append(imp)
                        all_pos_por_importacion[key] = pos_por_importacion.get(key, [])
                
            self.importaciones = all_importaciones
            self.pos_por_importacion = all_pos_por_importacion
            
            return self.importaciones, self.pos_por_importacion
            
        except Exception as e:
            print(f"Error procesando hojas: {str(e)}")
            raise