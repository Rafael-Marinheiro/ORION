document.addEventListener('DOMContentLoaded', function () {
  const themeSwitch = document.getElementById('theme-switch');
  const icon = document.getElementById('theme-icon');
  const bootstrapLink = document.getElementById('bootstrap-theme');
  if (!themeSwitch) return;

  function applyTheme(light) {
    document.body.classList.toggle('light-theme', light);
    if (bootstrapLink) {
      bootstrapLink.href = light
        ? bootstrapLink.href.replace('bootstrap-dark', 'bootstrap-light')
        : bootstrapLink.href.replace('bootstrap-light', 'bootstrap-dark');
    }
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
    localStorage.setItem('theme', light ? 'light' : 'dark');
  }

  const stored = localStorage.getItem('theme');
  themeSwitch.checked = stored ? stored === 'light' : document.body.classList.contains('light-theme');
  applyTheme(themeSwitch.checked);

  themeSwitch.addEventListener('change', function () {
    applyTheme(themeSwitch.checked);
  });
});
