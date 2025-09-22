from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from control_acceso.models import Sede, Estructura, Person, UserProfile, Visit
from django.utils import timezone
import random
from datetime import datetime, timedelta, time


class Command(BaseCommand):
    help = 'Poblar la base de datos con datos ficticios para testing'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando población de datos ficticios...')
        
        # Crear superusuario
        self.create_superuser()
        
        # Crear sedes
        self.create_sedes()
        
        # Crear estructura organizativa
        self.create_estructura()
        
        # Crear usuarios y perfiles
        self.create_users()
        
        # Crear personas
        self.create_persons()
        
        # Crear algunas visitas de ejemplo
        self.create_visits()
        
        self.stdout.write(
            self.style.SUCCESS('Base de datos poblada exitosamente con datos ficticios!')
        )

    def create_superuser(self):
        """Crear superusuario administrador"""
        if not User.objects.filter(username='admin').exists():
            user = User.objects.create_superuser(
                username='admin',
                email='admin@controlacceso.com',
                password='admin123',
                first_name='Administrador',
                last_name='Sistema'
            )
            self.stdout.write(f'Superusuario creado: {user.username}')
        else:
            self.stdout.write('Superusuario ya existe')

    def create_sedes(self):
        """Crear sedes ficticias"""
        sedes_data = [
            {
                'nombre': 'Sede Central Buenos Aires',
                'direccion': 'Av. Rivadavia 1234, CABA'
            },
            {
                'nombre': 'Sede La Plata',
                'direccion': 'Calle 7 entre 47 y 48, La Plata'
            },
            {
                'nombre': 'Sede Mar del Plata',
                'direccion': 'Av. Independencia 2500, Mar del Plata'
            },
            {
                'nombre': 'Sede Córdoba',
                'direccion': 'Av. Colón 1500, Córdoba Capital'
            }
        ]
        
        created_sedes = []
        for sede_data in sedes_data:
            sede, created = Sede.objects.get_or_create(
                nombre=sede_data['nombre'],
                defaults=sede_data
            )
            if created:
                self.stdout.write(f'Sede creada: {sede.nombre}')
            created_sedes.append(sede)
        
        return created_sedes

    def create_estructura(self):
        """Crear estructura organizativa ficticia"""
        # Instituciones principales
        instituciones = [
            {'unidad_organica': 'Dirección General de Seguridad', 'siglas': 'DGS'},
            {'unidad_organica': 'Dirección de Recursos Humanos', 'siglas': 'DRH'},
            {'unidad_organica': 'Dirección de Tecnología', 'siglas': 'DT'},
            {'unidad_organica': 'Dirección Administrativa', 'siglas': 'DA'},
        ]
        
        # Crear instituciones
        instituciones_created = []
        for inst_data in instituciones:
            inst, created = Estructura.objects.get_or_create(
                siglas=inst_data['siglas'],
                defaults=inst_data
            )
            if created:
                self.stdout.write(f'Institución creada: {inst.unidad_organica}')
            instituciones_created.append(inst)
        
        # Áreas por institución
        areas_data = [
            # Áreas de DGS
            {'unidad_organica': 'Departamento de Control de Acceso', 'siglas': 'DCA', 'padre': 'DGS'},
            {'unidad_organica': 'Departamento de Vigilancia', 'siglas': 'DV', 'padre': 'DGS'},
            {'unidad_organica': 'Departamento de Investigaciones', 'siglas': 'DI', 'padre': 'DGS'},
            
            # Áreas de DRH
            {'unidad_organica': 'Departamento de Personal', 'siglas': 'DP', 'padre': 'DRH'},
            {'unidad_organica': 'Departamento de Capacitación', 'siglas': 'DC', 'padre': 'DRH'},
            
            # Áreas de DT
            {'unidad_organica': 'Departamento de Sistemas', 'siglas': 'DS', 'padre': 'DT'},
            {'unidad_organica': 'Departamento de Comunicaciones', 'siglas': 'DCOM', 'padre': 'DT'},
            
            # Áreas de DA
            {'unidad_organica': 'Departamento de Compras', 'siglas': 'DCOMP', 'padre': 'DA'},
            {'unidad_organica': 'Departamento de Contabilidad', 'siglas': 'DCONT', 'padre': 'DA'},
        ]
        
        areas_created = []
        for area_data in areas_data:
            area, created = Estructura.objects.get_or_create(
                siglas=area_data['siglas'],
                defaults=area_data
            )
            if created:
                self.stdout.write(f'Área creada: {area.unidad_organica}')
            areas_created.append(area)
        
        # Subáreas (algunas)
        subareas_data = [
            {'unidad_organica': 'Sección Turnos Matutinos', 'siglas': 'STM', 'padre': 'DCA'},
            {'unidad_organica': 'Sección Turnos Vespertinos', 'siglas': 'STV', 'padre': 'DCA'},
            {'unidad_organica': 'Sección Redes', 'siglas': 'SR', 'padre': 'DS'},
            {'unidad_organica': 'Sección Desarrollo', 'siglas': 'SD', 'padre': 'DS'},
        ]
        
        for subarea_data in subareas_data:
            subarea, created = Estructura.objects.get_or_create(
                siglas=subarea_data['siglas'],
                defaults=subarea_data
            )
            if created:
                self.stdout.write(f'Subárea creada: {subarea.unidad_organica}')

    def create_users(self):
        """Crear usuarios y perfiles ficticios"""
        sedes = list(Sede.objects.all())
        
        users_data = [
            {
                'username': 'operador1',
                'email': 'operador1@controlacceso.com',
                'password': 'operador123',
                'first_name': 'María',
                'last_name': 'González',
                'is_admin': False
            },
            {
                'username': 'operador2',
                'email': 'operador2@controlacceso.com',
                'password': 'operador123',
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'is_admin': False
            },
            {
                'username': 'supervisor',
                'email': 'supervisor@controlacceso.com',
                'password': 'super123',
                'first_name': 'Ana',
                'last_name': 'Rodríguez',
                'is_admin': True
            },
            {
                'username': 'jefe_sede',
                'email': 'jefe@controlacceso.com',
                'password': 'jefe123',
                'first_name': 'Carlos',
                'last_name': 'López',
                'is_admin': True
            }
        ]
        
        for i, user_data in enumerate(users_data):
            if not User.objects.filter(username=user_data['username']).exists():
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )
                
                # Crear perfil de usuario
                sede = sedes[i % len(sedes)] if sedes else None
                UserProfile.objects.create(
                    user=user,
                    sede=sede,
                    is_admin=user_data['is_admin']
                )
                
                self.stdout.write(f'Usuario creado: {user.username} - Sede: {sede.nombre if sede else "Sin sede"}')

    def create_persons(self):
        """Crear personas ficticias"""
        personas_data = [
            {
                'nombre': 'Roberto',
                'apellido': 'Martínez',
                'dni': 12345678,
                'telefono': '1123456789',
                'email': 'roberto.martinez@email.com',
                'tarjetavisita': 'V001'
            },
            {
                'nombre': 'Laura',
                'apellido': 'Fernández',
                'dni': 23456789,
                'telefono': '1134567890',
                'email': 'laura.fernandez@email.com',
                'tarjetavisita': 'V002'
            },
            {
                'nombre': 'Miguel',
                'apellido': 'Sánchez',
                'dni': 34567890,
                'telefono': '1145678901',
                'email': 'miguel.sanchez@email.com',
                'tarjetavisita': 'V003'
            },
            {
                'nombre': 'Patricia',
                'apellido': 'Ruiz',
                'dni': 45678901,
                'telefono': '1156789012',
                'email': 'patricia.ruiz@email.com',
                'tarjetavisita': 'V004'
            },
            {
                'nombre': 'Diego',
                'apellido': 'Morales',
                'dni': 56789012,
                'telefono': '1167890123',
                'email': 'diego.morales@email.com',
                'tarjetavisita': 'V005'
            },
            {
                'nombre': 'Claudia',
                'apellido': 'Torres',
                'dni': 67890123,
                'telefono': '1178901234',
                'email': 'claudia.torres@email.com',
                'tarjetavisita': 'V006'
            },
            {
                'nombre': 'Andrés',
                'apellido': 'Vega',
                'dni': 78901234,
                'telefono': '1189012345',
                'email': 'andres.vega@email.com',
                'tarjetavisita': 'V007'
            },
            {
                'nombre': 'Silvia',
                'apellido': 'Castro',
                'dni': 89012345,
                'telefono': '1190123456',
                'email': 'silvia.castro@email.com',
                'tarjetavisita': 'V008'
            },
            {
                'nombre': 'Fernando',
                'apellido': 'Herrera',
                'dni': 90123456,
                'telefono': '1101234567',
                'email': 'fernando.herrera@email.com',
                'tarjetavisita': 'V009'
            },
            {
                'nombre': 'Gabriela',
                'apellido': 'Jiménez',
                'dni': 11234567,
                'telefono': '1112345678',
                'email': 'gabriela.jimenez@email.com',
                'tarjetavisita': 'V010'
            }
        ]
        
        for persona_data in personas_data:
            person, created = Person.objects.get_or_create(
                dni=persona_data['dni'],
                defaults=persona_data
            )
            if created:
                self.stdout.write(f'Persona creada: {person.get_full_name()}')

    def create_visits(self):
        """Crear visitas ficticias"""
        personas = list(Person.objects.all())
        sedes = list(Sede.objects.all())
        areas = list(Estructura.objects.filter(padre__isnull=False))  # Solo áreas, no instituciones
        usuarios = list(User.objects.filter(is_superuser=False))
        
        if not (personas and sedes and areas and usuarios):
            self.stdout.write('No hay suficientes datos para crear visitas')
            return
        
        # Crear visitas de los últimos 30 días
        base_date = timezone.now().date()
        
        for i in range(20):  # 20 visitas de ejemplo
            # Fecha aleatoria en los últimos 30 días
            days_ago = random.randint(0, 30)
            fecha = base_date - timedelta(days=days_ago)
            
            # Hora de entrada aleatoria entre 8:00 y 17:00
            hora_entrada = time(
                hour=random.randint(8, 17),
                minute=random.randint(0, 59)
            )
            
            # Decidir si la visita ya salió (80% de probabilidad si es de días anteriores)
            has_exit = days_ago > 0 and random.random() < 0.8
            
            fecha_salida = None
            hora_salida = None
            
            if has_exit:
                # Hora de salida entre 1-8 horas después de la entrada
                horas_duracion = random.randint(1, 8)
                hora_salida_datetime = datetime.combine(fecha, hora_entrada) + timedelta(hours=horas_duracion)
                
                if hora_salida_datetime.date() == fecha:
                    hora_salida = hora_salida_datetime.time()
                    fecha_salida = fecha
                else:
                    hora_salida = time(23, 59)
                    fecha_salida = fecha
            
            visit_data = {
                'person': random.choice(personas),
                'fecha': fecha,
                'hora_entrada': hora_entrada,
                'fecha_salida': fecha_salida,
                'hora_salida': hora_salida,
                'sede': random.choice(sedes),
                'area': random.choice(areas),
                'receptor_nombre': random.choice(['Carlos', 'Ana', 'Luis', 'María', 'José']),
                'receptor_apellido': random.choice(['García', 'López', 'Martín', 'Díaz', 'Hernández']),
                'observaciones': random.choice([
                    'Reunión de trabajo',
                    'Entrega de documentos',
                    'Consulta técnica',
                    'Visita institucional',
                    'Capacitación',
                    None
                ]),
                'created_by': random.choice(usuarios)
            }
            
            visit = Visit.objects.create(**visit_data)
            status = "ACTIVA" if not visit.hora_salida else "FINALIZADA"
            self.stdout.write(f'Visita creada: {visit.person.get_full_name()} - {visit.fecha} ({status})')