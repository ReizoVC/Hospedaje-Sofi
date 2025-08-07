// Animaciones suaves al cargar
document.addEventListener('DOMContentLoaded', function() {
  const elements = document.querySelectorAll('.fade-in-up');
  elements.forEach((element, index) => {
    element.style.animationDelay = `${index * 0.1}s`;
  });
});

// Funciones para manejar modales
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
  }
});