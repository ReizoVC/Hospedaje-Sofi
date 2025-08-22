let originalValues = {};
let isEditing = false;

function toggleEditMode() {
  const editButton = document.getElementById('editButton');
  const saveButton = document.getElementById('saveButton');
  const cancelButton = document.getElementById('cancelButton');
  const nombre = document.getElementById('nombre');
  const apellidos = document.getElementById('apellidos');
  const telefono = document.getElementById('telefono');

  if (!isEditing) {
    originalValues = {
      nombre: nombre.value,
      apellidos: apellidos.value,
      telefono: telefono.value
    };
    nombre.disabled = false;
    apellidos.disabled = false;
    telefono.disabled = false;
    editButton.style.display = 'none';
    saveButton.style.display = 'inline-flex';
    cancelButton.style.display = 'inline-flex';
    nombre.classList.add('editing');
    apellidos.classList.add('editing');
    telefono.classList.add('editing');
    isEditing = true;
  }
}

function cancelEdit() {
  const editButton = document.getElementById('editButton');
  const saveButton = document.getElementById('saveButton');
  const cancelButton = document.getElementById('cancelButton');
  const nombre = document.getElementById('nombre');
  const apellidos = document.getElementById('apellidos');
  const telefono = document.getElementById('telefono');

  nombre.value = originalValues.nombre;
  apellidos.value = originalValues.apellidos;
  telefono.value = originalValues.telefono;
  nombre.disabled = true;
  apellidos.disabled = true;
  telefono.disabled = true;
  editButton.style.display = 'inline-flex';
  saveButton.style.display = 'none';
  cancelButton.style.display = 'none';
  nombre.classList.remove('editing');
  apellidos.classList.remove('editing');
  telefono.classList.remove('editing');
  isEditing = false;
}
