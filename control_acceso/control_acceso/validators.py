from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Visit

def validate_tarjeta_visita_available(tarjeta, sede_id):
    """
    Valida que una tarjeta de visita no esté en uso en la misma sede 
    (visitas activas sin salida registrada).
    
    Parámetros:
    - tarjeta: Número de tarjeta a validar
    - sede_id: ID de la sede donde se intenta usar la tarjeta
    
    Devuelve:
    - True si la tarjeta está disponible
    - Lanza ValidationError si la tarjeta ya está en uso
    """
    if not tarjeta or not sede_id:
        return True
        
    # Verificar si existe alguna visita activa (sin salida) usando esta tarjeta en esta sede
    active_visit = Visit.objects.filter(
        person__tarjetavisita=tarjeta,
        sede_id=sede_id,
        hora_salida__isnull=True
    ).first()
    
    if active_visit:
        person = active_visit.person
        raise ValidationError(
            _(f'La tarjeta de visita #{tarjeta} ya está en uso por {person.nombre} {person.apellido} '
              f'desde {active_visit.fecha} {active_visit.hora_entrada}. '
              f'Debe registrar la salida antes de volver a usar esta tarjeta en esta sede.')
        )
    
    return True
