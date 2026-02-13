(function(){
  // Helpers de selección
  const $ = (sel)=>document.querySelector(sel);
  const $$ = (sel)=>document.querySelectorAll(sel);

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

  document.addEventListener('DOMContentLoaded', function(){
    // Valoraciones: cargar al inicio
    initValoraciones();
  });

  // -----------------
  // Valoraciones
  // -----------------
  function initValoraciones(){
    const cont = document.getElementById('valoraciones');
    if (!cont) return;

    const idh = cont.getAttribute('data-idhabitacion');
    const lista = document.getElementById('listaValoraciones');
    const promedioEl = document.getElementById('valoracionesPromedio');
    const totalEl = document.getElementById('valoracionesTotal');
    const form = document.getElementById('formValoracion');
    const msg = document.getElementById('valoracionMsg');
    const submitBtn = document.getElementById('btnEnviarValoracion');

    const renderLista = (items)=>{
      if (!lista) return;
      if (!items || items.length === 0){
        lista.innerHTML = '<p>Aún no hay valoraciones.</p>';
        return;
      }
      lista.innerHTML = items.map(v => {
        const fecha = v.fecha_creacion
          ? new Date(v.fecha_creacion).toLocaleString(undefined, {
              year: 'numeric',
              month: 'short',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
              hour12: false,
            })
          : '';
        const textoSeguro = (v.comentario || '').replaceAll('<','&lt;').replaceAll('>','&gt;');
        const nombre = v.usuario ? `${v.usuario.nombre || ''} ${v.usuario.apellidos || ''}`.trim() : '';
        const autor = nombre || 'Usuario';
        return `
          <div class="valoracion-item">
            <div class="valoracion-item-head">
              <span class="valoracion-puntos">${v.puntuacion}/5 ★</span>
              <span class="valoracion-fecha">${fecha}</span>
            </div>
            <div class="valoracion-autor">${autor}</div>
            <div class="valoracion-texto">${textoSeguro || '<em>Sin comentario</em>'}</div>
          </div>
        `;
      }).join('');
    };

    async function cargarValoraciones(){
      try {
        const res = await fetch(`/api/habitaciones/${idh}/valoraciones`);
        const data = await res.json();
        if (promedioEl) promedioEl.textContent = (data.promedio ?? 0).toFixed(1);
        if (totalEl) totalEl.textContent = String(data.total ?? 0);
        renderLista(data.valoraciones || []);
      } catch(err){
        if (lista) lista.innerHTML = '<p>No se pudieron cargar las valoraciones.</p>';
      }
    }

    if (form){
      const starInputs = form.querySelectorAll('input[name="puntuacion"]');

      const updateStars = () => {
        const selected = Number(form.querySelector('input[name="puntuacion"]:checked')?.value || 0);
        starInputs.forEach(inp => {
          const label = inp.parentElement;
          const val = Number(inp.value || 0);
          if (label) label.classList.toggle('filled', val <= selected);
        });
      };

      // Estado inicial: ninguna seleccionada
      starInputs.forEach(inp => { inp.checked = false; });
      starInputs.forEach(inp => {
        inp.addEventListener('change', updateStars);
        // Asegurar hover mantiene coloreado previamente seleccionado
        inp.parentElement?.addEventListener('mouseover', () => {
          starInputs.forEach(other => {
            const lbl = other.parentElement;
            if (!lbl) return;
            lbl.classList.toggle('filled', Number(other.value) <= Number(inp.value));
          });
        });
        inp.parentElement?.addEventListener('mouseout', updateStars);
      });

      // Estado inicial
      updateStars();

      form.addEventListener('submit', async (e)=>{
        e.preventDefault();
        const puntuacion = Number(form.querySelector('input[name="puntuacion"]:checked')?.value || 0);
        const comentario = document.getElementById('comentario')?.value || '';

        if (!puntuacion){
          if (msg){ msg.textContent = 'Selecciona una puntuación'; msg.classList.add('error'); }
          return;
        }

        if (submitBtn){ submitBtn.disabled = true; submitBtn.textContent = 'Enviando...'; }
        if (msg){ msg.textContent = ''; msg.className = 'valoracion-msg'; }

        try {
          const res = await fetch(`/api/habitaciones/${idh}/valoraciones`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ puntuacion, comentario })
          });
          const data = await res.json();
          if (!res.ok) throw new Error(data.error || 'No se pudo guardar');

          if (msg){ msg.textContent = data.message || 'Valoración guardada'; msg.classList.add('ok'); }
          form.reset();
          updateStars();
          await cargarValoraciones();
        } catch(err){
          if (msg){ msg.textContent = err.message; msg.classList.add('error'); }
        } finally {
          if (submitBtn){ submitBtn.disabled = false; submitBtn.textContent = 'Enviar valoración'; }
        }
      });
    }

    cargarValoraciones();
  }
})();
