// Подгрузка вынесенных кусков разметки (например, <div data-include="topbar-admin.html">).
// Работает только через http(s) — fetch локального файла по file:// браузер блокирует.
async function loadIncludes() {
  const nodes = [...document.querySelectorAll('[data-include]')];

  await Promise.all(nodes.map(async (node) => {
    const src = node.getAttribute('data-include');
    try {
      const response = await fetch(src);
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      node.outerHTML = await response.text();
    } catch (error) {
      console.error(`Не удалось подгрузить ${src}:`, error);
    }
  }));

  document.dispatchEvent(new Event('includes:ready'));
}

loadIncludes();

// .nav-pages-general — единственное место, где ссылки прописаны руками.
// Все остальные .nav-pages (например, в выпадашке бургера) — пустые
// заготовки, которые просто получают копию содержимого оттуда.
// Ждём includes:ready — .nav-pages-general может сам приехать через data-include.
document.addEventListener('includes:ready', () => {
  const source = document.querySelector('.nav-pages.nav-pages-general');
  if (!source) return;

  document.querySelectorAll('.nav-pages').forEach((nav) => {
    if (nav !== source) nav.innerHTML = source.innerHTML;
  });
});

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
document.addEventListener('includes:ready', () => {
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
});

function renderCart() {
  const approvedList = document.querySelector('.cart-items-approved ul');
  const doneList = document.querySelector('.cart-items-done ul');
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
