// Variables globales
let usuarioSeleccionado = null;
let mostrandoDesactivados = false;

// Función para cargar usuarios (activos o desactivados)
async function cargarUsuarios() {
  try {
    const endpoint = mostrandoDesactivados ? '/api/usuarios-desactivados' : '/api/usuarios-clientes';
    const response = await fetch(endpoint);
    const data = await response.json();

    if (response.ok) {
      mostrarUsuarios(data.usuarios);
    } else {
      mostrarError(data.error || 'Error al cargar usuarios');
    }
  } catch (error) {
    console.error('Error:', error);
    mostrarError('Error de conexión');
  }
}

// Animaciones suaves al cargar
document.addEventListener('DOMContentLoaded', function() {
  const elements = document.querySelectorAll('.fade-in-up');
  elements.forEach((element, index) => {
    element.style.animationDelay = `${index * 0.1}s`;
  });

  const slideElements = document.querySelectorAll('.slide-in-right');
  slideElements.forEach((element, index) => {
    element.style.animationDelay = `${(index + 2) * 0.1}s`;
  });

  // Cargar datos al iniciar
  cargarUsuarios();
});

// Función para cargar usuarios clientes desde la API
async function cargarUsuarios() {
  try {
    const endpoint = mostrandoDesactivados ? '/api/usuarios-desactivados' : '/api/usuarios-clientes';
    const response = await fetch(endpoint);
    if (!response.ok) {
      throw new Error('Error al cargar usuarios');
    }
    
    const usuarios = await response.json();
    mostrarUsuarios(usuarios);
    actualizarEstadisticas(usuarios);
  } catch (error) {
    console.error('Error:', error);
    mostrarError('Error al cargar los usuarios');
  }
}

// Función para mostrar usuarios en la tabla
function mostrarUsuarios(usuarios) {
  const tbody = document.getElementById('tabla-usuarios');
  tbody.innerHTML = '';

  usuarios.forEach(usuario => {
    const iniciales = obtenerIniciales(usuario.nombre, usuario.apellidos);
    const colorAvatar = obtenerColorAvatar(usuario.idusuario);
    
    const fila = document.createElement('tr');
    fila.setAttribute('data-usuario-id', usuario.idusuario);
    fila.innerHTML = `
      <td>
        <div class="user-info">
          <div class="user-avatar" style="background: ${colorAvatar};">
            ${iniciales}
          </div>
          <div>
            <div class="user-name">
              ${usuario.nombre} ${usuario.apellidos}${mostrandoDesactivados ? ' <span style="color: #ef4444; font-size: 0.8em;">(Desactivado)</span>' : ''}
            </div>
          </div>
        </div>
      </td>
      <td>
        <strong>${usuario.dni}</strong>
      </td>
      <td>
        <div class="contact-info">
          <span class="display-mode"><i class="fas fa-envelope"></i> ${usuario.correo}</span>
          <input type="email" class="form-control-inline edit-mode" name="correo" value="${usuario.correo}" placeholder="Correo electrónico" style="display: none;">
        </div>
      </td>
      <td>
        <div class="contact-info">
          <span class="display-mode">${usuario.telefono ? `<i class="fas fa-phone"></i> ${usuario.telefono}` : '<span class="text-muted">No registrado</span>'}</span>
          <input type="text" class="form-control-inline edit-mode" name="telefono" value="${usuario.telefono || ''}" placeholder="Número de teléfono" style="display: none;">
        </div>
      </td>
      <td>
        ${mostrandoDesactivados ? 
          `<button class="btn btn-success" title="Reactivar" onclick="reactivarUsuario('${usuario.idusuario}')">
            <i class="fas fa-check"></i>
          </button>` :
          `<div class="action-buttons">
            <button class="btn btn-edit display-mode" title="Editar datos de contacto" onclick="activarEdicion('${usuario.idusuario}')">
              <i class="fas fa-edit"></i>
            </button>
            <button class="btn btn-danger display-mode" title="Desactivar" onclick="eliminarUsuario('${usuario.idusuario}')">
              <i class="fas fa-ban"></i>
            </button>
            <button class="btn btn-success edit-mode" title="Guardar cambios" onclick="guardarEdicion('${usuario.idusuario}')" style="display: none;">
              <i class="fas fa-save"></i>
            </button>
            <button class="btn btn-secondary edit-mode" title="Cancelar edición" onclick="cancelarEdicion('${usuario.idusuario}')" style="display: none;">
              <i class="fas fa-times"></i>
            </button>
          </div>`
        }
      </td>
    `;
    tbody.appendChild(fila);
  });
}

// Función para actualizar estadísticas
function actualizarEstadisticas(usuarios) {
  document.getElementById('total-clientes').textContent = usuarios.length;
  document.getElementById('clientes-registrados').textContent = usuarios.length;
  // Las otras estadísticas las puedes calcular según tus necesidades
  document.getElementById('reservas-mes').textContent = '0'; // Placeholder
  document.getElementById('nuevos-mes').textContent = '0'; // Placeholder
}

// Función para obtener iniciales
function obtenerIniciales(nombre, apellidos) {
  const primerNombre = nombre.split(' ')[0];
  const primerApellido = apellidos.split(' ')[0];
  return (primerNombre.charAt(0) + primerApellido.charAt(0)).toUpperCase();
}

// Función para obtener color del avatar
function obtenerColorAvatar(id) {
  const colores = [
    'linear-gradient(135deg, #6366f1, #8b5cf6)',
    'linear-gradient(135deg, #10b981, #34d399)',
    'linear-gradient(135deg, #f59e0b, #fbbf24)',
    'linear-gradient(135deg, #ef4444, #f87171)',
    'linear-gradient(135deg, #3b82f6, #60a5fa)',
    'linear-gradient(135deg, #8b5cf6, #a78bfa)'
  ];
  return colores[id.length % colores.length];
}

// Funciones para modal
function openModal() {
  usuarioEditando = null;
  limpiarFormulario();
  const modal = document.getElementById('modalUsuario');
  modal.classList.add('show');
  modal.style.display = 'flex';
}

function closeModal() {
  const modal = document.getElementById('modalUsuario');
  modal.classList.remove('show');
  modal.style.display = 'none';
  usuarioEditando = null;
}

function limpiarFormulario() {
  document.getElementById('nombre').value = '';
  document.getElementById('apellidos').value = '';
  document.getElementById('dni').value = '';
  document.getElementById('email').value = '';
  document.getElementById('telefono').value = '';
  document.getElementById('password').value = '';
}

// Función para editar usuario
async function editarUsuario(id) {
  try {
    // Buscar el usuario en los datos cargados
    const response = await fetch('/api/usuarios-clientes');
    const usuarios = await response.json();
    const usuario = usuarios.find(u => u.idusuario === id);
    
    if (usuario) {
      usuarioEditando = usuario;
      
      // Llenar el formulario
      document.getElementById('nombre').value = usuario.nombre;
      document.getElementById('apellidos').value = usuario.apellidos;
      document.getElementById('dni').value = usuario.dni;
      document.getElementById('email').value = usuario.correo;
      document.getElementById('telefono').value = usuario.telefono || '';
      document.getElementById('password').value = ''; // No mostrar contraseña
      
      openModal();
    }
  } catch (error) {
    console.error('Error:', error);
    mostrarError('Error al cargar datos del usuario');
  }
}

// Función para guardar usuario (crear o actualizar)
async function guardarUsuario() {
  const nombre = document.getElementById('nombre').value;
  const apellidos = document.getElementById('apellidos').value;
  const dni = document.getElementById('dni').value;
  const email = document.getElementById('email').value;
  const telefono = document.getElementById('telefono').value;
  const password = document.getElementById('password').value;

  // Validaciones básicas
  if (!nombre || !apellidos || !dni || !email) {
    mostrarError('Por favor complete todos los campos obligatorios');
    return;
  }

  if (!usuarioEditando && !password) {
    mostrarError('La contraseña es obligatoria para nuevos usuarios');
    return;
  }

  const datos = {
    nombre,
    apellidos,
    dni,
    correo: email,
    telefono: telefono || null
  };

  if (password) {
    datos.clave = password;
  }

  try {
    let response;
    if (usuarioEditando) {
      // Actualizar usuario existente
      response = await fetch(`/api/usuarios-clientes/${usuarioEditando.idusuario}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(datos)
      });
    } else {
      // Crear nuevo usuario
      datos.clave = password; // Asegurar que la contraseña esté incluida
      response = await fetch('/api/usuarios-clientes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(datos)
      });
    }

    if (response.ok) {
      const resultado = await response.json();
      mostrarExito(resultado.message);
      closeModal();
      cargarUsuarios(); // Recargar la tabla
    } else {
      const error = await response.json();
      mostrarError(error.error || 'Error al guardar usuario');
    }
  } catch (error) {
    console.error('Error:', error);
    mostrarError('Error de conexión');
  }
}

// Función para desactivar usuario (eliminación lógica)
async function eliminarUsuario(id) {
  // Crear confirmación personalizada
  const confirmacion = await mostrarConfirmacion(
    '¿Está seguro de que desea desactivar este usuario?', 
    'El usuario no podrá acceder al sistema, pero sus datos se conservarán'
  );
  
  if (!confirmacion) {
    return;
  }

  try {
    const response = await fetch(`/api/usuarios-clientes/${id}`, {
      method: 'DELETE'
    });

    if (response.ok) {
      const resultado = await response.json();
      mostrarExito(resultado.message);
      cargarUsuarios(); // Recargar la tabla
    } else {
      const error = await response.json();
      mostrarError(error.error || 'Error al desactivar usuario');
    }
  } catch (error) {
    console.error('Error:', error);
    mostrarError('Error de conexión');
  }
}

// Funciones para mostrar mensajes
function mostrarError(mensaje) {
  showError(mensaje);
}

function mostrarExito(mensaje) {
  showSuccess(mensaje);
}

function mostrarInfo(mensaje) {
  showInfo(mensaje);
}

// Función para alternar entre usuarios activos y desactivados
function toggleUsuarios() {
  mostrandoDesactivados = !mostrandoDesactivados;
  const btnToggle = document.getElementById('btn-toggle');
  
  if (mostrandoDesactivados) {
    btnToggle.innerHTML = '<i class="fas fa-eye"></i> Ver Activos';
    btnToggle.className = 'btn btn-info';
  } else {
    btnToggle.innerHTML = '<i class="fas fa-eye-slash"></i> Ver Desactivados';
    btnToggle.className = 'btn btn-secondary';
  }
  
  cargarUsuarios();
}

// Función para reactivar usuario
async function reactivarUsuario(id) {
  const confirmacion = await mostrarConfirmacion(
    '¿Está seguro de que desea reactivar este usuario?',
    'El usuario podrá acceder nuevamente al sistema'
  );
  
  if (!confirmacion) {
    return;
  }

  try {
    const response = await fetch(`/api/usuarios-clientes/${id}/reactivar`, {
      method: 'PUT'
    });

    if (response.ok) {
      const resultado = await response.json();
      mostrarExito(resultado.message);
      cargarUsuarios(); // Recargar la tabla
    } else {
      const error = await response.json();
      mostrarError(error.error || 'Error al reactivar usuario');
    }
  } catch (error) {
    console.error('Error:', error);
    mostrarError('Error de conexión');
  }
}

// Cerrar modal al hacer clic fuera de él
document.addEventListener('click', function(event) {
  const modal = document.getElementById('modalUsuario');
  if (event.target === modal) {
    closeModal();
  }
});

// Cerrar modal con tecla Escape
document.addEventListener('keydown', function(event) {
  if (event.key === 'Escape') {
    closeModal();
  }
});

// Funciones de validación
function validarEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

function validarDNI(dni) {
  const regex = /^\d{8}$/;
  return regex.test(dni);
}

function validarTelefono(telefono) {
  // Acepta números de 9 dígitos, con o sin espacios/guiones
  const regex = /^[\d\s\-]{9,15}$/;
  return regex.test(telefono) && telefono.replace(/[\s\-]/g, '').length >= 9;
}

// Función para activar el modo de edición inline
function activarEdicion(id) {
  const fila = document.querySelector(`tr[data-usuario-id="${id}"]`);
  if (!fila) return;

  // Almacenar valores originales como atributos de datos
  const correoOriginal = fila.querySelector('input[name="correo"]').value;
  const telefonoOriginal = fila.querySelector('input[name="telefono"]').value;
  
  fila.setAttribute('data-correo-original', correoOriginal);
  fila.setAttribute('data-telefono-original', telefonoOriginal);

  // Ocultar elementos de display y mostrar elementos de edición
  fila.querySelectorAll('.display-mode').forEach(el => el.style.display = 'none');
  fila.querySelectorAll('.edit-mode').forEach(el => el.style.display = 'inline-block');
  
  // Agregar event listeners para teclas
  const inputs = fila.querySelectorAll('.edit-mode input');
  inputs.forEach(input => {
    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        guardarEdicion(id);
      } else if (e.key === 'Escape') {
        e.preventDefault();
        cancelarEdicion(id);
      }
    });
  });
  
  // Enfocar el primer input
  const primerInput = fila.querySelector('.edit-mode input');
  if (primerInput) primerInput.focus();
}

// Función para cancelar la edición inline
function cancelarEdicion(id) {
  const fila = document.querySelector(`tr[data-usuario-id="${id}"]`);
  if (!fila) return;

  // Mostrar elementos de display y ocultar elementos de edición
  fila.querySelectorAll('.edit-mode').forEach(el => el.style.display = 'none');
  fila.querySelectorAll('.display-mode').forEach(el => el.style.display = '');
  
  // Limpiar atributos de datos originales
  fila.removeAttribute('data-correo-original');
  fila.removeAttribute('data-telefono-original');
  
  // Recargar los datos originales para restaurar valores
  cargarUsuarios();
}

// Función para guardar la edición inline
async function guardarEdicion(id) {
  const fila = document.querySelector(`tr[data-usuario-id="${id}"]`);
  if (!fila) return;

  // Obtener valores originales almacenados
  const correoOriginal = fila.getAttribute('data-correo-original') || '';
  const telefonoOriginal = fila.getAttribute('data-telefono-original') || '';

  // Recopilar solo los datos editables (correo y teléfono)
  const datos = {
    correo: fila.querySelector('input[name="correo"]').value.trim(),
    telefono: fila.querySelector('input[name="telefono"]').value.trim()
  };

  // Validaciones para campos editables
  if (!datos.correo) {
    mostrarError('El correo electrónico es obligatorio');
    return;
  }

  if (!validarEmail(datos.correo)) {
    mostrarError('Por favor, ingrese un correo electrónico válido');
    return;
  }

  // El teléfono es opcional, pero si se proporciona debe ser válido
  if (datos.telefono && !validarTelefono(datos.telefono)) {
    mostrarError('Por favor, ingrese un número de teléfono válido (9 dígitos)');
    return;
  }

  // Verificar si realmente hay cambios
  const hayCambios = datos.correo !== correoOriginal || datos.telefono !== telefonoOriginal;
  
  if (!hayCambios) {
    mostrarInfo('No se detectaron cambios en los datos');
    cancelarEdicion(id);
    return;
  }

  // Construir mensaje de confirmación detallado
  let mensajeDetalle = 'Se realizarán los siguientes cambios:\n\n';
  
  if (datos.correo !== correoOriginal) {
    mensajeDetalle += `📧 Correo:\n   Anterior: ${correoOriginal}\n   Nuevo: ${datos.correo}\n\n`;
  }
  
  if (datos.telefono !== telefonoOriginal) {
    const telefonoMostrar = datos.telefono || 'Sin teléfono';
    const originalMostrar = telefonoOriginal || 'Sin teléfono';
    mensajeDetalle += `📱 Teléfono:\n   Anterior: ${originalMostrar}\n   Nuevo: ${telefonoMostrar}\n\n`;
  }

  // Confirmación antes de guardar
  const confirmacion = await mostrarConfirmacion(
    '¿Confirmar actualización de datos de contacto?',
    mensajeDetalle
  );
  
  if (!confirmacion) {
    return;
  }

  try {
    const response = await fetch(`/api/usuarios-clientes/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(datos)
    });

    if (response.ok) {
      const resultado = await response.json();
      mostrarExito('Datos de contacto actualizados correctamente');
      
      // Volver al modo de visualización
      fila.querySelectorAll('.edit-mode').forEach(el => el.style.display = 'none');
      fila.querySelectorAll('.display-mode').forEach(el => el.style.display = '');
      
      // Limpiar atributos de datos originales
      fila.removeAttribute('data-correo-original');
      fila.removeAttribute('data-telefono-original');
      
      // Recargar la tabla para mostrar los cambios
      cargarUsuarios();
    } else {
      const error = await response.json();
      mostrarError(error.error || 'Error al actualizar los datos de contacto');
    }
  } catch (error) {
    console.error('Error:', error);
    mostrarError('Error de conexión');
  }
}