/* Смекай: общие сценарии сайта.
   Шапка и подвал, всплывающие окна, оплата с QR-кодом, поддержка с Мысликом,
   связь с сервером личного кабинета, cookie, плавающий Мыслик. */
(function () {
  /* ---------- настройки: всё, что может понадобиться поменять ---------- */
  const CFG = {
    API: '',                      // адрес сервера кабинета, например https://api.smekai.ru. Пусто: кабинет работает на устройстве
    BOT: 'https://t.me/smekai_ru_bot',
    MAX_BOT: 'https://max.ru/id501807779599_bot',
    MAX: 'https://max.ru/join/nQJFTVidgdh_w-lFQo9rbmy54ErMxxp_vbMRjOdTJFo',
    TG: 'https://t.me/smekai_ru',
    BOOSTY: 'https://boosty.to/smekai',
    EMAIL: 'hello@smekai.ru',
    SBP_QR: '',                   // статический QR-код СБП из банка, например assets/pay/sbp.png. Пусто: не показывается
    REQ: { name: 'Индивидуальный предприниматель Ярмак Николай Владимирович', short: 'ИП Ярмак Н. В.',
           inn: '501807779599', ogrnip: '325774600563025' },
  };
  const PLANS = {
    free:   { title: 'Знакомство', price: 0,    about: '3 задания в день, открытый канал, викторина' },
    tasks:  { title: 'Задания',    price: 390,  about: 'закрытый канал с ежедневными заданиями и разборами по классу' },
    myslik: { title: 'Мыслик',     price: 890,  about: '30 разборов в день, фото домашки, закрытый канал, отчёт родителю' },
    family: { title: 'Семья',      price: 1490, about: 'всё из тарифа Мыслик для двух детей, отчёт по каждому' },
  };
  const root = document.body.dataset.root || './';
  const src = document.body.dataset.src || 'site';
  const rub = n => n.toLocaleString('ru-RU').replace(/ /g, ' ') + ' ₽';
  const esc = t => String(t ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

  const ICONS = {
    tg: '<svg viewBox="0 0 240 240" class="brand-ico"><circle cx="120" cy="120" r="120" fill="#2AABEE"/><path fill="#fff" d="M54.3 118.8c35-15.2 58.3-25.3 70-30.2 33.3-13.9 40.3-16.3 44.8-16.4 1 0 3.2.2 4.7 1.4 1.2 1 1.5 2.3 1.7 3.3.2 1 .4 3.1.2 4.7-1.8 19-9.6 65.1-13.6 86.3-1.7 9-5 12-8.2 12.3-7 .6-12.3-4.6-19-9-10.6-6.9-16.5-11.2-26.8-18-11.8-7.8-4.2-12.1 2.6-19.1 1.8-1.8 32.5-29.8 33.1-32.3.1-.3.1-1.5-.6-2.1-.7-.6-1.7-.4-2.5-.2-1 .2-17.9 11.4-50.6 33.5-4.8 3.3-9.1 4.9-13 4.8-4.3-.1-12.5-2.4-18.6-4.4-7.5-2.4-13.5-3.7-12.9-7.9.3-2.2 3.3-4.4 8.9-6.7z"/></svg>',
    max: `<img src="${root}assets/brand/max.svg" alt="" class="brand-ico">`,
    boosty: '<svg viewBox="0 0 24 24" class="brand-ico"><rect width="24" height="24" rx="6" fill="#F15F2C"/><path fill="#fff" d="M9.2 4.5h5.1l-1.9 5.6h3.9L9.6 19.5l1.8-6.4H7.5z"/></svg>',
    web: '<svg viewBox="0 0 24 24"><path d="M4 4h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-6v2h3v2H7v-2h3v-2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zm0 2v10h16V6H4z"/></svg>',
    home: '<svg viewBox="0 0 24 24"><path d="M12 3l9 8h-3v9h-5v-6h-2v6H6v-9H3z"/></svg>',
    card: '<svg viewBox="0 0 24 24"><path d="M3 5h18a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2zm0 4v8h18V9H3zm2 5h6v2H5z"/></svg>',
    qr: '<svg viewBox="0 0 24 24"><path d="M3 3h8v8H3V3zm2 2v4h4V5H5zm8-2h8v8h-8V3zm2 2v4h4V5h-4zM3 13h8v8H3v-8zm2 2v4h4v-4H5zm8-2h2v2h-2v-2zm4 0h4v2h-2v2h-2v-4zm-4 4h2v4h-2v-4zm4 2h2v2h-2v-2zm2-2h2v4h-2v-4z"/></svg>',
    help: '<svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 1 0 20 10 10 0 0 1 0-20zm0 14.5a1.3 1.3 0 1 0 0 2.6 1.3 1.3 0 0 0 0-2.6zM12 6c-2.2 0-3.8 1.3-4 3.3h2.2c.1-.9.8-1.4 1.8-1.4s1.8.6 1.8 1.4c0 .7-.4 1.1-1.3 1.7-1.1.7-1.7 1.4-1.6 2.9v.5h2.1V14c0-.8.3-1.1 1.3-1.8 1-.7 1.8-1.5 1.8-3C16.1 7.4 14.5 6 12 6z"/></svg>',
  };

  /* ---------- сервер кабинета ---------- */
  const SES = 'smk_session';
  const session = {
    get() { try { return localStorage.getItem(SES) || ''; } catch (e) { return ''; } },
    set(v) { try { v ? localStorage.setItem(SES, v) : localStorage.removeItem(SES); } catch (e) {} },
  };
  async function api(path, body, method) {
    if (!CFG.API) throw new Error('нет сервера');
    const r = await fetch(CFG.API.replace(/\/$/, '') + path, {
      method: method || (body ? 'POST' : 'GET'),
      headers: Object.assign({ 'Content-Type': 'application/json' }, session.get() ? { Authorization: 'Bearer ' + session.get() } : {}),
      body: body ? JSON.stringify(body) : undefined,
    });
    const d = await r.json().catch(() => ({ ok: false, error: 'Сервер не ответил' }));
    if (r.status === 401) session.set('');
    if (!d.ok) { const e = new Error(d.error || 'Ошибка'); e.status = r.status; throw e; }
    return d;
  }

  /* ---------- QR-код ---------- */
  let qrLib = null;
  function loadQr() {
    if (window.qrcode) return Promise.resolve();
    if (!qrLib) qrLib = new Promise((ok, no) => { const s = document.createElement('script'); s.src = root + 'assets/qrcode.js'; s.onload = ok; s.onerror = no; document.head.append(s); });
    return qrLib;
  }
  async function qr(el, text, size) {
    await loadQr();
    const q = window.qrcode(0, 'M'); q.addData(text); q.make();
    const n = q.getModuleCount(), cell = Math.max(2, Math.floor((size || 220) / (n + 8)));
    el.innerHTML = q.createSvgTag({ cellSize: cell, margin: cell * 4, scalable: true });
    const svg = el.querySelector('svg'); if (svg) { svg.setAttribute('role', 'img'); svg.setAttribute('aria-label', 'QR-код'); }
  }

  /* ---------- шапка ---------- */
  function header(active) {
    const items = [['kak-rabotaet.html', 'Как работает'], ['tarify.html', 'Цены'], ['lev.html', 'Мыслик и Лев'], ['viktorina/', 'Викторина'], ['faq.html', 'Вопросы']];
    return `<header class="top"><div class="wrap nav">
      <a class="brand" href="${root}"><img class="brand-mark" src="${root}assets/brand/mark.png" alt="">Смекай</a>
      <nav class="nav-links" id="navlinks">${items.map(([h, t]) => `<a href="${root}${h}"${active === h ? ' aria-current="page"' : ''}>${t}</a>`).join('')}
        <a href="${root}kabinet/" class="only-mob"${active === 'kabinet' ? ' aria-current="page"' : ''}>Личный кабинет</a></nav>
      <span class="sp"></span>
      <a class="btn btn-main btn-sm" href="${root}kabinet/">${ICONS.home}<span class="hide-mob-t">Личный кабинет</span><span class="only-mob-t">Кабинет</span></a>
      <button class="burger" id="burger" aria-label="Меню">☰</button>
    </div></header>`;
  }

  /* ---------- подвал ---------- */
  function footer() {
    return `<footer class="site"><div class="wrap">
      <div class="foot">
        <div style="max-width:300px"><a class="brand" href="${root}" style="margin-bottom:10px"><img class="brand-mark" src="${root}assets/brand/mark.png" alt="">Смекай</a>
          <p class="small muted">Помощник по учёбе для школьника. Ребёнок думает сам, родитель спокоен.</p>
          <div class="social">
            <a href="${CFG.TG}" target="_blank" rel="noopener" title="Канал в Telegram" aria-label="Telegram">${ICONS.tg}</a>
            <a href="${CFG.MAX}" target="_blank" rel="noopener" title="Канал в MAX" aria-label="MAX">${ICONS.max}</a>
            <a href="${CFG.BOOSTY}" target="_blank" rel="noopener" title="Boosty" aria-label="Boosty">${ICONS.boosty}</a>
          </div>
        </div>
        <div><div class="col-title">Продукт</div>
          <a href="${root}kak-rabotaet.html">Как работает</a><a href="${root}tarify.html">Цены</a><a href="${root}oplata.html">Оплата</a><a href="${root}kabinet/">Личный кабинет</a><a href="${root}viktorina/">Викторина</a></div>
        <div><div class="col-title">Помощь</div>
          <a href="${root}faq.html">Вопросы и ответы</a><a href="#" data-modal="support">Поддержка</a><a href="${root}lev.html">Мыслик и Лев</a></div>
        <div><div class="col-title">Документы</div>
          <a href="${root}oferta.html">Публичная оферта</a><a href="${root}policy.html">Обработка данных</a><a href="${root}rekvizity.html">Реквизиты</a></div>
      </div>
      <p class="copy">© 2026 Смекай. ${CFG.REQ.name}, ИНН ${CFG.REQ.inn}, ОГРНИП ${CFG.REQ.ogrnip}.<br>Условия оказания услуг в <a href="${root}oferta.html">публичной оферте</a>. Почта: <a href="mailto:${CFG.EMAIL}">${CFG.EMAIL}</a>.</p>
    </div></footer>`;
  }

  /* ---------- всплывающие окна ---------- */
  const MODALS = {
    start: () => `<h2>Где удобнее заниматься?</h2>
      <p class="small muted">Один и тот же Мыслик. Детям удобнее планшет или компьютер, родителям телефон.</p>
      <div class="choice">
        <a href="${root}kabinet/"><span class="ci">${ICONS.home}</span><div><b>Личный кабинет</b><span>Планшет или компьютер, без установки. Занятие, прогресс, тариф</span></div></a>
        <a href="${CFG.BOT}?start=${src}" target="_blank" rel="noopener"><span class="ci">${ICONS.tg}</span><div><b>Telegram</b><span>Бот Мыслик: задания, фото домашки, голос, отчёты родителю</span></div></a>
        <a href="${CFG.MAX_BOT}?start=${src}" target="_blank" rel="noopener"><span class="ci">${ICONS.max}</span><div><b>MAX</b><span>Бот Мыслик в MAX: задания, подсказки, отчёты родителю</span></div></a>
      </div>
      <div class="qr"><img src="${root}assets/qr-bot.png" alt="QR-код бота"><p class="small muted" style="margin-top:6px">Наведите камеру телефона, чтобы открыть бота в Telegram</p></div>`,
    channel: () => `<h2>Канал с заданиями</h2>
      <p class="small muted">Каждый день задания по группам классов, ответы с разбором.</p>
      <div class="choice">
        <a href="${CFG.TG}" target="_blank" rel="noopener"><span class="ci">${ICONS.tg}</span><div><b>Telegram</b><span>@smekai_ru</span></div></a>
        <a href="${CFG.MAX}" target="_blank" rel="noopener"><span class="ci">${ICONS.max}</span><div><b>MAX</b><span>Советы, задачи и викторины каждый вечер</span></div></a>
      </div>`,
    plan: (name) => {
      const p = PLANS[name] || PLANS.myslik;
      if (name === 'free') return `<h2>${p.title} <span class="muted" style="font-size:18px;font-weight:500">0 ₽</span></h2><p>Три задания в день в боте или в личном кабинете, открытый канал, викторина. Карта не нужна.</p>
        <div class="choice"><a href="${root}kabinet/"><span class="ci">${ICONS.home}</span><div><b>Личный кабинет</b><span>Планшет или компьютер</span></div></a>
        <a href="${CFG.BOT}?start=${src}" target="_blank" rel="noopener"><span class="ci">${ICONS.tg}</span><div><b>Бот в Telegram</b><span>Имя и класс, дальше первое задание</span></div></a>
        <a href="${CFG.MAX_BOT}?start=${src}" target="_blank" rel="noopener"><span class="ci">${ICONS.max}</span><div><b>Бот в MAX</b><span>Имя и класс, дальше первое задание</span></div></a></div>`;
      return `<h2>${p.title} <span class="muted" style="font-size:18px;font-weight:500">${rub(p.price)} в месяц</span></h2><p>${p.about[0].toUpperCase() + p.about.slice(1)}.</p><div id="modal-pay"></div>`;
    },
    support: () => `<div id="modal-support"></div>`,
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
    back.querySelector('.modal').classList.toggle('wide', name === 'support');
    back.classList.add('on'); document.body.style.overflow = 'hidden'; document.body.classList.add('modal-open');
    if (name === 'plan' && arg !== 'free') renderPay(document.getElementById('modal-pay'), arg, { compact: true });
    if (name === 'support') renderSupport(document.getElementById('modal-support'));
    const m = document.querySelector('myslik-face[float]');
    if (m && name !== 'support') m.react(name === 'plan' ? 'love' : 'hello', { text: name === 'start' ? 'Выбирай, где удобнее.' : undefined });
  }
  function closeModal() {
    const back = document.getElementById('modal-back'); if (!back) return;
    back.classList.remove('on'); document.body.style.overflow = ''; document.body.classList.remove('modal-open');
    clearInterval(payPoll);
  }
  document.addEventListener('click', e => {
    const a = e.target.closest('[data-modal]'); if (!a) return;
    e.preventDefault(); openModal(a.dataset.modal, a.dataset.arg);
  });

  /* ---------- оплата ---------- */
  let payPoll = null;
  function renderPay(el, plan, opt = {}) {
    if (!el) return;
    plan = PLANS[plan] && plan !== 'free' ? plan : 'myslik';
    const paid = ['tasks', 'myslik', 'family'];
    const renew = CFG.API && session.get() ? 'Автосписаний нет: оплачивается один месяц.' : 'Подписка на Boosty продлевается каждый месяц, отменить можно в настройках Boosty в один клик.';
    const legal = `<p class="pay-legal">Оплачивая, вы принимаете условия <a href="${root}oferta.html">публичной оферты</a>. Исполнитель ${CFG.REQ.short}, ИНН ${CFG.REQ.inn}. ${renew}</p>`;
    const pick = opt.compact ? '' : `<div class="pay-plans">${paid.map(k => `<button type="button" data-plan="${k}"${k === plan ? ' class="on"' : ''}><b>${PLANS[k].title}</b><span>${rub(PLANS[k].price)} в месяц</span></button>`).join('')}</div>`;
    el.innerHTML = `<div class="pay">${pick}<div class="pay-body"></div>${legal}</div>`;
    el.querySelectorAll('[data-plan]').forEach(b => b.onclick = () => renderPay(el, b.dataset.plan, opt));
    const body = el.querySelector('.pay-body');
    const p = PLANS[plan];
    const serverPay = CFG.API && session.get();

    if (serverPay) {
      body.innerHTML = `<p class="pay-sum">К оплате: <b>${rub(p.price)}</b>, тариф «${p.title}» на месяц</p>
        <label class="pay-mail">Почта для чека<input type="email" id="pay-email" placeholder="name@mail.ru" autocomplete="email"></label>
        <div class="choice">
          <a href="#" data-m="card"><span class="ci">${ICONS.card}</span><div><b>Картой или МИР</b><span>Откроется защищённая страница оплаты</span></div></a>
          <a href="#" data-m="sbp"><span class="ci">${ICONS.qr}</span><div><b>СБП по QR-коду</b><span>Наведите камеру телефона, оплата в приложении банка</span></div></a>
        </div><div class="pay-qr" id="pay-qr"></div><p class="pay-msg" id="pay-msg"></p>`;
      body.querySelectorAll('[data-m]').forEach(a => a.onclick = async e => {
        e.preventDefault();
        const msg = body.querySelector('#pay-msg'); msg.textContent = 'Создаю платёж…';
        try {
          const d = await api('/api/pay', { plan, method: a.dataset.m, email: body.querySelector('#pay-email').value.trim() });
          if (d.fallback) { location.href = d.fallback; return; }
          if (d.url) { location.href = d.url; return; }
          const box = body.querySelector('#pay-qr');
          if (window.matchMedia('(max-width:860px)').matches) box.innerHTML = `<a class="btn btn-main" href="${esc(d.qr)}">Открыть приложение банка</a>`;
          else await qr(box, d.qr, 240);
          msg.textContent = 'Отсканируйте код камерой телефона и подтвердите оплату в приложении банка. Страница обновится сама.';
          clearInterval(payPoll);
          payPoll = setInterval(async () => {
            try {
              const s = await api('/api/pay/status?id=' + encodeURIComponent(d.id));
              if (s.status === 'succeeded') { clearInterval(payPoll); box.innerHTML = ''; msg.innerHTML = `<b>Оплата прошла.</b> Тариф «${p.title}» действует до ${s.user.paid_until}. Ссылка в закрытый канал пришла в мессенджер.`; document.dispatchEvent(new CustomEvent('smk-paid')); }
              if (s.status === 'canceled') { clearInterval(payPoll); msg.textContent = 'Платёж отменён. Можно попробовать ещё раз.'; }
            } catch (err) {}
          }, 3000);
        } catch (err) { msg.textContent = err.message; }
      });
      return;
    }

    const loginHint = CFG.API ? `<p class="small" style="margin:6px 0 10px"><a href="${root}kabinet/?next=oplata">Войдите в личный кабинет</a>, чтобы доступ открылся сам сразу после оплаты.</p>` : '';
    const sbp = CFG.SBP_QR ? `<div class="pay-static"><img src="${root}${CFG.SBP_QR}" alt="QR-код СБП"><div><b>СБП по QR-коду банка</b><p class="small">Сумма ${rub(p.price)}. В назначении платежа укажите тариф и имя ребёнка, затем напишите в поддержку. Доступ откроем в течение часа.</p></div></div>` : '';
    body.innerHTML = `<p class="pay-sum">К оплате: <b>${rub(p.price)}</b>, тариф «${p.title}» на месяц</p>${loginHint}
      <div class="choice"><a href="${CFG.BOOSTY}" target="_blank" rel="noopener"><span class="ci">${ICONS.card}</span><div><b>Картой, МИР или СБП</b><span>Оплата на Boosty, выберите уровень «${p.title}». Чек приходит на почту</span></div></a></div>
      <div class="pay-phone"><div class="pay-qr" id="pay-qr"></div><div><b>Оплатить с телефона</b><p class="small">Наведите камеру на код: страница оплаты откроется на телефоне, там можно заплатить через СБП в приложении банка.</p></div></div>
      ${sbp}
      <p class="small muted" style="margin-top:12px">После оплаты бот пришлёт ссылку в закрытый канал и откроет доступ. Если за 15 минут ничего не пришло, <a href="#" data-modal="support">напишите в поддержку</a>, откроем вручную в тот же день.</p>`;
    qr(body.querySelector('#pay-qr'), CFG.BOOSTY, 170).catch(() => {});
  }

  /* ---------- поддержка: Мыслик отвечает на вопросы ---------- */
  let SUP = null;
  async function supData() {
    if (!SUP) SUP = await fetch(root + 'assets/support.json').then(r => r.json());
    return SUP;
  }
  const norm = t => ' ' + String(t || '').toLowerCase().replace(/ё/g, 'е').replace(/[^a-zа-я0-9 ]+/g, ' ') + ' ';
  function supMatch(d, text) {
    const t = norm(text); let best = null, score = 0;
    for (const it of d.items) {
      let s = 0;
      for (const k of it.keys) { const k2 = norm(k).trim(); if (k2 && t.includes(' ' + k2)) s += k2.includes(' ') ? 2 : 1; }
      if (s > score) { best = it; score = s; }
    }
    return best;
  }
  const fillUrl = u => u.replace('{SITE}', root).replace('{MAX}', CFG.MAX);

  async function renderSupport(el) {
    if (!el) return;
    const d = await supData();
    el.innerHTML = `<div class="sup">
      <div class="sup-head"><myslik-face age="6" mood="idle" class="sup-face"></myslik-face><div><b>Мыслик</b><span>поддержка Смекай, отвечаю сразу</span></div></div>
      <div class="sup-log" aria-live="polite"></div>
      <div class="sup-quick"></div>
      <form class="sup-in"><input type="text" placeholder="Напишите вопрос своими словами" maxlength="400" aria-label="Вопрос"><button class="btn btn-main btn-sm" type="submit">Спросить</button></form>
      <p class="small muted" style="margin-top:8px">Не нашли ответ? <a href="${CFG.BOT}?start=support" target="_blank" rel="noopener">Напишите в бота</a> или на <a href="mailto:${CFG.EMAIL}">${CFG.EMAIL}</a>.</p>
    </div>`;
    const log = el.querySelector('.sup-log'), face = el.querySelector('.sup-face'), quick = el.querySelector('.sup-quick'), form = el.querySelector('.sup-in');
    const add = (html, who) => { const m = document.createElement('div'); m.className = 'msg ' + (who || 'bot'); m.innerHTML = html; log.append(m); log.scrollTop = log.scrollHeight; return m; };
    const buttons = (ids) => {
      const box = document.createElement('div'); box.className = 'sup-acts';
      ids.forEach(id => {
        const a = d.actions[id]; if (!a) return;
        if (a.url) { const l = document.createElement('a'); l.className = 'btn btn-ghost btn-sm'; l.href = fillUrl(a.url); l.textContent = a.text; if (/^https?:/.test(l.href) && !l.href.includes(location.host)) { l.target = '_blank'; l.rel = 'noopener'; } box.append(l); }
        else { const b = document.createElement('button'); b.type = 'button'; b.className = 'btn btn-sun btn-sm'; b.textContent = a.text; b.onclick = () => flow(a.do); box.append(b); }
      });
      if (box.children.length) { log.append(box); log.scrollTop = log.scrollHeight; }
    };
    const answer = (it) => {
      if (face.react) face.react(['refund', 'no_access', 'bug'].includes(it.id) ? 'thinking' : 'hello', { bubble: false });
      add(fillUrl(it.a).replace(/\n/g, '<br>'));
      buttons(it.actions || []);
    };
    const flow = (kind) => {
      const f = d.flows[kind];
      add(esc(f.ask));
      const box = document.createElement('form'); box.className = 'sup-form';
      box.innerHTML = `<textarea required minlength="5" rows="3" placeholder="${kind === 'refund' ? 'Дата оплаты, сумма, способ оплаты' : 'Ваш вопрос'}"></textarea>
        <input type="text" required placeholder="Почта, телефон или ник в Telegram для ответа">
        <button class="btn btn-main btn-sm" type="submit">Отправить</button>`;
      log.append(box); log.scrollTop = log.scrollHeight; box.querySelector('textarea').focus();
      box.onsubmit = async e => {
        e.preventDefault();
        const text = box.querySelector('textarea').value.trim(), contact = box.querySelector('input').value.trim();
        box.querySelectorAll('textarea,input,button').forEach(x => x.disabled = true);
        if (CFG.API) {
          try { const r = await api('/api/ticket', { kind, text, contact }); add(esc(r.text)); if (face.react) face.react('love', { bubble: false }); return; }
          catch (err) { add('Не получилось отправить: ' + esc(err.message) + '. Письмо можно отправить на почту.'); }
        }
        const subj = (kind === 'refund' ? 'Возврат денег' : 'Вопрос в поддержку') + ' Смекай';
        const bodyTxt = `${text}\n\nКак связаться: ${contact}`;
        location.href = `mailto:${CFG.EMAIL}?subject=${encodeURIComponent(subj)}&body=${encodeURIComponent(bodyTxt)}`;
        add(`Открываю почту с готовым письмом на ${CFG.EMAIL}. Если почта не открылась, отправьте этот текст туда же или <a href="${CFG.BOT}?start=support" target="_blank" rel="noopener">в бота</a>. ${kind === 'refund' ? 'Деньги вернём в течение десяти рабочих дней.' : 'Ответим в течение рабочего дня.'}`);
      };
    };
    add(esc(d.hello));
    d.quick.forEach(id => {
      const it = d.items.find(x => x.id === id); if (!it) return;
      const b = document.createElement('button'); b.type = 'button'; b.className = 'chip'; b.textContent = it.q;
      b.onclick = () => { add(esc(it.q), 'kid'); if (id === 'human') flow('human'); else answer(it); };
      quick.append(b);
    });
    form.onsubmit = e => {
      e.preventDefault();
      const inp = form.querySelector('input'), q = inp.value.trim(); if (!q) return;
      inp.value = ''; add(esc(q), 'kid');
      const it = supMatch(d, q);
      if (it) answer(it);
      else { if (face.react) face.react('thinking', { bubble: false }); add(esc(d.fallback)); buttons(['human', 'pay']); }
    };
  }

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
    const m = document.createElement('myslik-face'); m.setAttribute('float', ''); m.setAttribute('mood', 'idle'); m.setAttribute('help', '');
    m.setAttribute('age', document.body.dataset.age || '5');
    document.body.append(m);
    m.addEventListener('myslik-help', () => openModal('support'));
    let seen = 0; try { seen = +localStorage.getItem('smk_float_seen') || 0; } catch (e) {}
    setTimeout(() => m.react('hello', { text: seen ? undefined : 'Привет! Меня можно таскать по экрану. Нажми «?», если нужна помощь.' }), 900);
    try { localStorage.setItem('smk_float_seen', seen + 1); } catch (e) {}
    let said = false;
    window.addEventListener('scroll', () => {
      if (said) return;
      const t = document.getElementById('price'); if (!t) return;
      if (t.getBoundingClientRect().top < window.innerHeight * .6) { said = true; m.react('idea', { text: 'Первые три задания в день бесплатно.' }); }
    }, { passive: true });
  }

  window.SMK = { CFG, PLANS, api, session, qr, pay: renderPay, support: renderSupport, modal: openModal, esc, rub, ICONS };

  /* ---------- сборка ---------- */
  document.addEventListener('DOMContentLoaded', () => {
    if (document.body.classList.contains('render')) return;   // режим записи стикеров
    const h = document.getElementById('site-header'); if (h) h.outerHTML = header(document.body.dataset.page || '');
    const f = document.getElementById('site-footer'); if (f) f.outerHTML = footer();
    const bg = document.getElementById('burger'); if (bg) bg.onclick = () => document.getElementById('navlinks').classList.toggle('open');
    document.querySelectorAll('[data-pay]').forEach(el => renderPay(el, new URLSearchParams(location.search).get('plan') || el.dataset.pay));
    document.querySelectorAll('[data-support]').forEach(el => renderSupport(el));
    cookie(); floater();
  });
})();
