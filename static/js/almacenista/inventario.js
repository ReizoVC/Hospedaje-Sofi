// Inventario - Almacenista
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

function openModal(id){ document.getElementById(id).style.display='flex'; }
function closeModal(id){ document.getElementById(id).style.display='none'; }

async function fetchProductos(params={}){
  const q = new URLSearchParams(params).toString();
  const res = await fetch('/api/productos'+(q?`?${q}`:''));
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

function abrirEditar(id){
  const row = [...document.querySelectorAll('#tbody-productos tr')].find(tr=> tr.children[0].textContent==id);
  if(!row) return;
  $('#modalProductoTitulo').textContent='Editar producto';
  $('#prod-id').value = id;
  $('#prod-nombre').value = row.children[1].textContent;
  $('#prod-cantidad').value = 0; // no editable aquí
  $('#prod-costo').value = (row.children[2].textContent.replace('S/','').trim()||'0');
  $('#prod-umbral').value = row.children[5].textContent;
  $('#prod-fv').value = row.children[6].textContent;
  if(!$('#prod-fv').value){
    $('#prod-sin-fv').checked = true;
    $('#prod-fv').disabled = true;
  } else {
    $('#prod-sin-fv').checked = false;
    $('#prod-fv').disabled = false;
  }
  openModal('modalProducto');
}

async function eliminarProducto(id){
  if(!confirm('¿Eliminar producto? Esta acción no se puede deshacer.')) return;
  const res = await fetch(`/api/productos/${id}`, {method:'DELETE'});
  const data = await res.json();
  if(!res.ok){ alert(data.error||'No se pudo eliminar'); return; }
  await cargar();
}

function abrirMovimiento(idproducto){
  $('#mov-idproducto').value = idproducto;
  $('#mov-tipo').value = 'entrada';
  $('#mov-cantidad').value = 1;
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
    $('#prod-cantidad').value=0;
    $('#prod-umbral').value=0;
    $('#prod-costo').value=0;
    $('#prod-fv').value='';
    $('#prod-sin-fv').checked=false;
    $('#prod-fv').disabled=false;
    openModal('modalProducto');
  });

  $('#btn-guardar-producto').addEventListener('click', async ()=>{
    const id = $('#prod-id').value;
    const body = {
      nombre: $('#prod-nombre').value.trim(),
      umbralminimo: parseInt($('#prod-umbral').value||'0',10),
      costo: parseInt($('#prod-costo').value||'0',10),
      fecha_vencimiento: document.getElementById('prod-sin-fv').checked ? null : ($('#prod-fv').value || null)
    };
    if(!id){ body.cantidad = parseInt($('#prod-cantidad').value||'0',10); }

    const url = id? `/api/productos/${id}`: '/api/productos';
    const method = id? 'PUT': 'POST';
    const res = await fetch(url, {method, headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
    const data = await res.json();
    if(!res.ok){ alert(data.error||'Error'); return; }
    closeModal('modalProducto');
    await cargar();
    await cargarStats();
  });

  $('#btn-registrar-mov').addEventListener('click', async ()=>{
    const body = {
      idproducto: parseInt($('#mov-idproducto').value,10),
      tipo: $('#mov-tipo').value,
      cantidad: parseInt($('#mov-cantidad').value||'0',10)
    };
    const res = await fetch('/api/movimientos', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
    const data = await res.json();
    if(!res.ok){ alert(data.error||'Error registrando movimiento'); return; }
    closeModal('modalMovimiento');
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
  });

  cargar();
  cargarStats();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initInventario);
} else {
  initInventario();
}
