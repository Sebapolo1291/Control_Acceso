import os
import django
import json
import base64

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'control_acceso.settings')
django.setup()

from control_acceso.models import Person

# Path to persons.json (adjust if needed)
JSON_PATH = os.path.join(os.path.dirname(__file__), '..', 'persons.json')

def main():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        persons = json.load(f)

    created = 0
    updated = 0
    for p in persons:
        dni = p.get('dni')
        if not dni:
            continue
        defaults = {
            'nombre': p.get('nombre'),
            'apellido': p.get('apellido'),
            'telefono': p.get('telefono'),
            'email': p.get('email'),
            'tarjetavisita': '1',
            'observaciones': p.get('observaciones'),
        }
        # Handle base64 photo if present
        photo_b64 = p.get('photo')
        if photo_b64:
            try:
                defaults['photo'] = base64.b64decode(photo_b64)
            except Exception:
                defaults['photo'] = None
        else:
            defaults['photo'] = None
        obj, created_flag = Person.objects.update_or_create(
            dni=dni,
            defaults=defaults
        )
        if created_flag:
            created += 1
        else:
            updated += 1
    print(f"Import finished. Created: {created}, Updated: {updated}")

if __name__ == '__main__':
    main()
