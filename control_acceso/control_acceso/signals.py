from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crea un perfil de usuario automáticamente cuando se crea un usuario nuevo
    """
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Guarda el perfil de usuario automáticamente cuando se guarda un usuario
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        # En caso de que el perfil no exista (usuarios antiguos)
        UserProfile.objects.create(user=instance)
