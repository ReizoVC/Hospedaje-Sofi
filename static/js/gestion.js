document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    let habitacionActual = null;
    let habitacionImagenActual = null;
    
    // Elementos del DOM
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const modal = document.getElementById('modal-habitacion');
    const modalImagenes = document.getElementById('modal-imagenes');
    const modalTitulo = document.getElementById('modal-titulo');
    const form = document.getElementById('form-habitacion');
    const btnNuevaHabitacion = document.getElementById('btn-nueva-habitacion');
    const btnCerrarModal = document.getElementById('btn-cerrar-modal');
    const btnCerrarModalImagenes = document.getElementById('btn-cerrar-modal-imagenes');
    const btnCerrarImagenes = document.getElementById('btn-cerrar-imagenes');
    const btnCancelar = document.getElementById('btn-cancelar');
    const habitacionesTbody = document.getElementById('habitaciones-tbody');

    // Inicialización
    inicializar();
    
    function inicializar() {
        configurarEventListeners();
        cargarHabitaciones();
    }
    
    function configurarEventListeners() {
        // Manejo de pestañas
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => cambiarTab(btn.dataset.tab));
        });
        
        // Modal
        btnNuevaHabitacion.addEventListener('click', () => abrirModal());
        btnCerrarModal.addEventListener('click', cerrarModal);
        btnCancelar.addEventListener('click', cerrarModal);
        
        // Modal de imágenes
        btnCerrarModalImagenes.addEventListener('click', cerrarModalImagenes);
        btnCerrarImagenes.addEventListener('click', cerrarModalImagenes);
        
        // Cerrar modal al hacer clic fuera
        modal.addEventListener('click', (e) => {
            if (e.target === modal) cerrarModal();
        });
        
        modalImagenes.addEventListener('click', (e) => {
            if (e.target === modalImagenes) cerrarModalImagenes();
        });
        
        // Formulario
        form.addEventListener('submit', guardarHabitacion);
    }
    
    function cambiarTab(tabId) {
        // Actualizar botones
        tabBtns.forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
        
        // Actualizar contenido
        tabContents.forEach(content => content.classList.remove('active'));
        document.getElementById(tabId).classList.add('active');
    }
    
    function abrirModal(habitacion = null) {
        habitacionActual = habitacion;
        
        if (habitacion) {
            modalTitulo.textContent = 'Editar Habitación';
            llenarFormulario(habitacion);
        } else {
            modalTitulo.textContent = 'Nueva Habitación';
            form.reset();
        }
        
        modal.classList.add('active');
    }
    
    function cerrarModal() {
        modal.classList.remove('active');
        form.reset();
        habitacionActual = null;
    }
    
    function abrirModalImagenes(idhabitacion) {
        habitacionImagenActual = idhabitacion;
        document.getElementById('modal-imagenes-titulo').textContent = `Gestionar Imágenes - Habitación ${idhabitacion}`;
        modalImagenes.classList.add('active');
        cargarImagenesHabitacion(idhabitacion);
    }
    
    function cerrarModalImagenes() {
        modalImagenes.classList.remove('active');
        habitacionImagenActual = null;
    }
    
    function llenarFormulario(habitacion) {
        document.getElementById('numero').value = habitacion.numero;
        document.getElementById('nombre').value = habitacion.nombre;
        document.getElementById('estado').value = habitacion.estado;
        document.getElementById('capacidad').value = habitacion.capacidad;
        document.getElementById('precio_noche').value = habitacion.precio_noche;
        document.getElementById('tamano_m2').value = habitacion.tamano_m2 || '';
        document.getElementById('camas').value = habitacion.camas || '';
        document.getElementById('descripcion').value = habitacion.descripcion || '';
        document.getElementById('servicios').value = habitacion.servicios ? habitacion.servicios.join(', ') : '';
    }
    
    async function guardarHabitacion(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const data = {
            numero: parseInt(formData.get('numero')),
            nombre: formData.get('nombre'),
            estado: formData.get('estado'),
            capacidad: parseInt(formData.get('capacidad')),
            precio_noche: parseFloat(formData.get('precio_noche')),
            tamano_m2: formData.get('tamano_m2') ? parseInt(formData.get('tamano_m2')) : null,
            camas: formData.get('camas'),
            descripcion: formData.get('descripcion'),
            servicios: formData.get('servicios') ? formData.get('servicios').split(',').map(s => s.trim()) : []
        };
        
        try {
            const url = habitacionActual ? 
                `/api/habitaciones/${habitacionActual.idhabitacion}` : 
                '/api/habitaciones';
            const method = habitacionActual ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                mostrarMensaje('Habitación guardada exitosamente', 'success');
                cerrarModal();
                cargarHabitaciones();
            } else {
                mostrarMensaje(result.error || 'Error al guardar habitación', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            mostrarMensaje('Error de conexión', 'error');
        }
    }
    
    async function cargarHabitaciones() {
        try {
            console.log('Cargando habitaciones...');
            const response = await fetch('/api/habitaciones');
            console.log('Response status:', response.status);
            
            if (response.ok) {
                const habitaciones = await response.json();
                console.log('Habitaciones recibidas:', habitaciones);
                renderizarHabitaciones(habitaciones);
            } else {
                const errorData = await response.json();
                console.error('Error response:', errorData);
                mostrarMensaje(`Error al cargar habitaciones: ${errorData.error || 'Error desconocido'}`, 'error');
            }
        } catch (error) {
            console.error('Error de red:', error);
            mostrarMensaje('Error de conexión al cargar habitaciones', 'error');
        }
    }
    
    function renderizarHabitaciones(habitaciones) {
        habitacionesTbody.innerHTML = '';
        
        habitaciones.forEach(habitacion => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${habitacion.idhabitacion}</td>
                <td>${habitacion.numero}</td>
                <td>${habitacion.nombre}</td>
                <td><span class="estado-badge estado-${habitacion.estado}">${habitacion.estado}</span></td>
                <td>${habitacion.capacidad}</td>
                <td>S/ ${habitacion.precio_noche}</td>
                <td>
                    <button class="btn-action btn-edit" onclick="editarHabitacion(${habitacion.idhabitacion})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-action btn-images" onclick="gestionarImagenes(${habitacion.idhabitacion})" title="Gestionar Imágenes">
                        <i class="fas fa-images"></i>
                    </button>
                    <button class="btn-action btn-delete" onclick="eliminarHabitacion(${habitacion.idhabitacion})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            habitacionesTbody.appendChild(row);
        });
    }
    
    // Funciones globales
    window.editarHabitacion = async function(id) {
        try {
            const response = await fetch(`/api/habitaciones/${id}`);
            const habitacion = await response.json();
            
            if (response.ok) {
                abrirModal(habitacion);
            } else {
                mostrarMensaje('Error al cargar habitación', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            mostrarMensaje('Error de conexión', 'error');
        }
    };
    
    window.eliminarHabitacion = async function(id) {
        if (!confirm('¿Estás seguro de que deseas eliminar esta habitación?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/habitaciones/${id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                mostrarMensaje('Habitación eliminada exitosamente', 'success');
                cargarHabitaciones();
            } else {
                const result = await response.json();
                mostrarMensaje(result.error || 'Error al eliminar habitación', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            mostrarMensaje('Error de conexión', 'error');
        }
    };
    
    // Funciones para gestión de imágenes
    window.gestionarImagenes = function(id) {
        abrirModalImagenes(id);
    };
    
    window.subirImagenes = async function() {
        const fileInput = document.getElementById('upload-imagenes');
        const files = fileInput.files;
        
        if (files.length === 0) {
            mostrarMensaje('Selecciona al menos una imagen', 'error');
            return;
        }
        
        for (let i = 0; i < files.length; i++) {
            const formData = new FormData();
            formData.append('imagen', files[i]);
            formData.append('idhabitacion', habitacionImagenActual);
            formData.append('orden', i + 1);
            
            try {
                const response = await fetch('/api/imagenes-habitacion', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    mostrarMensaje(error.error || 'Error al subir imagen', 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                mostrarMensaje('Error de conexión', 'error');
            }
        }
        
        fileInput.value = '';
        cargarImagenesHabitacion(habitacionImagenActual);
        mostrarMensaje('Imágenes subidas exitosamente', 'success');
    };
    
    async function cargarImagenesHabitacion(idhabitacion) {
        try {
            const response = await fetch(`/api/imagenes-habitacion/${idhabitacion}`);
            const imagenes = await response.json();
            
            if (response.ok) {
                renderizarImagenes(imagenes);
            } else {
                mostrarMensaje('Error al cargar imágenes', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            mostrarMensaje('Error de conexión', 'error');
        }
    }
    
    function renderizarImagenes(imagenes) {
        const container = document.getElementById('imagenes-list');
        container.innerHTML = '';
        
        imagenes.forEach(imagen => {
            const div = document.createElement('div');
            div.className = 'imagen-item';
            div.innerHTML = `
                <img src="/static/uploads/${imagen.url}" alt="Imagen habitación">
                <div class="imagen-controls">
                    <input type="number" class="orden-input" value="${imagen.orden}" 
                            onchange="actualizarOrden(${imagen.idimagen}, this.value)" min="1">
                    <button class="btn-delete-image" onclick="eliminarImagen(${imagen.idimagen})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            container.appendChild(div);
        });
    }
    
    window.actualizarOrden = async function(idimagen, nuevoOrden) {
        try {
            const response = await fetch(`/api/imagenes-habitacion/${idimagen}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ orden: parseInt(nuevoOrden) })
            });
            
            if (response.ok) {
                cargarImagenesHabitacion(habitacionImagenActual);
            } else {
                mostrarMensaje('Error al actualizar orden', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            mostrarMensaje('Error de conexión', 'error');
        }
    };
    
    window.eliminarImagen = async function(idimagen) {
        if (!confirm('¿Estás seguro de que deseas eliminar esta imagen?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/imagenes-habitacion/${idimagen}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                mostrarMensaje('Imagen eliminada exitosamente', 'success');
                cargarImagenesHabitacion(habitacionImagenActual);
            } else {
                const result = await response.json();
                mostrarMensaje(result.error || 'Error al eliminar imagen', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            mostrarMensaje('Error de conexión', 'error');
        }
    };
    
    function mostrarMensaje(mensaje, tipo) {
        // Implementación simple de notificación
        alert(mensaje);
    }
});