import os
import django
import csv
from datetime import datetime

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "control_acceso.settings")
django.setup()

from django.contrib.auth.models import User

CSV_PATH = 'C:\\Users\\angel.steklein\\Desktop\\users.csv'  # Path to your CSV file

def create_users_from_csv(csv_path):
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            email = row.get('email')
            username = row.get('username')

            first_name = row.get('name', '')
            split = str(first_name).split(' ')

            last_name = split[-1]
            first_name = split[0:-1]

            updated_at = str(row['updated_at']) + ":00"

            created_at = str(row['created_at']) + ":00"
            if updated_at == '00-00-0000 00:00:00':
                updated_at = '01-01-1970 00:00:00'
            if created_at == '00-00-0000 00:00:00':
                created_at = '01-01-1970 00:00:00'

            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password='12345678',
                    is_active=True,
                    is_staff=False
                )

                user.last_login = datetime.strptime(updated_at, '%d-%m-%Y %H:%M:%S')
                user.date_joined = datetime.strptime(created_at, '%d-%m-%Y %H:%M:%S')

                user.save()
                print(f"✅ Created user: {email}")
            else:
                print(f"⏩ User already exists: {email}")

if __name__ == "__main__":
    create_users_from_csv(CSV_PATH)

