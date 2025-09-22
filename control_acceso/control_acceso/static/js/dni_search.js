// Script para buscar personas por DNI automáticamente
document.addEventListener('DOMContentLoaded', function() {
    // Obtener el campo de DNI
    const dniField = document.getElementById('id_dni');
    
    if (dniField) {
        // Agregar listener para detectar cambios en el campo DNI
        dniField.addEventListener('blur', function() {
            const dni = this.value.trim();
            if (dni) {
                searchPersonByDNI(dni);
            }
        });
        
        // También podemos agregar un evento para buscar al presionar Enter
        dniField.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault(); // Prevenir el envío del formulario
                const dni = this.value.trim();
                if (dni) {
                    searchPersonByDNI(dni);
                }
            }
        });
    }
    
    // Función para buscar persona por DNI mediante AJAX
    function searchPersonByDNI(dni) {
        // Mostrar indicador de carga
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'block';
        }
        
        // Realizar petición AJAX
        fetch(`/search-person/?dni=${dni}`)
            .then(response => response.json())
            .then(data => {
                // Ocultar indicador de carga
                if (loadingIndicator) {
                    loadingIndicator.style.display = 'none';
                }
                
                if (data.found) {
                    // Rellenar el formulario con los datos encontrados
                    fillPersonForm(data);
                    
                    // Si tiene una visita activa, mostrar un mensaje
                    if (data.has_active_visit) {
                        showActiveVisitMessage(data);
                    }
                } else {
                    // Limpiar el formulario excepto el DNI
                    clearPersonForm(dni);
                    
                    // Opcional: Mostrar mensaje de que la persona no existe
                    const messageContainer = document.getElementById('message-container');
                    if (messageContainer) {
                        messageContainer.innerHTML = 
                            '<div class="alert alert-info alert-dismissible fade show" role="alert">' +
                            'Persona no encontrada. Por favor complete los datos para registrarla.' +
                            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' +
                            '</div>';
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                // Ocultar indicador de carga en caso de error
                if (loadingIndicator) {
                    loadingIndicator.style.display = 'none';
                }
                
                // Mostrar mensaje de error
                const messageContainer = document.getElementById('message-container');
                if (messageContainer) {
                    messageContainer.innerHTML = 
                        '<div class="alert alert-danger alert-dismissible fade show" role="alert">' +
                        'Error al buscar persona. Por favor intente nuevamente.' +
                        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' +
                        '</div>';
                }
            });
    }
    
    // Función para rellenar el formulario con los datos de la persona
    function fillPersonForm(data) {
        // Establecer ID de persona (en un campo oculto)
        const personIdField = document.getElementById('person_id');
        if (personIdField) {
            personIdField.value = data.id;
        }
        
        // Rellenar los campos del formulario
        document.getElementById('id_nombre').value = data.nombre || '';
        document.getElementById('id_apellido').value = data.apellido || '';
        document.getElementById('id_telefono').value = data.telefono || '';
        document.getElementById('id_email').value = data.email || '';
        document.getElementById('id_tarjetavisita').value = data.tarjetavisita || '';
        document.getElementById('id_observaciones').value = data.observaciones || '';
        
        // Si tiene foto, mostrarla
        if (data.has_photo) {
            // Obtener la foto mediante otra petición
            fetch(`/get-person-photo/${data.id}/`)
                .then(response => response.blob())
                .then(blob => {
                    const photoPreview = document.getElementById('photo-preview');
                    if (photoPreview) {
                        photoPreview.src = URL.createObjectURL(blob);
                        photoPreview.style.display = 'block';
                    }
                })
                .catch(error => console.error('Error al cargar la foto:', error));
        }
    }
    
    // Función para limpiar el formulario
    function clearPersonForm(dni) {
        // Mantener solo el DNI
        document.getElementById('id_nombre').value = '';
        document.getElementById('id_apellido').value = '';
        document.getElementById('id_telefono').value = '';
        document.getElementById('id_email').value = '';
        document.getElementById('id_tarjetavisita').value = '';
        document.getElementById('id_observaciones').value = '';
        
        // Limpiar ID de persona
        const personIdField = document.getElementById('person_id');
        if (personIdField) {
            personIdField.value = '';
        }
        
        // Limpiar vista previa de foto
        const photoPreview = document.getElementById('photo-preview');
        if (photoPreview) {
            photoPreview.src = '';
            photoPreview.style.display = 'none';
        }
    }
    
    // Función para mostrar mensaje de visita activa
    function showActiveVisitMessage(data) {
        const messageContainer = document.getElementById('message-container');
        if (messageContainer) {
            const visitInfo = `
                <strong>Sede:</strong> ${data.active_visit_sede}<br>
                <strong>Área:</strong> ${data.active_visit_area}<br>
                <strong>Subárea:</strong> ${data.active_visit_subarea || 'N/A'}<br>
                <strong>Fecha:</strong> ${data.active_visit_fecha}<br>
                <strong>Hora de entrada:</strong> ${data.active_visit_hora_entrada}
            `;
            
            messageContainer.innerHTML = 
                '<div class="alert alert-warning alert-dismissible fade show" role="alert">' +
                '<h5 class="alert-heading">¡Atención! Esta persona tiene una visita activa</h5>' +
                '<p>No se puede registrar una nueva visita hasta registrar la salida de la visita actual:</p>' +
                `<p>${visitInfo}</p>` +
                '<hr>' +
                `<a href="/register-exit/${data.active_visit_id}/" class="btn btn-primary">Registrar Salida</a>` +
                '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' +
                '</div>';
        }
    }
});