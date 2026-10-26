// .nav-pages-general — единственное место, где ссылки прописаны руками.
// Все остальные .nav-pages (например, в выпадашке бургера) — пустые
// заготовки, которые просто получают копию содержимого оттуда.
const navPagesSource = document.querySelector('.nav-pages.nav-pages-general');
if (navPagesSource) {
  document.querySelectorAll('.nav-pages').forEach((nav) => {
    if (nav !== navPagesSource) nav.innerHTML = navPagesSource.innerHTML;
  });
}

// Project id is read once; null if the attribute is missing or not an integer.
const PROJECT_ID = (() => {
  const raw = document.querySelector('main[data-project-id]')?.dataset.projectId;
  const id = Number.parseInt(raw, 10);
  return Number.isFinite(id) ? id : null;
})();

document.addEventListener('click', (event) => {
  const button = event.target.closest('.add-wishlist');
  if (!button) return;

  button.closest('li')?.classList.toggle('product-select');
  renderCart();
});

document.addEventListener('click', (event) => {
  const toggle = event.target.closest('.burger-toggle');

  if (toggle) {
    const header = toggle.closest('.topbar');
    const isOpen = header.classList.toggle('menu-open');
    toggle.setAttribute('aria-expanded', String(isOpen));
    return;
  }

  const openHeader = document.querySelector('.topbar.menu-open');
  if (openHeader && !openHeader.contains(event.target)) {
    openHeader.classList.remove('menu-open');
    openHeader.querySelector('.burger-toggle')?.setAttribute('aria-expanded', 'false');
  }
});

// Admin-bar: пункты переезжают в бургер по одному, как только реально
// перестают помещаться в строку — не по фиксированной ширине экрана.
// Ждём includes:ready — .topbar может сам приехать через data-include.
(() => {
  const header = document.querySelector('.topbar');
  const menu = header?.querySelector('.admin-bar-menu');
  // .admin-bar-overflow может содержать и постоянные пункты (выход, nav-pages) —
  // JS управляет только вложенной .admin-bar-overflow-items, остальное не трогает.
  const overflowItems = header?.querySelector('.admin-bar-overflow-items');
  if (!header || !menu || !overflowItems) return;

  const items = [...menu.children];
  const mobileQuery = window.matchMedia('(max-width: 768px)');

  function fits() {
    return menu.scrollWidth <= menu.clientWidth;
  }

  function lastCollapsible() {
    return [...menu.children].reverse().find((el) => !el.classList.contains('no-collapse'));
  }

  function update() {
    items.forEach((item) => menu.appendChild(item));
    overflowItems.innerHTML = '';

    if (mobileQuery.matches) {
      // На мобилке бургер всегда собирает всё целиком, без расчёта —
      // не полагаемся на scrollWidth у скрытого через display:none блока.
      // .no-collapse (например, «Админпанель») никогда туда не переносим —
      // его копия уже постоянно лежит рядом с «Выйти» в самой выпадашке.
      items.forEach((item) => {
        if (!item.classList.contains('no-collapse')) overflowItems.appendChild(item);
      });
    } else {
      let next;
      while (!fits() && (next = lastCollapsible())) {
        overflowItems.insertBefore(next, overflowItems.firstElementChild);
      }
    }

    // «Привет, ...» должно быть первым пунктом в выпадашке, если оно там оказалось.
    const greet = overflowItems.querySelector('.greet');
    if (greet) overflowItems.insertBefore(greet, overflowItems.firstElementChild);

    const hasOverflow = overflowItems.children.length > 0;
    header.classList.toggle('has-overflow', hasOverflow);

    if (!hasOverflow && header.classList.contains('menu-open')) {
      header.classList.remove('menu-open');
      header.querySelector('.burger-toggle')?.setAttribute('aria-expanded', 'false');
    }
  }

  new ResizeObserver(update).observe(menu);
  window.addEventListener('resize', update);
  mobileQuery.addEventListener('change', update);
  document.fonts?.ready.then(update);
  update();
})();

function renderCart() {
  const approvedList = document.querySelector('#cart-items-approved ul');
  const doneList = document.querySelector('#cart-items-done ul');
  const approvedTotalEl = document.querySelector('#sum-approved span');
  const selectedTotalEl = document.querySelector('#sum-done span');
  const grandTotalEl = document.querySelector('#total span');
  if (!approvedList || !doneList || !approvedTotalEl || !selectedTotalEl || !grandTotalEl) return;

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

  // 950 → 950, 41 000 → 41К, 41 500 → 41,5К, 1 500 000 → 1,5М
  function formatAmount(amount) {
    const suffixes = ['', 'К', 'М', 'Млрд'];
    const round = (value) => Math.round(value * 10) / 10;

    let value = amount;
    let i = 0;
    while (round(value) >= 1000 && i < suffixes.length - 1) {
      value /= 1000;
      i++;
    }

    return round(value).toString().replace('.', ',') + suffixes[i];
  }

  // 1500000 → 1.500.000
  function formatFullAmount(amount) {
    return amount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
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

  approvedTotalEl.textContent = formatAmount(approvedTotal);
  selectedTotalEl.textContent = formatAmount(selectedTotal);
  grandTotalEl.textContent = formatFullAmount(approvedTotal + selectedTotal);
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
// CART: confirm selection
// ==========================================
(() => {
  // data-item-id of every card matching the selector, as unique integers.
  function collectItemIds(selector) {
    const ids = new Set();
    document.querySelectorAll(selector).forEach((li) => {
      const id = Number.parseInt(li.getAttribute('data-item-id'), 10);
      if (Number.isFinite(id)) ids.add(id);
    });
    return [...ids];
  }

  async function errorMessage(response) {
    try {
      const data = await response.json();
      if (typeof data.title === 'string' && data.title) return data.title;
      if (typeof data.detail === 'string' && data.detail) return data.detail;
    } catch (e) {
      // Body is empty or not JSON, fall through.
    }
    return `Ошибка ${response.status}`;
  }

  document.addEventListener('click', async (event) => {
    const button = event.target.closest('#cart-confirm-button');
    if (!button || button.disabled) return;

    if (PROJECT_ID === null) {
      console.error('Cannot confirm selection: project id not found.');
      return;
    }

    // Approved cards (product-done) never carry product-select and are
    // not user-selectable, so they are left out of deselect_item_ids.
    const payload = {
      item_ids: collectItemIds('ul.product-grid > li.product-select[data-item-id]'),
      deselect_item_ids: collectItemIds(
        'ul.product-grid > li[data-item-id]:not(.product-select):not(.product-done)'
      ),
    };

    button.disabled = true;
    try {
      const response = await fetch(`/api/projects/${PROJECT_ID}/select`, {
        method: 'POST',
        credentials: 'same-origin', // cookie-based auth
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      // 201 with no body on success: the UI is intentionally left untouched.
      if (!response.ok) {
        alert(`Не удалось подтвердить выбор: ${await errorMessage(response)}`);
      }
    } catch (error) {
      console.error('Error confirming selection:', error);
      alert('Ошибка сети при подтверждении выбора. Проверьте подключение.');
    } finally {
      button.disabled = false;
    }
  });
})();

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
function createCommentElement(text, authorName) {
  const comment = document.createElement('div');
  comment.className = 'comment';
  comment.innerHTML = '<p><small class="comment-author"></small><span class="comment-text"></span></p>';
  comment.querySelector('.comment-author').textContent = authorName;
  comment.querySelector('.comment-text').textContent = text;
  return comment;
}

// 3. Fetch comments on page load (single bulk request)
async function loadComments(root = document) {
  const items = [...root.querySelectorAll('li[data-item-id]')];
  if (!items.length) return;

  // id -> список карточек (на случай, если один id встречается несколько раз)
  const itemsById = new Map();
  items.forEach((item) => {
    const id = Number(item.getAttribute('data-item-id'));
    if (!Number.isFinite(id)) return;
    if (!itemsById.has(id)) itemsById.set(id, []);
    itemsById.get(id).push(item);
  });

  const itemIds = [...itemsById.keys()];
  if (!itemIds.length) return;

  try {
    const response = await fetch('/api/items/bulk-comments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_ids: itemIds })
    });

    if (!response.ok) {
      console.error(`Failed to load comments. Status: ${response.status}`);
      return;
    }

    const data = await response.json();

    (data.items ?? []).forEach((entry) => {
      (itemsById.get(entry.id) ?? []).forEach((item) => {
        const list = item.querySelector('.comments-list');
        if (!list) return;

        list.innerHTML = ''; // Ensure it's empty before appending
        (entry.comments ?? []).forEach((c) => {
          list.appendChild(createCommentElement(c.text, c.author_name));
        });
      });
    });

    if (data.item_ids_not_found?.length) {
      console.warn('Items not found for comments:', data.item_ids_not_found);
    }
  } catch (error) {
    console.error('Network error while loading comments:', error);
  }
}

// Initialize comments fetching
// Скрипт может подключаться после DOMContentLoaded, поэтому проверяем readyState.
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => loadComments());
} else {
  loadComments();
}

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
      list.appendChild(createCommentElement(newComment.text, newComment.author_name));

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

// ==========================================
// NAV: click-to-scroll + scrollspy (nav-active)
// ==========================================

(() => {
  const navSectionUl = document.querySelector('.page-of-table nav ul.nav-section');
  const navScrollBox = document.querySelector('.page-of-table nav > div');
  const content = document.querySelector('.page-of-table > article.content');
  if (!navSectionUl || !navScrollBox || !content) return;

  const topLis = [...navSectionUl.children].filter((el) => el.tagName === 'LI');
  const rooms = [];

  topLis.forEach((li) => {
    if (li.querySelector(':scope > ul.nav-subsection')) return;

    const room = { roomLi: li, subLis: [], subHeadings: [] };
    const next = li.nextElementSibling;
    const subUl = next?.querySelector(':scope > ul.nav-subsection');

    if (subUl) {
      room.subWrapperLi = next;
      room.subUl = subUl;
      room.subLis = [...subUl.children].filter((el) => el.tagName === 'LI');
    }

    rooms.push(room);
  });

  // Мобилка: переносим ul.nav-subsection в общую вторую строку (.nav-subsection-row),
  // чтобы она скроллилась независимо от строки разделов. Перенос — разовый
  // (при загрузке и при пересечении брейкпоинта), а не на каждый тик скролла —
  // какой из списков сейчас виден, решает чистый CSS через .nav-active.
  const subsectionRow = document.querySelector('.page-of-table nav > .nav-subsection-row');
  const mobileQuery = window.matchMedia('(max-width: 768px)');

  function placeSubsections(isMobile) {
    if (!subsectionRow) return;

    rooms.forEach((room) => {
      if (!room.subUl) return;

      if (isMobile) {
        subsectionRow.appendChild(room.subUl);
      } else if (room.subWrapperLi) {
        room.subWrapperLi.appendChild(room.subUl);
      }
    });
  }

  placeSubsections(mobileQuery.matches);
  mobileQuery.addEventListener('change', (event) => placeSubsections(event.matches));

  const headings = [...content.querySelectorAll('h3')];

  rooms.forEach((room) => {
    const roomName = room.roomLi.querySelector('a')?.textContent.trim() ?? '';
    room.heading = headings.find((h) => h.textContent.includes(roomName));
    if (!room.heading) return;

    const rangeEnd = headings[headings.indexOf(room.heading) + 1] ?? null;
    const h4sInRange = [];
    let el = room.heading.nextElementSibling;
    while (el && el !== rangeEnd) {
      if (el.tagName === 'H4') h4sInRange.push(el);
      el = el.nextElementSibling;
    }

    room.subLis.forEach((subLi) => {
      const subName = subLi.querySelector('a')?.textContent.trim() ?? '';
      const heading = h4sInRange.find((h) => h.textContent.includes(subName));
      room.subHeadings.push(heading ?? null);
    });
  });

  function scrollToHeading(heading) {
    if (!heading) return;
    heading.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  rooms.forEach((room) => {
    room.roomLi.querySelector('a')?.addEventListener('click', (event) => {
      event.preventDefault();
      scrollToHeading(room.heading);
    });

    room.subLis.forEach((subLi, j) => {
      subLi.querySelector('a')?.addEventListener('click', (event) => {
        event.preventDefault();
        scrollToHeading(room.subHeadings[j]);
      });
    });
  });

  const watched = [];
  rooms.forEach((room) => {
    if (room.heading) {
      watched.push({ el: room.heading, roomLi: room.roomLi, subLi: null, room });
    }
    room.subHeadings.forEach((heading, j) => {
      if (heading) {
        watched.push({ el: heading, roomLi: room.roomLi, subLi: room.subLis[j], room });
      }
    });
  });

  // На мобилке строки разделов/подразделов скроллятся по горизонтали —
  // держим активный пункт по центру видимой области его собственного ряда.
  function centerHorizontally(container, el) {
    const containerRect = container.getBoundingClientRect();
    const elRect = el.getBoundingClientRect();
    const delta = (elRect.left + elRect.width / 2) - (containerRect.left + containerRect.width / 2);

    container.scrollTo({ left: container.scrollLeft + delta, behavior: 'smooth' });
  }

  let activeRoomLi = null;
  let activeSubLi = null;

  function setActive(entry) {
    document.querySelectorAll('.page-of-table nav .nav-active').forEach((el) => {
      el.classList.remove('nav-active');
    });
    entry.roomLi.classList.add('nav-active');
    if (entry.subLi) entry.subLi.classList.add('nav-active');

    if (entry.roomLi !== activeRoomLi) {
      activeRoomLi = entry.roomLi;

      const boxRect = navScrollBox.getBoundingClientRect();
      const liRect = activeRoomLi.getBoundingClientRect();
      const delta = liRect.top - boxRect.top;

      navScrollBox.scrollTo({ top: navScrollBox.scrollTop + delta, behavior: 'smooth' });

      if (mobileQuery.matches) centerHorizontally(navScrollBox, activeRoomLi);
    }

    if (entry.subLi && entry.subLi !== activeSubLi) {
      activeSubLi = entry.subLi;

      if (mobileQuery.matches && subsectionRow) centerHorizontally(subsectionRow, activeSubLi);
    }
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const match = watched.find((w) => w.el === entry.target);
        if (match) setActive(match);
      });
    },
    { rootMargin: '-10% 0px -85% 0px', threshold: 0 }
  );

  watched.forEach((w) => observer.observe(w.el));
})();

// ==========================================
// ADMIN: view another user's selection
// ==========================================
(() => {
  const PICKER = '.persona-picker';
  let activeController = null;

  // Full overwrite: cards with product-done are never touched.
  function applySelection(itemIds) {
    const ids = new Set(itemIds.map(Number));

    document.querySelectorAll('ul.product-grid > li').forEach((li) => {
      if (li.classList.contains('product-done')) return;

      const id = Number(li.getAttribute('data-item-id'));
      li.classList.toggle('product-select', ids.has(id));
    });

    renderCart();
  }

  async function loadSelection(userEmail) {
    if (PROJECT_ID === null || !userEmail) {
      console.error('Cannot load selection: missing project id or user email.');
      return;
    }

    // Cancel the previous in-flight request so only the latest one can touch the DOM.
    activeController?.abort();
    const controller = new AbortController();
    activeController = controller;

    const url = `/api/admin/projects/${PROJECT_ID}/selections`
      + `?user_email=${encodeURIComponent(userEmail)}`;

    try {
      const response = await fetch(url, { signal: controller.signal });

      if (!response.ok) {
        console.error(`Failed to load selection. Status: ${response.status}`);
        return;
      }

      const selection = await response.json();

      // Superseded by a newer request, or no selection made yet: do nothing.
      if (controller.signal.aborted || !selection) return;

      applySelection(selection.items ?? []);
    } catch (error) {
      if (error.name === 'AbortError') return;
      console.error('Network error while loading selection:', error);
    } finally {
      if (activeController === controller) activeController = null;
    }
  }

  // ---- dropdown behaviour ----

  function closeList(picker, { restoreFocus = false } = {}) {
    const toggle = picker.querySelector('.persona-toggle');
    picker.querySelector('.persona-list').hidden = true;
    picker.querySelector('.select-wrapper').classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
    if (restoreFocus) toggle.focus();
  }

  function closeAll() {
    document.querySelectorAll(PICKER).forEach((picker) => closeList(picker));
  }

  function openList(picker) {
    const toggle = picker.querySelector('.persona-toggle');
    const list = picker.querySelector('.persona-list');
    const rect = toggle.getBoundingClientRect();

    list.hidden = false;
    list.style.top = `${rect.bottom + 4}px`;
    list.style.left = `${rect.left}px`;
    list.style.minWidth = `${rect.width}px`;

    picker.querySelector('.select-wrapper').classList.add('is-open');
    toggle.setAttribute('aria-expanded', 'true');

    (list.querySelector('[aria-selected="true"]') ?? list.querySelector('[role="option"]'))
      ?.focus({ preventScroll: true });
  }

  function choose(picker, option) {
    picker.querySelectorAll('[role="option"]').forEach((o) => {
      o.setAttribute('aria-selected', String(o === option));
    });
    picker.querySelector('#persona-current').textContent = option.textContent.trim();

    closeList(picker, { restoreFocus: true });

    // Fires on every click, even on the already-selected or the only entry.
    loadSelection(option.dataset.email);
  }

  document.addEventListener('click', (event) => {
    const option = event.target.closest('.persona-list [role="option"]');
    if (option) {
      choose(option.closest(PICKER), option);
      return;
    }

    const toggle = event.target.closest('.persona-toggle');

    // Click anywhere else (or on another picker's toggle) closes open lists.
    document.querySelectorAll(PICKER).forEach((picker) => {
      if (!toggle || !picker.contains(toggle)) closeList(picker);
    });

    if (toggle) {
      const picker = toggle.closest(PICKER);
      const isOpen = !picker.querySelector('.persona-list').hidden;
      if (isOpen) closeList(picker);
      else openList(picker);
    }
  });

  document.addEventListener('keydown', (event) => {
    const picker = event.target.closest?.(PICKER);
    if (!picker) return;

    const list = picker.querySelector('.persona-list');

    if (event.key === 'Escape' && !list.hidden) {
      event.preventDefault();
      closeList(picker, { restoreFocus: true });
      return;
    }

    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      if (list.hidden) {
        openList(picker);
        return;
      }

      const options = [...list.querySelectorAll('[role="option"]')];
      const i = options.indexOf(document.activeElement);
      const next = event.key === 'ArrowDown'
        ? options[Math.min(i + 1, options.length - 1)]
        : options[Math.max(i - 1, 0)];
      next?.focus();
    }
  });

  // Tabbing out of the picker closes it.
  document.addEventListener('focusout', (event) => {
    const picker = event.target.closest?.(PICKER);
    if (picker && event.relatedTarget && !picker.contains(event.relatedTarget)) {
      closeList(picker);
    }
  });

  // The list is position: fixed, so any scroll or resize would leave it misplaced.
  window.addEventListener('resize', closeAll);
  window.addEventListener('scroll', (event) => {
    // Ignore scrolling inside the list itself.
    if (event.target.closest?.('.persona-list')) return;
    closeAll();
  }, true);
})();
