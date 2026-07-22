// Scroll reveal
const reveals = document.querySelectorAll('.section, .project-block, .exp-item, .skill-group, .stat, .shot');
reveals.forEach(el => el.classList.add('reveal'));

const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('visible');
      observer.unobserve(e.target);
    }
  });
}, { threshold: 0.08 });

reveals.forEach(el => observer.observe(el));

// Avatar: si hay foto cargada, mostrarla; si no, mostrar iniciales
window.addEventListener('DOMContentLoaded', () => {
  const img = document.getElementById('avatar-img');
  const initials = document.getElementById('avatar-initials');
  if (img && img.getAttribute('src') && img.getAttribute('src').trim() !== '') {
    img.style.display = 'block';
    if (initials) initials.style.display = 'none';
  }
});

// Gallery tabs (Desktop / Web)
function switchGallery(targetId, btn) {
  document.querySelectorAll('.gallery-grid').forEach(g => g.style.display = 'none');
  document.getElementById(targetId).style.display = 'grid';
  document.querySelectorAll('.gtab').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');
}

// Lightbox for gallery images
document.addEventListener('click', (e) => {
  const shot = e.target.closest('.shot');
  if (shot) {
    const img = shot.querySelector('img');
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightbox-img');
    lightboxImg.src = img.src;
    lightboxImg.alt = img.alt;
    lightbox.classList.add('open');
  }
});

function closeLightbox() {
  document.getElementById('lightbox').classList.remove('open');
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeLightbox();
});
