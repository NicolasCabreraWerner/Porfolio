document.addEventListener('DOMContentLoaded', () => {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
});

/* ── GALLERY LIGHTBOX ─────────────────────────────────────
   Recibe un array de imágenes por proyecto y permite navegar
   con flechas, teclado y miniaturas. */
let __lbImages = [];
let __lbIndex   = 0;

function openLightbox(images, startIndex) {
  if (typeof images === 'string') { images = [images]; }
  __lbImages = images || [];
  __lbIndex  = startIndex || 0;
  if (!__lbImages.length) return;

  const box = document.getElementById('lightbox');
  if (!box) return;
  box.classList.add('open');
  document.body.style.overflow = 'hidden';
  renderLightbox();
}

function renderLightbox() {
  const img     = document.getElementById('lightbox-img');
  const counter = document.getElementById('lightbox-counter');
  const thumbs  = document.getElementById('lightbox-thumbs');
  const prevBtn = document.getElementById('lightbox-prev');
  const nextBtn = document.getElementById('lightbox-next');
  if (!img) return;

  img.src = __lbImages[__lbIndex];

  const multi = __lbImages.length > 1;
  if (counter) {
    counter.textContent = multi ? `${__lbIndex + 1} / ${__lbImages.length}` : '';
    counter.style.display = multi ? 'block' : 'none';
  }
  if (prevBtn) prevBtn.style.display = multi ? 'flex' : 'none';
  if (nextBtn) nextBtn.style.display = multi ? 'flex' : 'none';

  if (thumbs) {
    if (multi) {
      thumbs.style.display = 'flex';
      thumbs.innerHTML = __lbImages.map((src, i) =>
        `<img src="${src}" class="lightbox-thumb ${i === __lbIndex ? 'on' : ''}" onclick="event.stopPropagation();lightboxGoTo(${i})"/>`
      ).join('');
    } else {
      thumbs.style.display = 'none';
      thumbs.innerHTML = '';
    }
  }
}

function lightboxGoTo(i) {
  __lbIndex = (i + __lbImages.length) % __lbImages.length;
  renderLightbox();
}
function lightboxPrev(e) { if (e) e.stopPropagation(); lightboxGoTo(__lbIndex - 1); }
function lightboxNext(e) { if (e) e.stopPropagation(); lightboxGoTo(__lbIndex + 1); }

function closeLightbox() {
  const box = document.getElementById('lightbox');
  if (!box) return;
  box.classList.remove('open');
  document.body.style.overflow = '';
}

document.addEventListener('keydown', e => {
  const box = document.getElementById('lightbox');
  if (!box || !box.classList.contains('open')) return;
  if (e.key === 'Escape')     closeLightbox();
  if (e.key === 'ArrowLeft')  lightboxPrev();
  if (e.key === 'ArrowRight') lightboxNext();
});

/* Swipe on mobile */
(function () {
  let touchX = null;
  document.addEventListener('touchstart', e => {
    const box = document.getElementById('lightbox');
    if (box && box.classList.contains('open')) touchX = e.touches[0].clientX;
  });
  document.addEventListener('touchend', e => {
    const box = document.getElementById('lightbox');
    if (!box || !box.classList.contains('open') || touchX === null) return;
    const dx = e.changedTouches[0].clientX - touchX;
    if (Math.abs(dx) > 40) { dx > 0 ? lightboxPrev() : lightboxNext(); }
    touchX = null;
  });
})();
