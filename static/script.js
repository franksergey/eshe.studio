(() => {
  const container = document.querySelector('.chapter nav > div');
  const list = container?.firstElementChild;
  const nav = container?.closest('nav');
  if (!container || !list || !nav) return;

  let stickStartY = 0;
  let maxTravel = 0;
  let ticking = false;

  function measure() {
    const topOffset = parseFloat(getComputedStyle(container).top) || 0;
    stickStartY = nav.offsetTop - topOffset;

    const stickDuration = nav.offsetHeight - container.clientHeight;
    const listOverflow = list.scrollHeight - container.clientHeight;
    maxTravel = Math.max(0, Math.min(stickDuration, listOverflow));

    update();
  }

  function update() {
    ticking = false;
    const progress = maxTravel <= 0
      ? 0
      : Math.min(Math.max(window.scrollY - stickStartY, 0), maxTravel);

    list.style.transform = progress ? `translateY(${-progress}px)` : '';
  }

  function onScroll() {
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(update);
    }
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', measure);
  new ResizeObserver(measure).observe(list);

  measure();
})();

document.addEventListener('click', (event) => {
  const button = event.target.closest('.add-wishlist');
  if (!button) return;

  button.closest('li')?.classList.toggle('product-select');
});
