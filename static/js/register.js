document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.querySelector('form');
    
    const showMessage = (message, type = 'info') => {
        if (typeof window.showSuccess === 'function' && type === 'success') {
            window.showSuccess(message);
        } else if (typeof window.showError === 'function' && type === 'error') {
            window.showError(message);
        } else {
            alert(message);
        }
    };
    
    registerForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            name: document.getElementById('name').value,
            lastName: document.getElementById('lastName').value,
            dni: document.getElementById('dni').value,
            phone: document.getElementById('phone').value,
            email: document.getElementById('email').value,
            password: document.getElementById('password').value
        };
        
        if (formData.dni.length !== 8) {
            showMessage('El DNI debe tener 8 dígitos', 'error');
            return;
        }
        
        if (formData.password.length < 6) {
            showMessage('La contraseña debe tener al menos 6 caracteres', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
        if (response.ok) {
                showMessage('¡Usuario registrado exitosamente!', 'success');
                const target = (data && data.authenticated) ? '/' : '/login';
                setTimeout(() => {
                    window.location.href = target;
                }, 800);
            } else {
                showMessage(data.error || 'Error al registrar usuario', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showMessage('Error de conexión. Intenta nuevamente.', 'error');
        }
    });
    
    const dniInput = document.getElementById('dni');
    dniInput.addEventListener('input', function() {
        this.value = this.value.replace(/\D/g, '');
        if (this.value.length > 8) {
            this.value = this.value.slice(0, 8);
        }
    });
});