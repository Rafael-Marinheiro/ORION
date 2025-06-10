document.addEventListener('DOMContentLoaded', function () {
  const themeSwitch = document.getElementById('theme-switch');
  const icon = document.getElementById('theme-icon');
  const bootstrapLink = document.getElementById('bootstrap-theme');
  if (!themeSwitch) return;

  themeSwitch.checked = document.body.classList.contains('light-theme');
  if (icon) {
    icon.textContent = themeSwitch.checked ? '🌙' : '🌞';
  }
  if (bootstrapLink && themeSwitch.checked) {
    bootstrapLink.href = bootstrapLink.href.replace('bootstrap-dark', 'bootstrap-light');
  }
  
  themeSwitch.addEventListener('change', function () {
    const light = themeSwitch.checked;
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
  });
});
