function toggleHabitacion(element) {
  // Simular cambio de estado al hacer clic
  const estados = ['disponible', 'ocupado', 'mantenimiento'];
  const iconos = {
    'disponible': 'fas fa-check-circle',
    'ocupado': 'fas fa-user', 
    'mantenimiento': 'fas fa-tools'
  };
  const puertas = {
    'disponible': 'fas fa-door-open',
    'ocupado': 'fas fa-door-closed',
    'mantenimiento': 'fas fa-exclamation-triangle'
  };
  const textos = {
    'disponible': 'Disponible',
    'ocupado': 'Ocupada',
    'mantenimiento': 'Mantenimiento'
  };

  let estadoActual = '';
  estados.forEach(estado => {
    if (element.classList.contains(estado)) {
      estadoActual = estado;
    }
  });

  let siguienteEstado = estados[(estados.indexOf(estadoActual) + 1) % estados.length];

  // Remover clase actual
  element.classList.remove(estadoActual);
  // Agregar nueva clase
  element.classList.add(siguienteEstado);

  // Actualizar icono
  const iconoElement = element.querySelector('.habitacion-icono i');
  iconoElement.className = iconos[siguienteEstado];

  // Actualizar icono de puerta
  const puertaElement = element.querySelector('.habitacion-numero i');
  puertaElement.className = `${puertas[siguienteEstado]} me-1`;

  // Actualizar texto
  const estadoElement = element.querySelector('.habitacion-estado');
  estadoElement.textContent = textos[siguienteEstado];

  // Actualizar estadísticas
  actualizarEstadisticas();
}

function actualizarEstadisticas() {
  const habitaciones = document.querySelectorAll('.habitacion');
  let disponibles = 0, ocupadas = 0, mantenimiento = 0;

  habitaciones.forEach(hab => {
    if (hab.classList.contains('disponible')) disponibles++;
    else if (hab.classList.contains('ocupado')) ocupadas++;
    else if (hab.classList.contains('mantenimiento')) mantenimiento++;
  });

  document.querySelectorAll('.stat-number')[1].textContent = disponibles;
  document.querySelectorAll('.stat-number')[2].textContent = ocupadas;
  document.querySelectorAll('.stat-number')[3].textContent = mantenimiento;
}

// Inicializar estadísticas al cargar la página
document.addEventListener('DOMContentLoaded', actualizarEstadisticas);