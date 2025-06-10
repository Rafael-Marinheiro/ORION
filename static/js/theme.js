const body = document.body;
const navbar = document.getElementById('navbar');
const themeSelect = document.getElementById('theme-select');

function applyTheme(theme) {
  body.dataset.theme = theme;
  if (theme === 'light') {
    navbar.classList.remove('navbar-dark', 'bg-dark');
    navbar.classList.add('navbar-light', 'bg-light');
    navbar.style.backgroundColor = '';
    themeSelect.value = 'light';
  } else {
    navbar.classList.remove('navbar-light', 'bg-light');
    navbar.classList.add('navbar-dark', 'bg-dark');
    navbar.style.backgroundColor = '#000';
    themeSelect.value = 'dark';
  }
}

function changeTheme() {
  const newTheme = themeSelect.value;
  localStorage.setItem('theme', newTheme);
  applyTheme(newTheme);
}

document.addEventListener('DOMContentLoaded', () => {
  const saved = localStorage.getItem('theme') || 'dark';
  applyTheme(saved);
  themeSelect.addEventListener('change', changeTheme);
});
