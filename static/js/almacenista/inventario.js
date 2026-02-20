// Inventario - Almacenista
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

function openModal(id){ document.getElementById(id).style.display='flex'; }
function closeModal(id){ document.getElementById(id).style.display='none'; }

async function fetchProductos(params={}){
  const q = new URLSearchParams(params).toString();
  const res = await fetch('api/productos'+(q?`?${q}`:''));
  return await res.json();
}

function renderProductos(items){
  const tbody = document.getElementById('tbody-productos');
  if(!Array.isArray(items) || items.length===0){
    tbody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding: 1rem;">Sin resultados</td></tr>';
    return;
  }
  tbody.innerHTML = items.map(p=>{
    const estado = p.agotado? 'agotado' : (p.bajo_stock? 'bajo' : 'ok');
    const pillClass = estado==='agotado'?'estado-agotado':(estado==='bajo'?'estado-bajo':'estado-ok');
    const dias = (p.dias_para_vencer===null || p.dias_para_vencer===undefined)? '' : p.dias_para_vencer;
    const fv = p.fecha_vencimiento || '';
    return `<tr>
      <td>${p.idproducto}</td>
      <td>${p.nombre}</td>
      <td>S/ ${Number(p.costo||0).toFixed(0)}</td>
      <td>S/ ${Number(p.costo_total||0).toFixed(0)}</td>
      <td>${p.cantidad}</td>
      <td>${p.umbralminimo}</td>
      <td>${fv}</td>
      <td>${dias}</td>
      <td><span class="estado-pill ${pillClass}">${estado}</span></td>
      <td class="acciones">
        <button class="btn btn-primary btn-icon" title="Registrar movimiento" aria-label="Registrar movimiento" onclick="abrirMovimiento(${p.idproducto})">
          <i class="fa-solid fa-right-left"></i>
        </button>
        <button class="btn btn-warn btn-icon" title="Editar" aria-label="Editar" onclick="abrirEditar(${p.idproducto})">
          <i class="fa-solid fa-pen"></i>
        </button>
        <button class="btn btn-danger btn-icon" title="Eliminar" aria-label="Eliminar" onclick="eliminarProducto(${p.idproducto})">
          <i class="fa-solid fa-trash"></i>
        </button>
      </td>
    </tr>`;
  }).join('');
}

async function cargar(){
  const data = await fetchProductos();
  renderProductos(data);
}

async function fetchLotesVencidos(){
  const res = await fetch('api/lotes/vencidos');
  return await res.json();
}

function renderLotesVencidos(items){
  const tbody = document.getElementById('tbody-vencidos');
  if(!Array.isArray(items) || items.length===0){
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 1rem;">Sin lotes vencidos</td></tr>';
    return;
  }
  tbody.innerHTML = items.map(l=>{
    const ingreso = (l.fecha_ingreso||'').replace('T',' ').slice(0,16);
    return `<tr>
      <td>${l.idlote}</td>
      <td>${l.producto || l.idproducto}</td>
      <td>${l.cantidad_actual}</td>
      <td>${l.cantidad_inicial}</td>
      <td>${l.fecha_vencimiento || ''}</td>
      <td>S/ ${Number(l.costo_unitario||0).toFixed(0)}</td>
      <td>${ingreso}</td>
    </tr>`;
  }).join('');
}

function abrirEditar(id){
  const row = [...document.querySelectorAll('#tbody-productos tr')].find(tr=> tr.children[0].textContent==id);
  if(!row) return;
  $('#modalProductoTitulo').textContent='Editar producto';
  $('#prod-id').value = id;
  $('#prod-nombre').value = row.children[1].textContent;
  $('#prod-umbral').value = row.children[5].textContent;
  
  // Ocultar campos de nuevo producto
  document.getElementById('prod-cantidad-row').style.display = 'none';
  document.getElementById('prod-costo-row').style.display = 'none';
  document.getElementById('prod-fv-row').style.display = 'none';
  document.getElementById('prod-sin-fv-row').style.display = 'none';
  
  // Mostrar campos de edición y lotes
  document.getElementById('lotes-header').style.display = 'block';
  document.getElementById('lotes-list').style.display = 'block';
  
  cargarLotesParaEdicion(id);
  openModal('modalProducto');
}

async function cargarLotesParaEdicion(idproducto){
  try {
    const res = await fetch(`api/lotes/producto/${idproducto}`);
    const lotes = await res.json();
    
    if(!Array.isArray(lotes)){
      document.getElementById('lotes-list').innerHTML = '<p style="text-align: center; color: #999; padding: 1rem;">Error al cargar lotes</p>';
      return;
    }
    
    if(lotes.length === 0){
      document.getElementById('lotes-list').innerHTML = '<p style="text-align: center; color: #999; padding: 1rem;">Sin lotes registrados</p>';
      return;
    }
    
    const html = lotes.map(l => {
      const estado = l.vencido ? 'vencido' : (l.dias_para_vencer !== null && l.dias_para_vencer <= 15 ? 'por-vencer' : 'vigente');
      const estadoColor = l.vencido ? '#ef4444' : (l.dias_para_vencer !== null && l.dias_para_vencer <= 15 ? '#f59e0b' : '#10b981');
      const fv = l.fecha_vencimiento ? new Date(l.fecha_vencimiento).toLocaleDateString() : 'Sin vencer';
      return `
        <div style="
          padding: 0.75rem;
          border: 1px solid #ddd;
          border-radius: 0.375rem;
          margin-bottom: 0.5rem;
          cursor: pointer;
          transition: all 0.2s;
          background: white;
        " 
        onmouseover="this.style.background='#f9fafb'; this.style.borderColor='#999';"
        onmouseout="this.style.background='white'; this.style.borderColor='#ddd';"
        onclick="abrirEditarLote(${l.idlote}, ${l.cantidad_actual}, ${l.cantidad_inicial}, '${l.fecha_vencimiento || ''}', ${l.costo_unitario}, '${l.fecha_ingreso || ''}')">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
              <strong>Lote #${l.idlote}</strong>
              <span style="
                display: inline-block;
                margin-left: 0.5rem;
                padding: 0.25rem 0.5rem;
                background: ${estadoColor};
                color: white;
                border-radius: 0.25rem;
                font-size: 0.75rem;
              ">${estado}</span>
            </div>
            <div style="text-align: right; font-size: 0.875rem; color: #666;">
              <p style="margin: 0;">Cant: ${l.cantidad_actual}/${l.cantidad_inicial}</p>
              <p style="margin: 0;">Vencimiento: ${fv}</p>
            </div>
          </div>
        </div>
      `;
    }).join('');
    
    document.getElementById('lotes-list').innerHTML = html;
  } catch(e) {
    document.getElementById('lotes-list').innerHTML = '<p style="text-align: center; color: #f00; padding: 1rem;">Error al cargar lotes</p>';
  }
}

function abrirEditarLote(idlote, cantidad_actual, cantidad_inicial, fecha_vencimiento, costo_unitario, fecha_ingreso){
  $('#lote-id').value = idlote;
  $('#lote-id-display').textContent = idlote;
  $('#lote-cantidad-actual').value = cantidad_actual;
  $('#lote-costo').value = costo_unitario;
  $('#lote-fecha-ingreso').textContent = fecha_ingreso ? new Date(fecha_ingreso).toLocaleString() : '-';
  
  // Actualizar estado del lote
  const hoy = new Date();
  if(fecha_vencimiento){
    const fv = new Date(fecha_vencimiento);
    const diasFalta = Math.floor((fv - hoy) / (1000 * 60 * 60 * 24));
    let estado = 'Vigente';
    let color = '#10b981';
    if(diasFalta < 0){
      estado = 'Vencido';
      color = '#ef4444';
    } else if(diasFalta <= 15){
      estado = `Por vencer (${diasFalta}d)`;
      color = '#f59e0b';
    }
    $('#lote-estado').textContent = estado;
    $('#lote-estado').style.background = color;
    $('#lote-estado').style.color = 'white';
    $('#lote-fv').value = fecha_vencimiento;
    $('#lote-sin-fv').checked = false;
    $('#lote-fv').disabled = false;
  } else {
    $('#lote-estado').textContent = 'Sin vencimiento';
    $('#lote-estado').style.background = '#6b7280';
    $('#lote-estado').style.color = 'white';
    $('#lote-fv').value = '';
    $('#lote-sin-fv').checked = true;
    $('#lote-fv').disabled = true;
  }
  
  closeModal('modalProducto');
  openModal('modalEditarLote');
}

async function eliminarProducto(id){
  // Cargar lotes del producto
  const res = await fetch(`api/lotes/producto/${id}`);
  const lotes = await res.json();
  
  if(!Array.isArray(lotes) || lotes.length === 0){
    alert('El producto no tiene lotes para eliminar');
    return;
  }
  
  // Guardar el ID del producto para usar después
  window._productoEnEliminacion = id;
  cargarLotesParaEliminar(lotes);
  openModal('modalEliminarLote');
}

function cargarLotesParaEliminar(lotes){
  const container = document.getElementById('lotes-eliminar-list');
  
  if(!Array.isArray(lotes) || lotes.length === 0){
    container.innerHTML = '<p style="text-align: center; color: #999; padding: 1rem;">Sin lotes registrados</p>';
    return;
  }
  
  const html = lotes.map(l => {
    const estado = l.vencido ? 'vencido' : (l.dias_para_vencer !== null && l.dias_para_vencer <= 15 ? 'por-vencer' : 'vigente');
    const estadoColor = l.vencido ? '#ef4444' : (l.dias_para_vencer !== null && l.dias_para_vencer <= 15 ? '#f59e0b' : '#10b981');
    const fv = l.fecha_vencimiento ? new Date(l.fecha_vencimiento).toLocaleDateString() : 'Sin vencer';
    return `
      <div style="
        padding: 0.75rem;
        border: 1px solid #ddd;
        border-radius: 0.375rem;
        margin-bottom: 0.5rem;
        background: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
      ">
        <div>
          <strong>Lote #${l.idlote}</strong>
          <span style="
            display: inline-block;
            margin-left: 0.5rem;
            padding: 0.25rem 0.5rem;
            background: ${estadoColor};
            color: white;
            border-radius: 0.25rem;
            font-size: 0.75rem;
          ">${estado}</span>
          <div style="font-size: 0.875rem; color: #666; margin-top: 0.25rem;">
            <p style="margin: 0;">Cant: ${l.cantidad_actual}/${l.cantidad_inicial}</p>
            <p style="margin: 0;">Costo: S/ ${l.costo_unitario} | Vencimiento: ${fv}</p>
          </div>
        </div>
        <button 
          type="button"
          class="btn btn-danger btn-icon"
          title="Eliminar lote"
          onclick="confirmarEliminarLote(${l.idlote})"
          style="margin-left: 1rem; flex-shrink: 0;">
          <i class="fa-solid fa-trash"></i>
        </button>
      </div>
    `;
  }).join('');
  
  container.innerHTML = html;
}

async function confirmarEliminarLote(idlote){
  if(!confirm('¿Eliminar este lote? Esta acción no se puede deshacer. Si tiene movimientos registrados, no se puede eliminar.')) return;
  
  const res = await fetch(`api/lotes/${idlote}`, {method: 'DELETE'});
  const data = await res.json();
  
  if(!res.ok){
    alert(data.error || 'Error al eliminar lote');
    return;
  }
  
  alert(data.message || 'Lote eliminado correctamente');
  closeModal('modalEliminarLote');
  await cargar();
  await cargarStats();
}

function abrirMovimiento(idproducto){
  $('#mov-idproducto').value = idproducto;
  $('#mov-tipo').value = 'entrada';
  $('#mov-cantidad').value = 1;
  $('#mov-costo').value = 0;
  $('#mov-fv').value = '';
  $('#mov-sin-fv').checked = false;
  toggleMovCampos();
  openModal('modalMovimiento');
}

async function cargarStats(){
  const data = await fetchProductos();
  const total = Array.isArray(data)? data.length : 0;
  const bajos = data.filter(p=>p.bajo_stock).length;
  const por15 = data.filter(p=> p.dias_para_vencer!==null && p.dias_para_vencer<=15).length;
  const stock = data.reduce((acc,p)=> acc + (p.cantidad||0), 0);
  const costoTotal = data.reduce((acc,p)=> acc + (p.costo_total||0), 0);
  document.getElementById('stat-productos').textContent = total;
  document.getElementById('stat-bajos').textContent = bajos;
  document.getElementById('stat-porvencer').textContent = por15;
  document.getElementById('stat-stock').textContent = stock;
  document.getElementById('stat-costototal').textContent = `S/ ${Number(costoTotal).toFixed(0)}`;
}

function initInventario(){
  $$('[data-close]')?.forEach(el=> el.addEventListener('click', e=> closeModal(e.target.getAttribute('data-close'))));

  $('#btn-nuevo').addEventListener('click', ()=>{
    $('#modalProductoTitulo').textContent='Nuevo producto';
    $('#prod-id').value='';
    $('#prod-nombre').value='';
    $('#prod-umbral').value=0;
    $('#prod-cantidad').value=0;
    $('#prod-costo').value=0;
    $('#prod-fv').value='';
    $('#prod-sin-fv').checked=false;
    
    // Mostrar campos de nuevo producto
    document.getElementById('prod-cantidad-row').style.display = 'block';
    document.getElementById('prod-costo-row').style.display = 'block';
    document.getElementById('prod-fv-row').style.display = 'block';
    document.getElementById('prod-sin-fv-row').style.display = 'block';
    
    // Ocultar campos de edición y lotes
    document.getElementById('lotes-header').style.display = 'none';
    document.getElementById('lotes-list').style.display = 'none';
    
    openModal('modalProducto');
  });

  $('#btn-guardar-producto').addEventListener('click', async ()=>{
    const id = $('#prod-id').value;
    const nombre = $('#prod-nombre').value.trim();
    const umbral = parseInt($('#prod-umbral').value||'0',10);
    
    if(!nombre){
      alert('El nombre del producto es requerido');
      return;
    }
    
    if(id){
      // Modo edición: solo actualiza nombre e umbral
      const body = { nombre, umbralminimo: umbral };
      const res = await fetch(`api/productos/${id}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body)
      });
      const data = await res.json();
      if(!res.ok){ alert(data.error||'Error'); return; }
      closeModal('modalProducto');
      await cargar();
      await cargarStats();
    } else {
      // Modo nuevo: crea producto con lote inicial
      const cantidad = parseInt($('#prod-cantidad').value||'0',10);
      const costo = parseInt($('#prod-costo').value||'0',10);
      const fv = $('#prod-sin-fv').checked ? null : ($('#prod-fv').value || null);
      
      const body = {
        nombre,
        umbralminimo: umbral,
        cantidad,
        costo,
        fecha_vencimiento: fv
      };
      
      const res = await fetch('api/productos', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body)
      });
      const data = await res.json();
      if(!res.ok){ alert(data.error||'Error'); return; }
      closeModal('modalProducto');
      await cargar();
      await cargarStats();
    }
  });

  $('#btn-registrar-mov').addEventListener('click', async ()=>{
    const tipo = $('#mov-tipo').value;
    const fv = $('#mov-sin-fv').checked ? null : ($('#mov-fv').value || null);
    const body = {
      idproducto: parseInt($('#mov-idproducto').value,10),
      tipo,
      cantidad: parseInt($('#mov-cantidad').value||'0',10)
    };
    if(tipo === 'entrada' || tipo === 'ajuste'){
      body.costo_unitario = parseInt($('#mov-costo').value||'0',10);
      body.fecha_vencimiento = fv;
    }
      const res = await fetch('api/movimientos', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
    const data = await res.json();
    if(!res.ok){ alert(data.error||'Error registrando movimiento'); return; }
    closeModal('modalMovimiento');
    await cargar();
    await cargarStats();
  });

  $('#btn-guardar-lote').addEventListener('click', async ()=>{
    const idlote = parseInt($('#lote-id').value, 10);
    const fv = $('#lote-sin-fv').checked ? null : ($('#lote-fv').value || null);
    const body = {
      cantidad_actual: parseInt($('#lote-cantidad-actual').value || '0', 10),
      costo_unitario: parseInt($('#lote-costo').value || '0', 10),
      fecha_vencimiento: fv
    };
    
    const res = await fetch(`api/lotes/${idlote}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if(!res.ok){ 
      alert(data.error || 'Error al guardar lote');
      return;
    }
    closeModal('modalEditarLote');
    await cargar();
    await cargarStats();
  });

  window.addEventListener('click', (e)=>{
    if(e.target.classList.contains('modal')) e.target.style.display='none';
  });

  document.addEventListener('change', (e)=>{
    if(e.target && e.target.id === 'prod-sin-fv'){
      const cb = e.target;
      const input = document.getElementById('prod-fv');
      if(cb.checked){
        input.value = '';
        input.disabled = true;
      } else {
        input.disabled = false;
      }
    }
    if(e.target && e.target.id === 'lote-sin-fv'){
      const cb = e.target;
      const input = document.getElementById('lote-fv');
      if(cb.checked){
        input.value = '';
        input.disabled = true;
      } else {
        input.disabled = false;
      }
    }
    if(e.target && e.target.id === 'mov-sin-fv'){
      const cb = e.target;
      const input = document.getElementById('mov-fv');
      if(cb.checked){
        input.value = '';
        input.disabled = true;
      } else {
        input.disabled = false;
      }
    }
    if(e.target && e.target.id === 'mov-tipo'){
      toggleMovCampos();
    }
  });

  document.querySelectorAll('.tab-btn').forEach(btn=>{
    btn.addEventListener('click', async ()=>{
      document.querySelectorAll('.tab-btn').forEach(b=> b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p=> p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.getAttribute('data-tab')).classList.add('active');
      if(btn.getAttribute('data-tab') === 'tab-vencidos'){
        const vencidos = await fetchLotesVencidos();
        renderLotesVencidos(vencidos);
      }
    });
  });

  cargar();
  cargarStats();
}

function toggleMovCampos(){
  const tipo = $('#mov-tipo').value;
  const esEntrada = (tipo === 'entrada' || tipo === 'ajuste');
  $('#mov-costo').disabled = !esEntrada;
  $('#mov-fv').disabled = !esEntrada || $('#mov-sin-fv').checked;
  $('#mov-sin-fv').disabled = !esEntrada;
  if(!esEntrada){
    $('#mov-costo').value = 0;
    $('#mov-fv').value = '';
    $('#mov-sin-fv').checked = false;
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initInventario);
} else {
  initInventario();
}
