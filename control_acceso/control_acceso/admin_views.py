from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import Visit, Person, Sede
import datetime
import base64

from django.http import HttpResponse
from django.template.loader import get_template
try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except ImportError:
    XHTML2PDF_AVAILABLE = False
from django.templatetags.static import static
import os

@login_required
def informe_visitas(request):
    sedes = Sede.objects.all()
    areas = Estructura.objects.filter(activo=True).order_by('unidad_organica')
    visitas = Visit.objects.select_related('person', 'sede', 'area', 'created_by').all()

    # Filtros avanzados
    fecha_inicio = request.GET.get('fecha_inicio', '').strip()
    fecha_fin = request.GET.get('fecha_fin', '').strip()
    nombre = request.GET.get('nombre', '').strip()
    apellido = request.GET.get('apellido', '').strip()
    dni = request.GET.get('dni', '').strip()
    tarjetavisita = request.GET.get('tarjetavisita', '').strip()
    sede_id = request.GET.get('sede', '').strip()
    area_id = request.GET.get('area', '').strip()
    usuario_id = request.GET.get('usuario', '').strip()

    if fecha_inicio:
        visitas = visitas.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        visitas = visitas.filter(fecha__lte=fecha_fin)
    if nombre:
        visitas = visitas.filter(person__nombre__icontains=nombre)
    if apellido:
        visitas = visitas.filter(person__apellido__icontains=apellido)
    if dni:
        visitas = visitas.filter(person__dni__icontains=dni)
    if tarjetavisita:
        visitas = visitas.filter(person__tarjetavisita__icontains=tarjetavisita)
    if sede_id:
        visitas = visitas.filter(sede_id=sede_id)
    if area_id:
        visitas = visitas.filter(area_id=area_id)
    if usuario_id:
        visitas = visitas.filter(created_by_id=usuario_id)

    # Primero obtenemos los usuarios antes de hacer el slice
    from django.core.paginator import Paginator
    visitas_ordenadas = visitas.order_by('-fecha', '-hora_entrada')
    usuarios = visitas_ordenadas.values_list('created_by__id', 'created_by__first_name', 'created_by__last_name', 'created_by__username').distinct()
    page_number = request.GET.get('page', 1)
    paginator = Paginator(visitas_ordenadas, 20)
    page_obj = paginator.get_page(page_number)
    visitas_paginadas = page_obj.object_list

    # Exportar a PDF con xhtml2pdf
    if request.GET.get('export') == 'pdf':
        if not XHTML2PDF_AVAILABLE:
            messages.error(request, 'xhtml2pdf no está instalado. No se puede exportar a PDF.')
        else:
            # Para PDF, usar todos los registros filtrados (no paginados)
            visitas_para_pdf = list(visitas_ordenadas)
            visitas_pdf = []
            for v in visitas_para_pdf:
                foto_base64 = None
                if v.person.photo:
                    foto_base64 = 'data:image/jpeg;base64,' + base64.b64encode(v.person.photo).decode('utf-8')
                if v.created_by:
                    usuario_registro = v.created_by.get_full_name() or v.created_by.username
                else:
                    usuario_registro = "-"
                visitas_pdf.append({
                    'fecha': v.fecha,
                    'dni': v.person.dni,
                    'nombre': v.person.get_full_name(),
                    'sede': v.sede.nombre,
                    'area': v.area.unidad_organica,
                    'hora_entrada': v.hora_entrada,
                    'hora_salida': v.hora_salida if v.hora_salida else '-',
                    'foto_base64': foto_base64,
                    'usuario_registro': usuario_registro
                })
            # Obtener logo como base64
            logo_base64 = None
            try:
                logo_path = os.path.join(
                    os.path.dirname(__file__),
                    'static', 'logo.png'
                )
                with open(logo_path, 'rb') as f:
                    logo_base64 = 'data:image/png;base64,' + base64.b64encode(f.read()).decode('utf-8')
            except Exception as e:
                # Intentar ruta alternativa
                try:
                    logo_path = os.path.join(
                        os.path.dirname(__file__),
                        '..', 'static', 'logo.png'
                    )
                    with open(logo_path, 'rb') as f:
                        logo_base64 = 'data:image/png;base64,' + base64.b64encode(f.read()).decode('utf-8')
                except Exception:
                    logo_base64 = None
            template = get_template('admin/informe_visitas.html')
            html = template.render({
                'visitas': visitas_para_pdf,
                'visitas_pdf': visitas_pdf,
                'sedes': sedes,
                'request': request,
                'pdf_export': True,
                'logo_base64': logo_base64,
            })
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="informe_visitas.pdf"'
            pisa_status = pisa.CreatePDF(html, dest=response)
            if pisa_status.err:
                return HttpResponse('Error al generar el PDF', status=500)
            return response

    return render(request, 'admin/informe_visitas.html', {
        'visitas': visitas_paginadas,
        'page_obj': page_obj,
        'paginator': paginator,
        'sedes': sedes,
        'areas': areas,
        'usuarios': usuarios,
    })
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Sede, Estructura
from .forms import SedeForm, EstructuraForm

# Administración de Sedes
@login_required
def sede_list(request):
    """Vista para listar todas las sedes"""
    sedes = Sede.objects.all().order_by('nombre')
    return render(request, 'admin/sede_list.html', {'sedes': sedes})

@login_required
def sede_create(request):
    """Vista para crear una nueva sede"""
    if request.method == 'POST':
        form = SedeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sede creada exitosamente.')
            return redirect('sede_list')
    else:
        form = SedeForm()
    
    return render(request, 'admin/sede_form.html', {
        'form': form,
        'title': 'Crear Sede',
    })

@login_required
def sede_edit(request, sede_id):
    """Vista para editar una sede existente"""
    sede = get_object_or_404(Sede, id=sede_id)
    
    if request.method == 'POST':
        form = SedeForm(request.POST, instance=sede)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sede actualizada exitosamente.')
            return redirect('sede_list')
    else:
        form = SedeForm(instance=sede)
    
    return render(request, 'admin/sede_form.html', {
        'form': form,
        'title': 'Editar Sede',
        'sede': sede,
    })

@login_required
def sede_delete(request, sede_id):
    """Vista para eliminar una sede"""
    sede = get_object_or_404(Sede, id=sede_id)
    
    if request.method == 'POST':
        # Verificar si hay áreas asociadas
        if sede.areas.exists():
            messages.error(request, 'No se puede eliminar la sede porque tiene áreas asociadas.')
            return redirect('sede_list')
        
        sede.delete()
        messages.success(request, 'Sede eliminada exitosamente.')
        return redirect('sede_list')
    
    return render(request, 'admin/sede_confirm_delete.html', {'sede': sede})

# Administración de Áreas
@login_required
def area_list(request):
    """Vista para listar todas las áreas"""
    areas = Estructura.objects.filter(padre__isnull=True)
    return render(request, 'admin/area_list.html', {'areas': areas})

@login_required
def area_create(request):
    """Vista para crear una nueva área"""
    if request.method == 'POST':
        form = SedeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Área creada exitosamente.')
            return redirect('area_list')
    else:
        form = SedeForm()
    
    return render(request, 'admin/area_form.html', {
        'form': form,
        'title': 'Crear Área',
    })

@login_required
def area_edit(request, area_id):
    """Vista para editar un área existente"""
    area = get_object_or_404(Estructura, id=area_id)
    
    if request.method == 'POST':
        form = SedeForm(request.POST, instance=area)
        if form.is_valid():
            form.save()
            messages.success(request, 'Área actualizada exitosamente.')
            return redirect('area_list')
    else:
        form = SedeForm(instance=area)
    
    return render(request, 'admin/area_form.html', {
        'form': form,
        'title': 'Editar Área',
        'area': area,
    })

@login_required
def area_delete(request, area_id):
    """Vista para eliminar un área"""
    area = get_object_or_404(Estructura, id=area_id)
    
    if request.method == 'POST':
        # Verificar si hay subáreas asociadas
        if area.subareas.exists():
            messages.error(request, 'No se puede eliminar el área porque tiene subáreas asociadas.')
            return redirect('area_list')
        
        area.delete()
        messages.success(request, 'Área eliminada exitosamente.')
        return redirect('area_list')
    
    return render(request, 'admin/area_confirm_delete.html', {'area': area})

# Administración de Subáreas
@login_required
def subarea_list(request):
    """Vista para listar todas las subáreas"""
    subareas = Estructura.objects.filter(padre__isnull=False)
    return render(request, 'admin/subarea_list.html', {'subareas': subareas})

@login_required
def subarea_create(request):
    """Vista para crear una nueva subárea"""
    areas = Estructura.objects.filter(padre__isnull=True, activo=True)
    
    if request.method == 'POST':
        unidad_organica = request.POST.get('unidad_organica')
        siglas = request.POST.get('siglas')
        padre = request.POST.get('padre')
        
        if unidad_organica and siglas and padre:
            Estructura.objects.create(
                unidad_organica=unidad_organica,
                siglas=siglas,
                padre=padre,
                activo=True
            )
            messages.success(request, 'Subárea creada exitosamente.')
            return redirect('subarea_list')
        else:
            messages.error(request, 'Por favor complete todos los campos.')
    
    return render(request, 'admin/subarea_form.html', {
        'areas': areas,
        'title': 'Crear Subárea'
    })

@login_required
def subarea_edit(request, subarea_id):
    """Vista para editar una subárea existente"""
    subarea = get_object_or_404(Estructura, id=subarea_id)
    areas = Estructura.objects.filter(padre__isnull=True, activo=True)
    
    if request.method == 'POST':
        unidad_organica = request.POST.get('unidad_organica')
        siglas = request.POST.get('siglas')
        padre = request.POST.get('padre')
        
        if unidad_organica and siglas and padre:
            subarea.unidad_organica = unidad_organica
            subarea.siglas = siglas
            subarea.padre = padre
            subarea.save()
            messages.success(request, 'Subárea actualizada exitosamente.')
            return redirect('subarea_list')
        else:
            messages.error(request, 'Por favor complete todos los campos.')
    
    return render(request, 'admin/subarea_form.html', {
        'subarea': subarea,
        'areas': areas,
        'title': 'Editar Subárea'
    })

@login_required
def subarea_delete(request, subarea_id):
    """Vista para eliminar una subárea"""
    subarea = get_object_or_404(Estructura, id=subarea_id)
    
    if request.method == 'POST':
        # Verificar si hay visitas asociadas
        if subarea.visits_as_subarea.exists():
            messages.error(request, 'No se puede eliminar la subárea porque tiene visitas asociadas.')
            return redirect('subarea_list')
        
        subarea.delete()
        messages.success(request, 'Subárea eliminada exitosamente.')
        return redirect('subarea_list')
    
    return render(request, 'admin/subarea_confirm_delete.html', {'subarea': subarea})

# Administración de Estructuras (Áreas y Subáreas)
@login_required
def estructura_list(request):
    """Vista para listar todas las estructuras (áreas y subáreas)"""
    areas = Estructura.objects.filter(padre__isnull=True).order_by('siglas')
    subareas = Estructura.objects.filter(padre__isnull=False).order_by('padre', 'siglas')
    return render(request, 'admin/estructura_list.html', {
        'areas': areas,
        'subareas': subareas
    })

@login_required
def estructura_create(request):
    """Vista para crear una nueva estructura (área o subárea)"""
    if request.method == 'POST':
        form = EstructuraForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Estructura creada exitosamente.')
            return redirect('estructura_list')
    else:
        form = EstructuraForm()
    
    return render(request, 'admin/estructura_form.html', {
        'form': form,
        'title': 'Crear Estructura'
    })

@login_required
def estructura_edit(request, estructura_id):
    """Vista para editar una estructura existente"""
    estructura = get_object_or_404(Estructura, id=estructura_id)
    if request.method == 'POST':
        form = EstructuraForm(request.POST, instance=estructura)
        if form.is_valid():
            form.save()
            messages.success(request, 'Estructura actualizada exitosamente.')
            return redirect('estructura_list')
    else:
        form = EstructuraForm(instance=estructura)
    
    return render(request, 'admin/estructura_form.html', {
        'form': form,
        'estructura': estructura,
        'title': 'Editar Estructura'
    })

@login_required
def estructura_delete(request, estructura_id):
    """Vista para eliminar una estructura"""
    estructura = get_object_or_404(Estructura, id=estructura_id)
    
    if request.method == 'POST':
        # Check if it's an area with subareas
        if estructura.padre is None and Estructura.objects.filter(padre=estructura.siglas).exists():
            messages.error(request, 'No se puede eliminar el área porque tiene subáreas asociadas.')
            return redirect('estructura_list')
        
        # Check if it has associated visits
        if estructura.visits_as_area.exists() or estructura.visits_as_subarea.exists():
            messages.error(request, 'No se puede eliminar la estructura porque tiene visitas asociadas.')
            return redirect('estructura_list')
        
        estructura.delete()
        messages.success(request, 'Estructura eliminada exitosamente.')
        return redirect('estructura_list')
    
    return render(request, 'admin/estructura_confirm_delete.html', {
        'estructura': estructura
    })

# Vista para cargar áreas basadas en la sede seleccionada (para formularios dinámicos)
def load_areas_for_form(request):
    """Vista para cargar áreas basadas en la sede seleccionada (para formularios)"""
    areas = Estructura.objects.filter(padre__isnull=True, activo=True).order_by('siglas')
    return JsonResponse(list(areas.values('id', 'unidad_organica', 'siglas')), safe=False)