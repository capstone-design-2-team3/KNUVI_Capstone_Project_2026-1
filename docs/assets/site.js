document.addEventListener('DOMContentLoaded', () => {
  const buttons = document.querySelectorAll('.tab-btn');
  const panels = document.querySelectorAll('.tab-panel');
  buttons.forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.dataset.target;
      buttons.forEach((b) => b.classList.toggle('active', b === button));
      panels.forEach((p) => p.classList.toggle('active', p.id === target));
    });
  });
});
