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
  renderCart();
});

function renderCart() {
  const approvedList = document.querySelector('.cart-items-approved');
  const doneList = document.querySelector('.cart-items-done');
  const totalEls = document.querySelectorAll('.cart-buttom p span');
  if (!approvedList || !doneList || totalEls.length < 3) return;

  const [approvedTotalEl, selectedTotalEl, grandTotalEl] = totalEls;

  function cardData(card) {
    const link = card.querySelector('hgroup a');
    const title = link ? link.textContent.replace(/\s*↗\s*$/, '').trim() : '';

    const priceRow = card.querySelector('.price .price-row');
    const priceSpan = priceRow?.querySelector('.price');
    const qtySpan = priceRow?.querySelector('.quantity');

    const digits = priceSpan ? priceSpan.textContent.replace(/\D/g, '') : '';
    const unitPrice = digits ? parseInt(digits, 10) : 0;

    const qtyDigits = qtySpan ? qtySpan.textContent.replace(/\D/g, '') : '';
    const qty = qtyDigits ? parseInt(qtyDigits, 10) : 1;

    return {
      title,
      priceOuterHTML: priceRow ? priceRow.outerHTML : '',
      lineTotal: unitPrice * qty,
    };
  }

  function formatRUB(amount) {
    return amount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ' ₽';
  }

  approvedList.innerHTML = '';
  let approvedTotal = 0;
  document.querySelectorAll('.product-grid li.product-done').forEach((card) => {
    const data = cardData(card);
    approvedTotal += data.lineTotal;

    const li = document.createElement('li');
    li.innerHTML = `<a>${data.title}</a>${data.priceOuterHTML}`;
    li.querySelector('a').addEventListener('click', () => {
      card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
    approvedList.appendChild(li);
  });

  doneList.innerHTML = '';
  let selectedTotal = 0;
  document.querySelectorAll('.product-grid li.product-select').forEach((card) => {
    const data = cardData(card);
    selectedTotal += data.lineTotal;

    const li = document.createElement('li');
    li.innerHTML = `
      <div>
        <a>${data.title}</a>
        ${data.priceOuterHTML}
      </div>
      <button type="button">Убрать</button>
    `;
    li.querySelector('a').addEventListener('click', () => {
      card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
    li.querySelector('button').addEventListener('click', () => {
      card.classList.remove('product-select');
      renderCart();
    });
    doneList.appendChild(li);
  });

  approvedTotalEl.textContent = formatRUB(approvedTotal);
  selectedTotalEl.textContent = formatRUB(selectedTotal);
  grandTotalEl.textContent = formatRUB(approvedTotal + selectedTotal);
}

renderCart();

document.addEventListener('click', (event) => {
  const toggle = event.target.closest('.comments-toggle');
  if (!toggle) return;

  toggle.closest('.comments-form')?.querySelector('textarea')?.focus();
});

function autosizeTextarea(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = `${textarea.scrollHeight}px`;
}

document.addEventListener('input', (event) => {
  const textarea = event.target.closest('.comments-form textarea');
  if (!textarea) return;

  autosizeTextarea(textarea);
});

document.addEventListener('submit', (event) => {
  const form = event.target.closest('.comments-form');
  if (!form) return;
  event.preventDefault();

  const textarea = form.querySelector('textarea');
  const text = textarea.value.trim();
  if (!text) return;

  // TODO: когда появится бэкенд — комментарий нужно будет отправлять на сервер здесь,
  // а не только добавлять в DOM. Пока комментарии не сохраняются между перезагрузками.
  const comment = document.createElement('div');
  comment.className = 'comment';
  comment.innerHTML = '<span class="comment-avatar"></span><p></p>';
  comment.querySelector('p').textContent = text;
  form.closest('.comments').querySelector('.comments-list').appendChild(comment);

  textarea.value = '';
  textarea.style.height = '';
  textarea.blur();
});
