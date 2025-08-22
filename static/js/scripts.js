const toggle = document.getElementById("menu-toggle");
const nav = document.getElementById("mobile-menu");

if (toggle && nav) {
    toggle.addEventListener("click", () => {
        nav.classList.toggle("active");
    });
}

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
                if (sessionBtn) sessionBtn.style.display = 'none';
                if (userAccount) userAccount.style.display = 'block';
                if (userNameSpan) {
                    userNameSpan.textContent = data.user.name || userNameSpan.textContent;
                }

                // Actualizar opciones de menú según rol de usuario
                const accountMenu = document.getElementById('account-menu');
                const mobileMenu = document.getElementById('mobile-menu');
                
                if (accountMenu && mobileMenu && data.user.rol >= 4) {
                    // Administrador (rol 4) - Un único enlace al panel
                    accountMenu.innerHTML = `
                        <a href="/user/profile">Mi Perfil</a>
                        <a href="/gestion">Panel de Gestión</a>
                        <a href="/reportes-admin">Reportes</a>
                        <a href="/inventario">Inventario</a>
                        <hr>
                        <a href="#" onclick="logout()">Cerrar Sesión</a>
                    `;
                    mobileMenu.innerHTML = `
                        <a href="/">Inicio</a>
                        <a href="/habitaciones">Habitaciones</a>
                        <a href="/nosotros">Nosotros</a>
                        <a href="/user/profile">Mi Perfil</a>
                        <a href="/gestion">Panel de Gestión</a>
                        <a href="/reportes-admin">Reportes</a>
                        <a href="/inventario">Inventario</a>
                        <a href="#" onclick="logout()">Cerrar Sesión</a>
                    `;
                } else if (accountMenu && mobileMenu && data.user.rol === 3) {
                    // Almacenista (rol 3) - Gestión de inventario y reportes básicos
                    accountMenu.innerHTML = `
                        <a href="/user/profile">Mi Perfil</a>
                        <a href="/inventario">Inventario</a>
                        <a href="/reportes-almacen">Reportes de Almacén</a>
                        <hr>
                        <a href="" onclick="logout()">Cerrar Sesión</a>
                    `;
                    mobileMenu.innerHTML = `
                        <a href="/">Inicio</a>
                        <a href="/habitaciones">Habitaciones</a>
                        <a href="/nosotros">Nosotros</a>
                        <a href="/user/profile">Mi Perfil</a>
                        <a href="/inventario">Inventario</a>
                        <a href="/reportes-almacen">Reportes de Almacén</a>
                        <a href="" onclick="logout()">Cerrar Sesión</a>
                    `;
                } else if (accountMenu && mobileMenu && data.user.rol === 2) {
                    // Recepcionista (rol 2) - Gestión de reservas y huéspedes
                    accountMenu.innerHTML = `
                        <a href="/user/profile">Mi Perfil</a>
                        <a href="/gestion-reservas">Gestión de Reservas</a>
                        <a href="/check">Check-in / Check-out</a>
                        <a href="/gestion-usuario">Gestión de Huéspedes</a>
                        <a href="/estado-habitaciones">Estado Habitaciones</a>
                        <hr>
                        <a href="" onclick="logout()">Cerrar Sesión</a>
                    `;
                    mobileMenu.innerHTML = `
                        <a href="/">Inicio</a>
                        <a href="/habitaciones">Habitaciones</a>
                        <a href="/nosotros">Nosotros</a>
                        <a href="/user/profile">Mi Perfil</a>
                        <a href="/gestion-reservas">Gestión de Reservas</a>
                        <a href="/check">Check-in / Check-out</a>
                        <a href="/gestion-usuario">Gestión de Huéspedes</a>
                        <a href="/estado-habitaciones">Estado Habitaciones</a>
                        <a href="" onclick="logout()">Cerrar Sesión</a>
                    `;
                } else if (accountMenu && mobileMenu) {
                    // Usuario normal (rol 1) - Cliente normal
                    accountMenu.innerHTML = `
                        <a href="/user/profile">Mi Perfil</a>
            <a href="/user/reservations">Mis Reservas</a>
            <a href="/user/reservations#historial">Historial</a>
            <a href="/user/settings">Configuración</a>
                        <hr>
            <a href="" onclick="logout()">Cerrar Sesión</a>
                    `;
                    mobileMenu.innerHTML = `
                        <a href="/">Inicio</a>
                        <a href="/habitaciones">Habitaciones</a>
                        <a href="/nosotros">Nosotros</a>
                        <a href="/user/profile">Mi Perfil</a>
            <a href="/user/reservations">Mis Reservas</a>
            <a href="/user/reservations#historial">Historial</a>
            <a href="/user/settings">Configuración</a>
                        <a href="" onclick="logout()">Cerrar Sesión</a>
                    `;
                }
            } else {
                // Usuario no autenticado - mostrar botón de login y opciones por defecto
                if (sessionBtn) sessionBtn.style.display = 'block';
                // Solo ocultar el bloque de cuenta si también existe el botón de sesión
                if (userAccount && sessionBtn) userAccount.style.display = 'none';

                const mobileMenu = document.getElementById('mobile-menu');
                if (mobileMenu) mobileMenu.innerHTML = `
                    <a href=\"/\">Inicio</a>
                    <a href=\"/habitaciones\">Habitaciones</a>
                    <a href=\"/nosotros\">Nosotros</a>
                    <a href=\"/login\">Iniciar Sesión</a>
                `;
            }
        })
        .catch(err => {
            console.error('Error checking auth status:', err);
            // En caso de error, mantener el estado renderizado por el servidor
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