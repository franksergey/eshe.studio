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

// ==========================================
// COMMENTS FEED LOGIC
// ==========================================

// 1. Author Name Management (Cookies + JS Variable Fallback)
let sessionAuthorName = null;

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

function setCookie(name, value, days) {
  try {
    let expires = "";
    if (days) {
      const date = new Date();
      date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
      expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
  } catch (e) {
    console.warn("Cookies are restricted. Falling back to session variable.");
  }
}

function getAuthorName() {
  // Check JS variable first
  if (sessionAuthorName) return sessionAuthorName;

  // Check Cookie second
  const cookieName = getCookie('author_name');
  if (cookieName) {
    sessionAuthorName = decodeURIComponent(cookieName);
    return sessionAuthorName;
  }

  // If neither exists, prompt the user
  let promptedName = prompt('Пожалуйста, введите ваше имя, чтобы оставить комментарий:');

  if (promptedName && promptedName.trim() !== '') {
    promptedName = promptedName.trim();
    sessionAuthorName = promptedName; // Save to JS variable
    setCookie('author_name', encodeURIComponent(promptedName), 365); // Save to Cookie for 1 year
    return sessionAuthorName;
  }

  // Return null if the user cancelled the prompt or entered an empty string
  return null;
}

// 2. Feed Initialization
document.addEventListener('DOMContentLoaded', () => {
  const commentSections = document.querySelectorAll('.comments[data-item-id]');

  commentSections.forEach(async (section) => {
    const itemId = section.getAttribute('data-item-id');

    // Construct the DOM for the feed and form
    const wrapper = document.createElement('div');
    wrapper.style.display = 'flex';
    wrapper.style.flexDirection = 'column';
    wrapper.style.gap = '0.3em';
    wrapper.style.flex = '1';
    wrapper.style.minWidth = '0';

    const feed = document.createElement('div');
    feed.style.display = 'flex';
    feed.style.flexDirection = 'column';
    feed.style.gap = '0.3em';
    feed.style.maxHeight = '120px';
    feed.style.overflowY = 'auto';
    feed.style.scrollbarWidth = 'none';

    const form = document.createElement('form');
    form.style.display = 'flex';
    form.style.gap = '0.3em';
    form.innerHTML = `
      <input type="text" name="text" placeholder="Написать..." required 
             style="flex: 1; min-width: 0; border: none; border-radius: 0.5em; padding: 0.3em 0.5em; font-size: inherit; background: rgba(var(--background-color-RGB), 0.9); color: rgba(var(--text-color-RGB), 1); outline: none;">
      <button type="submit" 
              style="border: none; border-radius: 0.5em; padding: 0.3em 0.6em; background: rgba(var(--background-color-RGB), 0.9); color: rgba(var(--text-color-RGB), 1); cursor: pointer; font-size: inherit; font-weight: bold;">
        ➤
      </button>
    `;

    wrapper.appendChild(feed);
    wrapper.appendChild(form);
    section.appendChild(wrapper);

    // Helper to append a comment to the DOM
    const appendComment = (commentData) => {
      const p = document.createElement('p');
      p.textContent = `${commentData.author_name}: ${commentData.text}`;
      feed.appendChild(p);
      feed.scrollTop = feed.scrollHeight;
    };

    // Fetch existing comments from the backend
    try {
      const response = await fetch(`/api/items/${itemId}/comments`);
      if (response.ok) {
        const comments = await response.json();
        comments.forEach(appendComment);
      } else if (response.status !== 404) {
        console.error(`Failed to load comments for item ${itemId}`);
      }
    } catch (err) {
      console.error(`Network error fetching comments for item ${itemId}:`, err);
    }

    // Handle new comment creation
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const input = form.querySelector('input');
      const button = form.querySelector('button');
      const text = input.value.trim();

      if (!text) return;

      // Ask for the author's name (or retrieve it if already saved)
      const authorName = getAuthorName();

      // If the user clicked "Cancel" on the prompt, abort the submission
      if (!authorName) return;

      // Loading state
      input.disabled = true;
      button.disabled = true;
      button.style.opacity = '0.5';

      try {
        const response = await fetch(`/api/items/${itemId}/comments`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            text: text,
            author_name: authorName // Use the dynamically retrieved name
          })
        });

        if (response.ok) {
          const newComment = await response.json();
          appendComment(newComment);
          input.value = ''; // Clear input
        } else {
          alert('Ошибка при сохранении комментария. Проверьте консоль.');
          console.error(await response.text());
        }
      } catch (err) {
        alert('Ошибка сети. Не удалось отправить комментарий.');
        console.error(err);
      } finally {
        // Remove loading state
        input.disabled = false;
        button.disabled = false;
        button.style.opacity = '1';
        input.focus();
      }
    });
  });
});
