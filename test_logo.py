#!/usr/bin/env python3
import os
import base64

def test_logo_paths():
    """Prueba diferentes rutas para encontrar el logo"""
    
    # Ruta 1: Desde el directorio actual
    logo_path1 = os.path.join('control_acceso', 'control_acceso', 'static', 'logo.png')
    
    # Ruta 2: Desde admin_views.py
    admin_views_dir = os.path.join('control_acceso', 'control_acceso')
    logo_path2 = os.path.join(admin_views_dir, 'static', 'logo.png')
    
    # Ruta 3: Alternativa
    logo_path3 = os.path.join(admin_views_dir, '..', 'static', 'logo.png')
    
    paths = [
        ('Ruta 1 (desde raíz)', logo_path1),
        ('Ruta 2 (desde admin_views)', logo_path2),
        ('Ruta 3 (alternativa)', logo_path3)
    ]
    
    for name, path in paths:
        print(f"\n{name}: {path}")
        if os.path.exists(path):
            print(f"✓ Archivo encontrado")
            try:
                with open(path, 'rb') as f:
                    logo_data = f.read()
                    logo_base64 = base64.b64encode(logo_data).decode('utf-8')
                    print(f"✓ Logo convertido a base64 exitosamente ({len(logo_base64)} caracteres)")
                    return path, logo_base64
            except Exception as e:
                print(f"✗ Error al leer el archivo: {e}")
        else:
            print(f"✗ Archivo no encontrado")
    
    return None, None

if __name__ == "__main__":
    print("Probando rutas del logo...")
    path, base64_data = test_logo_paths()
    
    if path:
        print(f"\n🎉 Logo encontrado en: {path}")
        print(f"Primeros 100 caracteres del base64: {base64_data[:100]}...")
    else:
        print("\n❌ No se pudo encontrar el logo en ninguna ruta")