(function(){
    const radios = document.querySelectorAll('input[name="plan"]');
    const form = document.querySelector('.plan-form');
    const montoHoy = document.getElementById('montoHoy');
    const montoSaldo = document.getElementById('montoSaldo');
    const saldoRow = document.getElementById('saldoRow');
    const detail = document.getElementById('payment-summary-detail');
    const saldoDetalle = document.getElementById('saldoDetalle');
    const fechaLimite = document.getElementById('fechaLimite');
    if (!form || !radios.length) return;

    const llegada = form.querySelector('input[name="inicio"]')?.value || '';
    const limitePago = (dateStr) => {
        if (!dateStr) return '';
        const parts = dateStr.split('-');
        if (parts.length !== 3) return '';
        const date = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
        date.setDate(date.getDate() - 2);
        return date.toLocaleDateString('es-ES', { day: '2-digit', month: 'long' });
    };

    const toggleWarning = () => {
        const selected = document.querySelector('input[name="plan"]:checked');
        if (selected && selected.value === 'parcial') {
            if (detail) detail.classList.remove('is-hidden');
            if (form && montoHoy) montoHoy.textContent = form.dataset.parcial || '0';
            if (saldoRow) saldoRow.classList.remove('is-hidden');
            if (form && montoSaldo) montoSaldo.textContent = form.dataset.saldo || '0';
            if (form && saldoDetalle) saldoDetalle.textContent = form.dataset.saldo || '0';
            if (fechaLimite) fechaLimite.textContent = limitePago(llegada) || '--';
        } else {
            if (detail) detail.classList.add('is-hidden');
            if (form && montoHoy) montoHoy.textContent = form.dataset.total || '0';
            if (saldoRow) saldoRow.classList.add('is-hidden');
        }
    };

    radios.forEach(radio => radio.addEventListener('change', toggleWarning));
    toggleWarning();
})();
