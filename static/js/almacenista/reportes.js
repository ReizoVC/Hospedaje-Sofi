// Reportes de Inventario - Almacenista

async function fetchJSON(url){ const r=await fetch(url); return await r.json(); }

async function cargar(){
  // Datos de inventario
  const productos = await fetchJSON('/api/productos');
  const bajo = await fetchJSON('/api/productos?bajos=1');
  const vencer = await fetchJSON('/api/productos?por_vencer_dias=15');
  const movs = await fetchJSON('/api/movimientos');

  // KPIs inventario
  const stockTotal = Array.isArray(productos)? productos.reduce((a,p)=> a + (p.cantidad||0), 0): 0;
  document.getElementById('inv-productos').textContent = Array.isArray(productos)? productos.length : '-';
  document.getElementById('inv-bajos').textContent = Array.isArray(bajo)? bajo.length : 0;
  document.getElementById('inv-vencer').textContent = Array.isArray(vencer)? vencer.length : 0;
  document.getElementById('inv-movs7').textContent = Array.isArray(movs)? movs.filter(m=>{
    if(!m.fecha) return false; const d = new Date(m.fecha); const dif=(Date.now()-d.getTime())/(1000*60*60*24); return dif<=7;
  }).length : 0;
  document.getElementById('inv-stock').textContent = stockTotal;

  // Alertas de inventario
  const ul = document.getElementById('alertas');
  const items = [];
  if(Array.isArray(bajo)) bajo.forEach(p=> items.push({
    txt: `Bajo stock: ${p.nombre} (${p.cantidad}/${p.umbralminimo})`,
    cls: 'alert-low'
  }));
  if(Array.isArray(vencer)) vencer.forEach(p=> items.push({
    txt: `Próximo a vencer: ${p.nombre} (vence ${p.fecha_vencimiento})`,
    cls: 'alert-exp'
  }));
  ul.innerHTML = items.length
    ? items.map(i=>`<li class="${i.cls}">${i.txt}</li>`).join('')
    : '<li class="muted">Sin alertas</li>';

  // Últimos movimientos
  const tbody = document.getElementById('tbody-movs');
  if(!Array.isArray(movs) || movs.length===0){
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 1rem;">Sin movimientos</td></tr>';
    return;
  }
  const byId = Object.fromEntries((productos||[]).map(p=>[p.idproducto,p.nombre]));
  tbody.innerHTML = movs.slice(0,25).map(m=>`<tr>
    <td>${(m.fecha||'').replace('T',' ').slice(0,16)}</td>
    <td>${byId[m.idproducto]||m.idproducto}</td>
    <td>${m.tipo}</td>
    <td>${m.cantidad}</td>
  </tr>`).join('');
}

document.addEventListener('DOMContentLoaded', cargar);
