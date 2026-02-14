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

	async function cargarIngresos(desde, hasta){
		const params = new URLSearchParams();
		if (desde && hasta){
			params.set('desde', desde);
			params.set('hasta', hasta);
		}
		const url = params.toString()
			? `api/reportes/admin/ingresos?${params.toString()}`
			: 'api/reportes/admin/ingresos';
		const res = await fetch(url);
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

	async function cargarTotalGeneralIngresos(){
		const totalBtn = document.getElementById('btn-total-ingresos');
		if (!totalBtn) return;
		try{
			totalBtn.disabled = true;
			totalBtn.textContent = 'Cargando...';
			const res = await fetch('api/reportes/admin/ingresos/total-general');
			if (!res.ok) throw new Error('Error al obtener total');
			const data = await res.json();
			totalBtn.textContent = fmt(data.total||0);
		} catch (e){
			totalBtn.textContent = 'Error al cargar';
		} finally {
			totalBtn.disabled = false;
		}
	}

	function llenarSelect(select, items, placeholder){
		if (!select) return;
		select.innerHTML = '';
		const base = document.createElement('option');
		base.value = '';
		base.textContent = placeholder;
		select.appendChild(base);
		const allOpt = document.createElement('option');
		allOpt.value = '__all__';
		allOpt.textContent = 'Todos';
		select.appendChild(allOpt);
		(items||[]).forEach(it=>{
			const opt = document.createElement('option');
			opt.value = it.value || '';
			opt.textContent = it.label || it.value || '';
			if (it.desde) opt.dataset.desde = it.desde;
			if (it.hasta) opt.dataset.hasta = it.hasta;
			select.appendChild(opt);
		});
	}

	function aplicarFiltro(select, otros){
		if (!select) return;
		const opt = select.selectedOptions && select.selectedOptions[0];
		if (!select.value || !opt){
			cargarIngresos();
			return;
		}
		if (select.value === '__all__'){
			(otros||[]).forEach(o=>{ if (o) o.value = ''; });
			cargarIngresos();
			return;
		}
		(otros||[]).forEach(o=>{ if (o) o.value = ''; });
		cargarIngresos(opt.dataset.desde, opt.dataset.hasta);
	}

	async function cargarPeriodosIngresos(){
		const selDia = document.getElementById('ingresos-dia');
		const selSemana = document.getElementById('ingresos-semana');
		const selMes = document.getElementById('ingresos-mes');
		if (!selDia && !selSemana && !selMes) return;
		const res = await fetch('api/reportes/admin/ingresos/periodos');
		if (!res.ok) return;
		const data = await res.json();
		llenarSelect(selDia, data.dias, 'Selecciona un dia');
		llenarSelect(selSemana, data.semanas, 'Selecciona una semana');
		llenarSelect(selMes, data.meses, 'Selecciona un mes');

		if (selDia){
			selDia.addEventListener('change', ()=>aplicarFiltro(selDia, [selSemana, selMes]));
		}
		if (selSemana){
			selSemana.addEventListener('change', ()=>aplicarFiltro(selSemana, [selDia, selMes]));
		}
		if (selMes){
			selMes.addEventListener('change', ()=>aplicarFiltro(selMes, [selDia, selSemana]));
		}
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

	const totalBtn = document.getElementById('btn-total-ingresos');
	if (totalBtn){
		totalBtn.addEventListener('click', cargarTotalGeneralIngresos);
	}

	cargarIngresos();
	cargarEgresos();
	cargarPeriodosIngresos();
})();

