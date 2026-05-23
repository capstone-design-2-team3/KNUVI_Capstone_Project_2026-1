const lightbox = document.querySelector('.lightbox');
const lightboxImg = document.querySelector('.lightbox img');
const closeBtn = document.querySelector('.lightbox button');

document.querySelectorAll('img.clickable').forEach((img) => {
  img.addEventListener('click', () => {
    lightboxImg.src = img.src;
    lightboxImg.alt = img.alt || 'Expanded paper figure';
    lightbox.classList.add('open');
  });
});

function closeLightbox(){
  lightbox.classList.remove('open');
  lightboxImg.src = '';
}
closeBtn.addEventListener('click', closeLightbox);
lightbox.addEventListener('click', (event) => {
  if (event.target === lightbox) closeLightbox();
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') closeLightbox();
});
