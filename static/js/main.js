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

function openLightbox(src){
  const box=document.getElementById('lightbox');
  const img=document.getElementById('lightbox-img');
  if(!box||!img)return;
  img.src=src;box.classList.add('open');document.body.style.overflow='hidden';
}
function closeLightbox(){
  const box=document.getElementById('lightbox');if(!box)return;
  box.classList.remove('open');document.body.style.overflow='';
}
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeLightbox();});
