(function(){
  const $ = (sel)=>document.querySelector(sel);

  const script = document.currentScript;
  const idhabitacion = Number(script?.dataset?.idhabitacion || script?.getAttribute('data-idhabitacion') || 0);
  const precioPorNoche = Number(script?.dataset?.precioNoche || script?.getAttribute('data-precio-noche') || 0);
  const minDateStr = script?.dataset?.minDate || script?.getAttribute('data-min-date') || '';

  const monthLabel = $('#dpMonthLabel');
  const grid = $('#dpGrid');
  const btnContinuar = $('#btnContinuar');
  const disponibilidad = $('#disponibilidadMensaje');

  let minDate = minDateStr ? new Date(minDateStr + 'T00:00:00') : new Date();
  minDate = normalizeDate(minDate);

  let currentMonth = new Date(minDate.getFullYear(), minDate.getMonth(), 1);
  let startDate = null;
  let endDate = null;
  let hoverDate = null;
  let fechasValidas = false;
  let blockedRanges = [];

  function normalizeDate(date){
    return new Date(date.getFullYear(), date.getMonth(), date.getDate());
  }

  function formatDate(date){
    return date.toISOString().split('T')[0];
  }

  function formatDateHuman(date){
    return date.toLocaleDateString('es-ES', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: '2-digit'
    });
  }

  function sameDay(a, b){
    return a && b && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
  }

  function isBlocked(date){
    if (!blockedRanges.length) return false;
    return blockedRanges.some((range) => {
      const inicio = normalizeDate(new Date(range.inicio + 'T00:00:00'));
      const fin = normalizeDate(new Date(range.fin + 'T00:00:00'));
      return date >= inicio && date <= fin;
    });
  }

  function isInRange(date){
     if (!startDate || !endDate) return false;
     const start = startDate < endDate ? startDate : endDate;
     const finish = startDate < endDate ? endDate : startDate;
     return date >= start && date <= finish;
  }

  function buildDayButton(date, isDisabled){
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'dp-day';
    btn.textContent = String(date.getDate());

    const blocked = !isDisabled && isBlocked(date);

    if (isDisabled || blocked){
      btn.classList.add('is-disabled');
      if (blocked) btn.classList.add('is-blocked');
      btn.disabled = true;
    } else {
      btn.addEventListener('click', () => onDateClick(date));
    }

    if (blocked){
      btn.title = 'No disponible';
    } else if (isDisabled){
      btn.title = 'Fecha no disponible';
    } else {
      btn.title = 'Disponible';
    }

    btn.addEventListener('mouseover', () => onDateHover(date, blocked, isDisabled));
    btn.addEventListener('mouseout', onDateHoverOut);

    if (sameDay(date, startDate)) btn.classList.add('is-start');
    if (sameDay(date, endDate)) btn.classList.add('is-end');
    if (!sameDay(date, startDate) && !sameDay(date, endDate) && isInRange(date)) {
      btn.classList.add('is-in-range');
    }

    return btn;
  }

  function onDateHover(date, blocked, isDisabled){
    if (!disponibilidad) return;
    if (blocked){
      setDisponibilidad('Fecha no disponible', 'error');
      return;
    }
    if (isDisabled){
      return;
    }
    setDisponibilidad(`Disponible: ${formatDateHuman(date)}`, 'success');
  }

  function onDateHoverOut(){
    if (!startDate || !endDate){
      setDisponibilidad('Selecciona un rango de fechas.', '');
    }
  }

  function renderCalendar(){
    if (!grid) return;
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();

    const monthName = currentMonth.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' });
    if (monthLabel) monthLabel.textContent = monthName;

    grid.innerHTML = '';
    const firstDay = new Date(year, month, 1);
    const startOffset = (firstDay.getDay() + 6) % 7;
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    for (let i = 0; i < startOffset; i++){
      const empty = document.createElement('div');
      empty.className = 'dp-empty';
      grid.appendChild(empty);
    }

    for (let day = 1; day <= daysInMonth; day++){
      const date = new Date(year, month, day);
      const isDisabled = date < minDate;
      const btn = buildDayButton(date, isDisabled);
      grid.appendChild(btn);
    }
  }

  async function cargarBloqueadas(){
    if (!idhabitacion) return;
    try {
      const response = await fetch(`/reservas/bloqueadas/${idhabitacion}`);
      const data = await response.json();
      blockedRanges = Array.isArray(data.rangos) ? data.rangos : [];
      renderCalendar();
    } catch (err){
      console.error('Error al cargar fechas bloqueadas:', err);
    }
  }

  function updateSummary(){
    const inicioTxt = $('#fechaInicioTxt');
    const finTxt = $('#fechaFinTxt');
    const nochesTxt = $('#nochesTxt');
    const totalTxt = $('#totalTxt');

    if (inicioTxt) inicioTxt.textContent = startDate ? formatDateHuman(startDate) : '--';
    if (finTxt) finTxt.textContent = endDate ? formatDateHuman(endDate) : '--';

    if (!startDate || !endDate){
      if (nochesTxt) nochesTxt.textContent = '0';
      if (totalTxt) totalTxt.textContent = '0';
      setDisponibilidad('Selecciona un rango de fechas.', '');
      fechasValidas = false;
      if (btnContinuar) btnContinuar.disabled = true;
      return;
    }

    const diffMs = Math.abs(endDate - startDate);
    const noches = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
    const total = noches * (precioPorNoche || 0);

    if (nochesTxt) nochesTxt.textContent = String(noches);
    if (totalTxt) totalTxt.textContent = String(total.toFixed(0));

    verificarDisponibilidad(startDate, endDate);
  }

  async function verificarDisponibilidad(inicio, fin){
    setDisponibilidad('Verificando disponibilidad...', 'loading');
    fechasValidas = false;
    if (btnContinuar) btnContinuar.disabled = true;

    try {
      const response = await fetch('/reservas/verificar-disponibilidad', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          idhabitacion: idhabitacion,
          fechainicio: formatDate(inicio),
          fechafin: formatDate(fin)
        })
      });
      const data = await response.json();
      if (data.disponible){
        setDisponibilidad('Habitacion disponible', 'success');
        fechasValidas = true;
        if (btnContinuar) btnContinuar.disabled = false;
      } else {
        setDisponibilidad(data.message || 'Habitacion no disponible', 'error');
      }
    } catch(err){
      console.error('Error al verificar disponibilidad:', err);
      setDisponibilidad('Error al verificar disponibilidad', 'error');
    }
  }

  function setDisponibilidad(texto, estado){
    if (!disponibilidad) return;
    disponibilidad.textContent = texto;
    disponibilidad.className = 'disponibilidad';
    if (estado) disponibilidad.classList.add(estado);
  }

  function onDateClick(date){
    const selected = normalizeDate(date);

    if (!startDate || (startDate && endDate)){
      startDate = selected;
      endDate = null;
      hoverDate = null;
    } else {
      endDate = selected;
      hoverDate = null;
      if (endDate < startDate){
        const temp = startDate;
        startDate = endDate;
        endDate = temp;
      }
    }

    renderCalendar();
    updateSummary();
  }

  function setupNavigation(){
    document.querySelectorAll('.dp-nav').forEach(btn => {
      btn.addEventListener('click', () => {
        const dir = Number(btn.getAttribute('data-dir') || 0);
        currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + dir, 1);
        renderCalendar();
      });
    });
  }

  if (btnContinuar){
    btnContinuar.addEventListener('click', () => {
      if (!fechasValidas || !startDate || !endDate) return;
      const url = `/reservas/paso-2/${idhabitacion}?inicio=${formatDate(startDate)}&fin=${formatDate(endDate)}`;
      window.location.href = url;
    });
  }

  setupNavigation();
  renderCalendar();
  updateSummary();
  cargarBloqueadas();
})();
