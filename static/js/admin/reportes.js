(function(){
	const tabBtns = document.querySelectorAll('.tab-btn');
	const tabs = document.querySelectorAll('.tab-content');
	tabBtns.forEach(b=>b.addEventListener('click', ()=>{
		tabBtns.forEach(x=>x.classList.remove('active'));
		tabs.forEach(x=>x.classList.remove('active'));
		b.classList.add('active');
		document.getElementById(b.dataset.tab).classList.add('active');
	}));

	function fmt(n){
		return new Intl.NumberFormat('es-PE', { style:'currency', currency:'PEN' }).format(n||0);
	}

	async function cargarIngresos(){
		const res = await fetch(`api/reportes/admin/ingresos`);
		const data = await res.json();
		const tb = document.getElementById('tbody-ingresos');
		if (!tb) return;
		tb.innerHTML = '';
		(data.items||[]).forEach(it=>{
			const tr = document.createElement('tr');
			tr.innerHTML = `
				<td>${it.fecha_inicio||''}</td>
				<td>${it.fecha_fin||''}</td>
				<td>${it.habitacion? (it.habitacion.numero || it.habitacion.nombre) : ''}</td>
				<td>${it.noches||0}</td>
				<td>${it.estado||''}</td>
				<td>${fmt(it.monto)}</td>
			`;
			tb.appendChild(tr);
		});
		const total = document.getElementById('total-ingresos');
		if (total) total.textContent = fmt(data.total||0);
	}

	async function cargarEgresos(){
		const res = await fetch(`api/reportes/admin/egresos`);
		const data = await res.json();
		const tb = document.getElementById('tbody-egresos');
		if (!tb) return;
		tb.innerHTML = '';
		(data.items||[]).forEach(it=>{
			const tr = document.createElement('tr');
			tr.innerHTML = `
				<td>${it.fecha? it.fecha.substring(0,10): ''}</td>
				<td>${it.producto? it.producto.nombre: ''}</td>
				<td>${it.tipo||''}</td>
				<td>${it.cantidad||0}</td>
				<td>${fmt(it.costo_unitario||0)}</td>
				<td>${fmt(it.monto||0)}</td>
			`;
			tb.appendChild(tr);
		});
		const total = document.getElementById('total-egresos');
		if (total) total.textContent = fmt(data.total||0);
	}

	cargarIngresos();
	cargarEgresos();
})();

