(() => {
  const btn = document.getElementById('btnPostular');
  if (!btn) return;

  btn.addEventListener('click', () => {
    const msg = 'Postulación ficticia por ahora. Pronto habilitaremos el formulario.';
    if (window.showInfo) {
      window.showInfo(msg);
      return;
    }
    alert(msg);
  });
})();
