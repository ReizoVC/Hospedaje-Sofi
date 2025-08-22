(function(){
  // Helpers de selección
  const $ = (sel)=>document.querySelector(sel);
  const $$ = (sel)=>document.querySelectorAll(sel);

  // Leer valores dinámicos desde el script tag que carga este archivo
  const thisScript = document.currentScript;
  const precioPorNoche = Number(thisScript?.dataset?.precioNoche || thisScript?.getAttribute('data-precio-noche') || 0);
  const idhabitacion = Number(thisScript?.dataset?.idhabitacion || thisScript?.getAttribute('data-idhabitacion') || 0);

  // Estado interno
  let fechasValidas = false;

  // Exponer funciones globales usadas en la plantilla
  window.cambiarImagen = function(nuevaImagen){
    const main = $('#imagen-main');
    if (main) main.src = nuevaImagen;
    // Actualizar clase active en miniaturas
    $$('.miniatura').forEach(img => img.classList.remove('active'));
    if (window.event && window.event.target) {
      window.event.target.classList.add('active');
    }
  };

  window.abrirModalReserva = function(){
    const modal = $('#modalReserva');
    if (!modal) return;
    modal.style.display = 'block';
    // Configurar fechas mínimas
    const hoy = new Date().toISOString().split('T')[0];
    const fi = $('#modal-fecha-inicio');
    const ff = $('#modal-fecha-fin');
    if (fi) fi.min = hoy;
    if (ff) ff.min = hoy;
  };

  window.cerrarModalReserva = function(){
    const modal = $('#modalReserva');
    if (!modal) return;
    modal.style.display = 'none';
    // Limpiar formulario
    const form = $('#formReserva');
    if (form) form.reset();
    const resumen = $('#resumenReserva');
    if (resumen) resumen.style.display = 'none';
    const msg = $('#disponibilidadMensaje');
    if (msg) msg.innerHTML = '';
    const btn = $('#btnConfirmarReserva');
    if (btn) btn.disabled = true;
    fechasValidas = false;
  };

  // Cerrar modal al hacer click fuera
  window.addEventListener('click', (event)=>{
    const modal = $('#modalReserva');
    if (event.target === modal) {
      window.cerrarModalReserva();
    }
  });

  document.addEventListener('DOMContentLoaded', function(){
    const fi = $('#modal-fecha-inicio');
    const ff = $('#modal-fecha-fin');
    if (fi && ff){
      fi.addEventListener('change', function(){
        ff.min = fi.value;
        if (ff.value && ff.value <= fi.value) {
          ff.value = '';
        }
        validarYCalcular();
      });
      ff.addEventListener('change', validarYCalcular);
    }
  });

  async function validarYCalcular(){
    const fechaInicio = $('#modal-fecha-inicio')?.value;
    const fechaFin = $('#modal-fecha-fin')?.value;
    const resumen = $('#resumenReserva');
    const mensaje = $('#disponibilidadMensaje');
    const btnConfirmar = $('#btnConfirmarReserva');

    if (mensaje) mensaje.innerHTML = '';
    if (btnConfirmar) btnConfirmar.disabled = true;
    fechasValidas = false;

    if (!fechaInicio || !fechaFin){
      if (resumen) resumen.style.display = 'none';
      return;
    }

    const inicio = new Date(fechaInicio);
    const fin = new Date(fechaFin);
    if (fin <= inicio){
      if (mensaje) mensaje.innerHTML = '<div class="error-mensaje">La fecha de salida debe ser posterior a la fecha de llegada</div>';
      if (resumen) resumen.style.display = 'none';
      return;
    }

    const diffTime = Math.abs(fin - inicio);
    const noches = Math.ceil(diffTime / (1000*60*60*24));
    const total = noches * (precioPorNoche || 0);

    const nochesEl = $('#cantidadNoches');
    const totalEl = $('#precioTotalModal');
    if (nochesEl) nochesEl.textContent = String(noches);
    if (totalEl) totalEl.textContent = String(total.toFixed(0));
    if (resumen) resumen.style.display = 'block';

    if (mensaje) mensaje.innerHTML = '<div class="loading-mensaje">Verificando disponibilidad...</div>';
    try {
      const response = await fetch('/reservas/verificar-disponibilidad', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          idhabitacion: idhabitacion,
          fechainicio: fechaInicio,
          fechafin: fechaFin
        })
      });
      const data = await response.json();
      if (data.disponible){
        if (mensaje) mensaje.innerHTML = '<div class="success-mensaje">✓ Habitación disponible</div>';
        if (btnConfirmar) btnConfirmar.disabled = false;
        fechasValidas = true;
      } else {
        if (mensaje) mensaje.innerHTML = '<div class="error-mensaje">✗ ' + (data.message||'No disponible') + '</div>';
        if (btnConfirmar) btnConfirmar.disabled = true;
        fechasValidas = false;
      }
    } catch(err){
      console.error('Error al verificar disponibilidad:', err);
      if (mensaje) mensaje.innerHTML = '<div class="error-mensaje">Error al verificar disponibilidad</div>';
      if (btnConfirmar) btnConfirmar.disabled = true;
      fechasValidas = false;
    }
  }

  window.confirmarReserva = async function(){
    if (!fechasValidas){
      alert('Por favor verifica las fechas seleccionadas');
      return;
    }
    const fechaInicio = $('#modal-fecha-inicio')?.value;
    const fechaFin = $('#modal-fecha-fin')?.value;
    const btn = $('#btnConfirmarReserva');
    if (btn){
      btn.disabled = true;
      btn.textContent = 'Procesando...';
    }
    try {
      const response = await fetch('/reservas/crear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          idhabitacion: idhabitacion,
          fechainicio: fechaInicio,
          fechafin: fechaFin
        })
      });
      const data = await response.json();
      if (data.success){
        alert(`¡Reserva creada exitosamente!\n\nCódigo de reserva: ${data.codigo_reserva}\n\nSerás redirigido a tus reservas.`);
        window.location.href = '/reservas/mis-reservas';
      } else {
        alert(data.message || 'Error al crear la reserva');
        if (btn){ btn.disabled = false; btn.textContent = 'Confirmar Reserva'; }
      }
    } catch(err){
      console.error('Error:', err);
      alert('Error al procesar la reserva. Inténtalo de nuevo.');
      if (btn){ btn.disabled = false; btn.textContent = 'Confirmar Reserva'; }
    }
  };
})();
