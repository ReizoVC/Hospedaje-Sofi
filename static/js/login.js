document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm') || document.querySelector('form');
    if (!loginForm) return;

    // Función fallback para mostrar mensajes si las funciones globales no están disponibles
    const showMessage = (message, type = 'info') => {
        if (typeof window.showSuccess === 'function' && type === 'success') {
            window.showSuccess(message);
        } else if (typeof window.showError === 'function' && type === 'error') {
            window.showError(message);
        } else {
            // Fallback básico
            alert(message);
        }
    };
    
    const redirectByRole = (rol) => {
        // Ajusta si tus rutas reales difieren
        if (rol === 4) return '/trabajadores/gestion';
        if (rol === 3) return '/trabajadores/inventario';
        if (rol === 2) return '/trabajadores/gestion-reservas';
        return '/';
    };

    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const endpoint = loginForm.dataset.loginEndpoint || '/api/login';
        const email = document.getElementById('email')?.value || '';
        const password = document.getElementById('password')?.value || '';
        
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });
            
            const data = await response.json().catch(() => ({}));
            
            if (response.ok) {
                showMessage('¡Sesión iniciada exitosamente!', 'success');
                const rol = data?.user?.rol;
                // Pequeña pausa para mostrar la notificación antes de redirigir
                setTimeout(() => {
                    window.location.href = redirectByRole(rol);
                }, 700);
            } else {
                showMessage(data.error || 'Error al iniciar sesión', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showMessage('Error de conexión. Intenta nuevamente.', 'error');
        }
    });
});