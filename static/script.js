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

// ==========================================
// COMMENTS LOGIC (API INTEGRATION)
// ==========================================

// 1. Author Name Management
let currentAuthorName = null;

try {
  currentAuthorName = localStorage.getItem('author_name');
} catch (e) {
  // LocalStorage might be blocked by browser settings
}

function getAuthorName() {
  if (currentAuthorName) return currentAuthorName;

  const name = prompt("Пожалуйста, введите ваше имя для оставления комментариев:");
  if (name && name.trim()) {
    currentAuthorName = name.trim();
    try {
      localStorage.setItem('author_name', currentAuthorName);
    } catch (e) {
      console.warn("Не удалось сохранить имя в localStorage.");
    }
    return currentAuthorName;
  }
  return null;
}

// 2. Helper to create a comment DOM element
function createCommentElement(text) {
  const comment = document.createElement('div');
  comment.className = 'comment';
  comment.innerHTML = '<span class="comment-avatar"></span><p></p>';
  comment.querySelector('p').textContent = text;
  return comment;
}

// 3. Fetch comments on page load
async function loadComments() {
  const items = document.querySelectorAll('li[data-item-id]');

  for (const item of items) {
    const itemId = item.getAttribute('data-item-id');
    if (!itemId) continue;

    try {
      const response = await fetch(`/api/items/${itemId}/comments`);
      if (response.ok) {
        const comments = await response.json();
        const list = item.querySelector('.comments-list');
        if (list) {
          list.innerHTML = ''; // Ensure it's empty before appending
          comments.forEach(c => {
            list.appendChild(createCommentElement(c.text));
          });
        }
      } else if (response.status !== 404) {
        console.error(`Failed to load comments for item ${itemId}. Status: ${response.status}`);
      }
    } catch (error) {
      console.error(`Network error while loading comments for item ${itemId}:`, error);
    }
  }
}

// Initialize comments fetching
document.addEventListener('DOMContentLoaded', loadComments);

// 4. Handle Comment Submission
document.addEventListener('submit', async (event) => {
  const form = event.target.closest('.comments-form');
  if (!form) return;
  event.preventDefault();

  const itemLi = form.closest('li[data-item-id]');
  if (!itemLi) {
    console.error("Item ID not found on the parent element.");
    return;
  }

  const itemId = itemLi.getAttribute('data-item-id');
  const textarea = form.querySelector('textarea');
  const text = textarea.value.trim();

  if (!text) return;

  const authorName = getAuthorName();
  if (!authorName) {
    alert("Имя обязательно для отправки комментария.");
    return;
  }

  // Disable form while submitting
  const submitBtn = form.querySelector('.comments-send');
  textarea.disabled = true;
  submitBtn.disabled = true;

  try {
    const response = await fetch(`/api/items/${itemId}/comments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: text,
        author_name: authorName
      })
    });

    if (response.ok) {
      const newComment = await response.json();

      // Append to DOM
      const list = form.closest('.comments').querySelector('.comments-list');
      list.appendChild(createCommentElement(newComment.text));

      // Reset form
      textarea.value = '';
      textarea.style.height = '';
      textarea.blur();
    } else {
      const errorData = await response.json().catch(() => ({}));
      alert(`Ошибка при отправке комментария: ${errorData.title || 'Неизвестная ошибка'}`);
    }
  } catch (error) {
    console.error("Error posting comment:", error);
    alert("Ошибка сети при отправке комментария. Проверьте подключение.");
  } finally {
    // Re-enable form
    textarea.disabled = false;
    submitBtn.disabled = false;
  }
});
