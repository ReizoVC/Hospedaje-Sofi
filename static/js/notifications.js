// Sistema de notificaciones y confirmaciones ligero para la UI

class NotificationSystem {
    constructor() {
        this.container = null;
        this.notifications = new Map();
        this.maxNotifications = 5;
        this.defaultDuration = 5000; // 5 segundos
        this.init();
    }

    init() {
        this.createContainer();
        this.bindEvents();
    }

    createContainer() {
        if (document.getElementById('notification-container')) {
            this.container = document.getElementById('notification-container');
            return;
        }

        this.container = document.createElement('div');
        this.container.id = 'notification-container';
        this.container.className = 'notification-container';
        document.body.appendChild(this.container);
    }

    bindEvents() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.clearAll();
            }
        });
    }

    show(message, type = 'info', options = {}) {
        const config = {
            duration: options.duration || this.defaultDuration,
            closable: options.closable !== false,
            persistent: options.persistent === true,
            onClick: options.onClick || null,
            id: options.id || this.generateId()
        };

        // Evitar duplicados si se especifica un ID
        if (config.id && this.notifications.has(config.id)) {
            return this.notifications.get(config.id);
        }

        if (this.notifications.size >= this.maxNotifications) {
            this.removeOldest();
        }

        const notification = this.createNotification(message, type, config);
        this.notifications.set(config.id, notification);
        this.container.appendChild(notification.element);

        requestAnimationFrame(() => {
            notification.element.classList.add('slide-in');
        });

        if (!config.persistent) {
            notification.timer = setTimeout(() => {
                this.remove(config.id);
            }, config.duration);

            this.startProgress(notification, config.duration);
        }

        return notification;
    }

    createNotification(message, type, config) {
        const element = document.createElement('div');
        element.className = `notification ${type}`;
        element.setAttribute('data-id', config.id);

        const content = document.createElement('div');
        content.className = 'notification-content';
        content.textContent = message;

        element.appendChild(content);

        if (config.closable) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'notification-close';
            closeBtn.innerHTML = '×';
            closeBtn.setAttribute('title', 'Cerrar');
            closeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.remove(config.id);
            });
            element.appendChild(closeBtn);
        }

        if (!config.persistent) {
            const progressBar = document.createElement('div');
            progressBar.className = 'notification-progress';
            element.appendChild(progressBar);
        }

        if (config.onClick) {
            element.style.cursor = 'pointer';
            element.addEventListener('click', () => {
                config.onClick();
                this.remove(config.id);
            });
        } else {
            element.addEventListener('click', () => {
                this.remove(config.id);
            });
        }

        return {
            element,
            config,
            timer: null,
            progressTimer: null
        };
    }

    startProgress(notification, duration) {
        const progressBar = notification.element.querySelector('.notification-progress');
        if (!progressBar) return;

        progressBar.style.width = '100%';
        progressBar.style.transition = `width ${duration}ms linear`;

        // Reducir progreso
        setTimeout(() => {
            progressBar.style.width = '0%';
        }, 10);
    }

    remove(id) {
        const notification = this.notifications.get(id);
        if (!notification) return;

        // Limpiar timers
        if (notification.timer) {
            clearTimeout(notification.timer);
        }
        if (notification.progressTimer) {
            clearTimeout(notification.progressTimer);
        }

        notification.element.classList.remove('slide-in');
        notification.element.classList.add('slide-out');

        // Eliminar del DOM
        setTimeout(() => {
            if (notification.element.parentNode) {
                notification.element.parentNode.removeChild(notification.element);
            }
            this.notifications.delete(id);
        }, 300);
    }

    removeOldest() {
        const firstKey = this.notifications.keys().next().value;
        if (firstKey) {
            this.remove(firstKey);
        }
    }

    clearAll() {
        for (const id of this.notifications.keys()) {
            this.remove(id);
        }
    }

    generateId() {
        return 'notification_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // Métodos de conveniencia para cada tipo
    
    success(message, options = {}) {
        return this.show(message, 'success', options);
    }

    error(message, options = {}) {
        return this.show(message, 'error', { duration: 7000, ...options });
    }

    warning(message, options = {}) {
        return this.show(message, 'warning', { duration: 6000, ...options });
    }

    info(message, options = {}) {
        return this.show(message, 'info', options);
    }
}

// Crear instancia global
window.notifications = new NotificationSystem();

// Funciones globales para compatibilidad con código existente
window.showNotification = (message, type = 'info', options = {}) => {
    return window.notifications.show(message, type, options);
};

window.showSuccess = (message, options = {}) => {
    return window.notifications.success(message, options);
};

window.showError = (message, options = {}) => {
    return window.notifications.error(message, options);
};

window.showWarning = (message, options = {}) => {
    return window.notifications.warning(message, options);
};

window.showInfo = (message, options = {}) => {
    return window.notifications.info(message, options);
};

// Reemplaza alert() por notificaciones
window.originalAlert = window.alert;
window.alert = function(message) {
    if (typeof message === 'string' && message.toLowerCase().includes('error')) {
        window.notifications.error(message);
    } else if (typeof message === 'string' && (message.toLowerCase().includes('éxito') || message.toLowerCase().includes('exitoso'))) {
        window.notifications.success(message);
    } else if (typeof message === 'string' && (message.toLowerCase().includes('advertencia') || message.toLowerCase().includes('cuidado'))) {
        window.notifications.warning(message);
    } else {
        window.notifications.info(message);
    }
};

// Funciones para mostrar mensajes específicos
window.mostrarError = (mensaje) => window.notifications.error(mensaje);
window.mostrarExito = (mensaje) => window.notifications.success(mensaje);
window.mostrarAdvertencia = (mensaje) => window.notifications.warning(mensaje);
window.mostrarInfo = (mensaje) => window.notifications.info(mensaje);

// Confirmación personalizada (Promise<boolean>)
window.mostrarConfirmacion = (mensaje, detalle = '') => {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.className = 'notification-modal';
        modal.innerHTML = `
            <div class="notification-modal-overlay"></div>
            <div class="notification-modal-content">
                <div class="notification-modal-header">
                    <i class="fas fa-question-circle"></i>
                    <h3>Confirmación</h3>
                </div>
                <div class="notification-modal-body">
                    <p class="confirmation-message">${mensaje}</p>
                    ${detalle ? `<p class="confirmation-detail">${detalle}</p>` : ''}
                </div>
                <div class="notification-modal-footer">
                    <button class="btn btn-cancel" onclick="closeConfirmation(false)">Cancelar</button>
                    <button class="btn btn-confirm" onclick="closeConfirmation(true)">Confirmar</button>
                </div>
            </div>
        `;

        if (!document.getElementById('confirmation-styles')) {
            const styles = document.createElement('style');
            styles.id = 'confirmation-styles';
            styles.textContent = `
                .notification-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    z-index: 10000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    opacity: 0;
                    transition: opacity 0.3s ease;
                }
                
                .notification-modal.show {
                    opacity: 1;
                }
                
                .notification-modal-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.6);
                    backdrop-filter: blur(5px);
                }
                
                .notification-modal-content {
                    position: relative;
                    background: white;
                    border-radius: 16px;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
                    max-width: 400px;
                    width: 90%;
                    transform: scale(0.9);
                    transition: transform 0.3s ease;
                }
                
                .notification-modal.show .notification-modal-content {
                    transform: scale(1);
                }
                
                .notification-modal-header {
                    padding: 24px 24px 16px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    border-bottom: 1px solid #e5e7eb;
                }
                
                .notification-modal-header i {
                    color: #f59e0b;
                    font-size: 24px;
                }
                
                .notification-modal-header h3 {
                    margin: 0;
                    font-size: 18px;
                    font-weight: 600;
                    color: #1f2937;
                }
                
                .notification-modal-body {
                    padding: 16px 24px;
                }
                
                .confirmation-message {
                    margin: 0 0 8px 0;
                    font-size: 16px;
                    font-weight: 500;
                    color: #374151;
                }
                
                .confirmation-detail {
                    margin: 0;
                    font-size: 14px;
                    color: #6b7280;
                }
                
                .notification-modal-footer {
                    padding: 16px 24px 24px;
                    display: flex;
                    gap: 12px;
                    justify-content: flex-end;
                }
                
                .notification-modal .btn {
                    padding: 10px 20px;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                
                .notification-modal .btn-cancel {
                    background: #f3f4f6;
                    color: #374151;
                }
                
                .notification-modal .btn-cancel:hover {
                    background: #e5e7eb;
                }
                
                .notification-modal .btn-confirm {
                    background: #ef4444;
                    color: white;
                }
                
                .notification-modal .btn-confirm:hover {
                    background: #dc2626;
                }
            `;
            document.head.appendChild(styles);
        }

        document.body.appendChild(modal);

        window.closeConfirmation = (result) => {
            modal.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(modal);
                delete window.closeConfirmation;
                resolve(result);
            }, 300);
        };

        const handleKeydown = (e) => {
            if (e.key === 'Escape') {
                window.closeConfirmation(false);
                document.removeEventListener('keydown', handleKeydown);
            }
        };

        modal.querySelector('.notification-modal-overlay').addEventListener('click', () => {
            window.closeConfirmation(false);
            document.removeEventListener('keydown', handleKeydown);
        });

        document.addEventListener('keydown', handleKeydown);

        setTimeout(() => modal.classList.add('show'), 10);
    });
};

// Exportar para módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationSystem;
}
