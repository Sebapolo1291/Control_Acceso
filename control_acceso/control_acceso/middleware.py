from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.utils.deprecation import MiddlewareMixin

class LoginRequiredMiddleware(MiddlewareMixin):
    """
    Middleware para requerir inicio de sesión en todas las páginas excepto login y admin.
    """
    
    # Vistas que están exentas de requerir inicio de sesión
    EXEMPT_URLS = [
        'login', 'admin:', 'static', 'media',
    ]
    
    def process_request(self, request):
        # Verificar si el usuario ya está autenticado
        if request.user.is_authenticated:
            return None
            
        # Obtener la URL actual
        current_url = resolve(request.path_info).url_name
        
        # Si la URL está en la lista de exentas, no hacer nada
        if current_url is None or any(url in str(current_url) for url in self.EXEMPT_URLS):
            return None
            
        # Redirigir a la página de login con next para volver después
        return redirect(f"{reverse('login')}?next={request.path}")
