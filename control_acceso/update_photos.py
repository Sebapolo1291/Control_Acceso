
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
        reader = csv.DictReader(f, delimiter='\t')  # Tab-separated
        debug_count = 0
        for row in reader:
            if debug_count < 5:
                print('DEBUG ROW:', row)
                debug_count += 1
            dni_csv = row.get('dni')
            photo_field = row.get('photo')
            if not dni_csv or not photo_field:
                continue
            try:
                # Remove data:image/jpeg;base64, if present
                if photo_field.startswith('data:image'):
                    photo_b64 = photo_field.split(',', 1)[1]
                else:
                    photo_b64 = photo_field
                photo_bin = base64.b64decode(photo_b64)
                # Normalize DNI for comparison
                dni_csv_clean = str(dni_csv).strip().lstrip('0')
                # Buscar coincidencias de DNI en la base (como string, sin ceros a la izquierda)
                persons = Person.objects.filter(dni=int(dni_csv_clean))
                if persons.exists():
                    for obj in persons:
                        obj.photo = photo_bin
                        obj.save(update_fields=['photo'])
                        updated += 1
                else:
                    not_found.append(dni_csv)
            except Exception as e:
                errors.append({'dni': dni_csv, 'error': str(e)})
    print(f"Photo update finished. Updated: {updated}, Errors: {len(errors)}, Not found: {len(not_found)}")
    if not_found:
        print("DNIs not found in DB:")
        print(not_found[:20])  # Show only first 20 for brevity
    if errors:
        print("Errores:")
        for err in errors:
            print(err)

if __name__ == '__main__':
    main()
