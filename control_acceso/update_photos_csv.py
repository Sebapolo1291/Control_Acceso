import os
import django
import csv
import base64

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'control_acceso.settings')
django.setup()

from control_acceso.models import Person

# Path to personitas.csv (adjust if needed)
CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'personitas.csv')

def main():
    updated = 0
    errors = []
    not_found = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        header = next(reader, None)
        for row in reader:
            if len(row) < 2:
                continue
            dni = row[0].strip().lstrip('0')
            photo_field = row[1].strip()
            if not dni or not photo_field:
                continue
            try:
                if photo_field.startswith('data:image'):
                    photo_b64 = photo_field.split(',', 1)[1]
                else:
                    photo_b64 = photo_field
                photo_bin = base64.b64decode(photo_b64)
                persons = Person.objects.filter(dni=int(dni))
                if persons.exists():
                    for obj in persons:
                        obj.photo = photo_bin
                        obj.save(update_fields=['photo'])
                        updated += 1
                else:
                    not_found.append(dni)
            except Exception as e:
                errors.append({'dni': dni, 'error': str(e)})
    print(f"Photo update finished. Updated: {updated}, Errors: {len(errors)}, Not found: {len(not_found)}")
    if not_found:
        print("DNIs not found in DB:")
        print(not_found[:20])
    if errors:
        print("Errores:")
        for err in errors:
            print(err)

if __name__ == '__main__':
    main()
