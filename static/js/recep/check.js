// Variables globales
let reservasCheck = { checkin: [], checkout: [] };

// Animaciones suaves al cargar
document.addEventListener('DOMContentLoaded', function() {
  const elements = document.querySelectorAll('.fade-in-up');
  elements.forEach((element, index) => {
    element.style.animationDelay = `${index * 0.1}s`;
  });
  
  // Cargar datos iniciales
  cargarDatos();
});

// Función para cargar todos los datos necesarios
async function cargarDatos() {
  try {
    await Promise.all([
      cargarReservasCheck(),
      cargarEstadisticasCheck()
    ]);
  } catch (error) {
    console.error('Error al cargar datos:', error);
    mostrarError('Error al cargar los datos de la aplicación');
  }
}

// Función para cargar reservas para check-in/check-out
async function cargarReservasCheck() {
  try {
    const response = await fetch('/api/check/reservas');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    reservasCheck = await response.json();
    actualizarTablaCheck();
  } catch (error) {
    console.error('Error al cargar reservas check:', error);
    mostrarError('Error al cargar las reservas para check-in/check-out');
  }
}

// Función para cargar estadísticas de check
async function cargarEstadisticasCheck() {
  try {
    const response = await fetch('/api/check/estadisticas');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const estadisticas = await response.json();
    actualizarEstadisticasCheck(estadisticas);
  } catch (error) {
    console.error('Error al cargar estadísticas check:', error);
    mostrarError('Error al cargar las estadísticas');
  }
}

// Función para actualizar las estadísticas en el DOM
function actualizarEstadisticasCheck(stats) {
  const statNumbers = document.querySelectorAll('.stat-number');
  statNumbers[0].textContent = stats.pendientes_checkin || 0;
  statNumbers[1].textContent = stats.pendientes_checkout || 0;
  statNumbers[2].textContent = stats.habitaciones_ocupadas || 0;
}

// Función para actualizar la tabla de check-in/check-out
function actualizarTablaCheck() {
  const tbody = document.querySelector('.custom-table tbody');
  if (!tbody) return;
  
  // Limpiar tabla completamente (incluye fila de carga)
  tbody.innerHTML = '';
  
  // Combinar reservas de check-in y check-out
  const todasLasReservas = [
    ...reservasCheck.checkin.map(r => ({ ...r, tipo: 'checkin' })),
    ...reservasCheck.checkout.map(r => ({ ...r, tipo: 'checkout' }))
  ];
  
  todasLasReservas.forEach((reserva, index) => {
    const tr = document.createElement('tr');
    
    // Generar avatar con las iniciales del usuario
    const iniciales = `${reserva.usuario.nombre.charAt(0)}${reserva.usuario.apellidos.charAt(0)}`;
    const colorAvatar = generarColorAvatar(reserva.usuario.nombre);
    
    // Formatear fechas
    const fechaInicio = new Date(reserva.fechainicio).toLocaleDateString('es-ES');
    const fechaFin = new Date(reserva.fechafin).toLocaleDateString('es-ES');
    
    // Determinar la información del estado y botón según el tipo
    let estadoInfo, botonAccion, fechaCheckin, fechaCheckout;
    
    if (reserva.tipo === 'checkin') {
      estadoInfo = { clase: 'warning', icono: 'fas fa-clock', texto: 'Reservado' };
      botonAccion = `
        <button class="btn btn-checkin" onclick="confirmarCheckin(${reserva.idreserva})">
          <i class="fas fa-sign-in-alt"></i>Check-In
        </button>
      `;
      fechaCheckin = '--';
      fechaCheckout = '--';
    } else {
      estadoInfo = { clase: 'success', icono: 'fas fa-check', texto: 'Ocupado' };
      botonAccion = `
        <button class="btn btn-checkout" onclick="confirmarCheckout(${reserva.idreserva})">
          <i class="fas fa-sign-out-alt"></i>Check-Out
        </button>
      `;
      fechaCheckin = new Date().toLocaleDateString('es-ES') + ' 14:00'; // Simulado
      fechaCheckout = '--';
    }
    
    tr.innerHTML = `
      <td><strong>${index + 1}</strong></td>
      <td><span style="font-weight: 600; color: var(--primary-color);">${reserva.codigoreserva}</span></td>
      <td>
        <div class="cliente-info">
          <div class="cliente-avatar" style="background: ${colorAvatar};">${iniciales}</div>
          ${reserva.usuario.nombre} ${reserva.usuario.apellidos}
        </div>
      </td>
      <td><span style="font-weight: 600;">${reserva.habitacion.numero}</span></td>
      <td><span class="badge ${estadoInfo.clase}"><i class="${estadoInfo.icono}"></i>${estadoInfo.texto}</span></td>
      <td style="font-weight: 500; color: ${fechaCheckin === '--' ? 'var(--secondary-color)' : 'inherit'};">${fechaCheckin}</td>
      <td style="color: var(--secondary-color);">${fechaCheckout}</td>
      <td>${botonAccion}</td>
    `;
    
    tbody.appendChild(tr);
  });
  
  // Si no hay reservas, mostrar mensaje
  if (todasLasReservas.length === 0) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td colspan="8" style="text-align: center; padding: 2rem; color: var(--secondary-color);">
        <i class="fas fa-calendar-times" style="font-size: 2rem; margin-bottom: 1rem; display: block;"></i>
        No hay reservas pendientes de check-in o check-out
      </td>
    `;
    tbody.appendChild(tr);
  }
}

// Función para generar color de avatar basado en el nombre
function generarColorAvatar(nombre) {
  const colores = [
    'var(--primary-color)',
    'var(--success-color)',
    'var(--warning-color)',
    '#8b5cf6',
    '#f59e0b',
    '#06b6d4'
  ];
  
  const index = nombre.charCodeAt(0) % colores.length;
  return colores[index];
}

// Función para confirmar check-in
function confirmarCheckin(idReserva) {
  const reserva = reservasCheck.checkin.find(r => r.idreserva === idReserva);
  if (!reserva) {
    mostrarError('Reserva no encontrada');
    return;
  }
  
  const contenido = `
    <div class="text-center">
      <i class="fas fa-question-circle modal-icon success-color"></i>
      <p class="modal-text">¿Estás seguro de realizar el Check-In para esta reserva?</p>
      <div class="reserva-info">
        <p><strong>Reserva:</strong> ${reserva.codigoreserva}</p>
        <p><strong>Cliente:</strong> ${reserva.usuario.nombre} ${reserva.usuario.apellidos}</p>
        <p><strong>Habitación:</strong> ${reserva.habitacion.numero}</p>
        <p><strong>DNI:</strong> ${reserva.usuario.dni}</p>
      </div>
      <small class="modal-subtext">Esta acción marcará la habitación como ocupada</small>
    </div>
  `;
  
  mostrarModal('Confirmar Check-In', contenido, [
    { texto: 'Cancelar', clase: 'btn-secondary', accion: 'cerrar' },
    { texto: 'Confirmar Check-In', clase: 'btn-success', accion: () => realizarCheckin(idReserva) }
  ]);
}

// Función para confirmar check-out
function confirmarCheckout(idReserva) {
  const reserva = reservasCheck.checkout.find(r => r.idreserva === idReserva);
  if (!reserva) {
    mostrarError('Reserva no encontrada');
    return;
  }
  
  const contenido = `
    <div class="text-center">
      <i class="fas fa-question-circle modal-icon warning-color"></i>
      <p class="modal-text">¿Deseas finalizar el Check-Out de esta reserva?</p>
      <div class="reserva-info">
        <p><strong>Reserva:</strong> ${reserva.codigoreserva}</p>
        <p><strong>Cliente:</strong> ${reserva.usuario.nombre} ${reserva.usuario.apellidos}</p>
        <p><strong>Habitación:</strong> ${reserva.habitacion.numero}</p>
      </div>
      <small class="modal-subtext">Esta acción liberará la habitación para limpieza</small>
    </div>
  `;
  
  mostrarModal('Confirmar Check-Out', contenido, [
    { texto: 'Cancelar', clase: 'btn-secondary', accion: 'cerrar' },
    { texto: 'Confirmar Check-Out', clase: 'btn-warning', accion: () => realizarCheckout(idReserva) }
  ]);
}

// Función para realizar check-in
async function realizarCheckin(idReserva) {
  try {
    const response = await fetch(`/api/check/checkin/${idReserva}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Error al realizar check-in');
    }
    
    const resultado = await response.json();
    mostrarExito(`Check-in realizado exitosamente para la habitación ${resultado.habitacion}`);
    
    // Cerrar modal y recargar datos
    cerrarModalActivo();
    await cargarDatos();
  } catch (error) {
    console.error('Error al realizar check-in:', error);
    mostrarError(error.message);
  }
}

// Función para realizar check-out
async function realizarCheckout(idReserva) {
  try {
    const response = await fetch(`/api/check/checkout/${idReserva}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Error al realizar check-out');
    }
    
    const resultado = await response.json();
    mostrarExito(`Check-out realizado exitosamente. Habitación ${resultado.habitacion} lista para limpieza`);
    
    // Cerrar modal y recargar datos
    cerrarModalActivo();
    await cargarDatos();
  } catch (error) {
    console.error('Error al realizar check-out:', error);
    mostrarError(error.message);
  }
}

// Funciones de modal mejoradas
function mostrarModal(titulo, contenido, botones = []) {
  // Crear modal
  const modal = document.createElement('div');
  modal.className = 'modal-overlay';
  modal.style.cssText = `
    position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
    background: rgba(0,0,0,0.5); z-index: 10000; 
    display: flex; align-items: center; justify-content: center;
    opacity: 0; transition: opacity 0.3s ease;
  `;
  
  const modalContent = document.createElement('div');
  modalContent.className = 'modal-content bg-white rounded';
  modalContent.style.cssText = `
    max-width: 500px; width: 90%; max-height: 80vh; overflow-y: auto;
    transform: scale(0.9); transition: transform 0.3s ease;
    border-radius: 16px; overflow: hidden;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  `;
  
  // Header del modal
  const header = document.createElement('div');
  header.className = 'modal-header';
  header.style.cssText = `
    padding: 1.5rem 1.5rem 1rem; background: var(--primary-color);
    color: white; display: flex; align-items: center; justify-content: space-between;
  `;
  header.innerHTML = `
    <h5 style="margin: 0; font-size: 1.1rem; font-weight: 600;">
      <i class="fas fa-sign-in-alt" style="margin-right: 0.5rem;"></i>${titulo}
    </h5>
    <button type="button" class="btn-close" onclick="this.closest('.modal-overlay').remove()" style="
      background: none; border: none; color: white; font-size: 1.5rem; cursor: pointer;
      width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;
    ">×</button>
  `;
  
  // Body del modal
  const body = document.createElement('div');
  body.className = 'modal-body';
  body.style.cssText = 'padding: 1.5rem; font-weight: 500;';
  body.innerHTML = contenido;
  
  // Footer del modal
  const footer = document.createElement('div');
  footer.className = 'modal-footer';
  footer.style.cssText = `
    padding: 1rem 1.5rem 1.5rem; display: flex; gap: 0.75rem; 
    justify-content: flex-end; border-top: none;
  `;
  
  botones.forEach(boton => {
    const btn = document.createElement('button');
    btn.className = `btn ${boton.clase}`;
    btn.innerHTML = `<i class="fas fa-${boton.clase.includes('success') ? 'check' : boton.clase.includes('warning') ? 'check' : 'times'}"></i> ${boton.texto}`;
    btn.onclick = () => {
      if (boton.accion === 'cerrar') {
        modal.remove();
      } else if (typeof boton.accion === 'function') {
        boton.accion();
      }
    };
    footer.appendChild(btn);
  });
  
  modalContent.appendChild(header);
  modalContent.appendChild(body);
  modalContent.appendChild(footer);
  modal.appendChild(modalContent);
  
  document.body.appendChild(modal);
  
  // Animar entrada
  setTimeout(() => {
    modal.style.opacity = '1';
    modalContent.style.transform = 'scale(1)';
  }, 10);
  
  // Cerrar modal al hacer clic fuera
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.remove();
    }
  });
}

function cerrarModalActivo() {
  const modal = document.querySelector('.modal-overlay');
  if (modal) {
    modal.remove();
  }
}

// Funciones para manejar modales (mantenidas para compatibilidad)
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('show');
    document.body.style.overflow = '';
  }
}

// Cerrar modal al hacer clic en el fondo
document.addEventListener('click', function(e) {
  if (e.target.classList.contains('modal')) {
    closeModal(e.target.id);
  }
});

// Cerrar modal con tecla Escape
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    const openModal = document.querySelector('.modal.show');
    if (openModal) {
      closeModal(openModal.id);
    }
    
    const modalOverlay = document.querySelector('.modal-overlay');
    if (modalOverlay) {
      modalOverlay.remove();
    }
  }
});

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
      <i class="fas fa-${tipo === 'error' ? 'exclamation-triangle' : tipo === 'success' ? 'check-circle' : 'info-circle'}" style="margin-right: 0.5rem;"></i>
      ${mensaje}
      <button type="button" class="btn-close-notif" onclick="this.parentElement.parentElement.remove()" style="
        background: none; border: none; margin-left: auto; cursor: pointer; 
        font-size: 1.2rem; color: inherit; opacity: 0.6;
      ">×</button>
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