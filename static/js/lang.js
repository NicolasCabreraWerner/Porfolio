function setLang(lang) {
  document.documentElement.lang = lang;

  // Update all elements with data-es / data-en
  document.querySelectorAll('[data-es],[data-en]').forEach(el => {
    const val = el.getAttribute('data-' + lang);
    if (val !== null) {
      // Use innerHTML for elements that contain HTML tags (strong, etc)
      if (val.includes('<')) {
        el.innerHTML = val;
      } else {
        el.textContent = val;
      }
    }
  });

  // Update button states
  document.getElementById('btn-es').classList.toggle('active', lang === 'es');
  document.getElementById('btn-en').classList.toggle('active', lang === 'en');

  // Persist choice
  localStorage.setItem('portfolio-lang', lang);
}

// On load: restore saved language or detect browser language
(function () {
  const saved = localStorage.getItem('portfolio-lang');
  const browserLang = navigator.language.slice(0, 2);
  const initial = saved || (browserLang === 'es' ? 'es' : 'en');
  if (initial !== 'es') setLang(initial);
})();
