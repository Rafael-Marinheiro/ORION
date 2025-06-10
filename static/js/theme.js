document.addEventListener('DOMContentLoaded', function () {
  const themeSwitch = document.getElementById('theme-switch');
  const icon = document.getElementById('theme-icon');
  if (!themeSwitch) return;

  themeSwitch.checked = document.body.classList.contains('light-theme');

  themeSwitch.addEventListener('change', function () {
    const light = themeSwitch.checked;
    document.body.classList.toggle('light-theme', light);
    const nav = document.querySelector('nav.navbar');
    if (nav) {
      if (light) {
        nav.classList.remove('navbar-dark', 'bg-dark');
        nav.classList.add('navbar-light', 'bg-light');
      } else {
        nav.classList.remove('navbar-light', 'bg-light');
        nav.classList.add('navbar-dark', 'bg-dark');
      }
    }
    if (icon) {
      icon.textContent = light ? '🌙' : '🌞';
    }
  });
});
