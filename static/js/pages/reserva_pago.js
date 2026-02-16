(function(){
  const form = document.getElementById('formPago');
  const cardName = document.getElementById('cardName');
  const cardNumber = document.getElementById('cardNumber');
  const cardExpiry = document.getElementById('cardExpiry');
  const cardCvv = document.getElementById('cardCvv');
  const submitBtn = form?.querySelector('button[type="submit"]');

  const script = document.currentScript;
  const idhabitacion = Number(script?.dataset?.idhabitacion || script?.getAttribute('data-idhabitacion') || 0);
  const fechainicio = script?.dataset?.fechainicio || script?.getAttribute('data-fechainicio') || '';
  const fechafin = script?.dataset?.fechafin || script?.getAttribute('data-fechafin') || '';
  const plan = script?.dataset?.plan || script?.getAttribute('data-plan') || 'total';

  if (!form) return;

  function randomChoice(items){
    return items[Math.floor(Math.random() * items.length)];
  }

  function randomDigits(count){
    let out = '';
    for (let i = 0; i < count; i++){
      out += Math.floor(Math.random() * 10);
    }
    return out;
  }

  function randomName(){
    const nombres = ['Sofi', 'Camila', 'Mateo', 'Diego', 'Valeria', 'Lucia', 'Andres', 'Bruno', 'Renata', 'Luis'];
    const apellidos = ['Garcia', 'Rojas', 'Perez', 'Torres', 'Gomez', 'Diaz', 'Silva', 'Ramirez', 'Morales', 'Vargas'];
    return `${randomChoice(nombres)} ${randomChoice(apellidos)}`;
  }

  function randomCardNumber(){
    const blocks = [randomDigits(4), randomDigits(4), randomDigits(4), randomDigits(4)];
    return blocks.join(' ');
  }

  function randomExpiry(){
    const month = String(Math.floor(Math.random() * 12) + 1).padStart(2, '0');
    const year = String((new Date().getFullYear() + Math.floor(Math.random() * 5) + 1) % 100).padStart(2, '0');
    return `${month}/${year}`;
  }

  function fillRandom(){
    if (cardName && !cardName.value.trim()) cardName.value = randomName();
    if (cardNumber) cardNumber.value = randomCardNumber();
    if (cardExpiry) cardExpiry.value = randomExpiry();
    if (cardCvv) cardCvv.value = randomDigits(3);
  }

  fillRandom();

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    if (!idhabitacion || !fechainicio || !fechafin){
      alert('Faltan datos de reserva. Vuelve al paso anterior.');
      return;
    }

    if (submitBtn){
      submitBtn.disabled = true;
      submitBtn.textContent = 'Procesando...';
    }

    try {
      const response = await fetch('/reservas/crear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          idhabitacion: idhabitacion,
          fechainicio: fechainicio,
          fechafin: fechafin,
          plan: plan
        })
      });
      const data = await response.json();
      if (data.success){
        const planTexto = plan === 'parcial' ? 'Pago inicial del 60%' : 'Pago completo';
        alert(`Pago realizado (${planTexto}).\n\nReserva confirmada.\nCodigo de reserva: ${data.codigo_reserva}`);
        window.location.href = '/user/reservations';
        return;
      }

      alert(data.message || 'No se pudo completar el pago');
    } catch(err){
      console.error('Error al procesar el pago:', err);
      alert('Error al procesar el pago. Intentalo de nuevo.');
    } finally {
      if (submitBtn){
        submitBtn.disabled = false;
        submitBtn.textContent = 'Pagar ahora';
      }
    }
  });
})();
