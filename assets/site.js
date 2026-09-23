/* Смекай: общие сценарии сайта. Шапка, всплывающие окна, cookie, плавающий Мыслик, счётчик. */
(function () {
  const BOT = 'https://t.me/smekai_ru_bot';
  const MAX = 'https://max.ru/join/nQJFTVidgdh_w-lFQo9rbmy54ErMxxp_vbMRjOdTJFo';
  const TG = 'https://t.me/smekai_ru';
  const BOOSTY = 'https://boosty.to/smekai';
  const root = document.body.dataset.root || './';
  const src = document.body.dataset.src || 'site';

  const ICONS = {
    tg: '<svg viewBox="0 0 24 24"><path d="M9.04 15.6l-.37 5.2c.53 0 .76-.23 1.04-.5l2.5-2.4 5.18 3.8c.95.52 1.63.25 1.87-.88L22.9 4.7c.31-1.4-.5-1.95-1.43-1.6L2.3 10.5c-1.37.53-1.35 1.3-.24 1.64l4.9 1.53L18.3 6.5c.53-.35 1.02-.16.62.2L9.04 15.6z"/></svg>',
    max: '<svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm-4.6 6.5h1.8l2.8 5 2.8-5h1.8v7h-1.7v-4.2l-2.4 4.2h-1l-2.4-4.2v4.2H7.4v-7z"/></svg>',
    web: '<svg viewBox="0 0 24 24"><path d="M4 4h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-6v2h3v2H7v-2h3v-2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zm0 2v10h16V6H4z"/></svg>',
    boosty: '<svg viewBox="0 0 24 24"><path d="M6.6 2h6.8l-2.6 9.4h4.9L9.4 22h-1l2.4-8.6H5.2L8.4 2z"/></svg>',
    vk: '<svg viewBox="0 0 24 24"><path d="M12.8 18c-6 0-9.5-4.1-9.6-11h3c.1 5 2.3 7.2 4.1 7.6V7h2.9v4.4c1.7-.2 3.5-2.2 4.1-4.4h2.8c-.5 2.7-2.4 4.7-3.8 5.5 1.4.7 3.6 2.4 4.4 5.5h-3.1c-.7-2.1-2.3-3.7-4.4-3.9V18h-.4z"/></svg>',
  };

  /* ---------- шапка ---------- */
  function header(active) {
    const items = [['kak-rabotaet.html', 'Как работает'], ['tarify.html', 'Цены'], ['lev.html', 'Мыслик и Лев'], ['faq.html', 'Вопросы']];
    return `<header class="top"><div class="wrap nav">
      <a class="brand" href="${root}"><i>С</i>Смекай</a>
      <nav class="nav-links" id="navlinks">${items.map(([h, t]) => `<a href="${root}${h}"${active === h ? ' aria-current="page"' : ''}>${t}</a>`).join('')}</nav>
      <span class="sp"></span>
      <a class="btn btn-main btn-sm" href="#" data-modal="start">Начать</a>
      <button class="burger" id="burger" aria-label="Меню">☰</button>
    </div></header>`;
  }

  /* ---------- подвал ---------- */
  function footer() {
    return `<footer class="site"><div class="wrap">
      <div class="foot">
        <div style="max-width:300px"><a class="brand" href="${root}" style="margin-bottom:10px"><i>С</i>Смекай</a>
          <p class="small muted">Помощник по учёбе для школьника. Ребёнок думает сам, родитель спокоен.</p>
          <div class="social">
            <a href="${TG}" target="_blank" rel="noopener" title="Telegram" aria-label="Telegram">${ICONS.tg}</a>
            <a href="${MAX}" target="_blank" rel="noopener" title="MAX" aria-label="MAX">${ICONS.max}</a>
            <a href="${BOOSTY}" target="_blank" rel="noopener" title="Boosty" aria-label="Boosty">${ICONS.boosty}</a>
          </div>
        </div>
        <div><div class="col-title">Продукт</div>
          <a href="${root}kak-rabotaet.html">Как работает</a><a href="${root}tarify.html">Цены</a><a href="${root}zanyatie/">Заниматься в браузере</a><a href="${root}viktorina/">Викторина</a></div>
        <div><div class="col-title">Персонажи</div>
          <a href="${root}lev.html">Мыслик и Лев</a><a href="${root}myslik/">Настроения и голос</a><a href="${root}faq.html">Вопросы</a></div>
        <div><div class="col-title">Документы</div>
          <a href="${root}oferta.html">Публичная оферта</a><a href="${root}policy.html">Обработка данных</a><a href="${root}rekvizity.html">Реквизиты</a><a href="#" data-modal="support">Поддержка</a></div>
      </div>
      <p class="copy">© 2026 Смекай. Сайт носит информационный характер; условия оказания услуг в <a href="${root}oferta.html">оферте</a>.</p>
    </div></footer>`;
  }

  /* ---------- всплывающие окна ---------- */
  const MODALS = {
    start: () => `<h2>Где удобнее заниматься?</h2>
      <p class="small muted">Один и тот же Мыслик, выбирайте по устройству. Прогресс в мессенджере и в браузере пока считается отдельно.</p>
      <div class="choice">
        <a href="${BOT}?start=${src}" target="_blank" rel="noopener"><span class="ci">${ICONS.tg}</span><div><b>Telegram</b><span>Телефон родителя или ребёнка. Стикеры, голос, отчёты</span></div></a>
        <a href="${MAX}" target="_blank" rel="noopener"><span class="ci">${ICONS.max}</span><div><b>MAX</b><span>Канал с заданиями, помощник появится позже</span></div></a>
        <a href="${root}zanyatie/"><span class="ci">${ICONS.web}</span><div><b>В браузере</b><span>Планшет или компьютер, без установки. Три задания в день бесплатно</span></div></a>
      </div>
      <div class="qr"><img src="${root}assets/qr-bot.png" alt="QR-код бота"><p class="small muted" style="margin-top:6px">Наведите камеру телефона, чтобы открыть бота</p></div>`,
    channel: () => `<h2>Канал с заданиями</h2>
      <p class="small muted">Каждый день одно задание по каждой группе классов, ответы с разбором.</p>
      <div class="choice">
        <a href="${TG}" target="_blank" rel="noopener"><span class="ci">${ICONS.tg}</span><div><b>Telegram</b><span>@smekai_ru</span></div></a>
        <a href="${MAX}" target="_blank" rel="noopener"><span class="ci">${ICONS.max}</span><div><b>MAX</b><span>Тот же канал для тех, кто в MAX</span></div></a>
      </div>`,
    plan: (name) => {
      const P = {
        free: ['Знакомство', '0 ₽', 'Три задания в день в боте или в браузере, открытый канал, викторина. Карта не нужна.'],
        tasks: ['Задания', '390 ₽ в месяц', 'Закрытый канал с ежедневными заданиями и разборами по классу. Без личного помощника.'],
        myslik: ['Мыслик', '890 ₽ в месяц', 'Помощник для одного ребёнка: 30 разборов в день, фото домашки, закрытый канал, отчёт родителю раз в неделю.'],
        family: ['Семья', '1 490 ₽ в месяц', 'Всё из тарифа Мыслик для двух детей, отдельный отчёт по каждому, ответы в первую очередь.'],
      }[name] || P.myslik;
      const pay = name === 'free'
        ? `<div class="choice"><a href="${BOT}?start=${src}" target="_blank" rel="noopener"><span class="ci">${ICONS.tg}</span><div><b>Открыть бота</b><span>Имя и класс, дальше первое задание</span></div></a>
           <a href="${root}zanyatie/"><span class="ci">${ICONS.web}</span><div><b>Заниматься в браузере</b><span>Планшет или компьютер</span></div></a></div>`
        : `<div class="choice"><a href="${BOOSTY}" target="_blank" rel="noopener"><span class="ci">${ICONS.boosty}</span><div><b>Оформить на Boosty</b><span>Карты российских банков, МИР, СБП. Отмена в один клик</span></div></a></div>
           <p class="small muted" style="margin-top:12px">После оплаты бот пришлёт ссылку в закрытый канал и откроет полный доступ. Если что-то не пришло, напишите в поддержку, ответим в течение дня.</p>`;
      return `<h2>${P[0]} <span class="muted" style="font-size:18px;font-weight:500">${P[1]}</span></h2><p>${P[2]}</p>${pay}`;
    },
    support: () => `<h2>Поддержка</h2><p class="small muted">Отвечаем в течение рабочего дня.</p>
      <div class="choice">
        <a href="${BOT}?start=support" target="_blank" rel="noopener"><span class="ci">${ICONS.tg}</span><div><b>Написать в бота</b><span>Самый быстрый способ</span></div></a>
        <a href="mailto:hello@smekai.ru"><span class="ci">${ICONS.web}</span><div><b>hello@smekai.ru</b><span>Для документов и возвратов</span></div></a>
      </div>`,
  };

  function openModal(name, arg) {
    let back = document.getElementById('modal-back');
    if (!back) {
      back = document.createElement('div'); back.id = 'modal-back'; back.className = 'modal-back';
      back.innerHTML = '<div class="modal" role="dialog" aria-modal="true"><button class="x" aria-label="Закрыть">×</button><div class="modal-body"></div></div>';
      document.body.append(back);
      back.addEventListener('click', e => { if (e.target === back || e.target.classList.contains('x')) closeModal(); });
      document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
    }
    const fn = MODALS[name]; if (!fn) return;
    back.querySelector('.modal-body').innerHTML = fn(arg);
    back.classList.add('on'); document.body.style.overflow = 'hidden';
    const m = document.querySelector('myslik-face[float]'); if (m) m.react(name === 'plan' ? 'love' : 'hello', { text: name === 'start' ? 'Выбирай, где удобнее.' : undefined });
  }
  function closeModal() {
    const back = document.getElementById('modal-back'); if (!back) return;
    back.classList.remove('on'); document.body.style.overflow = '';
  }
  document.addEventListener('click', e => {
    const a = e.target.closest('[data-modal]'); if (!a) return;
    e.preventDefault(); openModal(a.dataset.modal, a.dataset.arg);
  });
  window.smkModal = openModal;

  /* ---------- cookie и счётчик ---------- */
  function cookie() {
    let ok = null; try { ok = localStorage.getItem('smk_cookie'); } catch (e) {}
    if (ok === 'yes') { loadMetrika(); return; }
    if (ok === 'no') return;
    const el = document.createElement('div'); el.className = 'cookie on';
    el.innerHTML = `<p>Сайт использует файлы cookie и счётчик посещений, чтобы работать стабильно и понимать, что читают чаще. Продолжая пользоваться сайтом, вы соглашаетесь с <a href="${root}policy.html">политикой обработки данных</a>.</p>
      <div class="btns"><button class="btn btn-main btn-sm" data-c="yes">Хорошо</button><button class="btn btn-ghost btn-sm" data-c="no">Только необходимые</button></div>`;
    el.addEventListener('click', e => {
      const b = e.target.closest('[data-c]'); if (!b) return;
      try { localStorage.setItem('smk_cookie', b.dataset.c); } catch (err) {}
      el.remove(); if (b.dataset.c === 'yes') loadMetrika();
    });
    document.body.append(el);
  }
  function loadMetrika() {
    const id = document.body.dataset.metrika; if (!id || !/^\d+$/.test(id) || window.ym) return;
    (function (m, e, t, r, i, k, a) { m[i] = m[i] || function () { (m[i].a = m[i].a || []).push(arguments); }; m[i].l = 1 * new Date();
      k = e.createElement(t); a = e.getElementsByTagName(t)[0]; k.async = 1; k.src = r; a.parentNode.insertBefore(k, a); })
      (window, document, 'script', 'https://mc.yandex.ru/metrika/tag.js', 'ym');
    window.ym(+id, 'init', { clickmap: true, trackLinks: true, accurateTrackBounce: true });
  }

  /* ---------- плавающий Мыслик ---------- */
  function floater() {
    if (document.body.dataset.float === 'off' || !window.customElements.get('myslik-face')) return;
    const m = document.createElement('myslik-face'); m.setAttribute('float', ''); m.setAttribute('mood', 'idle');
    if (document.body.dataset.who) m.setAttribute('who', document.body.dataset.who);
    document.body.append(m);
    let seen = 0; try { seen = +localStorage.getItem('smk_float_seen') || 0; } catch (e) {}
    setTimeout(() => m.react('hello', { text: seen ? undefined : 'Привет! Меня можно таскать по экрану.' }), 900);
    try { localStorage.setItem('smk_float_seen', seen + 1); } catch (e) {}
    // реагирует на прокрутку до тарифов и на завершение страницы
    let said = false;
    window.addEventListener('scroll', () => {
      if (said) return;
      const t = document.getElementById('price'); if (!t) return;
      if (t.getBoundingClientRect().top < window.innerHeight * .6) { said = true; m.react('idea', { text: 'Первые три задания в день бесплатно.' }); }
    }, { passive: true });
  }

  /* ---------- сборка ---------- */
  document.addEventListener('DOMContentLoaded', () => {
    const h = document.getElementById('site-header'); if (h) h.outerHTML = header(document.body.dataset.page || '');
    const f = document.getElementById('site-footer'); if (f) f.outerHTML = footer();
    const bg = document.getElementById('burger'); if (bg) bg.onclick = () => document.getElementById('navlinks').classList.toggle('open');
    cookie(); floater();
  });
})();
