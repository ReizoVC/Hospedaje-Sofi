async function cancelarReserva(codigoReserva) {
  if (!confirm('¿Estás seguro de que deseas cancelar esta reserva?')) {
    return;
  }

  try {
    const response = await fetch(`/reservas/cancelar/${codigoReserva}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    const data = await response.json();

    if (data.success) {
      alert('Reserva cancelada exitosamente');
      location.reload();
    } else {
      alert(data.message || 'Error al cancelar la reserva');
    }
  } catch (error) {
    alert('Error al cancelar la reserva. Inténtalo de nuevo.');
  }
}

async function completarPago(codigoReserva) {
  if (!confirm('¿Deseas completar el pago de esta reserva?')) {
    return;
  }

  try {
    const response = await fetch(`/reservas/completar-pago/${codigoReserva}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    const data = await response.json();

    if (data.success) {
      alert('Pago completado. Tu reserva quedó confirmada.');
      location.reload();
    } else {
      alert(data.message || 'Error al completar el pago');
    }
  } catch (error) {
    alert('Error al completar el pago. Intentalo de nuevo.');
  }
}
