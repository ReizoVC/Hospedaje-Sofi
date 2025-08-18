document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.querySelector('form');
    
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
    
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showMessage('¡Sesión iniciada exitosamente!', 'success');
                // Pequeña pausa para mostrar la notificación antes de redirigir
                setTimeout(() => {
                    window.location.href = '/';
                }, 1000);
            } else {
                showMessage(data.error || 'Error al iniciar sesión', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showMessage('Error de conexión. Intenta nuevamente.', 'error');
        }
    });
});