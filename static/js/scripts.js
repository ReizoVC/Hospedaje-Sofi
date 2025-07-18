const toggle = document.getElementById("menu-toggle");
const nav = document.getElementById("mobile-menu");

toggle.addEventListener("click", () => {
    nav.classList.toggle("active");
});

// Verificar si el usuario está autenticado al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
    
    // Toggle para el menú de cuenta
    const accountToggle = document.getElementById("account-toggle");
    const accountMenu = document.getElementById("account-menu");
    
    if (accountToggle && accountMenu) {
        accountToggle.addEventListener("click", (e) => {
            e.stopPropagation();
            accountMenu.classList.toggle("active");
        });
        
        // Cerrar menú al hacer clic fuera
        document.addEventListener("click", () => {
            accountMenu.classList.remove("active");
        });
        
        // Prevenir que el menú se cierre al hacer clic dentro
        accountMenu.addEventListener("click", (e) => {
            e.stopPropagation();
        });
    }
});

// Cerrar menú móvil al cambiar tamaño de ventana
window.addEventListener('resize', () => {
    if (window.innerWidth > 768) {
        const mobileMenu = document.getElementById('mobile-menu');
        if (mobileMenu && mobileMenu.classList.contains('active')) {
            mobileMenu.classList.remove('active');
        }
    }
});

function checkAuthStatus() {
    fetch('/api/check-auth')
        .then(res => res.json())
        .then(data => {
            const sessionBtn = document.getElementById('session-btn');
            const userAccount = document.getElementById('user-account');
            const userNameSpan = document.getElementById('user-name');

            if (data.authenticated && data.user) {
                // Usuario autenticado - mostrar botón de cuenta
                sessionBtn.style.display = 'none';
                userAccount.style.display = 'block';
                userNameSpan.textContent = data.user.name;

                // Actualizar opciones de menú según rol de usuario
                const accountMenu = document.getElementById('account-menu');
                const mobileMenu = document.getElementById('mobile-menu');
                if (data.user.rol >= 3) {
                    accountMenu.innerHTML = `
                        <a href="#perfil">Perfil</a>
                        <a href="#gestion-personal">Gestion de Personal</a>
                        <a href="#reportes">Reportes</a>
                        <a href="#ingresos">Ingresos</a>
                        <a href="#egresos">Egresos</a>
                        <hr>
                        <a href="#" onclick="logout()">Cerrar Sesión</a>
                    `;
                    mobileMenu.innerHTML = `
                        <a href="/">Inicio</a>
                        <a href="/habitaciones">Habitaciones</a>
                        <a href="#nosotros">Nosotros</a>
                        <a href="#perfil">Perfil</a>
                        <a href="#gestion-personal">Gestion de Personal</a>
                        <a href="#reportes">Reportes</a>
                        <a href="#ingresos">Ingresos</a>
                        <a href="#egresos">Egresos</a>
                        <a href="#" onclick="logout()">Cerrar Sesión</a>
                    `;
                } else {
                    accountMenu.innerHTML = `
                        <a href="#perfil">Mi Perfil</a>
                        <a href="#reservas">Mis Reservas</a>
                        <a href="#configuracion">Configuración</a>
                        <hr>
                        <a href="#" onclick="logout()">Cerrar Sesión</a>
                    `;
                    mobileMenu.innerHTML = `
                        <a href="/">Inicio</a>
                        <a href="/habitaciones">Habitaciones</a>
                        <a href="#nosotros">Nosotros</a>
                        <a href="#perfil">Mi Perfil</a>
                        <a href="#reservas">Mis Reservas</a>
                        <a href="#configuracion">Configuración</a>
                        <a href="#" onclick="logout()">Cerrar Sesión</a>
                    `;
                }
            } else {
                // Usuario no autenticado - mostrar botón de login y opciones por defecto
                sessionBtn.style.display = 'block';
                userAccount.style.display = 'none';

                const mobileMenu = document.getElementById('mobile-menu');
                mobileMenu.innerHTML = `
                    <a href=\"/\">Inicio</a>
                    <a href=\"/habitaciones\">Habitaciones</a>
                    <a href=\"#nosotros\">Nosotros</a>
                    <a href=\"/login\">Iniciar Sesión</a>
                `;
            }
        })
        .catch(err => {
            console.error('Error checking auth status:', err);
            // En caso de error, mostrar botón de login
            document.getElementById('session-btn').style.display = 'block';
            document.getElementById('user-account').style.display = 'none';
        });
}

function logout() {
    fetch("/api/logout", { method: "POST" })
    .then(res => res.json())
    .then(() => {
        // Actualizar la interfaz después del logout
        checkAuthStatus();
        window.location.reload();
    })
    .catch(err => console.error("Logout failed", err));
}