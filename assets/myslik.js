/* Мыслик: анимированный персонаж Смекай.
 *
 * Подключение:  <script src="assets/myslik.js"></script>
 *               <myslik-face mood="idle" size="240"></myslik-face>
 *
 * Настроения (атрибут mood или класс на элементе):
 *   idle, think, yay, party, sad, angry, surprised, sleepy, wave, love, shy
 *   Для совместимости с викториной классы oops = sad.
 *
 * Из скрипта:
 *   el.mood('yay')                    сменить настроение
 *   el.say('Привет!', {ms: 3000})     облачко с текстом, печатается по буквам
 *   el.speak('Привет!', profile)      озвучить голосом браузера, рот двигается
 *   el.react('correct' | 'wrong' | 'hello' | 'thinking' | 'bye')  готовые реакции
 *   Myslik.voices()                   список русских голосов браузера
 *   Myslik.profiles                   пресеты: boy, girl, parent
 */
(function () {
  const CSS = `
:host{display:inline-block;position:relative;line-height:0;--sun:#FFC933;--ink:#1B1F3B;--body:#3E7BFA;--body-dark:#2F63D6;--face:#FFFFFF}
:host([hidden]){display:none}
.stage{position:relative;width:100%;height:100%}
svg{width:100%;height:100%;overflow:visible;display:block}
.tb{transform-box:fill-box;transform-origin:center}
.rig{transform-box:fill-box;transform-origin:50% 100%;animation:sway 5.2s ease-in-out infinite}
.body{transform-box:fill-box;transform-origin:50% 100%;animation:breathe 3.4s ease-in-out infinite}
.shadow{transform-box:fill-box;transform-origin:center;animation:shadow 3.4s ease-in-out infinite}
.eye{transform-box:fill-box;transform-origin:center}
.eyes.blink .eye{animation:blink .16s ease-in-out}
.pupils{transition:transform .25s ease}
.brow{transform-box:fill-box;transform-origin:center;transition:transform .25s ease,opacity .2s}
.mouth path,.mouth ellipse{transition:opacity .12s}
.m{opacity:0}.m.on{opacity:1}
.arm{transform-box:fill-box;transform-origin:50% 0;transition:transform .35s ease}
.glow{fill:var(--sun);opacity:.22;transform-box:fill-box;transform-origin:center;animation:idleglow 4.6s ease-in-out infinite}
.rays{opacity:0;transform-box:fill-box;transform-origin:center;transition:opacity .2s}
.bulb{transition:fill .25s}
.sparks,.hearts,.tears,.steam,.zzz,.drop,.wow{opacity:0;transition:opacity .2s}
.spark{transform-box:fill-box;transform-origin:center}
.cheek{transition:opacity .3s}
/* --- настроения --- */
:host(.think) .pupils{transform:translate(2px,-3px)}
:host(.think) .brow.l{transform:translate(0,-2px) rotate(-8deg)}
:host(.think) .brow.r{transform:translate(0,1px) rotate(6deg)}
:host(.think) .arm.r{transform:rotate(-95deg) translate(2px,0)}
:host(.think) .drop{opacity:1;animation:drop 1.6s ease-in infinite}
:host(.think) .bulb{fill:#FFD95C}
:host(.think) .glow{animation:thinkglow 1.1s ease-in-out infinite}
:host(.yay) .rig{animation:jump .7s ease}
:host(.yay) .body{animation:squash .7s ease}
:host(.yay) .arm.l{transform:rotate(45deg)}:host(.yay) .arm.r{transform:rotate(-45deg)}
:host(.yay) .bulb,:host(.party) .bulb{fill:#FFE14D}
:host(.yay) .glow,:host(.party) .glow{animation:none;opacity:.75;transform:scale(1.35)}
:host(.yay) .rays,:host(.party) .rays{opacity:1;animation:spin 3s linear infinite}
:host(.yay) .sparks,:host(.party) .sparks{opacity:1}
:host(.yay) .spark,:host(.party) .spark{animation:tw .8s ease-in-out infinite}
:host(.party) .rig{animation:bounce 1s ease-in-out infinite}
:host(.party) .arm.l{animation:wave 1s ease-in-out infinite}
:host(.party) .arm.r{animation:wave 1s ease-in-out infinite reverse}
:host(.sad) .rig{animation:slump .6s ease forwards}
:host(.sad) .brow.l{transform:translate(1px,-1px) rotate(14deg)}
:host(.sad) .brow.r{transform:translate(-1px,-1px) rotate(-14deg)}
:host(.sad) .pupils{transform:translate(0,2px)}
:host(.sad) .tears{opacity:1}
:host(.sad) .tear{animation:tear 1.4s ease-in infinite}
:host(.sad) .tear.b{animation-delay:.5s}
:host(.sad) .bulb{fill:#C9CCD9}:host(.sad) .glow{animation:none;opacity:0}
:host(.angry) .rig{animation:shake .4s ease-in-out 2}
:host(.angry) .brow.l{transform:translate(2px,3px) rotate(-22deg)}
:host(.angry) .brow.r{transform:translate(-2px,3px) rotate(22deg)}
:host(.angry) .cheek{opacity:.9}
:host(.angry) .steam{opacity:1}
:host(.angry) .puff{animation:puff 1.2s ease-out infinite}
:host(.angry) .puff.b{animation-delay:.4s}:host(.angry) .puff.c{animation-delay:.8s}
:host(.angry) .bulb{fill:#FF8A65}:host(.angry) .glow{fill:#FF8A65;animation:thinkglow .5s ease-in-out infinite}
:host(.surprised) .rig{animation:startle .5s ease}
:host(.surprised) .eye{transform:scale(1.22)}
:host(.surprised) .brow.l,:host(.surprised) .brow.r{transform:translate(0,-4px)}
:host(.surprised) .wow{opacity:1;animation:wow .6s ease}
:host(.surprised) .glow{animation:none;opacity:.6;transform:scale(1.2)}
:host(.sleepy) .rig{animation:sway 7s ease-in-out infinite}
:host(.sleepy) .eye{transform:scaleY(.35)}
:host(.sleepy) .brow.l,:host(.sleepy) .brow.r{transform:translate(0,2px)}
:host(.sleepy) .zzz{opacity:1}
:host(.sleepy) .z{animation:zz 2.4s ease-out infinite}
:host(.sleepy) .z.b{animation-delay:.8s}:host(.sleepy) .z.c{animation-delay:1.6s}
:host(.sleepy) .bulb{fill:#C9CCD9}:host(.sleepy) .glow{animation:none;opacity:0}
:host(.wave) .arm.r{animation:wave .55s ease-in-out 4}
:host(.wave) .brow.l,:host(.wave) .brow.r{transform:translate(0,-2px)}
:host(.love) .hearts{opacity:1}
:host(.love) .heart{animation:float 2s ease-out infinite}
:host(.love) .heart.b{animation-delay:.7s}:host(.love) .heart.c{animation-delay:1.3s}
:host(.love) .cheek{opacity:.95}
:host(.love) .bulb{fill:#FF8FA3}:host(.love) .glow{fill:#FF8FA3;opacity:.5;animation:none;transform:scale(1.2)}
:host(.shy) .cheek{opacity:1}
:host(.shy) .pupils{transform:translate(-2px,2px)}
:host(.shy) .rig{animation:sway 3s ease-in-out infinite}
:host(.shy) .arm.l{transform:rotate(-30deg)}
/* --- облачко --- */
.bubble{position:absolute;left:78%;bottom:78%;min-width:120px;max-width:min(320px,70vw);background:#fff;color:var(--ink);
  border:2px solid var(--ink);border-radius:18px;padding:10px 14px;font:600 15px/1.35 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
  line-height:1.35;box-shadow:0 8px 24px rgba(27,31,59,.14);opacity:0;transform:translateY(8px) scale(.94);transform-origin:0 100%;
  transition:opacity .22s,transform .22s;pointer-events:none;z-index:2;white-space:pre-wrap}
.bubble::after{content:"";position:absolute;left:14px;bottom:-11px;width:16px;height:16px;background:#fff;border-left:2px solid var(--ink);
  border-bottom:2px solid var(--ink);transform:rotate(-45deg);border-radius:0 0 0 4px}
.bubble.on{opacity:1;transform:translateY(0) scale(1)}
.bubble.left{left:auto;right:78%;transform-origin:100% 100%}
.bubble.left::after{left:auto;right:14px;transform:rotate(-135deg)}
.bubble .cur{display:inline-block;width:2px;height:1em;background:var(--ink);vertical-align:-2px;margin-left:1px;animation:cur .8s step-end infinite}
/* --- ключевые кадры --- */
@keyframes sway{0%,100%{transform:rotate(-1.4deg)}50%{transform:rotate(1.4deg)}}
@keyframes breathe{0%,100%{transform:scale(1,1)}50%{transform:scale(1.012,1.03)}}
@keyframes shadow{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}
@keyframes blink{0%,100%{transform:scaleY(1)}50%{transform:scaleY(.06)}}
@keyframes idleglow{0%,100%{opacity:.18;transform:scale(1)}50%{opacity:.4;transform:scale(1.08)}}
@keyframes thinkglow{0%,100%{opacity:.25;transform:scale(1)}50%{opacity:.8;transform:scale(1.25)}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes tw{0%,100%{transform:scale(.6) rotate(0);opacity:.5}50%{transform:scale(1.15) rotate(20deg);opacity:1}}
@keyframes jump{0%{transform:translateY(0)}30%{transform:translateY(-14px)}55%{transform:translateY(0)}72%{transform:translateY(-6px)}100%{transform:translateY(0)}}
@keyframes squash{0%{transform:scale(1,1)}15%{transform:scale(1.08,.9)}35%{transform:scale(.94,1.08)}60%{transform:scale(1.04,.96)}100%{transform:scale(1,1)}}
@keyframes bounce{0%,100%{transform:translateY(0) rotate(-3deg)}50%{transform:translateY(-8px) rotate(3deg)}}
@keyframes wave{0%,100%{transform:rotate(-60deg)}50%{transform:rotate(-120deg)}}
@keyframes slump{to{transform:translateY(4px) scale(.98)}}
@keyframes tear{0%{transform:translateY(0);opacity:0}15%{opacity:1}100%{transform:translateY(22px);opacity:0}}
@keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-3px) rotate(-1deg)}75%{transform:translateX(3px) rotate(1deg)}}
@keyframes puff{0%{transform:translateY(0) scale(.4);opacity:0}30%{opacity:.9}100%{transform:translateY(-16px) scale(1.2);opacity:0}}
@keyframes startle{0%{transform:translateY(0) scale(1)}30%{transform:translateY(-5px) scale(1.04)}100%{transform:translateY(0) scale(1)}}
@keyframes wow{0%{transform:scale(.3);opacity:0}60%{transform:scale(1.15);opacity:1}100%{transform:scale(1);opacity:1}}
@keyframes zz{0%{transform:translate(0,0) scale(.6);opacity:0}30%{opacity:1}100%{transform:translate(10px,-22px) scale(1.2);opacity:0}}
@keyframes float{0%{transform:translateY(0) scale(.5);opacity:0}25%{opacity:1}100%{transform:translateY(-30px) scale(1.1);opacity:0}}
@keyframes drop{0%{transform:translateY(0);opacity:0}20%{opacity:1}100%{transform:translateY(9px);opacity:0}}
@keyframes cur{50%{opacity:0}}
@media (prefers-reduced-motion:reduce){.rig,.body,.shadow,.glow{animation:none!important}}
`;

  const SVG = `
<svg viewBox="-12 -16 124 136" aria-hidden="true">
<defs>
  <radialGradient id="gBody" cx="38%" cy="30%" r="75%"><stop offset="0" stop-color="#5B92FF"/><stop offset=".65" stop-color="#3E7BFA"/><stop offset="1" stop-color="#2C5FD6"/></radialGradient>
  <radialGradient id="gBulb" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="#FFF6CC"/><stop offset="1" stop-color="#FFD95C"/></radialGradient>
  <radialGradient id="gIris" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="#3A4166"/><stop offset="1" stop-color="#1B1F3B"/></radialGradient>
</defs>
<ellipse class="shadow" cx="50" cy="109" rx="26" ry="4" fill="#1B1F3B" opacity=".10"/>
<g class="rig">
  <g class="lamp">
    <g class="sparks" fill="var(--sun)">
      <path class="spark" d="M4 30l2 5 5 2-5 2-2 5-2-5-5-2 5-2z"/>
      <path class="spark" d="M94 42l1.6 4 4 1.6-4 1.6-1.6 4-1.6-4-4-1.6 4-1.6z"/>
      <path class="spark" d="M90 6l1.2 3 3 1.2-3 1.2-1.2 3-1.2-3-3-1.2 3-1.2z"/>
    </g>
    <g class="rays" stroke="var(--sun)" stroke-width="2.6" stroke-linecap="round">
      <line x1="50" y1="-8" x2="50" y2="-2"/><line x1="35" y1="-1" x2="39" y2="3"/><line x1="65" y1="-1" x2="61" y2="3"/>
      <line x1="29" y1="12" x2="35" y2="12"/><line x1="71" y1="12" x2="65" y2="12"/>
    </g>
    <circle class="glow" cx="50" cy="12" r="16"/>
    <line x1="50" y1="30" x2="50" y2="21" stroke="var(--ink)" stroke-width="3" stroke-linecap="round"/>
    <circle class="bulb" cx="50" cy="12" r="8.5" fill="url(#gBulb)"/>
    <path d="M47 15 q3 -5 6 0" stroke="#E0A93A" stroke-width="1.2" fill="none" opacity=".6"/>
    <circle cx="46.8" cy="8.6" r="2.4" fill="#fff" opacity=".9"/>
    <rect x="45.2" y="19.4" width="9.6" height="4.2" rx="1.6" fill="#8891AE"/>
    <g class="steam" fill="#B9C0D6"><circle class="puff a" cx="38" cy="26" r="3"/><circle class="puff b" cx="62" cy="24" r="3.6"/><circle class="puff c" cx="50" cy="-2" r="2.6"/></g>
    <g class="zzz" fill="var(--ink)" font-family="Arial,sans-serif" font-weight="800">
      <text class="z a" x="70" y="30" font-size="9">z</text><text class="z b" x="74" y="24" font-size="11">z</text><text class="z c" x="79" y="18" font-size="13">Z</text>
    </g>
    <g class="hearts" fill="#FF6B81">
      <path class="heart a" d="M22 40c-3-4-9-1-6 4l6 6 6-6c3-5-3-8-6-4z"/>
      <path class="heart b" d="M78 34c-2.4-3.2-7.2-.8-4.8 3.2l4.8 4.8 4.8-4.8c2.4-4-2.4-6.4-4.8-3.2z"/>
      <path class="heart c" d="M50 -4c-2-2.6-6-.6-4 2.6l4 4 4-4c2-3.2-2-5.2-4-2.6z"/>
    </g>
    <g class="wow"><path d="M84 24 l3 -6 3 6 -3 -1z" fill="var(--sun)"/><text x="80" y="20" font-size="10" font-weight="800" fill="var(--ink)" font-family="Arial,sans-serif">!</text></g>
  </g>
  <g class="arm l"><path d="M20 70 Q8 74 10 84" stroke="var(--body-dark)" stroke-width="7" fill="none" stroke-linecap="round"/></g>
  <g class="arm r"><path d="M80 70 Q92 74 90 84" stroke="var(--body-dark)" stroke-width="7" fill="none" stroke-linecap="round"/></g>
  <g class="body">
    <path d="M18 67 C18 41 32 29 50 29 C68 29 82 41 82 67 C82 89 68 103 50 103 C32 103 18 89 18 67Z" fill="url(#gBody)"/>
    <ellipse cx="38" cy="40" rx="9" ry="5" fill="#fff" opacity=".16" transform="rotate(-25 38 40)"/>
    <path d="M30 77 C30 65 38 59 50 59 C62 59 70 65 70 77 C70 91 62 98 50 98 C38 98 30 91 30 77Z" fill="var(--face)" opacity=".95"/>
    <g class="cheeks"><circle class="cheek" cx="30" cy="70" r="4.6" fill="#FF8FA3" opacity=".55"/><circle class="cheek" cx="70" cy="70" r="4.6" fill="#FF8FA3" opacity=".55"/></g>
    <g class="brows" stroke="var(--ink)" stroke-width="2.6" stroke-linecap="round" fill="none">
      <path class="brow l" d="M32 45 Q39 42 46 45"/><path class="brow r" d="M54 45 Q61 42 68 45"/>
    </g>
    <g class="eyes">
      <g class="eye l"><ellipse cx="39" cy="55" rx="7.2" ry="8.2" fill="#fff"/></g>
      <g class="eye r"><ellipse cx="61" cy="55" rx="7.2" ry="8.2" fill="#fff"/></g>
      <g class="pupils">
        <circle cx="40" cy="56" r="4.3" fill="url(#gIris)"/><circle cx="62" cy="56" r="4.3" fill="url(#gIris)"/>
        <circle cx="41.6" cy="54.2" r="1.5" fill="#fff"/><circle cx="63.6" cy="54.2" r="1.5" fill="#fff"/>
        <circle cx="38.8" cy="57.6" r=".7" fill="#fff" opacity=".8"/><circle cx="60.8" cy="57.6" r=".7" fill="#fff" opacity=".8"/>
      </g>
      <g class="happy m" stroke="var(--ink)" stroke-width="3.4" fill="none" stroke-linecap="round">
        <path d="M32 57 Q39 48 46 57"/><path d="M54 57 Q61 48 68 57"/>
      </g>
      <g class="tears" fill="#7FB7FF"><path class="tear a" d="M35 62 q2.5 4 0 6 q-2.5 -2 0 -6z"/><path class="tear b" d="M65 62 q2.5 4 0 6 q-2.5 -2 0 -6z"/></g>
    </g>
    <g class="mouth">
      <path class="m smile on" d="M42 74 Q50 81 58 74" stroke="var(--ink)" stroke-width="3" fill="none" stroke-linecap="round"/>
      <g class="m grin"><path d="M40 71 Q50 71 60 71 Q59 85 50 86 Q41 85 40 71Z" fill="var(--ink)"/><path d="M44 80 Q50 76 56 80 Q54 85 50 85 Q46 85 44 80Z" fill="#FF6B81"/></g>
      <g class="m open"><ellipse cx="50" cy="77" rx="5" ry="5.6" fill="var(--ink)"/><ellipse cx="50" cy="80" rx="3" ry="2" fill="#FF6B81"/></g>
      <g class="m half"><path d="M43 75 Q50 79 57 75 Q56 80 50 80.5 Q44 80 43 75Z" fill="var(--ink)"/></g>
      <path class="m flat" d="M43 76 L57 76" stroke="var(--ink)" stroke-width="3" fill="none" stroke-linecap="round"/>
      <path class="m frown" d="M42 79 Q50 72 58 79" stroke="var(--ink)" stroke-width="3" fill="none" stroke-linecap="round"/>
      <ellipse class="m o" cx="50" cy="77" rx="3.6" ry="4.6" fill="var(--ink)"/>
      <path class="m grit" d="M42 76 h16 M46 73.5 v5 M50 73.5 v5 M54 73.5 v5" stroke="var(--ink)" stroke-width="2.2" fill="none" stroke-linecap="round"/>
    </g>
    <g class="drop" fill="#7FB7FF"><path d="M73 48 q3 5 0 7.5 q-3 -2.5 0 -7.5z"/></g>
  </g>
</g>
</svg>`;

  const MOODS = ['idle', 'think', 'yay', 'party', 'sad', 'angry', 'surprised', 'sleepy', 'wave', 'love', 'shy'];
  const ALIAS = { oops: 'sad', celebrate: 'party', happy: 'yay', hi: 'wave' };
  const MOUTH = { idle: 'smile', think: 'flat', yay: 'grin', party: 'grin', sad: 'frown', angry: 'grit',
                  surprised: 'o', sleepy: 'half', wave: 'smile', love: 'grin', shy: 'smile' };
  const HAPPY_EYES = new Set(['yay', 'party', 'love']);
  const TALK = ['open', 'half', 'smile', 'open', 'o', 'half'];

  const REACT = {
    hello:    { mood: 'wave',      say: ['Привет! Я Мыслик.', 'Здравствуй! Готов к уроку?', 'Привет! Что сегодня решаем?'] },
    correct:  { mood: 'yay',       say: ['Верно!', 'Точно!', 'Да, именно так!', 'Отлично, правильно.', 'Вот это да, с первого раза!'] },
    wrong:    { mood: 'sad',       say: ['Пока не то.', 'Почти, но нет.', 'Не сходится. Проверь ещё раз.', 'Хм, попробуй иначе.'] },
    thinking: { mood: 'think',     say: ['Дай подумать…', 'Так, смотрим на условие…', 'Хм-м…'] },
    bye:      { mood: 'wave',      say: ['Пока! Заходи завтра.', 'До встречи!', 'Молодец сегодня. Пока!'] },
    streak:   { mood: 'party',     say: ['Три подряд! Ты в ударе!', 'Серия! Так держать!'] },
    surprise: { mood: 'surprised', say: ['Ого!', 'Ничего себе!'] },
    tired:    { mood: 'sleepy',    say: ['Может, перерыв?', 'Пять минут отдыха, и продолжим.'] },
    love:     { mood: 'love',      say: ['Ты мне нравишься!', 'Обожаю, когда получается!'] },
    angry:    { mood: 'angry',     say: ['Эй! Так нечестно.', 'Не списывай!'] },
  };

  class MyslikFace extends HTMLElement {
    static get observedAttributes() { return ['mood', 'size', 'class', 'talking']; }
    constructor() {
      super();
      const root = this.attachShadow({ mode: 'open' });
      const style = document.createElement('style'); style.textContent = CSS;
      const stage = document.createElement('div'); stage.className = 'stage'; stage.innerHTML = SVG;
      this._bubble = document.createElement('div'); this._bubble.className = 'bubble';
      stage.appendChild(this._bubble);
      root.append(style, stage);
      this._q = {}; this._talkTimer = null; this._blinkTimer = null; this._sayTimer = null; this._moodTimer = null;
      this._current = 'idle';
    }
    connectedCallback() {
      this._applySize();
      this._applyClasses();
      this._scheduleBlink();
      this._glance();
      if (!this._followBound) { this._followBound = this._follow.bind(this); window.addEventListener('pointermove', this._followBound, { passive: true }); }
    }
    disconnectedCallback() {
      clearTimeout(this._blinkTimer); clearTimeout(this._glanceTimer); clearInterval(this._talkTimer); clearTimeout(this._sayTimer); clearTimeout(this._moodTimer);
      window.removeEventListener('pointermove', this._followBound);
    }
    attributeChangedCallback(n) {
      if (n === 'size') this._applySize();
      if (n === 'mood' || n === 'class') this._applyClasses();
      if (n === 'talking') this._talking(this.hasAttribute('talking'));
    }
    _applySize() {
      const s = this.getAttribute('size');
      if (s) { this.style.width = s + 'px'; this.style.height = s + 'px'; }
    }
    _applyClasses() {
      let m = this.getAttribute('mood') || 'idle';
      for (const c of this.classList) { if (MOODS.includes(c) || ALIAS[c]) m = ALIAS[c] || c; }
      m = ALIAS[m] || m; if (!MOODS.includes(m)) m = 'idle';
      for (const x of MOODS) this.classList.toggle(x, x === m);
      this._current = m;
      this._setMouth(MOUTH[m]);
      const eyes = this.shadowRoot.querySelector('.eyes');
      eyes.querySelector('.happy').classList.toggle('on', HAPPY_EYES.has(m));
      eyes.querySelectorAll('.eye, .pupils').forEach(e => e.style.opacity = HAPPY_EYES.has(m) ? 0 : 1);
      this.shadowRoot.querySelector('.brows').style.opacity = HAPPY_EYES.has(m) ? 0 : 1;
      // разовые настроения сами возвращаются к покою
      clearTimeout(this._moodTimer);
      const once = { yay: 1800, wave: 2400, surprised: 1600, angry: 1800 }[m];
      if (once) this._moodTimer = setTimeout(() => { if (this._current === m) this.mood('idle'); }, once);
    }
    _setMouth(kind) {
      this.shadowRoot.querySelectorAll('.mouth .m').forEach(e => e.classList.toggle('on', e.classList.contains(kind)));
    }
    _scheduleBlink() {
      clearTimeout(this._blinkTimer);
      this._blinkTimer = setTimeout(() => {
        const eyes = this.shadowRoot.querySelector('.eyes');
        eyes.classList.add('blink'); setTimeout(() => eyes.classList.remove('blink'), 170);
        if (Math.random() < .25) setTimeout(() => { eyes.classList.add('blink'); setTimeout(() => eyes.classList.remove('blink'), 170); }, 260);
        this._scheduleBlink();
      }, 2600 + Math.random() * 3200);
    }
    _glance() {
      clearTimeout(this._glanceTimer);
      this._glanceTimer = setTimeout(() => {
        if (!this._pointerNear && this._current === 'idle') {
          const x = (Math.random() * 5 - 2.5).toFixed(1), y = (Math.random() * 3 - 1.5).toFixed(1);
          this._pupil(x, y); setTimeout(() => this._pupil(0, 0), 900 + Math.random() * 900);
        }
        this._glance();
      }, 2500 + Math.random() * 3500);
    }
    _pupil(x, y) {
      if (!['idle', 'wave', 'shy'].includes(this._current) && !(x === 0 && y === 0)) return;
      this.shadowRoot.querySelector('.pupils').style.transform = `translate(${x}px,${y}px)`;
    }
    _follow(e) {
      if (this._current !== 'idle' && this._current !== 'wave') return;
      const r = this.getBoundingClientRect(); if (!r.width) return;
      const cx = r.left + r.width / 2, cy = r.top + r.height * .45;
      const dx = e.clientX - cx, dy = e.clientY - cy, d = Math.hypot(dx, dy);
      this._pointerNear = d < r.width * 3;
      if (!this._pointerNear) { this._pupil(0, 0); return; }
      const k = Math.min(1, d / (r.width * 1.5));
      this._pupil((dx / d * 3 * k).toFixed(2), (dy / d * 2.4 * k).toFixed(2));
    }
    _talking(on) {
      clearInterval(this._talkTimer);
      if (!on) { this._setMouth(MOUTH[this._current]); return; }
      let i = 0;
      this._talkTimer = setInterval(() => { this._setMouth(TALK[i++ % TALK.length]); }, 110 + Math.random() * 40);
    }
    /* ---------- публичный API ---------- */
    mood(m) { this.setAttribute('mood', m); return this; }
    say(text, opts = {}) {
      const b = this._bubble; clearTimeout(this._sayTimer);
      b.classList.toggle('left', !!opts.left);
      b.innerHTML = ''; b.classList.add('on');
      const cur = document.createElement('span'); cur.className = 'cur';
      const span = document.createElement('span'); b.append(span, cur);
      let i = 0; const speed = opts.speed ?? 28;
      const tick = () => {
        if (i < text.length) { span.textContent = text.slice(0, ++i); this._sayTimer = setTimeout(tick, speed); }
        else { cur.remove(); this._sayTimer = setTimeout(() => b.classList.remove('on'), opts.ms ?? Math.max(2200, text.length * 70)); }
      };
      tick(); return this;
    }
    hush() { clearTimeout(this._sayTimer); this._bubble.classList.remove('on'); return this; }
    react(kind, opts = {}) {
      const r = REACT[kind]; if (!r) return this;
      this.mood(r.mood);
      const phrase = opts.text || r.say[Math.floor(Math.random() * r.say.length)];
      if (opts.bubble !== false) this.say(phrase, opts);
      if (opts.voice) this.speak(phrase, opts.profile, { bubble: false });
      return this;
    }
    speak(text, profile, opts = {}) {
      if (!('speechSynthesis' in window)) return this;
      const P = typeof profile === 'string' ? Myslik.profiles[profile] : (profile || Myslik.profiles.boy);
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(Myslik.clean(text));
      u.lang = 'ru-RU'; u.rate = P.rate; u.pitch = P.pitch; u.volume = 1;
      const v = Myslik.pick(P); if (v) u.voice = v;
      u.onstart = () => this.setAttribute('talking', '');
      u.onend = u.onerror = () => this.removeAttribute('talking');
      if (opts.bubble !== false) this.say(text, opts);
      window.speechSynthesis.speak(u);
      return this;
    }
  }

  const Myslik = {
    MOODS, REACT,
    profiles: {
      boy:    { label: 'Мыслик для мальчика', prefer: ['Pavel', 'Dmitry', 'Yuri', 'male', 'Google русский'], gender: 'male',   pitch: 1.25, rate: 1.0 },
      girl:   { label: 'Мыслик для девочки',  prefer: ['Milena', 'Irina', 'Svetlana', 'Katya', 'Google русский'], gender: 'female', pitch: 1.2, rate: 1.02 },
      parent: { label: 'Мыслик для родителя', prefer: ['Irina', 'Svetlana', 'Milena', 'Pavel', 'Google русский'], gender: 'any',  pitch: 1.0, rate: 0.96 },
    },
    voices() {
      return (window.speechSynthesis?.getVoices() || []).filter(v => /^ru/i.test(v.lang));
    },
    pick(P) {
      const vs = Myslik.voices(); if (!vs.length) return null;
      if (P.voiceURI) { const f = vs.find(v => v.voiceURI === P.voiceURI || v.name === P.voiceURI); if (f) return f; }
      for (const name of P.prefer || []) { const f = vs.find(v => v.name.toLowerCase().includes(name.toLowerCase())); if (f) return f; }
      const nat = vs.find(v => /natural|neural|premium|enhanced/i.test(v.name)); if (nat) return nat;
      return vs[0];
    },
    clean(t) {
      return String(t).replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu, '').replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
    },
  };
  window.Myslik = Myslik;
  if (!customElements.get('myslik-face')) customElements.define('myslik-face', MyslikFace);
  if (window.speechSynthesis) window.speechSynthesis.onvoiceschanged = () => { document.dispatchEvent(new Event('myslik-voices')); };
})();
