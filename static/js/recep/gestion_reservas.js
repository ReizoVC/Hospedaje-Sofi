let reservas = [];
let usuarios = [];
let habitaciones = [];

document.addEventListener('DOMContentLoaded', function() {
  const elements = document.querySelectorAll('.fade-in-up');
  elements.forEach((element, index) => {
    element.style.animationDelay = `${index * 0.1}s`;
  });
  
  cargarDatos();
});

async function cargarDatos() {
  try {
    await Promise.all([
      cargarReservas(),
      cargarEstadisticas(),
      cargarUsuarios(),
      cargarHabitaciones()
    ]);
  } catch (error) {
    mostrarError('Error al cargar los datos de la aplicación');
  }
}

// Función para cargar reservas
async function cargarReservas() {
  try {
  const response = await fetch('recep/api/reservas');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const todasLasReservas = await response.json();
    
    // Filtrar las reservas completadas (no se muestran en este menú)
    reservas = todasLasReservas.filter(reserva => reserva.estado !== 'completada');
    
    actualizarTablaReservas();
  } catch (error) {
    mostrarError('Error al cargar las reservas');
  }
}

// Función para cargar estadísticas
async function cargarEstadisticas() {
  try {
  const response = await fetch('recep/api/reservas/estadisticas');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const estadisticas = await response.json();
    actualizarEstadisticas(estadisticas);
  } catch (error) {
    mostrarError('Error al cargar las estadísticas');
  }
}

// Función para cargar usuarios
async function cargarUsuarios() {
  try {
    const response = await fetch('api/usuarios-clientes');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    usuarios = await response.json();
  } catch (error) {
  }
}

// Función para cargar habitaciones
async function cargarHabitaciones() {
  try {
    const response = await fetch('api/habitaciones-estado');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    habitaciones = await response.json();
  } catch (error) {
  }
}

// Función para actualizar las estadísticas en el DOM
function actualizarEstadisticas(stats) {
  const statNumbers = document.querySelectorAll('.stat-number');
  statNumbers[0].textContent = stats.pendientes || 0;
  statNumbers[1].textContent = stats.confirmadas || 0;
  statNumbers[2].textContent = stats.activas || 0;
  statNumbers[3].textContent = stats.canceladas || 0;
  statNumbers[4].textContent = stats.total || 0;
}

// Función para actualizar la tabla de reservas
function actualizarTablaReservas() {
  const tbody = document.getElementById('reservasTableBody');
  if (!tbody) return;
  
  tbody.innerHTML = '';
  
  if (reservas.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align: center; padding: 3rem 1rem; color: var(--secondary-color);">
          <i class="fas fa-calendar-times" style="font-size: 2rem; margin-bottom: 1rem; display: block;"></i>
          No hay reservas registradas
        </td>
      </tr>
    `;
    return;
  }
  
  reservas.forEach(reserva => {
    const tr = document.createElement('tr');
    
    const fechaInicio = new Date(reserva.fechainicio);
    const fechaHoy = new Date();
    fechaHoy.setHours(0, 0, 0, 0);
    const yaComenzo = fechaInicio <= fechaHoy;
    const esPendiente = reserva.estado === 'pendiente';
    
    const puedeEditarCompleto = esPendiente && !yaComenzo;
    
    const iniciales = `${reserva.usuario.nombre.charAt(0)}${reserva.usuario.apellidos.charAt(0)}`;
    const colorAvatar = generarColorAvatar(reserva.usuario.nombre);
    
    const fechaInicioStr = fechaInicio.toLocaleDateString('es-ES');
    const fechaFinStr = new Date(reserva.fechafin).toLocaleDateString('es-ES');
    
    const badgeInfo = obtenerBadgeInfo(reserva.estado);
    
    let botonEditar = '';
    
    if (puedeEditarCompleto) {
      botonEditar = `<button class="btn btn-sm btn-outline-primary" title="Editar reserva pendiente" onclick="editarReserva(${reserva.idreserva})">
        <i class="fas fa-edit"></i>
      </button>`;
    } else if (!esPendiente && !yaComenzo) {
      botonEditar = `<button class="btn btn-sm btn-outline-secondary" title="Solo cambio de estado (no pendiente)" onclick="editarReserva(${reserva.idreserva})">
        <i class="fas fa-edit"></i>
        <i class="fas fa-flag" style="font-size: 0.7em; margin-left: 2px;"></i>
      </button>`;
    } else if (yaComenzo && esPendiente) {
      botonEditar = `<button class="btn btn-sm btn-outline-warning" title="Solo cambio de estado (ya comenzó)" onclick="editarReserva(${reserva.idreserva})">
        <i class="fas fa-edit"></i>
        <i class="fas fa-clock" style="font-size: 0.7em; margin-left: 2px;"></i>
      </button>`;
    } else {
      botonEditar = `<button class="btn btn-sm btn-outline-danger" title="Solo cambio de estado (ya comenzó y confirmada)" onclick="editarReserva(${reserva.idreserva})">
        <i class="fas fa-edit"></i>
        <i class="fas fa-ban" style="font-size: 0.7em; margin-left: 2px;"></i>
      </button>`;
    }
    
    tr.innerHTML = `
      <td><strong>${reserva.idreserva}</strong></td>
      <td>
        <div class="usuario-info">
          <div class="usuario-avatar" style="background: ${colorAvatar};">${iniciales}</div>
          ${reserva.usuario.nombre} ${reserva.usuario.apellidos}
        </div>
      </td>
      <td><span style="font-weight: 600; color: var(--primary-color);">${reserva.habitacion.numero}</span></td>
      <td style="font-weight: 500;">${fechaInicioStr}</td>
      <td style="font-weight: 500;">${fechaFinStr}</td>
      <td><span class="badge ${badgeInfo.clase}"><i class="${badgeInfo.icono} me-1"></i>${badgeInfo.texto}</span></td>
      <td>
        ${botonEditar}
        <button class="btn btn-sm btn-outline-danger" title="Eliminar" onclick="eliminarReserva(${reserva.idreserva})">
          <i class="fas fa-trash"></i>
        </button>
      </td>
    `;
    
    tbody.appendChild(tr);
  });
}

// Función para generar color de avatar basado en el nombre
function generarColorAvatar(nombre) {
  const colores = [
    'linear-gradient(135deg, #667eea, #764ba2)',
    'linear-gradient(135deg, #10b981, #34d399)',
    'linear-gradient(135deg, #ef4444, #f87171)',
    'linear-gradient(135deg, #8b5cf6, #a78bfa)',
    'linear-gradient(135deg, #f59e0b, #fbbf24)',
    'linear-gradient(135deg, #06b6d4, #67e8f9)'
  ];
  
  const index = nombre.charCodeAt(0) % colores.length;
  return colores[index];
}

// Función para obtener la información del badge según el estado
function obtenerBadgeInfo(estado) {
  const badges = {
    'pendiente': { clase: 'bg-warning', icono: 'fas fa-clock', texto: 'Pendiente' },
    'confirmada': { clase: 'bg-success', icono: 'fas fa-check', texto: 'Confirmada' },
    'activa': { clase: 'bg-primary', icono: 'fas fa-play', texto: 'Activa' },
    'cancelada': { clase: 'bg-danger', icono: 'fas fa-times', texto: 'Cancelada' },
    'completada': { clase: 'bg-secondary', icono: 'fas fa-check-circle', texto: 'Completada' }
  };
  
  return badges[estado] || { clase: 'bg-secondary', icono: 'fas fa-question', texto: 'Desconocido' };
}

// Función para obtener los estados disponibles según el estado actual
function obtenerEstadosDisponibles(estadoActual) {
  // Estados que se pueden seleccionar manualmente (sin 'activa' y sin 'completada')
  const estadosEditables = [
    { valor: 'pendiente', texto: 'Pendiente' },
    { valor: 'confirmada', texto: 'Confirmada' },
    { valor: 'cancelada', texto: 'Cancelada' }
  ];
  
  // Lógica de transiciones de estado permitidas
  const transicionesPermitidas = {
    'pendiente': ['pendiente', 'confirmada', 'cancelada'],
    'confirmada': ['confirmada', 'cancelada'],
    'activa': ['cancelada'], // Desde activa solo se puede cancelar manualmente
    'completada': [], // Las completadas no se pueden editar
    'cancelada': ['cancelada'] // Las canceladas no se pueden cambiar
  };
  
  const estadosPermitidos = transicionesPermitidas[estadoActual] || [estadoActual];
  return estadosEditables.filter(estado => estadosPermitidos.includes(estado.valor));
}

// Función para mostrar modal mejorado
function mostrarModalMejorado(contenido) {
  const modal = document.createElement('div');
  modal.className = 'modal-overlay modal-edit-overlay';
  modal.style.cssText = `
    position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
    background: rgba(0,0,0,0.6); z-index: 10000; 
    display: flex; align-items: center; justify-content: center;
    backdrop-filter: blur(4px);
  `;
  
  const modalContent = document.createElement('div');
  modalContent.className = 'modal-edit-container';
  modalContent.innerHTML = contenido;
  
  modal.appendChild(modalContent);
  document.body.appendChild(modal);
  
  // Cerrar modal al hacer clic fuera
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.remove();
    }
  });
  
  // Animación de entrada
  setTimeout(() => {
    modal.style.opacity = '1';
    modalContent.style.transform = 'scale(1)';
  }, 10);
}

// Función para actualizar una reserva
async function actualizarReserva(event, idReserva) {
  event.preventDefault();
  
  const formData = new FormData(event.target);
  const data = Object.fromEntries(formData.entries());
  
  // Validar fechas
  const fechaInicio = new Date(data.fechainicio);
  const fechaFin = new Date(data.fechafin);
  
  if (fechaInicio >= fechaFin) {
    mostrarError('La fecha de inicio debe ser anterior a la fecha de fin');
    return;
  }
  
  try {
  const response = await fetch(`recep/api/reservas/${idReserva}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Error al actualizar la reserva');
    }
    
    mostrarExito('Reserva actualizada exitosamente');
    
    // Cerrar modal y recargar datos
    document.querySelector('.modal-overlay').remove();
    await cargarReservas();
    await cargarEstadisticas();
  } catch (error) {
    mostrarError(error.message);
  }
}

// Función para cambiar estado desde el modal simplificado
async function cambiarEstadoReservaModal(event, idReserva) {
  event.preventDefault();
  
  const formData = new FormData(event.target);
  const nuevoEstado = formData.get('estado');
  
  try {
  const response = await fetch(`recep/api/reservas/${idReserva}/estado`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ estado: nuevoEstado })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Error al cambiar el estado');
    }
    
    mostrarExito('Estado de reserva actualizado exitosamente');
    
    // Cerrar modal y recargar datos
    document.querySelector('.modal-overlay').remove();
    await cargarReservas();
    await cargarEstadisticas();
  } catch (error) {
    mostrarError(error.message);
  }
}

// Función para cambiar el estado de una reserva
async function cambiarEstadoReserva(idReserva, nuevoEstado) {
  try {
  const response = await fetch(`recep/api/reservas/${idReserva}/estado`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ estado: nuevoEstado })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Error al cambiar el estado');
    }
    
    mostrarExito('Estado de reserva actualizado exitosamente');
    await cargarReservas();
    await cargarEstadisticas();
  } catch (error) {
    mostrarError(error.message);
  }
}

// Función para editar una reserva
function editarReserva(idReserva) {
  const reserva = reservas.find(r => r.idreserva === idReserva);
  if (!reserva) {
    mostrarError('Reserva no encontrada');
    return;
  }
  
  const fechaInicio = new Date(reserva.fechainicio);
  const fechaHoy = new Date();
  fechaHoy.setHours(0, 0, 0, 0);
  
  const yaComenzo = fechaInicio <= fechaHoy;
  const esPendiente = reserva.estado === 'pendiente';
  
  const puedeEditarCompleto = esPendiente && !yaComenzo;
  
  if (!puedeEditarCompleto) {
    mostrarModalEstadoSolo(reserva, yaComenzo, esPendiente);
    return;
  }
  
  const fechaInicioStr = fechaInicio.toISOString().split('T')[0];
  const fechaFin = new Date(reserva.fechafin).toISOString().split('T')[0];
  
  const habitacionesDisponibles = habitaciones.filter(h => 
    h.estado === 'disponible' || h.idhabitacion === reserva.habitacion.idhabitacion
  );
  
  const opcionesHabitaciones = habitacionesDisponibles.map(h => 
    `<option value="${h.idhabitacion}" ${h.idhabitacion === reserva.habitacion.idhabitacion ? 'selected' : ''}>${h.numero} - ${h.nombre} ($${h.precio_noche}/noche)</option>`
  ).join('');
  
  const estadosDisponibles = obtenerEstadosDisponibles(reserva.estado);
  const opcionesEstados = estadosDisponibles.map(estado => 
    `<option value="${estado.valor}" ${estado.valor === reserva.estado ? 'selected' : ''}>${estado.texto}</option>`
  ).join('');
  
  const modalHTML = `
    <div class="modal-edit-header">
      <div class="modal-edit-icon">
        <i class="fas fa-edit"></i>
      </div>
      <div>
        <h4 class="modal-edit-title">Editar Reserva #${idReserva}</h4>
        <p class="modal-edit-subtitle">Modifica los detalles de la reserva pendiente</p>
      </div>
    </div>
    
    <form id="formEditarReserva" onsubmit="actualizarReserva(event, ${idReserva})">
      <div class="modal-edit-content">
        
        <!-- Información actual de la reserva -->
        <div class="info-card">
          <div class="info-card-header">
            <i class="fas fa-info-circle"></i>
            <span>Información de la Reserva</span>
          </div>
          <div class="info-card-body">
            <div class="info-row">
              <span class="info-label">Usuario (Fijo):</span>
              <span class="info-value">${reserva.usuario.nombre} ${reserva.usuario.apellidos}</span>
            </div>
            <div class="info-row">
              <span class="info-label">DNI:</span>
              <span class="info-value">${reserva.usuario.dni || 'No especificado'}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Estado Actual:</span>
              <span class="info-value status-${reserva.estado}">${obtenerBadgeInfo(reserva.estado).texto}</span>
            </div>
          </div>
        </div>
        
        <!-- Formulario de edición -->
        <div class="form-grid">
          <!-- Usuario fijo - campo oculto -->
          <input type="hidden" name="idusuario" value="${reserva.usuario.idusuario}">
          
          <div class="form-group form-group-full">
            <label for="editHabitacion" class="form-label">
              <i class="fas fa-door-open"></i>
              Habitación
            </label>
            <select id="editHabitacion" name="idhabitacion" class="form-control" required>
              ${opcionesHabitaciones}
            </select>
          </div>
          
          <div class="form-group">
            <label for="editFechaInicio" class="form-label">
              <i class="fas fa-calendar-check"></i>
              Fecha de Inicio
            </label>
            <input type="date" id="editFechaInicio" name="fechainicio" class="form-control" value="${fechaInicioStr}" required>
          </div>
          
          <div class="form-group">
            <label for="editFechaFin" class="form-label">
              <i class="fas fa-calendar-times"></i>
              Fecha de Fin
            </label>
            <input type="date" id="editFechaFin" name="fechafin" class="form-control" value="${fechaFin}" required>
          </div>
          
          <div class="form-group form-group-full">
            <label for="editEstado" class="form-label">
              <i class="fas fa-flag"></i>
              Estado de la Reserva
            </label>
            <select id="editEstado" name="estado" class="form-control" required>
              ${opcionesEstados}
            </select>
          </div>
        </div>
        
      </div>
      
      <div class="modal-edit-footer">
        <button type="button" class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">
          <i class="fas fa-times"></i>
          Cancelar
        </button>
        <button type="submit" class="btn btn-success">
          <i class="fas fa-save"></i>
          Guardar Cambios
        </button>
      </div>
    </form>
  `;
  
  mostrarModalMejorado(modalHTML);
}

// Función para mostrar modal solo de cambio de estado (cuando no se puede editar completamente)
function mostrarModalEstadoSolo(reserva, yaComenzo, esPendiente) {
  const estadosDisponibles = obtenerEstadosDisponibles(reserva.estado);
  const opcionesEstados = estadosDisponibles.map(estado => 
    `<option value="${estado.valor}" ${estado.valor === reserva.estado ? 'selected' : ''}>${estado.texto}</option>`
  ).join('');
  
  const fechaInicio = new Date(reserva.fechainicio).toLocaleDateString('es-ES');
  const fechaFin = new Date(reserva.fechafin).toLocaleDateString('es-ES');
  
  // Determinar el motivo por el cual no se puede editar
  let motivoRestriccion = '';
  let colorHeader = '';
  let iconoHeader = '';
  
  if (yaComenzo && !esPendiente) {
    motivoRestriccion = 'La reserva ya comenzó y no está en estado pendiente';
    colorHeader = 'linear-gradient(135deg, #dc2626, #ef4444)';
    iconoHeader = 'fas fa-ban';
  } else if (yaComenzo && esPendiente) {
    motivoRestriccion = 'La reserva ya comenzó (solo cambio de estado)';
    colorHeader = 'linear-gradient(135deg, #f59e0b, #d97706)';
    iconoHeader = 'fas fa-exclamation-triangle';
  } else if (!yaComenzo && !esPendiente) {
    motivoRestriccion = 'Solo las reservas pendientes pueden editarse completamente';
    colorHeader = 'linear-gradient(135deg, #6366f1, #8b5cf6)';
    iconoHeader = 'fas fa-lock';
  }
  
  const modalHTML = `
    <div class="modal-edit-header" style="background: ${colorHeader};">
      <div class="modal-edit-icon">
        <i class="${iconoHeader}"></i>
      </div>
      <div>
        <h4 class="modal-edit-title">Cambio de Estado - Reserva #${reserva.idreserva}</h4>
        <p class="modal-edit-subtitle">${motivoRestriccion}</p>
      </div>
    </div>
    
    <form id="formCambiarEstado" onsubmit="cambiarEstadoReservaModal(event, ${reserva.idreserva})">
      <div class="modal-edit-content">
        
        <!-- Advertencia -->
        <div class="alert alert-info" style="margin-bottom: 1.5rem;">
          <i class="fas fa-info-circle me-2"></i>
          <strong>Edición restringida:</strong> ${motivoRestriccion}. 
          ${reserva.estado === 'activa' ? 'Las reservas activas solo pueden ser canceladas o completadas mediante check-out.' : 'Solo es posible cambiar el estado.'}
        </div>
        
        <!-- Información de la reserva (solo lectura) -->
        <div class="info-card">
          <div class="info-card-header">
            <i class="fas fa-lock"></i>
            <span>Información de la Reserva (Solo Lectura)</span>
          </div>
          <div class="info-card-body">
            <div class="info-row">
              <span class="info-label">Usuario:</span>
              <span class="info-value">${reserva.usuario.nombre} ${reserva.usuario.apellidos}</span>
            </div>
            <div class="info-row">
              <span class="info-label">DNI:</span>
              <span class="info-value">${reserva.usuario.dni || 'No especificado'}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Habitación:</span>
              <span class="info-value">${reserva.habitacion.numero} - ${reserva.habitacion.nombre}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Fecha de Inicio:</span>
              <span class="info-value">${fechaInicio}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Fecha de Fin:</span>
              <span class="info-value">${fechaFin}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Estado Actual:</span>
              <span class="info-value status-${reserva.estado}">${obtenerBadgeInfo(reserva.estado).texto}</span>
            </div>
          </div>
        </div>
        
        <!-- Solo cambio de estado -->
        <div class="form-group form-group-full">
          <label for="nuevoEstado" class="form-label">
            <i class="fas fa-flag"></i>
            Nuevo Estado de la Reserva
          </label>
          <select id="nuevoEstado" name="estado" class="form-control" required>
            ${opcionesEstados}
          </select>
          <small class="form-text text-muted" style="margin-top: 0.5rem; color: var(--secondary-color); font-size: 0.8rem;">
            Solo se muestran los estados permitidos según el flujo de la reserva.
          </small>
        </div>
        
      </div>
      
      <div class="modal-edit-footer">
        <button type="button" class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">
          <i class="fas fa-times"></i>
          Cancelar
        </button>
        <button type="submit" class="btn btn-warning">
          <i class="fas fa-edit"></i>
          Cambiar Estado
        </button>
      </div>
    </form>
  `;
  
  mostrarModalMejorado(modalHTML);
}

// Función para eliminar una reserva
async function eliminarReserva(idReserva) {
  const reserva = reservas.find(r => r.idreserva === idReserva);
  if (!reserva) {
    mostrarError('Reserva no encontrada');
    return;
  }
  
  if (!confirm(`¿Está seguro de que desea eliminar la reserva #${idReserva}?`)) {
    return;
  }
  
  try {
  const response = await fetch(`recep/api/reservas/${idReserva}`, {
      method: 'DELETE'
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Error al eliminar la reserva');
    }
    
    mostrarExito('Reserva eliminada exitosamente');
    await cargarReservas();
    await cargarEstadisticas();
  } catch (error) {
    mostrarError(error.message);
  }
}

// Funciones utilitarias para mostrar mensajes
function mostrarError(mensaje) {
  mostrarNotificacion(mensaje, 'error');
}

function mostrarExito(mensaje) {
  mostrarNotificacion(mensaje, 'success');
}

function mostrarInfo(mensaje) {
  mostrarNotificacion(mensaje, 'info');
}

function mostrarNotificacion(mensaje, tipo) {
  // Crear elemento de notificación
  const notificacion = document.createElement('div');
  notificacion.className = `alert alert-${tipo} position-fixed`;
  notificacion.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
  notificacion.innerHTML = `
    <div class="d-flex align-items-center">
      <i class="fas fa-${tipo === 'error' ? 'exclamation-triangle' : tipo === 'success' ? 'check-circle' : 'info-circle'} me-2"></i>
      ${mensaje}
      <button type="button" class="btn-close ms-auto" onclick="this.parentElement.parentElement.remove()"></button>
    </div>
  `;
  
  document.body.appendChild(notificacion);
  
  // Auto-remover después de 5 segundos
  setTimeout(() => {
    if (notificacion.parentElement) {
      notificacion.remove();
    }
  }, 5000);
}

function mostrarModal(contenido) {
  // Crear modal simple
  const modal = document.createElement('div');
  modal.className = 'modal-overlay';
  modal.style.cssText = `
    position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
    background: rgba(0,0,0,0.5); z-index: 10000; 
    display: flex; align-items: center; justify-content: center;
  `;
  
  const modalContent = document.createElement('div');
  modalContent.className = 'modal-content bg-white p-4 rounded';
  modalContent.style.cssText = 'max-width: 500px; width: 90%; max-height: 80vh; overflow-y: auto;';
  modalContent.innerHTML = `
    ${contenido}
    <div class="mt-3">
      <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cerrar</button>
    </div>
  `;
  
  modal.appendChild(modalContent);
  document.body.appendChild(modal);
  
  // Cerrar modal al hacer clic fuera
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.remove();
    }
  });
}

// Función para abrir modal de nueva reserva
function abrirModalNuevaReserva() {
  const opcionesUsuarios = usuarios.map(u => 
    `<option value="${u.idusuario}">${u.nombre} ${u.apellidos} (${u.dni})</option>`
  ).join('');
  
  const opcionesHabitaciones = habitaciones.filter(h => h.estado === 'disponible').map(h => 
    `<option value="${h.idhabitacion}">${h.numero} - ${h.nombre} ($${h.precio_noche}/noche)</option>`
  ).join('');
  
  const hoy = new Date().toISOString().split('T')[0];
  
  const formulario = `
    <h5>Nueva Reserva</h5>
    <form id="formNuevaReserva" onsubmit="crearReserva(event)">
      <div class="mb-3">
        <label for="selectUsuario" class="form-label">Usuario:</label>
        <select id="selectUsuario" name="idusuario" class="form-control" required>
          <option value="">Seleccione un usuario</option>
          ${opcionesUsuarios}
        </select>
      </div>
      
      <div class="mb-3">
        <label for="selectHabitacion" class="form-label">Habitación:</label>
        <select id="selectHabitacion" name="idhabitacion" class="form-control" required>
          <option value="">Seleccione una habitación</option>
          ${opcionesHabitaciones}
        </select>
      </div>
      
      <div class="row">
        <div class="col-md-6 mb-3">
          <label for="fechaInicio" class="form-label">Fecha de Inicio:</label>
          <input type="date" id="fechaInicio" name="fechainicio" class="form-control" min="${hoy}" required>
        </div>
        <div class="col-md-6 mb-3">
          <label for="fechaFin" class="form-label">Fecha de Fin:</label>
          <input type="date" id="fechaFin" name="fechafin" class="form-control" min="${hoy}" required>
        </div>
      </div>
      
      <div class="mb-3">
        <label for="selectEstado" class="form-label">Estado:</label>
        <select id="selectEstado" name="estado" class="form-control" required>
          <option value="pendiente">Pendiente</option>
          <option value="confirmada">Confirmada</option>
        </select>
      </div>
      
      <div class="d-flex gap-2">
        <button type="submit" class="btn btn-success">Crear Reserva</button>
        <button type="button" class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancelar</button>
      </div>
    </form>
  `;
  
  mostrarModal(formulario);
}

// Función para crear una nueva reserva
async function crearReserva(event) {
  event.preventDefault();
  
  const formData = new FormData(event.target);
  const data = Object.fromEntries(formData.entries());
  
  // Validar fechas
  const fechaInicio = new Date(data.fechainicio);
  const fechaFin = new Date(data.fechafin);
  
  if (fechaInicio >= fechaFin) {
    mostrarError('La fecha de inicio debe ser anterior a la fecha de fin');
    return;
  }
  
  try {
  const response = await fetch('recep/api/reservas', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Error al crear la reserva');
    }
    
    const resultado = await response.json();
    mostrarExito(`Reserva creada exitosamente. Código: ${resultado.codigo_reserva}`);
    
    // Cerrar modal y recargar datos
    document.querySelector('.modal-overlay').remove();
    await cargarReservas();
    await cargarEstadisticas();
  } catch (error) {
    console.error('Error al crear reserva:', error);
    mostrarError(error.message);
  }
}