// Animaciones suaves al cargar
document.addEventListener('DOMContentLoaded', function() {
  const elements = document.querySelectorAll('.fade-in-up');
  elements.forEach((element, index) => {
    element.style.animationDelay = `${index * 0.1}s`;
  });
});