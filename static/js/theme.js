document.addEventListener('DOMContentLoaded', function() {
  const toggleButton = document.getElementById('theme-toggle');
  if (!toggleButton) return;

  toggleButton.addEventListener('click', function() {
    const body = document.body;
    const nav = document.querySelector('nav.navbar');
    const light = body.classList.toggle('light-theme');
    if (light) {
      if (nav) {
        nav.classList.remove('navbar-dark', 'bg-dark');
        nav.classList.add('navbar-light', 'bg-light');
      }
      toggleButton.textContent = '🌙';
    } else {
      if (nav) {
        nav.classList.remove('navbar-light', 'bg-light');
        nav.classList.add('navbar-dark', 'bg-dark');
      }
      toggleButton.textContent = '🌞';
    }
  });
});
