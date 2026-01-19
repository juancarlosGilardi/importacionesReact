# diagnostic_ocr.py
import subprocess
import os
import sys

print("=== DIAGNÓSTICO TESSERACT OCR ===")
print(f"Python: {sys.version}")
print(f"Directorio actual: {os.getcwd()}")

# 1. Verificar PATH
print("\n=== VARIABLE PATH ===")
paths = os.environ.get('PATH', '').split(';')
for path in paths[:10]:  # Mostrar primeros 10
    if 'tesseract' in path.lower() or 'Tesseract-OCR' in path:
        print(f"  📍 {path}")

# 2. Buscar tesseract.exe
print("\n=== BUSCANDO TESSERACT.EXE ===")
common_paths = [
    r"C:\Program Files\Tesseract-OCR",
    r"C:\Program Files (x86)\Tesseract-OCR",
    os.path.join(os.environ.get('ProgramFiles', ''), 'Tesseract-OCR'),
    os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'Tesseract-OCR'),
    r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR".format(os.getlogin()),
]

for path in common_paths:
    exe_path = os.path.join(path, 'tesseract.exe')
    if os.path.exists(exe_path):
        print(f"✅ ENCONTRADO: {exe_path}")
        
        # Probar ejecución
        try:
            result = subprocess.run([exe_path, '--version'], 
                                  capture_output=True, text=True)
            print(f"  Versión: {result.stdout.split('\\n')[0]}")
        except Exception as e:
            print(f"  Error ejecutando: {e}")
    else:
        print(f"❌ No encontrado: {exe_path}")

# 3. Intentar ejecutar directamente
print("\n=== PRUEBA DIRECTA ===")
try:
    result = subprocess.run(['tesseract', '--version'], 
                          capture_output=True, text=True, shell=True)
    print(f"✅ Tesseract ejecutado exitosamente")
    print(f"Salida: {result.stdout[:100]}")
except Exception as e:
    print(f"❌ Error: {e}")