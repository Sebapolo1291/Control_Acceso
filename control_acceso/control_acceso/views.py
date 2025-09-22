from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User

# Vista de detalle de persona
@login_required
@user_passes_test(lambda u: u.is_superuser or (hasattr(u, 'profile') and u.profile.is_admin))
def person_detail(request, person_id):
    person = get_object_or_404(Person, id=person_id)
    return render(request, 'person_detail.html', {'person': person})

# Vista de edición de persona
@login_required
@user_passes_test(lambda u: u.is_superuser or (hasattr(u, 'profile') and u.profile.is_admin))
def person_edit(request, person_id):
    person = get_object_or_404(Person, id=person_id)
    if request.method == 'POST':
        post_data = request.POST.copy()
        photo_file = request.FILES.get('photo_data_url')
        if photo_file and photo_file.size > 0:
            photo_bytes = photo_file.read()
            post_data['photo_data_url'] = ''  # No usar el campo oculto, solo para creacion
        form = PersonForm(post_data, instance=person)
        if form.is_valid():
            if photo_file and photo_file.size > 0:
                person.photo = photo_bytes
            form.save()
            return redirect('person_detail', person_id=person.id)
    else:
        form = PersonForm(instance=person)
    return render(request, 'person_edit.html', {'form': form, 'person': person})
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test

# Vista para listar personas solo para admin
@login_required
@user_passes_test(lambda u: u.is_superuser or (hasattr(u, 'profile') and u.profile.is_admin))
def person_list(request):
    nombre = request.GET.get('nombre', '').strip()
    apellido = request.GET.get('apellido', '').strip()
    dni = request.GET.get('dni', '').strip()
    tarjetavisita = request.GET.get('tarjetavisita', '').strip()

    persons = Person.objects.all()
    if nombre:
        persons = persons.filter(nombre__icontains=nombre)
    if apellido:
        persons = persons.filter(apellido__icontains=apellido)
    if dni:
        persons = persons.filter(dni__icontains=dni)
    if tarjetavisita:
        persons = persons.filter(tarjetavisita__icontains=tarjetavisita)

    persons = persons.order_by('apellido', 'nombre')
    paginator = Paginator(persons, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Para el template: solo se pasan los filtros que aplican a personas
    filtros = {
        'nombre': nombre,
        'apellido': apellido,
        'dni': dni,
        'tarjetavisita': tarjetavisita,
    }

    return render(request, 'person_list.html', {'persons': page_obj, 'filtros': filtros})
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from .models import Visit, Person, Sede, Estructura
from .forms import VisitForm, PersonForm
import base64
from django.core.files.base import ContentFile
from datetime import date

from django.db.models import Max
from django.utils import timezone

def home(request):
    """Vista para la página principal"""
    user_sede = None
    if hasattr(request.user, 'profile'):
        user_sede = request.user.profile.sede
    
    # Filtros base para visitas
    visits_queryset = Visit.objects.all()

    # Aplicar filtro por sede si el usuario no es superuser y tiene una sede asignada
    if not request.user.is_superuser and hasattr(request.user, 'profile') and not request.user.profile.is_admin and user_sede:
        visits_queryset = visits_queryset.filter(sede=user_sede)

    # Estadísticas generales
    active_visits_count = visits_queryset.filter(hora_salida__isnull=True).count()
    today_visits_count = visits_queryset.filter(fecha=timezone.localtime(timezone.now()).date()).count()
    total_visits_count = visits_queryset.count()
    people_count = Person.objects.count()

    # Últimas visitas: Filtrar solo las que tienen hora de salida (visitas completadas)
    recent_visits = visits_queryset.filter(hora_salida__isnull=False).order_by('-fecha', '-hora_entrada')[:10]

    context = {
        'active_visits_count': active_visits_count,
        'today_visits_count': today_visits_count,
        'people_count': people_count,
        'total_visits_count': total_visits_count,
        'recent_visits': recent_visits,
    }
    
    return render(request, 'home.html', context)

def search_person(request):
    """Vista para buscar una persona por DNI y verificar si tiene una visita activa"""
    dni = request.GET.get('dni', '')
    if dni:
        try:
            person = Person.objects.get(dni=dni)
            # Verificar si la persona tiene una visita activa
            user_sede = None
            if hasattr(request.user, 'profile'):
                user_sede = request.user.profile.sede
            
            if not request.user.is_superuser and hasattr(request.user, 'profile') and not request.user.profile.is_admin and user_sede:
                active_visit = Visit.objects.filter(
                    person=person,
                    hora_salida__isnull=True,
                    sede=user_sede
                ).first()
            else:
                active_visit = Visit.objects.filter(
                    person=person,
                    hora_salida__isnull=True
                ).first()
            
            # Preparar la respuesta con los datos de la persona
            response_data = {
                'found': True,
                'id': person.id,
                'nombre': person.nombre,
                'apellido': person.apellido,
                'dni': person.dni,
                'telefono': person.telefono,
                'email': person.email,
                'tarjetavisita': person.tarjetavisita,
                'observaciones': person.observaciones,
                'has_active_visit': active_visit is not None,
                'has_photo': bool(person.photo)
            }
            
            # Si tiene una visita activa, agregar la información detallada
            if active_visit:
                response_data.update({
                    'active_visit_id': active_visit.id,
                    'active_visit_sede': active_visit.sede.nombre if active_visit.sede else '',
                    'active_visit_area': active_visit.area.unidad_organica if active_visit.area else '',
                    'active_visit_subarea': '',  # Si necesitas incluir subárea
                    'active_visit_fecha': active_visit.fecha.strftime('%Y-%m-%d'),
                    'active_visit_hora_entrada': active_visit.hora_entrada.strftime('%H:%M'),
                    'active_visit_tarjeta': person.tarjetavisita
                })
            
            return JsonResponse(response_data)
            
        except Person.DoesNotExist:
            return JsonResponse({'found': False})
    return JsonResponse({'found': False})

def register_visit(request):
    """Vista para registrar una nueva visita"""
    # Verificar si hay un DNI en la URL para prellenar
    dni_from_url = request.GET.get('dni')
    
    # Obtener la sede del usuario
    user_sede = None
    if hasattr(request.user, 'profile'):
        user_sede = request.user.profile.sede
    
    # Si el usuario no es admin y no tiene sede asignada, mostrar mensaje y redirigir
    if not request.user.is_superuser and not hasattr(request.user, 'profile') or \
       not request.user.is_superuser and not request.user.profile.is_admin and not user_sede:
        messages.error(request, "No tienes una sede asignada. Por favor, contacta con un administrador.")
        return redirect('home')
    
    if request.method == 'POST':
        # Obtener el DNI del formulario
        submitted_dni = request.POST.get('dni')
        person_id = request.POST.get('person_id')
        
        # Si el usuario no es admin, forzar la sede del usuario
        submitted_sede = request.POST.get('sede')
        if not request.user.is_superuser and hasattr(request.user, 'profile') and not request.user.profile.is_admin:
            if user_sede:
                # Forzar la sede del usuario en el POST data
                request.POST = request.POST.copy()
                request.POST['sede'] = str(user_sede.id)
                submitted_sede = str(user_sede.id)
            else:
                messages.error(request, "No tienes una sede asignada. Por favor, contacta con un administrador.")
                return redirect('register_visit')
        
        # Verificar si ya existe una persona con ese DNI y determinar si tiene visitas activas
        existing_person = None
        has_active_visit = False
        
        try:
            if person_id:
                existing_person = Person.objects.get(id=person_id)
            elif submitted_dni:
                existing_person = Person.objects.get(dni=submitted_dni)
                
            if existing_person:
                # Si el usuario no es admin, verificar solo visitas activas en su sede
                if not request.user.is_superuser and hasattr(request.user, 'profile') and not request.user.profile.is_admin:
                    has_active_visit = Visit.objects.filter(
                        person=existing_person,
                        hora_salida__isnull=True,
                        sede=user_sede
                    ).exists()
                else:
                    # Para admins, verificar todas las visitas activas
                    has_active_visit = Visit.objects.filter(
                        person=existing_person,
                        hora_salida__isnull=True
                    ).exists()
                
                # Si tiene una visita activa, mostrar advertencia y continuar
                if has_active_visit:
                    messages.warning(request, 'ATENCIÓN: Esta persona tiene una visita sin registrar salida.')
                    
        except Person.DoesNotExist:
            # Si la persona no existe, continuamos con el proceso normal
            pass
        
        # Si llegamos aquí, continuamos con el proceso normal independientemente de si hay visitas activas
        visit_form = VisitForm(request.POST)
        
        if not visit_form.is_valid():
            # Si el formulario de visita no es válido, volver con errores
            messages.error(request, 'Por favor corrija los errores en el formulario de visita.')
            person_form = PersonForm(request.POST, request.FILES)
            return render(request, 'register_visit.html', {
                'person_form': person_form,
                'visit_form': visit_form
            })
        
        # Ahora manejamos la persona
        person_form = None
        if existing_person:
            # Si la persona existe, actualizamos sus datos
            person_form = PersonForm(request.POST, request.FILES, instance=existing_person)
        else:
            # Si la persona no existe, crear nueva
            person_form = PersonForm(request.POST, request.FILES)
        
        if person_form.is_valid():
            # Obtener la tarjeta de visita y la sede
            tarjeta_visita = person_form.cleaned_data.get('tarjetavisita')
            sede_id = visit_form.cleaned_data.get('sede').id
            
            # Validar que la tarjeta no esté en uso en esta sede
            if tarjeta_visita:
                # Buscar visitas activas con esta tarjeta en esta sede
                active_visit_with_card = Visit.objects.filter(
                    person__tarjetavisita=tarjeta_visita,
                    sede_id=sede_id,
                    hora_salida__isnull=True
                ).first()
                
                if active_visit_with_card:
                    person_with_card = active_visit_with_card.person
                    error_message = (f'La tarjeta #{tarjeta_visita} ya está en uso por {person_with_card.nombre} {person_with_card.apellido} '
                                    f'desde {active_visit_with_card.fecha} a las {active_visit_with_card.hora_entrada.strftime("%H:%M")}. '
                                    f'Debe registrar la salida antes de volver a usar esta tarjeta en esta sede.')
                    messages.error(request, error_message)
                    return render(request, 'register_visit.html', {
                        'person_form': person_form,
                        'visit_form': visit_form
                    })
            
            # Si todo está bien, guardar la persona
            person = person_form.save(commit=False)
            
            # Procesar la foto si existe
            photo_data = request.POST.get('photo_data_url')
            if photo_data and ';base64,' in photo_data:
                format, imgstr = photo_data.split(';base64,')
                binary_data = base64.b64decode(imgstr)
                person.photo = binary_data
            
            person.save()
        else:
            # Si hay errores en el formulario que no son por DNI duplicado, los mostramos
            # Eliminamos el error de DNI único si existe
            if 'dni' in person_form.errors and 'Ya existe Persona con este DNI' in str(person_form.errors['dni']):
                # Eliminamos solo ese error específico
                person_form.errors.pop('dni', None)
            
            # Si todavía hay otros errores, los mostramos
            if person_form.errors:
                messages.error(request, 'Por favor corrija los errores en el formulario de persona.')
                return render(request, 'register_visit.html', {
                    'person_form': person_form,
                    'visit_form': visit_form
                })
        
        # Crear la visita
        visit = visit_form.save(commit=False)
        visit.person = person
        
        # Forzar la sede del usuario si no es admin
        if not request.user.is_superuser and hasattr(request.user, 'profile') and not request.user.profile.is_admin:
            visit.sede = user_sede
        
        # Usar fecha y hora actual con la configuración de timezone de Django (Argentina)
        current_datetime = timezone.localtime(timezone.now())
        visit.fecha = current_datetime.date()
        visit.hora_entrada = current_datetime.time()
        
        # Registrar el usuario que creó la visita
        visit.created_by = request.user
        
        visit.save()
        
        messages.success(request, 'Visita registrada exitosamente.')
        return redirect('visit_detail', visit_id=visit.id)
        
    else:
        # Método GET
        person_form = PersonForm()
        visit_form = VisitForm()
        
        # Preseleccionar la sede del usuario si no es admin
        if not request.user.is_superuser and hasattr(request.user, 'profile') and not request.user.profile.is_admin and user_sede:
            visit_form.fields['sede'].initial = user_sede.id
            # Deshabilitar el campo de sede para usuarios no admin
            visit_form.fields['sede'].widget.attrs['disabled'] = 'disabled'
            # También podemos ocultar las otras sedes del dropdown
            visit_form.fields['sede'].queryset = Sede.objects.filter(id=user_sede.id)
            
            # Mostrar todas las áreas activas ordenadas por unidad orgánica
            visit_form.fields['area'].queryset = Estructura.objects.filter(activo=True).order_by('unidad_organica')
        
        # Si hay un DNI en la URL, intentar buscar la persona
        if dni_from_url:
            try:
                person = Person.objects.get(dni=dni_from_url)
                
                # Verificar si la persona tiene una visita activa
                # Si el usuario no es admin, verificar solo visitas en su sede
                if not request.user.is_superuser and hasattr(request.user, 'profile') and not request.user.profile.is_admin:
                    has_active_visit = Visit.objects.filter(
                        person=person,
                        hora_salida__isnull=True,
                        sede=user_sede
                    ).exists()
                else:
                    # Para admins, verificar todas las visitas activas
                    has_active_visit = Visit.objects.filter(
                        person=person,
                        hora_salida__isnull=True
                    ).exists()
                
                if has_active_visit:
                    messages.warning(request, 'Esta persona tiene una salida pendiente. No se puede registrar una nueva visita.')
                
                person_form = PersonForm(instance=person)
                # También establecemos un valor inicial para el campo oculto person_id
                person_form.initial['person_id'] = person.id
            except Person.DoesNotExist:
                # Si la persona no existe, solo prellenamos el DNI
                person_form.initial['dni'] = dni_from_url
    
    return render(request, 'register_visit.html', {
        'person_form': person_form,
        'visit_form': visit_form
    })

def visit_detail(request, visit_id):
    """Vista para ver los detalles de una visita"""
    visit = get_object_or_404(Visit, id=visit_id)
    
    # Verificar permisos de sede
    user_sede = None
    if hasattr(request.user, 'profile'):
        user_sede = request.user.profile.sede
    
    # Si el usuario no es admin, solo puede ver detalles de visitas de su sede
    if not request.user.is_superuser and hasattr(request.user, 'profile') and not request.user.profile.is_admin:
        if not user_sede or visit.sede.id != user_sede.id:
            messages.error(request, "No tienes permiso para ver detalles de visitas de otras sedes.")
            return redirect('visit_list')
    
    return render(request, 'visit_detail.html', {'visit': visit})

def list_visits(request):
    """Vista para listar las visitas activas (alias de visit_list)"""
    # Obtener la sede del usuario
    user_sede = None
    if hasattr(request.user, 'profile'):
        user_sede = request.user.profile.sede
    
    # Filtrar por sede si el usuario no es admin
    if not request.user.is_superuser and hasattr(request.user, 'profile') and not request.user.profile.is_admin and user_sede:
        visits = Visit.objects.filter(hora_salida__isnull=True, sede=user_sede).order_by('-fecha', '-hora_entrada')
    else:
        visits = Visit.objects.filter(hora_salida__isnull=True).order_by('-fecha', '-hora_entrada')
    
    return render(request, 'list_visits.html', {'visits': visits})

def visit_list(request):
    """Vista para listar las visitas activas"""
    # Obtener la sede del usuario
    user_sede = None
    if hasattr(request.user, 'profile'):
        user_sede = request.user.profile.sede

    # Filtros GET
    nombre = request.GET.get('nombre', '').strip()
    apellido = request.GET.get('apellido', '').strip()
    dni = request.GET.get('dni', '').strip()
    tarjetavisita = request.GET.get('tarjetavisita', '').strip()
    fecha_inicio = request.GET.get('fecha_inicio', '').strip()
    fecha_fin = request.GET.get('fecha_fin', '').strip()
    area_id = request.GET.get('area', '').strip()
    usuario_id = request.GET.get('usuario', '').strip()
    sede_id = request.GET.get('sede', '').strip()

    # Base queryset: solo visitas activas
    if not request.user.is_superuser and hasattr(request.user, 'profile') and not request.user.profile.is_admin and user_sede:
        visits = Visit.objects.filter(hora_salida__isnull=True, sede=user_sede)
        sedes = Sede.objects.filter(id=user_sede.id)
    else:
        visits = Visit.objects.filter(hora_salida__isnull=True)
        sedes = Sede.objects.all()

    # Aplicar filtros
    if nombre:
        visits = visits.filter(person__nombre__icontains=nombre)
    if apellido:
        visits = visits.filter(person__apellido__icontains=apellido)
    if dni:
        visits = visits.filter(person__dni__icontains=dni)
    if tarjetavisita:
        visits = visits.filter(person__tarjetavisita__icontains=tarjetavisita)
    if fecha_inicio:
        visits = visits.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        visits = visits.filter(fecha__lte=fecha_fin)
    if area_id:
        visits = visits.filter(area_id=area_id)
    if usuario_id:
        visits = visits.filter(created_by_id=usuario_id)
    if sede_id:
        visits = visits.filter(sede_id=sede_id)

    visits = visits.select_related('person', 'sede', 'area', 'created_by').order_by('-fecha', '-hora_entrada')

    # Opciones para selects
    areas = Estructura.objects.filter(activo=True).order_by('unidad_organica')
    
    # Obtener todos los usuarios que han creado visitas activas (sin importar filtros actuales)
    # Aplicar restricciones de sede si el usuario no es admin
    if not request.user.is_superuser and hasattr(request.user, 'profile') and not request.user.profile.is_admin and user_sede:
        # Solo usuarios que han creado visitas activas en la sede del usuario actual
        user_ids = Visit.objects.filter(hora_salida__isnull=True, sede=user_sede).exclude(created_by__isnull=True).values_list('created_by', flat=True).distinct()
        usuarios = User.objects.filter(id__in=user_ids).values_list('id', 'first_name', 'last_name', 'username').order_by('first_name', 'last_name')
    else:
        # Todos los usuarios que han creado visitas activas
        user_ids = Visit.objects.filter(hora_salida__isnull=True).exclude(created_by__isnull=True).values_list('created_by', flat=True).distinct()
        usuarios = User.objects.filter(id__in=user_ids).values_list('id', 'first_name', 'last_name', 'username').order_by('first_name', 'last_name')

    return render(request, 'visit_list.html', {
        'visits': visits,
        'sedes': sedes,
        'areas': areas,
        'usuarios': usuarios,
    })

def checkout_visit(request, visit_id):
    """Vista para registrar la salida de una visita"""
    visit = get_object_or_404(Visit, id=visit_id)
    
    # Verificar permisos de sede
    user_sede = None
    if hasattr(request.user, 'profile'):
        user_sede = request.user.profile.sede
    
    # Si el usuario no es admin, solo puede registrar salidas de su sede
    if not request.user.is_superuser and hasattr(request.user, 'profile') and not request.user.profile.is_admin:
        if not user_sede or visit.sede.id != user_sede.id:
            messages.error(request, "No tienes permiso para registrar la salida de visitas de otras sedes.")
            return redirect('visit_list')
    
    if request.method == 'POST':
        # Usar timezone de Django para obtener la fecha y hora actual en Argentina
        current_datetime = timezone.localtime(timezone.now())
        visit.fecha_salida = current_datetime.date()
        visit.hora_salida = current_datetime.time()
        visit.save()
        
        # Mensaje de éxito con información sobre la tarjeta de visita
        if visit.person.tarjetavisita:
            messages.success(request, f'Salida registrada exitosamente. La tarjeta #{visit.person.tarjetavisita} está ahora disponible.')
        else:
            messages.success(request, 'Salida registrada exitosamente.')
            
        return redirect('visit_list')
    
    return render(request, 'checkout_visit.html', {'visit': visit})

def register_exit(request, visit_id):
    """Vista para registrar la salida de una visita (alias de checkout_visit)"""
    visit = get_object_or_404(Visit, id=visit_id)
    
    # Verificar permisos de sede
    user_sede = None
    if hasattr(request.user, 'profile'):
        user_sede = request.user.profile.sede
    
    # Si el usuario no es admin, solo puede registrar salidas de su sede
    if not request.user.is_superuser and hasattr(request.user, 'profile') and not request.user.profile.is_admin:
        if not user_sede or visit.sede.id != user_sede.id:
            messages.error(request, "No tienes permiso para registrar la salida de visitas de otras sedes.")
            return redirect('visit_list')
    
    if request.method == 'POST':
        # Usar timezone de Django para obtener la fecha y hora actual en Argentina
        current_datetime = timezone.localtime(timezone.now())
        visit.fecha_salida = current_datetime.date()
        visit.hora_salida = current_datetime.time()
        visit.save()
        
        # Mensaje de éxito con información sobre la tarjeta de visita
        if visit.person.tarjetavisita:
            messages.success(request, f'Salida registrada exitosamente. La tarjeta #{visit.person.tarjetavisita} está ahora disponible.')
        else:
            messages.success(request, 'Salida registrada exitosamente.')
            
        return redirect('visit_list')
    
    return render(request, 'register_exit.html', {'visit': visit})

def get_person_photo(request):
    """Vista para obtener la foto de una persona en formato base64"""
    person_id = request.GET.get('person_id')
    if person_id:
        try:
            person = Person.objects.get(id=person_id)
            if person.photo:
                # Convertir la foto a base64
                photo_base64 = base64.b64encode(person.photo).decode('utf-8')
                return JsonResponse({'photo': photo_base64})
            else:
                return JsonResponse({'photo': None})
        except Person.DoesNotExist:
            return JsonResponse({'error': 'Persona no encontrada'}, status=404)
    return JsonResponse({'error': 'ID de persona no proporcionado'}, status=400)

def get_person_photo_direct(request, person_id):
    """Vista para obtener la foto de una persona directamente como imagen"""
    person = get_object_or_404(Person, id=person_id)
    
    if person.photo:
        return HttpResponse(person.photo, content_type='image/jpeg')
    else:
        # Devolver una imagen por defecto o un error 404
        return HttpResponse(status=404)

def check_tarjeta_disponible(request):
    """
    Vista AJAX para verificar si una tarjeta de visita está disponible en una sede.
    """
    tarjeta = request.GET.get('tarjeta')
    sede_id = request.GET.get('sede_id')
    
    if not tarjeta or not sede_id:
        return JsonResponse({'available': True})
    
    # Buscar visitas activas con esta tarjeta en esta sede
    active_visit = Visit.objects.filter(
        person__tarjetavisita=tarjeta,
        sede_id=sede_id,
        hora_salida__isnull=True
    ).first()
    
    if active_visit:
        person = active_visit.person
        message = (f'La tarjeta #{tarjeta} ya está en uso por <strong>{person.nombre} {person.apellido}</strong> '
                  f'desde {active_visit.fecha} a las {active_visit.hora_entrada.strftime("%H:%M")}.<br><br>'
                  f'Debe registrar la salida antes de volver a usar esta tarjeta en esta sede.')
        
        return JsonResponse({
            'available': False,
            'message': message,
            'visit_id': active_visit.id
        })
    
    return JsonResponse({'available': True})

def validate_tarjeta_visita(tarjeta, sede_id):
    """
    Función auxiliar para validar si una tarjeta de visita está disponible en una sede.
    Retorna (disponible, mensaje_error, visita_activa)
    """
    if not tarjeta or not sede_id:
        return True, None, None
    
    # Buscar visitas activas con esta tarjeta en esta sede
    active_visit = Visit.objects.filter(
        person__tarjetavisita=tarjeta,
        sede_id=sede_id,
        hora_salida__isnull=True
    ).first()
    
    if active_visit:
        person = active_visit.person
        error_message = (f'La tarjeta #{tarjeta} ya está en uso por {person.nombre} {person.apellido} '
                        f'desde {active_visit.fecha} a las {active_visit.hora_entrada.strftime("%H:%M")}. '
                        f'Debe registrar la salida antes de volver a usar esta tarjeta en esta sede.')
        return False, error_message, active_visit
    
    return True, None, None


def mostrar_buscador_internos(request):
    """Muestra la página del buscador interno usando un iframe."""
    context = {
        'url_buscador': 'https://internos.minseg.gob.ar/buscador.php'
    }
    return render(request, 'internos.html', context)

def visit_history(request):
    """Vista para listar el histórico completo de visitas (con y sin salida)"""
    # Obtener la sede del usuario
    user_sede = None
    if hasattr(request.user, 'profile'):
        user_sede = request.user.profile.sede

    # Filtros GET
    nombre = request.GET.get('nombre', '').strip()
    apellido = request.GET.get('apellido', '').strip()
    dni = request.GET.get('dni', '').strip()
    tarjetavisita = request.GET.get('tarjetavisita', '').strip()
    fecha_inicio = request.GET.get('fecha_inicio', '').strip()
    fecha_fin = request.GET.get('fecha_fin', '').strip()
    area_id = request.GET.get('area', '').strip()
    usuario_id = request.GET.get('usuario', '').strip()
    sede_id = request.GET.get('sede', '').strip()
    estado = request.GET.get('estado', '').strip()  # 'activas', 'completadas', '' para todas

    # Base queryset: todas las visitas
    if not request.user.is_superuser and hasattr(request.user, 'profile') and not request.user.profile.is_admin and user_sede:
        visits = Visit.objects.filter(sede=user_sede)
        sedes = Sede.objects.filter(id=user_sede.id)
    else:
        visits = Visit.objects.all()
        sedes = Sede.objects.all()

    # Aplicar filtros
    if nombre:
        visits = visits.filter(person__nombre__icontains=nombre)
    if apellido:
        visits = visits.filter(person__apellido__icontains=apellido)
    if dni:
        visits = visits.filter(person__dni__icontains=dni)
    if tarjetavisita:
        visits = visits.filter(person__tarjetavisita__icontains=tarjetavisita)
    if fecha_inicio:
        visits = visits.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        visits = visits.filter(fecha__lte=fecha_fin)
    if area_id:
        visits = visits.filter(area_id=area_id)
    if usuario_id:
        visits = visits.filter(created_by_id=usuario_id)
    if sede_id:
        visits = visits.filter(sede_id=sede_id)
    
    # Filtro por estado
    if estado == 'activas':
        visits = visits.filter(hora_salida__isnull=True)
    elif estado == 'completadas':
        visits = visits.filter(hora_salida__isnull=False)

    visits = visits.select_related('person', 'sede', 'area', 'created_by').order_by('-fecha', '-hora_entrada')

    # Paginación
    paginator = Paginator(visits, 50)  # 50 por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Opciones para selects
    areas = Estructura.objects.filter(activo=True).order_by('unidad_organica')
    
    # Obtener todos los usuarios que han creado visitas (sin importar filtros actuales)
    # Aplicar restricciones de sede si el usuario no es admin
    if not request.user.is_superuser and hasattr(request.user, 'profile') and not request.user.profile.is_admin and user_sede:
        # Solo usuarios que han creado visitas en la sede del usuario actual
        user_ids = Visit.objects.filter(sede=user_sede).exclude(created_by__isnull=True).values_list('created_by', flat=True).distinct()
        usuarios = User.objects.filter(id__in=user_ids).values_list('id', 'first_name', 'last_name', 'username').order_by('first_name', 'last_name')
    else:
        # Todos los usuarios que han creado visitas
        user_ids = Visit.objects.exclude(created_by__isnull=True).values_list('created_by', flat=True).distinct()
        usuarios = User.objects.filter(id__in=user_ids).values_list('id', 'first_name', 'last_name', 'username').order_by('first_name', 'last_name')

    return render(request, 'visit_history.html', {
        'visits': page_obj,
        'sedes': sedes,
        'areas': areas,
        'usuarios': usuarios,
    })