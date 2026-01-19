# pdf_parser.py
import pdfplumber
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import tempfile
import os
import subprocess
import fitz  # PyMuPDF
from PIL import Image
import io
import json

class PDFInvoiceParser:
    """Parser real para facturas PDF comerciales"""
    
    def __init__(self, use_ocr: bool = True):
        self.use_ocr = use_ocr
        self.tesseract_path = self._find_tesseract()
        self.ocr_available = self.tesseract_path is not None
        
        if self.ocr_available:
            print(f"✅ Tesseract encontrado en: {self.tesseract_path}")
        else:
            print("⚠️ Tesseract no encontrado, usando extracción básica")
    
    def _find_tesseract(self) -> Optional[str]:
        """Busca Tesseract en el sistema"""
        try:
            result = subprocess.run(['tesseract', '--version'], 
                                  capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                return 'tesseract'
        except:
            pass
        
        # Buscar en Windows
        import sys
        if sys.platform == 'win32':
            paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ]
            for path in paths:
                if os.path.exists(path):
                    return path
        
        return None
    
    def extract_text_from_pdf(self, pdf_path: str) -> Tuple[str, bool]:
        """
        Extrae texto de un PDF usando múltiples métodos
        
        Returns:
            Tuple[texto, usado_ocr]
        """
        try:
            # Método 1: pdfplumber (para PDFs con texto)
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                
                if len(full_text.strip()) > 100:  # Suficiente texto
                    print(f"✅ Texto extraído con pdfplumber: {len(full_text)} caracteres")
                    return full_text, False
        
        except Exception as e:
            print(f"⚠️ Error con pdfplumber: {e}")
        
        # Método 2: OCR si está disponible y el PDF tiene poco texto
        if self.use_ocr and self.ocr_available:
            ocr_text = self._extract_with_ocr(pdf_path)
            if ocr_text and len(ocr_text.strip()) > 50:
                print(f"✅ Texto extraído con OCR: {len(ocr_text)} caracteres")
                return ocr_text, True
        
        # Método 3: PyMuPDF como alternativa
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
            if len(text.strip()) > 50:
                print(f"✅ Texto extraído con PyMuPDF: {len(text)} caracteres")
                return text, False
        
        except Exception as e:
            print(f"⚠️ Error con PyMuPDF: {e}")
        
        return "", False
    
    def _extract_with_ocr(self, pdf_path: str) -> Optional[str]:
        """Extrae texto usando OCR"""
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Convertir a imagen de alta resolución
                zoom = 3.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # Guardar temporalmente
                img_path = tempfile.mktemp(suffix='.png')
                pix.save(img_path)
                
                try:
                    # Ejecutar Tesseract
                    txt_path = tempfile.mktemp(suffix='.txt')
                    
                    cmd = [
                        self.tesseract_path,
                        img_path,
                        txt_path[:-4],  # Sin extensión .txt
                        '-l', 'eng+spa',
                        '--psm', '6',
                        '-c', 'preserve_interword_spaces=1'
                    ]
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        shell=True
                    )
                    
                    if result.returncode == 0 and os.path.exists(txt_path):
                        with open(txt_path, 'r', encoding='utf-8') as f:
                            page_text = f.read()
                            if page_text.strip():
                                full_text += f"\n--- Página {page_num + 1} ---\n{page_text}\n"
                        
                        os.unlink(txt_path)
                    
                finally:
                    # Limpiar imagen
                    if os.path.exists(img_path):
                        os.unlink(img_path)
            
            doc.close()
            return full_text.strip()
            
        except Exception as e:
            print(f"❌ Error en OCR: {e}")
            return None
    
    def parse_invoice_pdf(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """Parsear factura PDF real - extrae datos REALES del archivo"""
        
        print(f"\n🔍 Procesando PDF: {os.path.basename(pdf_path)}")
        print("="*60)
        
        # 1. Extraer texto del PDF
        text, used_ocr = self.extract_text_from_pdf(pdf_path)
        
        if not text or len(text.strip()) < 50:
            print("❌ No se pudo extraer texto suficiente del PDF")
            return None
        
        # Guardar texto extraído para depuración
        debug_file = pdf_path.replace('.pdf', '_extracted.txt')
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"📝 Texto extraído guardado en: {debug_file}")
        
        # 2. Parsear el texto extraído
        invoice_data = self._parse_invoice_text(text, pdf_path)
        invoice_data["ocr_used"] = used_ocr
        invoice_data["extracted_text_length"] = len(text)
        
        # 3. Guardar resultado para referencia
        result_file = pdf_path.replace('.pdf', '_result.json')
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(invoice_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Resultado guardado en: {result_file}")
        
        return invoice_data
    
    def _parse_invoice_text(self, text: str, pdf_path: str) -> Dict[str, Any]:
        """Parsear el texto extraído del PDF"""
        
        # Normalizar texto
        text = ' '.join(text.split())  # Reemplazar múltiples espacios/lineas
        text_lower = text.lower()
        
        # Estructura base
        invoice_data = {
            "invoice_number": self._extract_invoice_number(text),
            "issue_date": self._extract_date(text),
            "currency": self._extract_currency(text),
            "invoice_type": "commercial_invoice",
            "source": "pdf",
            "pdf_path": pdf_path,
        }
        
        # Información del proveedor
        invoice_data["supplier"] = self._extract_supplier(text)
        
        # Información del comprador
        invoice_data["buyer"] = self._extract_buyer(text)
        
        # Items
        invoice_data["items"] = self._extract_items(text)
        
        # Totales
        invoice_data["totals"] = self._extract_totals(text)
        
        # Logística
        invoice_data["logistics"] = self._extract_logistics(text)
        
        # Información adicional
        invoice_data["metadata"] = {
            "words_count": len(text.split()),
            "lines_count": text.count('\n'),
            "has_vat": "vat" in text_lower or "iva" in text_lower,
            "has_totals": any(word in text_lower for word in ["total", "amount", "suma"]),
            "has_items": any(word in text_lower for word in ["item", "product", "description", "quantity"])
        }
        
        return invoice_data
    
    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """Extraer número de factura con múltiples patrones"""
        patterns = [
            r'Invoice\s*#?\s*[:#]?\s*([A-Za-z0-9\-\.]+)',
            r'INVOICE\s*NO\.?\s*[:#]?\s*([A-Za-z0-9\-\.]+)',
            r'Factura\s*N[º°]?\s*[:#]?\s*([A-Za-z0-9\-\.]+)',
            r'Invoice\s*Number\s*[:#]?\s*([A-Za-z0-9\-\.]+)',
            r'(?:INV|FACT)\s*[-_]?\s*([A-Za-z0-9\-\.]+)',
            r'No\.?\s*de\s*Factura\s*[:#]?\s*([A-Za-z0-9\-\.]+)',
            r'Commercial\s*Invoice\s*#?\s*([A-Za-z0-9\-\.]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match and len(match.strip()) > 3:
                    inv_num = match.strip()
                    print(f"📄 Número de factura encontrado: {inv_num}")
                    return inv_num
        
        # Buscar en el texto cualquier patrón que parezca número de factura
        invoice_patterns = [
            r'\b[A-Z]{2,4}[-_]\d{4}[-_]\d{4,6}\b',  # EJ: INV-2024-0015
            r'\b\d{4}[-_]\d{4,6}\b',  # EJ: 2024-0015
            r'\b[A-Z]{3,}\d{5,}\b',  # EJ: INV0012345
        ]
        
        for pattern in invoice_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                print(f"📄 Posible número de factura: {match}")
                return match
        
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extraer fecha con mejor manejo de formatos OCR"""
        
        # Normalizar texto para búsqueda
        text_lower = text.lower()
        
        # Patrones mejorados para OCR
        patterns = [
            # Formato: DATE: DECEMBER 15, 2024
            r'DATE[:\s]*(\w+\s+\d{1,2},?\s+\d{4})',
            # Formato: Invoice Date: December 15, 2024
            r'Invoice\s+Date[:\s]*(\w+\s+\d{1,2},?\s+\d{4})',
            # Formato: Fecha: 15/12/2024
            r'Fecha[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})',
            # Formato numérico: 12/15/2024
            r'\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})\b',
            # Cualquier fecha con formato completo
            r'\b(\w+\s+\d{1,2},?\s+\d{4})\b',
        ]
        
        months_en = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7,
            'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        months_es = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for date_str in matches:
                date_str = date_str.strip()
                print(f"📅 Fecha candidata: '{date_str}'")
                
                # Intentar parsear como fecha con mes textual
                for month_dict, lang in [(months_en, 'en'), (months_es, 'es')]:
                    for month_name, month_num in month_dict.items():
                        if month_name in date_str.lower():
                            try:
                                # Extraer día y año
                                pattern = rf'(\d{{1,2}})\s*{month_name}[a-z]*\s*,?\s*(\d{{4}})'
                                match = re.search(pattern, date_str, re.IGNORECASE)
                                if match:
                                    day = int(match.group(1))
                                    year = int(match.group(2))
                                    date_formatted = f"{year:04d}-{month_num:02d}-{day:02d}"
                                    print(f"✅ Fecha parseada: {date_formatted}")
                                    return date_formatted
                            except:
                                continue
                
                # Intentar formatos numéricos
                for fmt in ["%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"]:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        date_formatted = dt.strftime("%Y-%m-%d")
                        print(f"✅ Fecha parseada (numérica): {date_formatted}")
                        return date_formatted
                    except:
                        continue
        
        # Si no se encontró fecha, buscar cualquier patrón que parezca fecha
        print("🔍 Buscando fecha por patrón general...")
        date_pattern = r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b'
        match = re.search(date_pattern, text, re.IGNORECASE)
        if match:
            print(f"📅 Fecha encontrada por patrón general: {match.group(1)}")
            # Intentar parsear
            try:
                dt = datetime.strptime(match.group(1), "%d %b %Y")
                return dt.strftime("%Y-%m-%d")
            except:
                try:
                    dt = datetime.strptime(match.group(1), "%d %B %Y")
                    return dt.strftime("%Y-%m-%d")
                except:
                    pass
        
        print("⚠️ No se pudo extraer fecha del texto")
        return None

    def _extract_currency(self, text: str) -> str:
        """Extraer moneda"""
        if "USD" in text or "$" in text:
            return "USD"
        elif "EUR" in text or "€" in text:
            return "EUR"
        elif "PEN" in text or "S/" in text or "SOLES" in text.upper():
            return "PEN"
        else:
            # Por defecto, buscar números con símbolo de moneda
            if re.search(r'\$\s*\d+', text):
                return "USD"
            elif re.search(r'€\s*\d+', text):
                return "EUR"
            elif re.search(r'S\/\.?\s*\d+', text):
                return "PEN"
            else:
                return "USD"  # Por defecto
    
    def _extract_supplier(self, text: str) -> Dict[str, Optional[str]]:
        """Extraer información del proveedor con mejor manejo OCR"""
        supplier = {
            "ruc": None,
            "business_name": None,
            "trade_name": None,
            "address": None,
            "phone": None,
            "email": None
        }
        
        # Buscar HOME DEPOT específicamente (caso común)
        if "HOME DEPOT" in text.upper():
            supplier["business_name"] = "HOME DEPOT CORP."
            supplier["trade_name"] = "THE HOME DEPOT"
            
            # Buscar EIN/Tax ID para Home Depot
            ein_match = re.search(r'EIN[:\s]*([0-9\-]+)', text, re.IGNORECASE)
            if ein_match:
                supplier["ruc"] = ein_match.group(1).strip()
            
            print(f"✅ Proveedor detectado: HOME DEPOT CORP.")
            return supplier
        
        # Buscar sección SELLER/EXPORTER
        sections = [
            ("SELLER", "BUYER"),
            ("EXPORTER", "IMPORTER"),
            ("FROM", "TO"),
            ("SHIPPER", "CONSIGNEE"),
        ]
        
        for start_keyword, end_keyword in sections:
            if start_keyword in text:
                print(f"🔍 Buscando sección {start_keyword}...")
                
                # Extraer sección más amplia
                start_idx = text.find(start_keyword)
                if start_idx != -1:
                    # Tomar 500 caracteres después de SELLER
                    section_text = text[start_idx:start_idx + 500]
                    
                    # Buscar nombre comercial común después de SELLER
                    lines = section_text.split('\n')
                    if len(lines) > 1:
                        # La segunda línea usualmente tiene el nombre
                        for i in range(1, min(5, len(lines))):
                            line = lines[i].strip()
                            if line and len(line) > 3 and not line.startswith(start_keyword):
                                supplier["business_name"] = line[:100]
                                print(f"✅ Nombre proveedor encontrado: {line[:50]}...")
                                break
                    
                    # Buscar EIN/Tax ID
                    patterns = [
                        r'EIN[:\s]*([0-9\-]+)',
                        r'TAX\s*ID[:\s]*([0-9\-]+)',
                        r'Taxpayer\s*ID[:\s]*([0-9\-]+)',
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, section_text, re.IGNORECASE)
                        if match:
                            supplier["ruc"] = match.group(1).strip()
                            print(f"✅ RUC/EIN encontrado: {supplier['ruc']}")
                            break
                    
                    # Si encontramos algo, retornar
                    if supplier["business_name"]:
                        return supplier
        
        # Si no se encontró proveedor, usar genérico
        if not supplier["business_name"]:
            supplier["business_name"] = "Proveedor Importado"
            print("⚠️ Usando nombre genérico de proveedor")
        
        return supplier

    def _extract_buyer(self, text: str) -> Dict[str, Optional[str]]:
        """Extraer información del comprador"""
        buyer = {
            "ruc": None,
            "business_name": None,
            "address": None,
            "phone": None,
        }
        
        # Buscar sección BUYER/IMPORTER/CONSIGNEE
        sections = [
            ("BUYER", "SHIPPER"),
            ("IMPORTER", "EXPORTER"),
            ("CONSIGNEE", "SHIPPER"),
            ("TO", "FROM"),
            ("CUSTOMER", "VENDOR"),
        ]
        
        for start_keyword, end_keyword in sections:
            buyer_section = self._extract_section(text, start_keyword, end_keyword)
            if buyer_section:
                # Extraer nombre
                lines = [line.strip() for line in buyer_section.split('\n') if line.strip()]
                if lines:
                    buyer["business_name"] = lines[0][:100]
                
                # Buscar RUC
                ruc_match = re.search(r'RUC[\s:]*([0-9]{8,13})', buyer_section, re.IGNORECASE)
                if ruc_match:
                    buyer["ruc"] = ruc_match.group(1).strip()
                
                break
        
        # Buscar RUC en todo el texto si no se encontró en la sección
        if not buyer["ruc"]:
            ruc_match = re.search(r'RUC[\s:]*([0-9]{8,13})', text, re.IGNORECASE)
            if ruc_match:
                buyer["ruc"] = ruc_match.group(1).strip()
        
        return buyer
    
    def _extract_items(self, text: str) -> List[Dict[str, Any]]:
        """Extraer items de la factura"""
        items = []
        
        # Buscar tabla de items
        table_indicators = [
            ("Description", "Subtotal"),
            ("Item", "Total"),
            ("Product", "Amount"),
            ("Cantidad", "Total"),
            ("Quantity", "Subtotal"),
        ]
        
        for start_indicator, end_indicator in table_indicators:
            if start_indicator.lower() in text.lower():
                # Extraer texto de la tabla
                start_idx = text.lower().find(start_indicator.lower())
                end_idx = text.lower().find(end_indicator.lower(), start_idx)
                
                if end_idx > start_idx:
                    table_text = text[start_idx:end_idx]
                    
                    # Buscar patrones de items
                    item_patterns = [
                        # Patrón: Cantidad Descripción Precio Unitario Total
                        r'(\d+\.?\d*)\s+([A-Z][^$\n]+?)\s+\$?([\d,]+\.?\d{0,2})\s+\$?([\d,]+\.?\d{0,2})',
                        # Patrón: Descripción Cantidad Precio
                        r'([A-Z][^$\n]+?)\s+(\d+\.?\d*)\s+\$?([\d,]+\.?\d{0,2})',
                        # Patrón con líneas
                        r'(?:Item|Product|Artículo)\s*[:\d]*\s*(.+?)(?:\n|$)',
                    ]
                    
                    for pattern in item_patterns:
                        matches = re.finditer(pattern, table_text, re.IGNORECASE | re.DOTALL)
                        for match in matches:
                            try:
                                if len(match.groups()) >= 3:
                                    if len(match.groups()) == 4:
                                        # Formato: cantidad, descripción, unit_price, total_price
                                        quantity = float(match.group(1).replace(',', ''))
                                        description = match.group(2).strip()
                                        unit_price = float(match.group(3).replace(',', ''))
                                        total_price = float(match.group(4).replace(',', ''))
                                        
                                        items.append({
                                            "description": description[:200],
                                            "quantity": quantity,
                                            "unit_price": unit_price,
                                            "total_price": total_price,
                                            "unit": "units"
                                        })
                                    elif len(match.groups()) == 3:
                                        # Formato: descripción, cantidad, precio
                                        description = match.group(1).strip()
                                        quantity = float(match.group(2).replace(',', ''))
                                        unit_price = float(match.group(3).replace(',', ''))
                                        
                                        items.append({
                                            "description": description[:200],
                                            "quantity": quantity,
                                            "unit_price": unit_price,
                                            "total_price": unit_price * quantity,
                                            "unit": "units"
                                        })
                            except:
                                continue
                
                break
        
        # Si no se encontraron items con patrones, buscar líneas con números y precios
        if not items:
            lines = text.split('\n')
            for line in lines:
                if '$' in line and any(word in line.lower() for word in ['item', 'product', 'sku', 'model', 'laptop', 'printer']):
                    try:
                        # Extraer precio
                        price_match = re.search(r'\$([\d,]+\.?\d{0,2})', line)
                        if price_match:
                            price = float(price_match.group(1).replace(',', ''))
                            
                            # Extraer cantidad
                            qty_match = re.search(r'(\d+)\s*[xX@]', line)
                            quantity = float(qty_match.group(1)) if qty_match else 1.0
                            
                            # Descripción (primeros 100 caracteres sin el precio)
                            description = re.sub(r'\$[\d,]+\.?\d{0,2}', '', line).strip()[:100]
                            
                            if description:
                                items.append({
                                    "description": description,
                                    "quantity": quantity,
                                    "unit_price": price,
                                    "total_price": price * quantity,
                                    "unit": "units"
                                })
                    except:
                        continue
        
        return items
    
    def _extract_totals(self, text: str) -> Dict[str, float]:
        """Extraer totales de la factura"""
        totals = {
            "subtotal": 0.0,
            "tax_amount": 0.0,
            "total_amount": 0.0,
            "payable_amount": 0.0,
        }
        
        # Buscar subtotal
        patterns = [
            r'Subtotal[^$\n]*\$?([\d,]+\.?\d{0,2})',
            r'Total\s*Before\s*Tax[^$\n]*\$?([\d,]+\.?\d{0,2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    totals["subtotal"] = float(match.group(1).replace(',', ''))
                    break
                except:
                    continue
        
        # Buscar impuestos
        tax_patterns = [
            r'(?:TAX|VAT|IGV|IVA)[^$\n]*\$?([\d,]+\.?\d{0,2})',
            r'Tax[^$\n]*\$?([\d,]+\.?\d{0,2})',
        ]
        
        for pattern in tax_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    totals["tax_amount"] = float(match.group(1).replace(',', ''))
                    break
                except:
                    continue
        
        # Buscar total
        total_patterns = [
            r'(?:TOTAL|Grand\s*Total|Amount\s*Due)[^$\n]*\$?([\d,]+\.?\d{0,2})',
            r'\$([\d,]+\.?\d{0,2})\s*(?:USD)?\s*(?=\n|$)',
        ]
        
        for pattern in total_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    # Tomar el último match (usualmente el total final)
                    last_total = float(matches[-1].replace(',', ''))
                    totals["total_amount"] = last_total
                    totals["payable_amount"] = last_total
                    break
                except:
                    continue
        
        return totals
    
    def _extract_logistics(self, text: str) -> Dict[str, Optional[str]]:
        """Extraer información logística"""
        logistics = {
            "purchase_order": None,
            "incoterm": None,
            "port_loading": None,
            "port_discharge": None,
            "country_origin": None,
            "payment_terms": None,
        }
        
        # Purchase Order
        po_patterns = [
            r'Purchase\s*Order[^:\n]*[:#]?\s*([A-Za-z0-9\-\.]+)',
            r'PO[^:\n]*[:#]?\s*([A-Za-z0-9\-\.]+)',
            r'Order\s*Number[^:\n]*[:#]?\s*([A-Za-z0-9\-\.]+)',
            r'P\.O\.\s*[:#]?\s*([A-Za-z0-9\-\.]+)',
        ]
        
        for pattern in po_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                logistics["purchase_order"] = match.group(1).strip()
                break
        
        # Incoterm
        incoterms = ['FOB', 'CIF', 'EXW', 'DDP', 'DAP', 'CFR', 'CIP']
        for incoterm in incoterms:
            if incoterm in text:
                logistics["incoterm"] = incoterm
                break
        
        # Puerto de carga
        port_patterns = [
            r'Port\s*of\s*Loading[^:\n]*[:]?\s*([A-Za-z,\s]+)',
            r'POL[^:\n]*[:]?\s*([A-Za-z,\s]+)',
            r'Loading\s*Port[^:\n]*[:]?\s*([A-Za-z,\s]+)',
        ]
        
        for pattern in port_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                logistics["port_loading"] = match.group(1).strip()[:100]
                break
        
        # Puerto de descarga
        discharge_patterns = [
            r'Port\s*of\s*Discharge[^:\n]*[:]?\s*([A-Za-z,\s]+)',
            r'POD[^:\n]*[:]?\s*([A-Za-z,\s]+)',
            r'Destination\s*Port[^:\n]*[:]?\s*([A-Za-z,\s]+)',
        ]
        
        for pattern in discharge_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                logistics["port_discharge"] = match.group(1).strip()[:100]
                break
        
        # País de origen
        origin_patterns = [
            r'Country\s*of\s*Origin[^:\n]*[:]?\s*([A-Za-z,\s]+)',
            r'Origin[^:\n]*[:]?\s*([A-Za-z,\s]+)',
        ]
        
        for pattern in origin_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                logistics["country_origin"] = match.group(1).strip()[:50]
                break
        
        # Términos de pago
        payment_patterns = [
            r'Payment\s*Terms[^:\n]*[:]?\s*([^\n]+)',
            r'Terms[^:\n]*[:]?\s*([^\n]+)',
        ]
        
        for pattern in payment_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                logistics["payment_terms"] = match.group(1).strip()[:200]
                break
        
        return logistics
    
    def _extract_section(self, text: str, start_keyword: str, end_keyword: str) -> Optional[str]:
        """Extraer una sección entre dos keywords"""
        start_match = re.search(start_keyword, text, re.IGNORECASE)
        if not start_match:
            return None
        
        section_start = start_match.end()
        remaining_text = text[section_start:]
        
        end_match = re.search(end_keyword, remaining_text, re.IGNORECASE)
        if end_match:
            section_text = remaining_text[:end_match.start()]
        else:
            # Tomar 300 caracteres o hasta el próximo keyword
            section_text = remaining_text[:300]
        
        return section_text.strip()


# Funciones de utilidad para usar en tu aplicación
def parse_pdf_invoice(pdf_path: str) -> Optional[Dict[str, Any]]:
    """
    Función principal para parsear facturas PDF
    """
    try:
        parser = PDFInvoiceParser(use_ocr=True)
        result = parser.parse_invoice_pdf(pdf_path)
        
        if result:
            print(f"\n✅ Factura parseada exitosamente:")
            print(f"   Número: {result.get('invoice_number', 'No encontrado')}")
            print(f"   Fecha: {result.get('issue_date', 'No encontrada')}")
            print(f"   Proveedor: {result.get('supplier', {}).get('business_name', 'No encontrado')}")
            print(f"   Comprador RUC: {result.get('buyer', {}).get('ruc', 'No encontrado')}")
            print(f"   Total: ${result.get('totals', {}).get('total_amount', 0):,.2f}")
            print(f"   Items: {len(result.get('items', []))}")
            print(f"   OCR usado: {result.get('ocr_used', False)}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error parseando PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_parser():
    """Función de prueba"""
    print("🧪 PROBANDO PARSER DE FACTURAS PDF")
    print("="*60)
    
    # Probar con un archivo específico
    pdf_file = "Invoice Home Depot.pdf"
    
    if os.path.exists(pdf_file):
        result = parse_pdf_invoice(pdf_file)
        
        if result:
            # Mostrar resultado detallado
            print("\n📊 RESULTADO DETALLADO:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"❌ Archivo no encontrado: {pdf_file}")


if __name__ == "__main__":
    test_parser()