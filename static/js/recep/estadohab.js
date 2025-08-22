let habitaciones = [];

const ESTADOS_CONFIG = {
  'disponible': {
    icon: 'fas fa-check-circle',
    puerta: 'fas fa-door-open',
    texto: 'Disponible',
    clase: 'disponible'
  },
  'ocupada': {
    icon: 'fas fa-user',
    puerta: 'fas fa-door-closed', 
    texto: 'Ocupada',
    clase: 'ocupado'
  },
  'mantenimiento': {
    icon: 'fas fa-tools',
    puerta: 'fas fa-exclamation-triangle',
    texto: 'Mantenimiento',
    clase: 'mantenimiento'
  }
};

async function cargarHabitaciones() {
  try {
    const response = await fetch('/api/habitaciones-estado');
    
    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    habitaciones = data;
    
  renderizarHabitaciones();
  actualizarEstadisticas();
    
  } catch (error) {
    mostrarError('Error al cargar las habitaciones. Por favor, intenta de nuevo.');
  }
}

function renderizarHabitaciones() {
  const grid = document.getElementById('habitaciones-grid');
  
  if (habitaciones.length === 0) {
    grid.innerHTML = `
      <div class="error-container">
        <i class="fas fa-home"></i>
        <h3>No hay habitaciones registradas</h3>
        <p>Contacta al administrador para agregar habitaciones al sistema.</p>
      </div>
    `;
    return;
  }
  
  grid.innerHTML = habitaciones.map(habitacion => {
    const estado = habitacion.estado.toLowerCase();
    const config = ESTADOS_CONFIG[estado] || ESTADOS_CONFIG['disponible'];
    
    return `
      <div class="habitacion ${config.clase}" 
           data-id="${habitacion.idhabitacion}" 
           data-numero="${habitacion.numero}">
        <div class="habitacion-icono">
          <i class="${config.icon}"></i>
        </div>
        <div class="habitacion-numero">
          <i class="${config.puerta} me-1"></i>
          ${habitacion.numero}
        </div>
        <div class="habitacion-estado">${config.texto}</div>
        <div class="habitacion-info">
          <small>${habitacion.nombre}</small>
        </div>
      </div>
    `;
  }).join('');
}

function mostrarError(mensaje) {
  const grid = document.getElementById('habitaciones-grid');
  grid.innerHTML = `
    <div class="error-container">
      <i class="fas fa-exclamation-triangle"></i>
      <h3>Error</h3>
      <p>${mensaje}</p>
      <button class="retry-button" onclick="cargarHabitaciones()">
        <i class="fas fa-redo me-1"></i>
        Reintentar
      </button>
    </div>
  `;
}

function actualizarEstadisticas() {
  const contadores = {
    total: habitaciones.length,
    disponible: 0,
    ocupada: 0,
    mantenimiento: 0
  };
  
  habitaciones.forEach(habitacion => {
    const estado = habitacion.estado.toLowerCase();
    if (contadores.hasOwnProperty(estado)) {
      contadores[estado]++;
    }
  });
  
  const statNumbers = document.querySelectorAll('.stat-number');
  if (statNumbers.length >= 4) {
    statNumbers[0].textContent = contadores.total;
    statNumbers[1].textContent = contadores.disponible;
    statNumbers[2].textContent = contadores.ocupada;
    statNumbers[3].textContent = contadores.mantenimiento;
  }
}

document.addEventListener('DOMContentLoaded', function() {
  cargarHabitaciones();
  
  setInterval(cargarHabitaciones, 30000);
});

function refrescarHabitaciones() {
  const grid = document.getElementById('habitaciones-grid');
  grid.innerHTML = `
    <div class="loading-container">
      <div class="spinner"></div>
      <p>Actualizando habitaciones...</p>
    </div>
  `;
  cargarHabitaciones();
}