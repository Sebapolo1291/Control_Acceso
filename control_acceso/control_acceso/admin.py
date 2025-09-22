from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import Sede, Person, Visit, UserProfile, Estructura

# Define un filtro personalizado para visitas activas/inactivas
class ActiveVisitFilter(admin.SimpleListFilter):
    title = 'estado de visita'
    parameter_name = 'active'
    
    def lookups(self, request, model_admin):
        return (
            ('active', 'Visitas activas'),
            ('inactive', 'Visitas completadas'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(hora_salida__isnull=True)
        if self.value() == 'inactive':
            return queryset.filter(hora_salida__isnull=False)

# Define un admin en línea para UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil de usuario'
    
# Define una nueva clase admin para User que incluye el UserProfile
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_sede')
    
    def get_sede(self, obj):
        if hasattr(obj, 'profile') and obj.profile.sede:
            return obj.profile.sede.nombre
        return 'Sin sede asignada'
    get_sede.short_description = 'Sede'

# Re-registrar el modelo User con el nuevo admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Registrar los modelos propios
@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'activo')
    search_fields = ('nombre', 'direccion')
    list_filter = ('activo',)

@admin.register(Estructura)
class EstructuraAdmin(admin.ModelAdmin):
    list_display = ('unidad_organica', 'siglas', 'padre', 'activo')
    search_fields = ('unidad_organica', 'siglas', 'padre')
    list_filter = ('activo', 'padre')
    ordering = ('siglas',)

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('dni', 'nombre', 'apellido', 'telefono', 'email', 'tarjetavisita')
    search_fields = ('dni', 'nombre', 'apellido', 'tarjetavisita')
    list_filter = ('created_at',)

@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('person', 'fecha', 'hora_entrada', 'hora_salida', 'sede', 'area')
    search_fields = ('person__dni', 'person__nombre', 'person__apellido', 'area__unidad_organica')
    list_filter = ('fecha', 'sede', 'area', 'hora_salida')
    date_hierarchy = 'fecha'
    ordering = ('-fecha', '-hora_entrada')
    raw_id_fields = ('person',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'sede', 'is_admin')
    search_fields = ('user__username', 'sede__nombre')
    list_filter = ('is_admin', 'sede')
