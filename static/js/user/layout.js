// Marcar el enlace activo del sidebar y auto-ocultar alertas
document.addEventListener('DOMContentLoaded', function() {
	const currentPath = window.location.pathname;
	const sidebarLinks = document.querySelectorAll('.sidebar-nav a');

	sidebarLinks.forEach(link => {
		if (link.getAttribute('href') === currentPath) {
			link.classList.add('active');
		}
	});

	const alerts = document.querySelectorAll('.alert');
	alerts.forEach(alert => {
		setTimeout(() => {
			alert.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
			alert.style.opacity = '0';
			alert.style.transform = 'translateY(-20px)';
			setTimeout(() => alert.remove(), 500);
		}, 5000);
	});
});

