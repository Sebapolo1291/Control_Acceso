from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Sede(models.Model):
    nombre = models.CharField(_('Nombre'), max_length=255)
    direccion = models.CharField(_('Dirección'), max_length=255, null=True, blank=True)
    activo = models.BooleanField(_('Activo'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = _('Sede')
        verbose_name_plural = _('Sedes')
        ordering = ['nombre']



class Estructura(models.Model):
    unidad_organica = models.CharField(_('Unidad orgánica'), max_length=255)
    siglas = models.CharField(_('Siglas'), max_length=50)
    padre = models.CharField(_('Padre (siglas)'), max_length=50, blank=True, null=True, 
                           help_text=_('Siglas del área padre. Dejar en blanco si es un área principal.'))
    activo = models.BooleanField(_('Activo'), default=True)
    nombre_anterior = models.CharField(_('Nombre anterior'), max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'CONTROL_ACCESO_ESTRUCTURA'
        ordering = ['siglas']
        verbose_name = _('Estructura organizativa')
        verbose_name_plural = _('Estructuras organizativas')

    def __str__(self):
        return self.unidad_organica
    
    def clean(self):
        # Si tiene padre, verificar que el padre exista
        if self.padre:
            parent_exists = Estructura.objects.filter(siglas=self.padre).exists()
            if not parent_exists:
                raise ValidationError({
                    'padre': _('El área padre con siglas %(siglas)s no existe.'),
                }, params={'siglas': self.padre})
        
        # Si cambia las siglas y es un área padre, actualizar también a las subáreas
        if self.pk:
            original = Estructura.objects.get(pk=self.pk)
            if original.siglas != self.siglas and not original.padre:
                # Es un área que cambió sus siglas, actualizar las subáreas
                Estructura.objects.filter(padre=original.siglas).update(padre=self.siglas)
    
    def is_institucion(self):
        """Devuelve True si es una institución (no tiene padre)"""
        return self.padre is None
    
    def is_area(self):
        """Devuelve True si es un área (tiene padre y no es subárea)"""
        if self.padre:
            parent = self.get_parent()
            return parent and parent.is_institucion()
        return False
    
    def is_subarea(self):
        """Devuelve True si es una subárea (su padre es un área)"""
        if self.padre:
            parent = self.get_parent()
            return parent and parent.is_area()
        return False
    
    def get_areas(self):
        """Obtiene todas las áreas activas de esta institución"""
        if self.is_institucion():
            return Estructura.objects.filter(padre=self.siglas, activo=True)
        return Estructura.objects.none()
    
    def get_subareas(self):
        """Obtiene todas las subáreas activas de esta área"""
        if self.is_area():
            return Estructura.objects.filter(padre=self.siglas, activo=True)
        return Estructura.objects.none()

class Person(models.Model):
    nombre = models.CharField(_('Nombre'), max_length=255, null=True, blank=True)
    apellido = models.CharField(_('Apellido'), max_length=255, null=True, blank=True)
    dni = models.IntegerField(_('DNI'), unique=True)
    telefono = models.CharField(_('Teléfono'), max_length=20, null=True, blank=True)
    email = models.EmailField(_('Email'), max_length=255, null=True, blank=True)
    tarjetavisita = models.CharField(_('Tarjeta de visita'), max_length=10, null=True, blank=True)
    observaciones = models.TextField(_('Observaciones'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    photo = models.BinaryField(null=True, blank=True, editable=True)

    class Meta:
        verbose_name = _('Persona')
        verbose_name_plural = _('Personas')
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.apellido}, {self.nombre} - DNI: {self.dni}"

    def get_full_name(self):
        return f"{self.nombre} {self.apellido}".strip()
    
    def has_active_visit(self, sede=None):
        """Verifica si la persona tiene una visita activa, opcionalmente filtrada por sede"""
        query = {'person': self, 'hora_salida__isnull': True}
        if sede:
            query['sede'] = sede
        return Visit.objects.filter(**query).exists()

class UserProfile(models.Model):
    """Perfil de usuario extendido para manejar el acceso a sedes"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Sede asignada'))
    is_admin = models.BooleanField(_('Es administrador'), default=False, 
                                help_text=_('Los administradores pueden ver todas las sedes'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.sede.nombre if self.sede else 'Sin sede asignada'}"

    class Meta:
        verbose_name = _('Perfil de usuario')
        verbose_name_plural = _('Perfiles de usuario')
    
    def can_access_sede(self, sede_id):
        """Determina si el usuario puede acceder a una sede específica"""
        # Administradores y superusuarios pueden acceder a todas las sedes
        if self.is_admin or self.user.is_superuser:
            return True
        
        # Usuario normal solo puede acceder a su sede asignada
        return self.sede and str(self.sede.id) == str(sede_id)

class Visit(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name=_('Persona'))
    fecha = models.DateField(_('Fecha'), default=timezone.now)
    hora_entrada = models.TimeField(_('Hora de entrada'), default=timezone.now)
    fecha_salida = models.DateField(_('Fecha de salida'), null=True, blank=True)
    hora_salida = models.TimeField(_('Hora de salida'), null=True, blank=True)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, verbose_name=_('Sede'))
    area = models.ForeignKey(Estructura, on_delete=models.CASCADE, verbose_name=_('Área'))
    receptor_nombre = models.CharField(_('Nombre del receptor'), max_length=255, null=True, blank=True)
    receptor_apellido = models.CharField(_('Apellido del receptor'), max_length=255, null=True, blank=True)
    observaciones = models.TextField(_('Observaciones'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='created_visits', verbose_name=_('Creado por'))

    class Meta:
        verbose_name = _('Visita')
        verbose_name_plural = _('Visitas')
        ordering = ['-fecha', '-hora_entrada']

    def __str__(self):
        return f"{self.person} - {self.fecha} {self.hora_entrada}"
        
    def get_receptor_full_name(self):
        if self.receptor_nombre or self.receptor_apellido:
            return f"{self.receptor_nombre} {self.receptor_apellido}".strip()
        return "No especificado"
    
    def clean(self):
        # Validar que la fecha/hora de salida sea posterior a la de entrada
        if self.hora_salida and self.fecha_salida:
            fecha_hora_salida = timezone.datetime.combine(self.fecha_salida, self.hora_salida)
            fecha_hora_entrada = timezone.datetime.combine(self.fecha, self.hora_entrada)
            if fecha_hora_salida <= fecha_hora_entrada:
                raise ValidationError({
                    'hora_salida': _('La fecha y hora de salida debe ser posterior a la de entrada.'),
                })
        
        # Validar que la tarjeta no esté en uso en esta sede
        # Solo validar si tenemos tanto la persona como la sede asignadas
        if hasattr(self, 'person') and self.person and self.sede and not self.hora_salida:
            if self.person.tarjetavisita:
                # Buscar visitas activas con esta tarjeta en esta sede (excluyendo esta misma visita)
                active_visits = Visit.objects.filter(
                    person__tarjetavisita=self.person.tarjetavisita,
                    sede=self.sede,
                    hora_salida__isnull=True
                )
                
                if self.pk:  # Si es una actualización, excluir esta misma visita
                    active_visits = active_visits.exclude(pk=self.pk)
                
                if active_visits.exists():
                    other_visit = active_visits.first()
                    raise ValidationError({
                        'person': _('La tarjeta #%(tarjeta)s ya está en uso por %(persona)s desde %(fecha)s a las %(hora)s.'),
                    }, params={
                        'tarjeta': self.person.tarjetavisita,
                        'persona': other_visit.person.get_full_name(),
                        'fecha': other_visit.fecha,
                        'hora': other_visit.hora_entrada.strftime('%H:%M')
                    })
        
    @staticmethod
    def get_argentina_datetime():
        """Retorna la fecha y hora actual de Argentina."""
        return timezone.localtime(timezone.now())
        
    @staticmethod
    def get_argentina_date():
        """Retorna la fecha actual de Argentina."""
        return timezone.localtime(timezone.now()).date()
        
    @staticmethod
    def get_argentina_time():
        """Retorna la hora actual de Argentina."""
        return timezone.localtime(timezone.now()).time()
    
    def register_exit(self):
        """Registra la salida de la visita con la fecha y hora actual"""
        if self.hora_salida:
            raise ValidationError(_('Esta visita ya tiene registrada la salida.'))
        
        now = timezone.localtime(timezone.now())
        self.fecha_salida = now.date()
        self.hora_salida = now.time()
        self.save()
