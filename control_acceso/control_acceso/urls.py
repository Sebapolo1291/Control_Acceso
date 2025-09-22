from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as django_auth_views  # Add this import
from . import views
from . import admin_views
from . import auth_views

urlpatterns = [
    path('admin/informe-visitas/', admin_views.informe_visitas, name='informe_visitas'),
    path('admin/', admin.site.urls),
    
    # Rutas de autenticación
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    
    # Página principal
    path('', views.home, name='home'),
    
    # Gestión de visitas
    path('visitas/registrar/', views.register_visit, name='register_visit'),
    path('visitas/lista/', views.visit_list, name='visit_list'),
    path('visitas/historico/', views.visit_history, name='visit_history'),
    path('visitas/<int:visit_id>/', views.visit_detail, name='visit_detail'),
    path('visitas/<int:visit_id>/salida/', views.register_exit, name='register_exit'),
    
    # API para búsquedas y carga dinámica
    path('api/buscar-persona/', views.search_person, name='search_person'),
    path('api/get-person-photo/', views.get_person_photo, name='get_person_photo'),
    # Listado de personas solo para admin
    path('personas/lista/', views.person_list, name='person_list'),
    path('personas/<int:person_id>/', views.person_detail, name='person_detail'),
    path('personas/<int:person_id>/editar/', views.person_edit, name='person_edit'),
    
    
    
    # Administración de Sedes
    path('gestion/sedes/', admin_views.sede_list, name='sede_list'),
    path('gestion/sedes/crear/', admin_views.sede_create, name='sede_create'),
    path('gestion/sedes/editar/<int:sede_id>/', admin_views.sede_edit, name='sede_edit'),
    path('gestion/sedes/eliminar/<int:sede_id>/', admin_views.sede_delete, name='sede_delete'),
    
    # Administración de Estructura (Areas y Subareas)
    path('gestion/estructuras/', admin_views.estructura_list, name='estructura_list'),
    path('gestion/estructuras/crear/', admin_views.estructura_create, name='estructura_create'),
    path('gestion/estructuras/editar/<int:estructura_id>/', admin_views.estructura_edit, name='estructura_edit'),
    path('gestion/estructuras/eliminar/<int:estructura_id>/', admin_views.estructura_delete, name='estructura_delete'),
    
    # API para verificar disponibilidad de tarjetas de visita
    path('api/check-tarjeta-disponible/', views.check_tarjeta_disponible, name='check_tarjeta_disponible'),
    
    # API para obtener la foto de una persona
    path('get-person-photo/<int:person_id>/', views.get_person_photo_direct, name='get_person_photo'),

    path('buscador-internos/', views.mostrar_buscador_internos, name='internos'),


    # Rutas para FlotaEstructura
    path('admin/sedes/', admin_views.sede_list, name='sede_list'),
    path('admin/areas/', admin_views.area_list, name='area_list'),
    path('admin/subareas/', admin_views.subarea_list, name='subarea_list'),
    
    # Cambiar contraseña
    path('password_change/', django_auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change.html',
        success_url='/'
    ), name='password_change'),
]
