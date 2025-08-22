function confirmarEliminacion() {
  if (confirm('¿Estás seguro de que deseas eliminar tu cuenta? Esta acción no se puede deshacer.')) {
    if (confirm('¿Realmente estás seguro? Se perderán todos tus datos.')) {
      // Aquí iría la lógica para eliminar la cuenta
      alert('Funcionalidad de eliminación de cuenta en desarrollo');
    }
  }
}
