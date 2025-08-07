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
});

// Funciones para modal nativo
function openModal() {
  const modal = document.getElementById('modalUsuario');
  modal.classList.add('show');
  modal.style.display = 'flex';
}

function closeModal() {
  const modal = document.getElementById('modalUsuario');
  modal.classList.remove('show');
  modal.style.display = 'none';
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