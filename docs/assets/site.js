document.addEventListener('DOMContentLoaded', () => {
  const buttons = document.querySelectorAll('[data-tab]');
  const panels = document.querySelectorAll('[data-panel]');
  buttons.forEach(btn => btn.addEventListener('click', () => {
    const id = btn.dataset.tab;
    buttons.forEach(b => b.classList.toggle('active', b === btn));
    panels.forEach(p => p.classList.toggle('active', p.dataset.panel === id));
  }));

  const lightbox = document.querySelector('.lightbox');
  const lightboxImg = document.querySelector('.lightbox img');
  const close = document.querySelector('.lightbox button');
  document.querySelectorAll('.clickable').forEach(img => {
    img.addEventListener('click', () => {
      lightboxImg.src = img.currentSrc || img.src;
      lightbox.classList.add('open');
    });
  });
  close.addEventListener('click', () => lightbox.classList.remove('open'));
  lightbox.addEventListener('click', (e) => { if(e.target === lightbox) lightbox.classList.remove('open'); });
});
