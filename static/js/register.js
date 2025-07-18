document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.querySelector('form');
    
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
        
        // Validaciones básicas
        if (formData.dni.length !== 8) {
            alert('El DNI debe tener 8 dígitos');
            return;
        }
        
        if (formData.password.length < 6) {
            alert('La contraseña debe tener al menos 6 caracteres');
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
                alert('Usuario registrado exitosamente');
                // Redirigir al login
                window.location.href = '/login';
            } else {
                alert(data.error || 'Error al registrar usuario');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error de conexión. Intenta nuevamente.');
        }
    });
    
    // Validación del DNI en tiempo real
    const dniInput = document.getElementById('dni');
    dniInput.addEventListener('input', function() {
        this.value = this.value.replace(/\D/g, '');
        if (this.value.length > 8) {
            this.value = this.value.slice(0, 8);
        }
    });
});