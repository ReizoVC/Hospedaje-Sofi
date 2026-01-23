document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    let habitacionActual = null;
    let habitacionImagenActual = null;
    let reservaActual = null;
    // Prefijo base dinámico según la ruta actual (p.ej. /trabajadores)
    const BASE = '/' + (window.location.pathname.split('/')[1] || '');
    
    // Elementos del DOM
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const modal = document.getElementById('modal-habitacion');
    const modalImagenes = document.getElementById('modal-imagenes');
    const modalTitulo = document.getElementById('modal-titulo');
    const form = document.getElementById('form-habitacion');
    const btnNuevaHabitacion = document.getElementById('btn-nueva-habitacion');
    const btnCerrarModal = document.getElementById('btn-cerrar-modal');
    const personalTbody = document.getElementById('personal-tbody');
    const btnNuevoPersonal = document.getElementById('btn-nuevo-personal');
    const desactivadosTbody = document.getElementById('desactivados-tbody');
    const btnRefrescarDesactivados = document.getElementById('btn-refrescar-desactivados');
    const btnCerrarModalImagenes = document.getElementById('btn-cerrar-modal-imagenes');
    const btnCerrarImagenes = document.getElementById('btn-cerrar-imagenes');
    const btnCancelar = document.getElementById('btn-cancelar');
    const habitacionesTbody = document.getElementById('habitaciones-tbody');
    const reservasTbody = document.getElementById('reservas-tbody');
    const btnNuevaReserva = document.getElementById('btn-nueva-reserva');
    const modalReserva = document.getElementById('modal-reserva');
    const modalReservaTitulo = document.getElementById('modal-reserva-titulo');
    const btnCerrarModalReserva = document.getElementById('btn-cerrar-modal-reserva');
    const btnCancelarReserva = document.getElementById('btn-cancelar-reserva');
    const formReserva = document.getElementById('form-reserva');
    // Modal Personal
    const modalPersonal = document.getElementById('modal-personal');
    const modalPersonalTitulo = document.getElementById('modal-personal-titulo');
    const btnCerrarModalPersonal = document.getElementById('btn-cerrar-modal-personal');
    const btnCancelarPersonal = document.getElementById('btn-cancelar-personal');
    const formPersonal = document.getElementById('form-personal');
    let personalActual = null;

    // Inicialización
    inicializar();
    
    function inicializar() {
        configurarEventListeners();
        cargarHabitaciones();
        // Activar pestaña en base al hash de la URL si existe
    activarPestañaPorHash();
    cargarReservas();
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

    // Modal de reservas
        if (btnNuevaReserva) btnNuevaReserva.addEventListener('click', () => abrirModalReserva());
        if (btnCerrarModalReserva) btnCerrarModalReserva.addEventListener('click', cerrarModalReserva);
        if (btnCancelarReserva) btnCancelarReserva.addEventListener('click', cerrarModalReserva);
        if (modalReserva) {
            modalReserva.addEventListener('click', (e) => {
                if (e.target === modalReserva) cerrarModalReserva();
            });
        }
        if (formReserva) formReserva.addEventListener('submit', guardarReserva);

    // Personal
        if (btnNuevoPersonal) {
            btnNuevoPersonal.addEventListener('click', () => abrirModalPersonal());
        }
        // Modal Personal
        if (btnCerrarModalPersonal) btnCerrarModalPersonal.addEventListener('click', cerrarModalPersonal);
        if (btnCancelarPersonal) btnCancelarPersonal.addEventListener('click', cerrarModalPersonal);
        if (modalPersonal) {
            modalPersonal.addEventListener('click', (e) => { if (e.target === modalPersonal) cerrarModalPersonal(); });
        }
        if (formPersonal) formPersonal.addEventListener('submit', guardarPersonal);

    // Desactivados
        if (btnRefrescarDesactivados) {
            btnRefrescarDesactivados.addEventListener('click', cargarDesactivados);
        }
    }
    
    function cambiarTab(tabId) {
        // Actualizar botones
        tabBtns.forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
        
        // Actualizar contenido
        tabContents.forEach(content => content.classList.remove('active'));
        document.getElementById(tabId).classList.add('active');
    // Actualizar hash de la URL sin recargar
    if (['habitaciones', 'reservas', 'personal', 'desactivados'].includes(tabId)) {
            history.replaceState(null, '', `#${tabId}`);
        }
    // Lazy load por pestaña
        if (tabId === 'personal') cargarPersonal();
        if (tabId === 'desactivados') cargarDesactivados();
    }

    // ======= PERSONAL DESACTIVADOS =======
    async function cargarDesactivados(){
        if (!desactivadosTbody) return;
        try {
            const res = await fetch(`${BASE}/api/personal/desactivados`);
            const data = await res.json();
            if (res.ok) {
                const filtrado = Array.isArray(data) ? data.filter(p => p.rol !== 4) : [];
                renderizarDesactivados(filtrado);
            }
            else showError(data.error || 'Error al cargar desactivados');
        } catch (e) { showError('Error de conexión'); }
    }
    function renderizarDesactivados(lista){
        desactivadosTbody.innerHTML = '';
        lista.forEach(p => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${p.nombre}</td>
                <td>${p.apellidos}</td>
                <td>${p.correo}</td>
                <td>${p.dni}</td>
                <td>${p.telefono || ''}</td>
                <td>
                    <button class="btn-action" onclick="reactivarPersonal('${p.idusuario}')"><i class="fas fa-user-check"></i> Reactivar</button>
                </td>`;
            desactivadosTbody.appendChild(tr);
        });
    }
    window.reactivarPersonal = async function(id){
        const rol = parseInt(prompt('Asignar rol (2=Recep, 3=Almacenista, 4=Admin):', 2));
        if (![2,3,4].includes(rol)) { showWarning('Rol inválido'); return; }
        try {
            const res = await fetch(`${BASE}/api/personal/${id}/reactivar`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ rol }) });
            const data = await res.json();
            if (res.ok) { showSuccess('Personal reactivado'); cargarDesactivados(); cargarPersonal(); }
            else showError(data.error || 'No se pudo reactivar');
        } catch (e) { showError('Error de conexión'); }
    }

    function activarPestañaPorHash() {
        const hash = window.location.hash.replace('#', '');
        if (['habitaciones', 'reservas', 'personal', 'desactivados'].includes(hash)) {
            cambiarTab(hash);
        }
    // Cambiar pestaña si el hash cambia
        window.addEventListener('hashchange', () => {
            const nuevoHash = window.location.hash.replace('#', '');
            if (['habitaciones', 'reservas', 'personal', 'desactivados'].includes(nuevoHash)) {
                cambiarTab(nuevoHash);
            }
        });
    }
    async function cargarPersonal(){
        if (!personalTbody) return;
        try {
            const res = await fetch(`${BASE}/api/personal`);
            const data = await res.json();
            if (res.ok) {
                const filtrado = Array.isArray(data) ? data.filter(p => p.rol !== 4) : [];
                renderizarPersonal(filtrado);
            }
            else showError(data.error || 'Error al cargar personal');
        } catch (e) { showError('Error de conexión'); }
    }

    function renderizarPersonal(lista){
        personalTbody.innerHTML = '';
        lista.forEach(p => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${p.nombre}</td>
                <td>${p.apellidos}</td>
                <td>${p.correo}</td>
                <td>${p.dni}</td>
                <td>${p.telefono || ''}</td>
                <td>${rolLabel(p.rol)}</td>
                <td>
                    <button class="btn-action btn-edit" onclick="editarPersonal('${p.idusuario}')"><i class="fas fa-edit"></i></button>
                    <button class="btn-action btn-delete" onclick="desactivarPersonal('${p.idusuario}')"><i class="fas fa-user-slash"></i></button>
                </td>`;
            personalTbody.appendChild(tr);
        });
    }

    function rolLabel(rol){
        switch(rol){
            case 2: return 'Recepcionista';
            case 3: return 'Almacenista';
            case 4: return 'Administrador';
            default: return rol;
        }
    }

    window.editarPersonal = async function(id){
        try {
            const res = await fetch(`${BASE}/api/personal`);
            const lista = await res.json();
            const actual = Array.isArray(lista) ? lista.find(u => u.idusuario === id) : null;
            if (!actual) { showError('Personal no encontrado'); return; }
            abrirModalPersonal(actual);
        } catch (e) { showError('Error de conexión'); }
    }

    window.desactivarPersonal = async function(id){
        const ok = await mostrarConfirmacion('¿Desactivar personal?', 'Podrás reactivarlo luego');
        if (!ok) return;
        try {
            const r = await fetch(`${BASE}/api/personal/${id}`, { method: 'DELETE' });
            const d = await r.json();
            if (r.ok) { showSuccess('Personal desactivado'); cargarPersonal(); }
            else showError(d.error || 'No se pudo desactivar');
        } catch (e) { showError('Error de conexión'); }
    }

    // ==== Modal de Personal ====
    function abrirModalPersonal(actual = null){
        personalActual = actual;
        if (modalPersonalTitulo) modalPersonalTitulo.textContent = actual ? 'Editar Personal' : 'Nuevo Personal';
        if (formPersonal) formPersonal.reset();
        if (actual){
            document.getElementById('per-nombre').value = actual.nombre || '';
            document.getElementById('per-apellidos').value = actual.apellidos || '';
            document.getElementById('per-correo').value = actual.correo || '';
            document.getElementById('per-dni').value = actual.dni || '';
            document.getElementById('per-telefono').value = actual.telefono || '';
            document.getElementById('per-rol').value = String([2,3].includes(actual.rol) ? actual.rol : 2);
        }
        if (modalPersonal) modalPersonal.classList.add('active');
    }
    function cerrarModalPersonal(){
        if (modalPersonal) modalPersonal.classList.remove('active');
        if (formPersonal) formPersonal.reset();
        personalActual = null;
    }
    async function guardarPersonal(e){
        e.preventDefault();
        const fd = new FormData(formPersonal);
        const payload = Object.fromEntries(fd.entries());
        payload.rol = parseInt(payload.rol, 10);
        if (!payload.clave) delete payload.clave;
        try {
            if (!personalActual){
                if (!payload.clave){ showWarning('Ingrese una clave'); return; }
                const res = await fetch(`${BASE}/api/personal`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                const raw = await res.text();
                let data; try { data = JSON.parse(raw); } catch { data = { raw } }
                if (res.ok){ showSuccess('Personal creado'); cerrarModalPersonal(); cargarPersonal(); }
                else {
                    const safePayload = { ...payload }; if (safePayload.clave) safePayload.clave = '***';
                    console.error('Error creando personal', { status: res.status, statusText: res.statusText, response: data, payload: safePayload });
                    showError((data && data.error) || 'No se pudo crear');
                }
            } else {
                const res = await fetch(`${BASE}/api/personal/${personalActual.idusuario}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                const raw = await res.text();
                let data; try { data = JSON.parse(raw); } catch { data = { raw } }
                if (res.ok){ showSuccess('Personal actualizado'); cerrarModalPersonal(); cargarPersonal(); }
                else {
                    console.error('Error actualizando personal', { status: res.status, statusText: res.statusText, response: data, id: personalActual.idusuario });
                    showError((data && data.error) || 'No se pudo actualizar');
                }
            }
        } catch (e) { console.error('Error de conexión al crear/actualizar personal', e); showError('Error de conexión'); }
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
                `${BASE}/api/habitaciones/${habitacionActual.idhabitacion}` : 
                `${BASE}/api/habitaciones`;
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
            const response = await fetch(`${BASE}/api/habitaciones`);
            
            if (response.ok) {
                const habitaciones = await response.json();
                renderizarHabitaciones(habitaciones);
            } else {
                const errorData = await response.json();
                mostrarMensaje(`Error al cargar habitaciones: ${errorData.error || 'Error desconocido'}`, 'error');
            }
        } catch (error) {
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

    // ======= RESERVAS (ADMIN) =======
    function abrirModalReserva(reserva = null) {
        reservaActual = reserva;
        if (reserva) {
            modalReservaTitulo.textContent = 'Editar Reserva';
        } else {
            modalReservaTitulo.textContent = 'Nueva Reserva';
            formReserva.reset();
        }
        // Cargar opciones y luego llenar si edita
        cargarOpcionesReserva().then(() => {
            if (reserva) llenarFormularioReserva(reserva);
            modalReserva.classList.add('active');
        });
    }

    function cerrarModalReserva() {
        if (modalReserva) modalReserva.classList.remove('active');
        reservaActual = null;
        if (formReserva) formReserva.reset();
    }

    async function cargarOpcionesReserva() {
        try {
            const res = await fetch(`${BASE}/api/reservas/opciones`);
            if (!res.ok) throw new Error('No se pudo cargar opciones');
            const data = await res.json();
            const selUsuario = document.getElementById('res-usuario');
            const selHabitacion = document.getElementById('res-habitacion');
            selUsuario.innerHTML = '';
            selHabitacion.innerHTML = '';
            data.usuarios.forEach(u => {
                const opt = document.createElement('option');
                opt.value = u.idusuario;
                opt.textContent = `${u.nombre} ${u.apellidos} - ${u.correo}`;
                selUsuario.appendChild(opt);
            });
            data.habitaciones.forEach(h => {
                const opt = document.createElement('option');
                opt.value = h.idhabitacion;
                opt.textContent = `#${h.numero} - ${h.nombre}`;
                selHabitacion.appendChild(opt);
            });
        } catch (e) {
            mostrarMensaje('Error al cargar opciones', 'error');
        }
    }

    function llenarFormularioReserva(reserva) {
        document.getElementById('res-usuario').value = reserva.idusuario;
        document.getElementById('res-habitacion').value = reserva.idhabitacion;
        document.getElementById('res-fechainicio').value = reserva.fechainicio;
        document.getElementById('res-fechafin').value = reserva.fechafin;
        document.getElementById('res-estado').value = reserva.estado;
    }

    async function guardarReserva(e) {
        e.preventDefault();
        const fd = new FormData(formReserva);
        const data = Object.fromEntries(fd.entries());
        try {
            const url = reservaActual ? `${BASE}/api/reservas/${reservaActual.idreserva}` : `${BASE}/api/reservas`;
            const method = reservaActual ? 'PUT' : 'POST';
            const resp = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await resp.json();
            if (resp.ok) {
                mostrarMensaje('Reserva guardada', 'success');
                cerrarModalReserva();
                cargarReservas();
            } else {
                mostrarMensaje(result.error || 'Error al guardar', 'error');
            }
        } catch (err) {
            mostrarMensaje('Error de conexión', 'error');
        }
    }

    async function cargarReservas() {
        if (!reservasTbody) return;
        try {
            const res = await fetch(`${BASE}/api/reservas`);
            const data = await res.json();
            if (res.ok) {
                renderizarReservas(data);
            } else {
                mostrarMensaje(data.error || 'Error al cargar reservas', 'error');
            }
        } catch (e) {
            mostrarMensaje('Error de conexión', 'error');
        }
    }

    function renderizarReservas(reservas) {
        reservasTbody.innerHTML = '';
        reservas.forEach(r => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${r.idreserva}</td>
                <td>${r.codigoreserva}</td>
                <td>${r.usuario ? (r.usuario.nombre + ' ' + r.usuario.apellidos) : '-'}</td>
                <td>${r.habitacion ? ('#' + r.habitacion.numero + ' ' + r.habitacion.nombre) : '-'}</td>
                <td>${r.fechainicio}</td>
                <td>${r.fechafin}</td>
                <td><span class="estado-badge">${r.estado}</span></td>
                <td>
                    <button class="btn-action btn-edit" onclick="editarReserva(${r.idreserva})"><i class="fas fa-edit"></i></button>
                    <button class="btn-action btn-delete" onclick="eliminarReserva(${r.idreserva})"><i class="fas fa-trash"></i></button>
                </td>
            `;
            reservasTbody.appendChild(tr);
        });
    }

    window.editarReserva = async function(id) {
        try {
            const res = await fetch(`${BASE}/api/reservas/${id}`);
            const data = await res.json();
            if (res.ok) {
                abrirModalReserva(data);
            } else {
                mostrarMensaje(data.error || 'Error al cargar reserva', 'error');
            }
        } catch (e) {
            mostrarMensaje('Error de conexión', 'error');
        }
    }

    window.eliminarReserva = async function(id) {
        const ok = await mostrarConfirmacion('¿Eliminar reserva?', 'Esta acción no se puede deshacer');
        if (!ok) return;
        try {
            const res = await fetch(`${BASE}/api/reservas/${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (res.ok) {
                mostrarMensaje('Reserva eliminada', 'success');
                cargarReservas();
            } else {
                mostrarMensaje(data.error || 'No se pudo eliminar', 'error');
            }
        } catch (e) {
            mostrarMensaje('Error de conexión', 'error');
        }
    }
    
    // Funciones globales
    window.editarHabitacion = async function(id) {
        try {
            const response = await fetch(`${BASE}/api/habitaciones/${id}`);
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
        const confirmacion = await mostrarConfirmacion(
            '¿Estás seguro de que deseas eliminar esta habitación?',
            'Esta acción no se puede deshacer'
        );
        
        if (!confirmacion) {
            return;
        }
        
        try {
            const response = await fetch(`${BASE}/api/habitaciones/${id}`, {
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
                const response = await fetch(`${BASE}/api/imagenes-habitacion`, {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    mostrarMensaje(error.error || 'Error al subir imagen', 'error');
                }
            } catch (error) {
                mostrarMensaje('Error de conexión', 'error');
            }
        }
        
        fileInput.value = '';
        cargarImagenesHabitacion(habitacionImagenActual);
        mostrarMensaje('Imágenes subidas exitosamente', 'success');
    };
    
    async function cargarImagenesHabitacion(idhabitacion) {
        try {
            const response = await fetch(`${BASE}/api/imagenes-habitacion/${idhabitacion}`);
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
            const response = await fetch(`${BASE}/api/imagenes-habitacion/${idimagen}`, {
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
            mostrarMensaje('Error de conexión', 'error');
        }
    };
    
    window.eliminarImagen = async function(idimagen) {
        const confirmacion = await mostrarConfirmacion(
            '¿Estás seguro de que deseas eliminar esta imagen?',
            'Esta acción no se puede deshacer'
        );
        
        if (!confirmacion) {
            return;
        }
        
    try {
            const response = await fetch(`${BASE}/api/imagenes-habitacion/${idimagen}`, {
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
            mostrarMensaje('Error de conexión', 'error');
        }
    };
    
    function mostrarMensaje(mensaje, tipo) {
        // Usar el sistema de notificaciones modernas
        switch(tipo) {
            case 'success':
                showSuccess(mensaje);
                break;
            case 'error':
                showError(mensaje);
                break;
            case 'warning':
                showWarning(mensaje);
                break;
            default:
                showInfo(mensaje);
        }
    }
});