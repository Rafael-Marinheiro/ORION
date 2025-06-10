const body = document.body;
const navbar = document.getElementById('navbar');
const toggleBtn = document.getElementById('theme-toggle');

function applyTheme(theme) {
  body.dataset.theme = theme;
  if (theme === 'light') {
    navbar.classList.remove('navbar-dark', 'bg-dark');
    navbar.classList.add('navbar-light', 'bg-light');
    navbar.style.backgroundColor = '';
    toggleBtn.innerText = 'Modo Escuro';
  } else {
    navbar.classList.remove('navbar-light', 'bg-light');
    navbar.classList.add('navbar-dark', 'bg-dark');
    navbar.style.backgroundColor = '#000';
    toggleBtn.innerText = 'Modo Claro';
  }
}

function toggleTheme() {
  const newTheme = body.dataset.theme === 'light' ? 'dark' : 'light';
  localStorage.setItem('theme', newTheme);
  applyTheme(newTheme);
}

document.addEventListener('DOMContentLoaded', () => {
  const saved = localStorage.getItem('theme') || 'dark';
  applyTheme(saved);
  toggleBtn.addEventListener('click', toggleTheme);
});
