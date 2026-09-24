/* Персонажи Смекай, версия 3: Мыслик растёт с 1 по 8 класс и в 9 становится Львом.
 *
 * Подключение:  <script src="assets/myslik.js"></script>
 *               <myslik-face age="3" size="240"></myslik-face>       второклассник-третьеклассник
 *               <myslik-face age="8"></myslik-face>                  восьмиклассник
 *               <myslik-face age="10"></myslik-face>                 Лев (любой возраст от 9)
 *               <myslik-face who="lev"></myslik-face>                то же, что age="10"
 *               <myslik-face float age="5"></myslik-face>            плавающий помощник, можно таскать
 *
 * Возраст меняет пропорции плавно: у младшего круглое тело, большие глаза низко, щёки, короткие руки,
 * большая лампа. К восьмому классу тело вытягивается, глаза выше и уже, брови прямее, лампа меньше,
 * а свет вокруг неё теплеет, намекая на будущую гриву. С девятого класса это Лев: грива вместо лампы,
 * уши, золотые глаза, усмешка. Лев тоже взрослеет к одиннадцатому.
 *
 * Настроения: idle, think, yay, party, sad, angry, surprised, sleepy, wave, love, shy
 * API:  el.mood('yay')  el.say('Текст')  el.speak('Текст','girl')  el.react('correct')
 *       el.grow(11, 4000)   вырастить до класса за время, с превращением в Льва на границе
 *       el.age              текущий возраст числом
 * События: myslik-tap {zone, kind}, myslik-grown {age}, myslik-help (кнопка «?» у атрибута help)
 */
(function () {
  const CSS = `
:host{display:inline-block;position:relative;line-height:0;touch-action:none;user-select:none;-webkit-user-select:none;--sun:#FFC933;--ink:#1B1F3B}
:host([hidden]){display:none}
:host([float]){position:fixed;z-index:9000;width:150px;height:150px;cursor:grab;filter:drop-shadow(0 10px 18px rgba(27,31,59,.22))}
:host([float][dragging]){cursor:grabbing;transition:none!important}
@media(max-width:1024px){:host([float]){width:128px;height:128px}}
@media(max-width:640px){:host([float]){width:106px;height:106px}}
.help{display:none;position:absolute;right:4%;top:18%;width:30px;height:30px;border-radius:50%;border:2px solid #fff;background:var(--ink);color:#fff;
  font:800 16px/26px -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;text-align:center;cursor:pointer;box-shadow:0 4px 10px rgba(27,31,59,.3);padding:0;z-index:3}
:host([help]) .help{display:block}
.help:hover{background:#2A3160}
.hint{display:none}
:host([float]) .hint{display:block;position:absolute;left:50%;bottom:-6px;transform:translateX(-50%);font:600 11px/1 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
  color:#fff;background:var(--ink);padding:4px 8px;border-radius:999px;white-space:nowrap;opacity:0;transition:opacity .3s;pointer-events:none}
:host([float]) .hint.on{opacity:.92}
.stage{position:relative;width:100%;height:100%}
svg{width:100%;height:100%;overflow:visible;display:block}
.rig{transform-box:fill-box;transform-origin:50% 100%;animation:sway 6.5s ease-in-out infinite}
.body{transform-box:fill-box;transform-origin:50% 100%;animation:breathe 4s ease-in-out infinite}
.shadow{transform-box:fill-box;transform-origin:center;animation:shadow 4s ease-in-out infinite}
.lid{transform-box:fill-box;transform-origin:50% 0;transform:scaleY(0)}
.eyes.blink .lid{animation:lid .3s ease-in-out}
.pupils{transition:transform .28s ease}
.brow{transform-box:fill-box;transform-origin:center;transition:transform .3s ease,opacity .2s}
.m{opacity:0;transition:opacity .1s}.m.on{opacity:1}
.arm{transform-box:fill-box;transform-origin:50% 0;transition:transform .4s cubic-bezier(.2,.8,.3,1.2)}
.glow{fill:var(--sun);opacity:.14;transform-box:fill-box;transform-origin:center;animation:idleglow 5s ease-in-out infinite}
.halo{transform-box:fill-box;transform-origin:center;animation:idleglow 5s ease-in-out infinite}
.rays{opacity:0;transform-box:fill-box;transform-origin:center;transition:opacity .25s}
.bulb{transition:fill .3s}
.fil{transition:opacity .3s;opacity:.35}
.mane{transform-box:fill-box;transform-origin:center;animation:maneidle 6s ease-in-out infinite}
.sparks,.hearts,.tears,.steam,.zzz,.drop,.wow{opacity:0;transition:opacity .25s}
.spark{transform-box:fill-box;transform-origin:center}
.cheek{transition:opacity .3s}
.zone{cursor:pointer}
:host(.morph-out) .lamp{animation:burst .7s ease-in forwards}
:host(.morph-out) .body,:host(.morph-out) .arm{animation:fadeout .7s ease-in forwards}
:host(.morph-in) .mane{animation:manepop .8s cubic-bezier(.2,.9,.3,1.3)}
:host(.morph-in) .body,:host(.morph-in) .arm,:host(.morph-in) .ears{animation:fadein .6s ease-out}
/* --- настроения --- */
:host(.think) .pupils{transform:translate(1.6px,-2.4px)}
:host(.think) .brow.l{transform:translate(0,-1.6px) rotate(-7deg)}
:host(.think) .brow.r{transform:translate(0,.8px) rotate(5deg)}
:host(.think) .arm.r{transform:rotate(-92deg) translate(2px,0)}
:host(.think) .drop{opacity:1;animation:drop 1.8s ease-in infinite}
:host(.think) .bulb{fill:url(#gBulbOn)}:host(.think) .fil{opacity:.9}
:host(.think) .glow{animation:thinkglow 1.2s ease-in-out infinite}
:host(.think) .mane{animation:manethink 1.2s ease-in-out infinite}
:host(.yay) .rig{animation:hop .6s ease}
:host(.yay) .body{animation:squash .6s ease}
:host(.yay) .arm.l{transform:rotate(38deg)}:host(.yay) .arm.r{transform:rotate(-38deg)}
:host(.yay) .bulb,:host(.party) .bulb{fill:url(#gBulbOn)}:host(.yay) .fil,:host(.party) .fil{opacity:1}
:host(.yay) .glow,:host(.party) .glow{animation:none;opacity:.6;transform:scale(1.3)}
:host(.yay) .rays,:host(.party) .rays{opacity:1;animation:spin 4s linear infinite}
:host(.yay) .sparks,:host(.party) .sparks{opacity:1}
:host(.yay) .spark,:host(.party) .spark{animation:tw .9s ease-in-out infinite}
:host(.yay) .mane,:host(.party) .mane{animation:maneyay .9s ease-in-out infinite}
:host(.yay) .mane .glow,:host(.party) .mane .glow,:host(.surprised) .mane .glow{transform:scale(1.08);opacity:.35}
:host(.party) .rig{animation:bounce 1.1s ease-in-out infinite}
:host(.party) .arm.l{animation:waveL 1.1s ease-in-out infinite}
:host(.party) .arm.r{animation:wave 1.1s ease-in-out infinite reverse}
:host(.sad) .rig{animation:slump .6s ease forwards}
:host(.sad) .brow.l{transform:translate(1px,-1px) rotate(12deg)}
:host(.sad) .brow.r{transform:translate(-1px,-1px) rotate(-12deg)}
:host(.sad) .pupils{transform:translate(0,1.6px)}
:host(.sad) .tears{opacity:1}:host(.sad) .tear{animation:tear 1.5s ease-in infinite}:host(.sad) .tear.b{animation-delay:.5s}
:host(.sad) .bulb{fill:url(#gBulbOff)}:host(.sad) .glow{animation:none;opacity:0}:host(.sad) .fil{opacity:.1}
:host(.sad) .mane{animation:none;transform:scale(.96);opacity:.85}
:host(.angry) .rig{animation:shake .38s ease-in-out 2}
:host(.angry) .brow.l{transform:translate(1.6px,2.6px) rotate(-20deg)}
:host(.angry) .brow.r{transform:translate(-1.6px,2.6px) rotate(20deg)}
:host(.angry) .cheek{opacity:.75}
:host(.angry) .steam{opacity:1}:host(.angry) .puff{animation:puff 1.2s ease-out infinite}:host(.angry) .puff.b{animation-delay:.4s}:host(.angry) .puff.c{animation-delay:.8s}
:host(.angry) .bulb{fill:#FF9A76}:host(.angry) .glow{fill:#FF8A65;animation:thinkglow .55s ease-in-out infinite}
:host(.surprised) .rig{animation:startle .45s ease}
:host(.surprised) .eye{transform-box:fill-box;transform-origin:center;transform:scale(1.16)}
:host(.surprised) .brow.l,:host(.surprised) .brow.r{transform:translate(0,-3.2px)}
:host(.surprised) .wow{opacity:1;animation:wow .5s ease}
:host(.surprised) .glow{animation:none;opacity:.5;transform:scale(1.2)}
:host(.sleepy) .rig{animation:sway 7.5s ease-in-out infinite}
:host(.sleepy) .eyes .eye,:host(.sleepy) .eyes .pupils{opacity:0!important}
:host(.sleepy) .brow.l,:host(.sleepy) .brow.r{transform:translate(0,1.8px)}
:host(.sleepy) .zzz{opacity:1}:host(.sleepy) .z{animation:zz 2.6s ease-out infinite}:host(.sleepy) .z.b{animation-delay:.9s}:host(.sleepy) .z.c{animation-delay:1.8s}
:host(.sleepy) .bulb{fill:url(#gBulbOff)}:host(.sleepy) .glow{animation:none;opacity:0}:host(.sleepy) .fil{opacity:.1}
:host(.wave) .arm.r{animation:wave .55s ease-in-out 4}
:host(.wave) .brow.l,:host(.wave) .brow.r{transform:translate(0,-1.4px)}
:host(.love) .hearts{opacity:1}:host(.love) .heart{animation:float 2.2s ease-out infinite}:host(.love) .heart.b{animation-delay:.7s}:host(.love) .heart.c{animation-delay:1.4s}
:host(.love) .cheek{opacity:.8}
:host(.love) .bulb{fill:#FFB0BE}:host(.love) .glow{fill:#FF8FA3;opacity:.4;animation:none;transform:scale(1.2)}
:host(.shy) .cheek{opacity:.9}
:host(.shy) .pupils{transform:translate(-1.8px,1.6px)}
:host(.shy) .rig{animation:sway 3.2s ease-in-out infinite}
:host(.shy) .arm.l{transform:rotate(-28deg)}
/* --- облачко --- */
.bubble{position:absolute;left:74%;bottom:80%;min-width:130px;max-width:min(300px,68vw);background:#fff;color:var(--ink);
  border:1.5px solid rgba(27,31,59,.22);border-radius:16px;padding:10px 14px;font:500 15px/1.4 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
  box-shadow:0 10px 28px rgba(27,31,59,.16);opacity:0;transform:translateY(8px) scale(0);transform-origin:0 100%;
  transition:opacity .22s,transform .22s cubic-bezier(.3,1.4,.6,1);pointer-events:none;z-index:2;white-space:pre-wrap;text-align:left}
.bubble::after{content:"";position:absolute;left:14px;bottom:-9px;width:14px;height:14px;background:#fff;
  border-left:1.5px solid rgba(27,31,59,.22);border-bottom:1.5px solid rgba(27,31,59,.22);transform:rotate(-45deg);border-radius:0 0 0 3px}
.bubble.on{opacity:1;transform:translateY(0) scale(1)}
.bubble.left{left:auto;right:74%;transform-origin:100% 100%}
.bubble.left::after{left:auto;right:14px;transform:rotate(-135deg)}
.bubble.top{bottom:92%;min-width:0;transform-origin:50% 100%}
.bubble.top::after{left:var(--tail,50%)}
.bubble.below{bottom:auto;top:96%;transform-origin:0 0}
.bubble.below::after{bottom:auto;top:-9px;transform:rotate(135deg)}
.bubble.below.left::after{transform:rotate(45deg)}
.bubble .cur{display:inline-block;width:2px;height:1em;background:var(--ink);vertical-align:-2px;margin-left:1px;animation:cur .8s step-end infinite}
/* --- ключевые кадры --- */
@keyframes sway{0%,100%{transform:rotate(-1deg)}50%{transform:rotate(1deg)}}
@keyframes breathe{0%,100%{transform:scale(1,1)}50%{transform:scale(1.008,1.022)}}
@keyframes shadow{0%,100%{transform:scale(1)}50%{transform:scale(1.04)}}
@keyframes lid{0%{transform:scaleY(0)}32%{transform:scaleY(1)}52%{transform:scaleY(1)}100%{transform:scaleY(0)}}
@keyframes idleglow{0%,100%{opacity:.12;transform:scale(1)}50%{opacity:.3;transform:scale(1.07)}}
@keyframes thinkglow{0%,100%{opacity:.2;transform:scale(1)}50%{opacity:.7;transform:scale(1.22)}}
@keyframes maneidle{0%,100%{transform:scale(1) rotate(0)}50%{transform:scale(1.02) rotate(.6deg)}}
@keyframes manethink{0%,100%{transform:scale(1)}50%{transform:scale(1.06)}}
@keyframes maneyay{0%,100%{transform:scale(1.04) rotate(-1.5deg)}50%{transform:scale(1.1) rotate(1.5deg)}}
@keyframes manepop{0%{transform:scale(.2);opacity:0}60%{opacity:1}100%{transform:scale(1);opacity:1}}
@keyframes burst{0%{transform:scale(1);opacity:1}100%{transform:scale(3.2);opacity:0}}
@keyframes fadeout{to{opacity:0}}
@keyframes fadein{from{opacity:0}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes tw{0%,100%{transform:scale(.6) rotate(0);opacity:.4}50%{transform:scale(1.1) rotate(20deg);opacity:1}}
@keyframes hop{0%{transform:translateY(0)}30%{transform:translateY(-9px)}55%{transform:translateY(0)}75%{transform:translateY(-3px)}100%{transform:translateY(0)}}
@keyframes squash{0%{transform:scale(1,1)}18%{transform:scale(1.05,.94)}40%{transform:scale(.96,1.05)}65%{transform:scale(1.02,.98)}100%{transform:scale(1,1)}}
@keyframes bounce{0%,100%{transform:translateY(0) rotate(-2deg)}50%{transform:translateY(-6px) rotate(2deg)}}
@keyframes wave{0%,100%{transform:rotate(-60deg)}50%{transform:rotate(-118deg)}}
@keyframes waveL{0%,100%{transform:rotate(60deg)}50%{transform:rotate(118deg)}}
@keyframes slump{to{transform:translateY(3px) scale(.985)}}
@keyframes tear{0%{transform:translateY(0);opacity:0}15%{opacity:1}100%{transform:translateY(20px);opacity:0}}
@keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-2.5px) rotate(-1deg)}75%{transform:translateX(2.5px) rotate(1deg)}}
@keyframes puff{0%{transform:translateY(0) scale(.4);opacity:0}30%{opacity:.8}100%{transform:translateY(-15px) scale(1.2);opacity:0}}
@keyframes startle{0%{transform:translateY(0) scale(1)}30%{transform:translateY(-4px) scale(1.03)}100%{transform:translateY(0) scale(1)}}
@keyframes wow{0%{transform:scale(.3);opacity:0}60%{transform:scale(1.1);opacity:1}100%{transform:scale(1);opacity:1}}
@keyframes zz{0%{transform:translate(0,0) scale(.6);opacity:0}30%{opacity:1}100%{transform:translate(10px,-22px) scale(1.2);opacity:0}}
@keyframes float{0%{transform:translateY(0) scale(.5);opacity:0}25%{opacity:1}100%{transform:translateY(-28px) scale(1.05);opacity:0}}
@keyframes drop{0%{transform:translateY(0);opacity:0}20%{opacity:1}100%{transform:translateY(8px);opacity:0}}
@keyframes cur{50%{opacity:0}}
@media (prefers-reduced-motion:reduce){.rig,.body,.shadow,.glow,.mane,.halo{animation:none!important}}
`;

  const lerp = (a, b, t) => a + (b - a) * t;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const f1 = n => (+n).toFixed(1);
  const mixHex = (a, b, t) => {
    const p = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
    const A = p(a), B = p(b);
    return '#' + A.map((v, i) => Math.round(lerp(v, B[i], t)).toString(16).padStart(2, '0')).join('');
  };

  /* ---------- геометрия по возрасту ---------- */
  function params(age) {
    const lev = age >= 9;
    const t = lev ? clamp((age - 9) / 2, 0, 1) : clamp((age - 1) / 7, 0, 1);
    if (!lev) return {
      lev: false, t, scale: lerp(.84, 1.02, t),
      bodyTop: lerp(33, 25, t), bodyBot: lerp(103, 106, t), bodyRx: lerp(35.5, 29, t),
      faceCy: lerp(80, 73.5, t), faceRx: lerp(22, 18.2, t), faceRy: lerp(21, 19, t),
      eyeCy: lerp(59, 52.5, t), eyeDx: lerp(10, 11, t), eyeRx: lerp(8.4, 5.8, t), eyeRy: lerp(9.4, 6.4, t),
      pupilR: lerp(5.3, 3.5, t), irisR: lerp(5.3, 3.5, t),
      browY: lerp(46, 44.6, t), browArc: lerp(4, 1.4, t), browW: lerp(2.8, 2, t), browDx: lerp(6, 6.8, t),
      cheekRx: lerp(6, 3.4, t), cheekRy: lerp(3.8, 2.2, t), cheekOp: lerp(.6, .18, t), cheekY: lerp(73, 69.5, t),
      mouthY: lerp(77, 75, t), mouthW: lerp(10.5, 13, t), smile: lerp(7, 4, t),
      armW: lerp(8, 5.8, t), armLen: lerp(.9, 1.4, t), armY: lerp(72, 65, t),
      lampS: lerp(1.25, .9, t), stemTop: lerp(21, 22, t),
      halo: t > .55 ? (t - .55) / .45 : 0,
      c0: mixHex('#74A8FF', '#5E93FF', t), c1: mixHex('#4F8CFF', '#3E7BFA', t), c2: mixHex('#3566DC', '#2853C4', t),
      armC: mixHex('#3D72E4', '#2F63D6', t), irisC0: '#4A5AA8', irisC1: '#26306B', irisC2: '#151A3D',
      mouthKind: 'smile',
    };
    return {
      lev: true, t, scale: lerp(1.04, 1.08, t),
      bodyTop: lerp(27, 25, t), bodyBot: lerp(105, 107, t), bodyRx: lerp(30, 30.5, t),
      faceCy: lerp(74, 73.5, t), faceRx: lerp(18.5, 18.5, t), faceRy: lerp(19, 19.5, t),
      eyeCy: lerp(53.5, 53, t), eyeDx: lerp(10.8, 11, t), eyeRx: lerp(6.2, 6, t), eyeRy: lerp(6.4, 6.1, t),
      pupilR: 3.6, irisR: 3.8,
      browY: lerp(45.5, 45.8, t), browArc: lerp(1.5, 1, t), browW: lerp(2.2, 2.4, t), browDx: 7,
      cheekRx: 3.4, cheekRy: 2.2, cheekOp: lerp(.22, .14, t), cheekY: 70,
      mouthY: 75.5, mouthW: 13, smile: 3.6,
      armW: lerp(6.2, 6.4, t), armLen: lerp(1.38, 1.45, t), armY: lerp(66, 65, t),
      lampS: 0, stemTop: 22, halo: 0,
      maneR: lerp(45, 49, t), maneIn: lerp(37.5, 40, t),
      c0: mixHex('#3D5BD6', '#3450C9', t), c1: mixHex('#2743A8', '#22399A', t), c2: mixHex('#1B2C70', '#172562', t),
      armC: mixHex('#22398F', '#1D3180', t), irisC0: '#C9962B', irisC1: '#7A5A12', irisC2: '#3A2A06',
      mouthKind: 'smirk',
    };
  }

  function manePath(cx, cy, rOut, rIn, n, phase) {
    let d = '';
    for (let i = 0; i < n; i++) {
      const a0 = phase + (i / n) * Math.PI * 2, a1 = phase + ((i + .5) / n) * Math.PI * 2, a2 = phase + ((i + 1) / n) * Math.PI * 2;
      const x0 = cx + rIn * Math.cos(a0), y0 = cy + rIn * Math.sin(a0);
      const xm = cx + rOut * 1.08 * Math.cos(a1), ym = cy + rOut * 1.08 * Math.sin(a1);
      const x2 = cx + rIn * Math.cos(a2), y2 = cy + rIn * Math.sin(a2);
      d += (i ? '' : `M${x0.toFixed(1)} ${y0.toFixed(1)} `) + `Q${xm.toFixed(1)} ${ym.toFixed(1)} ${x2.toFixed(1)} ${y2.toFixed(1)} `;
    }
    return d + 'Z';
  }

  function defs(p) {
    return `<defs>
  <radialGradient id="gBody" cx="36%" cy="26%" r="80%"><stop offset="0" stop-color="${p.c0}"/><stop offset=".58" stop-color="${p.c1}"/><stop offset="1" stop-color="${p.c2}"/></radialGradient>
  <radialGradient id="gFace" cx="50%" cy="38%" r="72%"><stop offset="0" stop-color="#FFFFFF"/><stop offset=".85" stop-color="#F1F4FB"/><stop offset="1" stop-color="#E6EAF6"/></radialGradient>
  <radialGradient id="gSclera" cx="50%" cy="65%" r="70%"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#E4E8F3"/></radialGradient>
  <radialGradient id="gIris" cx="40%" cy="36%" r="66%"><stop offset="0" stop-color="${p.irisC0}"/><stop offset=".55" stop-color="${p.irisC1}"/><stop offset="1" stop-color="${p.irisC2}"/></radialGradient>
  <radialGradient id="gBulb" cx="42%" cy="34%" r="66%"><stop offset="0" stop-color="#FFFBEA"/><stop offset=".7" stop-color="#F6E7B1"/><stop offset="1" stop-color="#E5CF86"/></radialGradient>
  <radialGradient id="gBulbOn" cx="42%" cy="34%" r="66%"><stop offset="0" stop-color="#FFFDF0"/><stop offset=".6" stop-color="#FFE270"/><stop offset="1" stop-color="#F5B91E"/></radialGradient>
  <radialGradient id="gBulbOff" cx="42%" cy="34%" r="66%"><stop offset="0" stop-color="#E9ECF4"/><stop offset="1" stop-color="#C3C8D8"/></radialGradient>
  <linearGradient id="gMane" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFD966"/><stop offset="1" stop-color="#E9A825"/></linearGradient>
  <linearGradient id="gMetal" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#C4CBDF"/><stop offset=".5" stop-color="#8E96B3"/><stop offset="1" stop-color="#6E7794"/></linearGradient>
  <radialGradient id="gHalo" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#FFD966" stop-opacity=".55"/><stop offset="1" stop-color="#FFD966" stop-opacity="0"/></radialGradient>
  <filter id="soft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="2.2"/></filter>
  <filter id="softer" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="4"/></filter>
</defs>`;
  }

  function lampMyslik(p) {
    const s = p.lampS, cx = 50, cy = 12;
    return `
<g class="lamp zone" data-zone="lamp">
  ${p.halo ? `<circle class="halo" cx="50" cy="50" r="46" fill="url(#gHalo)" opacity="${(p.halo * .9).toFixed(2)}"/>` : ''}
  <g class="sparks" fill="var(--sun)">
    <path class="spark" d="M4 30l1.8 4.6 4.6 1.8-4.6 1.8-1.8 4.6-1.8-4.6-4.6-1.8 4.6-1.8z"/>
    <path class="spark" d="M94 42l1.4 3.6 3.6 1.4-3.6 1.4-1.4 3.6-1.4-3.6-3.6-1.4 3.6-1.4z"/>
    <path class="spark" d="M90 6l1.1 2.8 2.8 1.1-2.8 1.1-1.1 2.8-1.1-2.8-2.8-1.1 2.8-1.1z"/>
  </g>
  <g transform="translate(${cx} ${cy}) scale(${s}) translate(${-cx} ${-cy})">
    <g class="rays" stroke="var(--sun)" stroke-width="2.2" stroke-linecap="round">
      <line x1="50" y1="-7" x2="50" y2="-2"/><line x1="36" y1="-1" x2="39.5" y2="2.5"/><line x1="64" y1="-1" x2="60.5" y2="2.5"/>
      <line x1="30" y1="12" x2="35.5" y2="12"/><line x1="70" y1="12" x2="64.5" y2="12"/>
    </g>
    <circle class="glow" cx="50" cy="12" r="16" filter="url(#soft)"/>
    <path d="M48.4 ${p.stemTop + 8} L48.4 23.4 M51.6 ${p.stemTop + 8} L51.6 23.4" stroke="url(#gMetal)" stroke-width="1.8" stroke-linecap="round"/>
    <circle class="bulb" cx="50" cy="12" r="8.2" fill="url(#gBulb)"/>
    <circle cx="50" cy="12" r="8.2" fill="none" stroke="#fff" stroke-width=".6" opacity=".5"/>
    <path class="fil" d="M46.5 15 q1.2 -6 3.5 -2 q2.3 -4 3.5 2" stroke="#D9A21B" stroke-width="1" fill="none" stroke-linecap="round"/>
    <path d="M45.2 9.6 q1.6 -4 5.4 -3.8" stroke="#fff" stroke-width="1.7" fill="none" stroke-linecap="round" opacity=".9"/>
    <ellipse cx="53.6" cy="16" rx="1.4" ry="2.2" fill="#fff" opacity=".35" transform="rotate(-30 53.6 16)"/>
    <rect x="45.2" y="19.4" width="9.6" height="4.4" rx="1.5" fill="url(#gMetal)"/>
    <path d="M45.6 21 h8.8 M45.6 22.4 h8.8" stroke="#fff" stroke-width=".5" opacity=".35"/>
  </g>
  <g class="steam" fill="#B9C0D6"><circle class="puff a" cx="38" cy="26" r="2.8"/><circle class="puff b" cx="62" cy="24" r="3.3"/><circle class="puff c" cx="50" cy="-2" r="2.4"/></g>
  <g class="zzz" fill="var(--ink)" font-family="Arial,sans-serif" font-weight="700"><text class="z a" x="70" y="30" font-size="8">z</text><text class="z b" x="74" y="24" font-size="10">z</text><text class="z c" x="79" y="18" font-size="12">Z</text></g>
  <g class="hearts" fill="#FF6B81"><path class="heart a" d="M22 40c-3-4-9-1-6 4l6 6 6-6c3-5-3-8-6-4z"/><path class="heart b" d="M78 34c-2.4-3.2-7.2-.8-4.8 3.2l4.8 4.8 4.8-4.8c2.4-4-2.4-6.4-4.8-3.2z"/><path class="heart c" d="M50 -4c-2-2.6-6-.6-4 2.6l4 4 4-4c2-3.2-2-5.2-4-2.6z"/></g>
  <g class="wow"><text x="80" y="22" font-size="11" font-weight="800" fill="var(--sun)" font-family="Arial,sans-serif">!</text></g>
</g>`;
  }

  function maneLev(p) {
    return `
<g class="lamp zone" data-zone="lamp">
  <g class="sparks" fill="var(--sun)">
    <path class="spark" d="M0 36l1.8 4.6 4.6 1.8-4.6 1.8-1.8 4.6-1.8-4.6-4.6-1.8 4.6-1.8z"/>
    <path class="spark" d="M98 50l1.4 3.6 3.6 1.4-3.6 1.4-1.4 3.6-1.4-3.6-3.6-1.4 3.6-1.4z"/>
    <path class="spark" d="M92 4l1.1 2.8 2.8 1.1-2.8 1.1-1.1 2.8-1.1-2.8-2.8-1.1 2.8-1.1z"/>
  </g>
  <g class="mane">
    <circle class="glow" cx="50" cy="54" r="30" filter="url(#softer)"/>
    <path d="${manePath(50, 55, p.maneR + 1, p.maneIn, 18, -Math.PI / 2)}" fill="#C98A14" opacity=".55" filter="url(#soft)"/>
    <path d="${manePath(50, 55, p.maneR, p.maneIn, 18, -Math.PI / 2)}" fill="url(#gMane)"/>
    <path d="${manePath(50, 55, p.maneR - 6, p.maneIn - 4, 18, -Math.PI / 2 + .17)}" fill="#FFE59A" opacity=".5"/>
    <path d="${manePath(50, 55, p.maneIn - 3, p.maneIn - 7, 18, -Math.PI / 2)}" fill="#E9A825" opacity=".35"/>
  </g>
  <g class="rays" stroke="var(--sun)" stroke-width="2" stroke-linecap="round"><line x1="50" y1="-2" x2="50" y2="3"/><line x1="22" y1="12" x2="26" y2="15"/><line x1="78" y1="12" x2="74" y2="15"/></g>
  <g class="ears"><ellipse cx="29" cy="31" rx="6.4" ry="6.8" fill="url(#gBody)"/><ellipse cx="29" cy="31.6" rx="3.4" ry="3.8" fill="#8EA6FF" opacity=".5"/>
     <ellipse cx="71" cy="31" rx="6.4" ry="6.8" fill="url(#gBody)"/><ellipse cx="71" cy="31.6" rx="3.4" ry="3.8" fill="#8EA6FF" opacity=".5"/></g>
  <circle class="bulb" cx="50" cy="12" r="0" fill="none"/>
  <g class="steam" fill="#B9C0D6"><circle class="puff a" cx="36" cy="18" r="2.8"/><circle class="puff b" cx="64" cy="16" r="3.3"/><circle class="puff c" cx="50" cy="-2" r="2.4"/></g>
  <g class="zzz" fill="var(--sun)" font-family="Arial,sans-serif" font-weight="700"><text class="z a" x="78" y="26" font-size="8">z</text><text class="z b" x="82" y="20" font-size="10">z</text><text class="z c" x="87" y="14" font-size="12">Z</text></g>
  <g class="hearts" fill="#FF6B81"><path class="heart a" d="M14 46c-3-4-9-1-6 4l6 6 6-6c3-5-3-8-6-4z"/><path class="heart b" d="M88 40c-2.4-3.2-7.2-.8-4.8 3.2l4.8 4.8 4.8-4.8c2.4-4-2.4-6.4-4.8-3.2z"/><path class="heart c" d="M50 -6c-2-2.6-6-.6-4 2.6l4 4 4-4c2-3.2-2-5.2-4-2.6z"/></g>
  <g class="wow"><text x="86" y="30" font-size="11" font-weight="800" fill="var(--sun)" font-family="Arial,sans-serif">!</text></g>
</g>`;
  }

  function bodySvg(p) {
    const top = p.bodyTop, bot = p.bodyBot, rx = p.bodyRx, midY = (top + bot) / 2;
    const bodyPath = `M${f1(50 - rx)} ${f1(midY)} C${f1(50 - rx)} ${f1(top + 12)} ${f1(50 - rx * .55)} ${f1(top)} 50 ${f1(top)} C${f1(50 + rx * .55)} ${f1(top)} ${f1(50 + rx)} ${f1(top + 12)} ${f1(50 + rx)} ${f1(midY)} C${f1(50 + rx)} ${f1(bot - 14)} ${f1(50 + rx * .56)} ${f1(bot)} 50 ${f1(bot)} C${f1(50 - rx * .56)} ${f1(bot)} ${f1(50 - rx)} ${f1(bot - 14)} ${f1(50 - rx)} ${f1(midY)}Z`;
    const ex1 = 50 - p.eyeDx, ex2 = 50 + p.eyeDx, ey = p.eyeCy;
    const bl = `M${f1(ex1 - p.browDx)} ${f1(p.browY)} Q${f1(ex1)} ${f1(p.browY - p.browArc)} ${f1(ex1 + p.browDx)} ${f1(p.browY)}`;
    const br = `M${f1(ex2 - p.browDx)} ${f1(p.browY)} Q${f1(ex2)} ${f1(p.browY - p.browArc)} ${f1(ex2 + p.browDx)} ${f1(p.browY)}`;
    const mw = p.mouthW / 2, my = p.mouthY;
    const eye = (cx) => `
      <g class="eye"><ellipse cx="${f1(cx)}" cy="${f1(ey)}" rx="${f1(p.eyeRx)}" ry="${f1(p.eyeRy)}" fill="url(#gSclera)"/>
        <path d="M${f1(cx - p.eyeRx)} ${f1(ey)} A${f1(p.eyeRx)} ${f1(p.eyeRy)} 0 0 1 ${f1(cx + p.eyeRx)} ${f1(ey)}" fill="#1B1F3B" opacity=".08"/>
        <ellipse class="lid" cx="${f1(cx)}" cy="${f1(ey)}" rx="${f1(p.eyeRx + .7)}" ry="${f1(p.eyeRy + .7)}" fill="url(#gBody)"/></g>`;
    const armL = `M${f1(50 - rx + 13)} ${f1(p.armY)} Q${f1(50 - rx - 2)} ${f1(p.armY + 4)} ${f1(50 - rx - 2 + 1)} ${f1(p.armY + 14 * p.armLen)}`;
    const armR = `M${f1(50 + rx - 13)} ${f1(p.armY)} Q${f1(50 + rx + 2)} ${f1(p.armY + 4)} ${f1(50 + rx + 2 - 1)} ${f1(p.armY + 14 * p.armLen)}`;
    return `
<g class="arm l zone" data-zone="arm"><path d="${armL}" stroke="${p.armC}" stroke-width="${f1(p.armW)}" fill="none" stroke-linecap="round"/><path d="${armL}" stroke="#fff" stroke-width="${f1(p.armW * .28)}" fill="none" stroke-linecap="round" opacity=".14" transform="translate(-1 -1)"/></g>
<g class="arm r zone" data-zone="arm"><path d="${armR}" stroke="${p.armC}" stroke-width="${f1(p.armW)}" fill="none" stroke-linecap="round"/><path d="${armR}" stroke="#fff" stroke-width="${f1(p.armW * .28)}" fill="none" stroke-linecap="round" opacity=".14" transform="translate(-1 -1)"/></g>
<g class="body">
  <path class="zone" data-zone="body" d="${bodyPath}" fill="url(#gBody)"/>
  <ellipse cx="50" cy="${f1(bot - 9)}" rx="${f1(rx * .8)}" ry="7" fill="#0D1440" opacity=".22" filter="url(#softer)"/>
  <ellipse cx="${f1(50 - rx * .42)}" cy="${f1(top + 12)}" rx="${f1(rx * .26)}" ry="5" fill="#fff" opacity=".2" filter="url(#soft)" transform="rotate(-28 ${f1(50 - rx * .42)} ${f1(top + 12)})"/>
  <path d="M${f1(50 - rx * .78)} ${f1(midY - 6)} C${f1(50 - rx * .78)} ${f1(top + 10)} ${f1(50 - rx * .3)} ${f1(top + 5)} 50 ${f1(top + 5)}" stroke="#fff" stroke-width="1" fill="none" opacity=".14"/>
  <ellipse class="zone" data-zone="face" cx="50" cy="${f1(p.faceCy)}" rx="${f1(p.faceRx)}" ry="${f1(p.faceRy)}" fill="url(#gFace)" opacity=".97"/>
  <g class="cheeks"><ellipse class="cheek" cx="${f1(50 - p.faceRx + 2)}" cy="${f1(p.cheekY)}" rx="${f1(p.cheekRx)}" ry="${f1(p.cheekRy)}" fill="#FF8FA3" opacity="${p.cheekOp.toFixed(2)}" filter="url(#soft)"/><ellipse class="cheek" cx="${f1(50 + p.faceRx - 2)}" cy="${f1(p.cheekY)}" rx="${f1(p.cheekRx)}" ry="${f1(p.cheekRy)}" fill="#FF8FA3" opacity="${p.cheekOp.toFixed(2)}" filter="url(#soft)"/></g>
  <g class="brows" stroke="var(--ink)" stroke-width="${f1(p.browW)}" stroke-linecap="round" fill="none"><path class="brow l" d="${bl}"/><path class="brow r" d="${br}"/></g>
  <g class="eyes zone" data-zone="eyes">
    ${eye(ex1)}${eye(ex2)}
    <g class="pupils">
      <circle cx="${f1(ex1 + .8)}" cy="${f1(ey + .8)}" r="${f1(p.irisR)}" fill="url(#gIris)"/><circle cx="${f1(ex2 + .8)}" cy="${f1(ey + .8)}" r="${f1(p.irisR)}" fill="url(#gIris)"/>
      <circle cx="${f1(ex1 + .8)}" cy="${f1(ey + .8)}" r="${f1(p.pupilR * .48)}" fill="#0E1230"/><circle cx="${f1(ex2 + .8)}" cy="${f1(ey + .8)}" r="${f1(p.pupilR * .48)}" fill="#0E1230"/>
      <circle cx="${f1(ex1 + 2.2)}" cy="${f1(ey - 1)}" r="${f1(p.pupilR * .32)}" fill="#fff"/><circle cx="${f1(ex2 + 2.2)}" cy="${f1(ey - 1)}" r="${f1(p.pupilR * .32)}" fill="#fff"/>
      <circle cx="${f1(ex1 - .6)}" cy="${f1(ey + 2.2)}" r=".6" fill="#fff" opacity=".7"/><circle cx="${f1(ex2 - .6)}" cy="${f1(ey + 2.2)}" r=".6" fill="#fff" opacity=".7"/>
    </g>
    <g class="shut m" stroke="var(--ink)" stroke-width="2.4" fill="none" stroke-linecap="round"><path d="M${f1(ex1 - p.eyeRx)} ${f1(ey)} Q${f1(ex1)} ${f1(ey + p.eyeRy * .75)} ${f1(ex1 + p.eyeRx)} ${f1(ey)}"/><path d="M${f1(ex2 - p.eyeRx)} ${f1(ey)} Q${f1(ex2)} ${f1(ey + p.eyeRy * .75)} ${f1(ex2 + p.eyeRx)} ${f1(ey)}"/><path d="M${f1(ex1 - p.eyeRx * .55)} ${f1(ey + p.eyeRy * .26)} l-1.5 2M${f1(ex1)} ${f1(ey + p.eyeRy * .375)} l0 2.3M${f1(ex1 + p.eyeRx * .55)} ${f1(ey + p.eyeRy * .26)} l1.5 2M${f1(ex2 - p.eyeRx * .55)} ${f1(ey + p.eyeRy * .26)} l-1.5 2M${f1(ex2)} ${f1(ey + p.eyeRy * .375)} l0 2.3M${f1(ex2 + p.eyeRx * .55)} ${f1(ey + p.eyeRy * .26)} l1.5 2" stroke-width="1.3"/></g>
    <g class="happy m" stroke="var(--ink)" stroke-width="2.8" fill="none" stroke-linecap="round"><path d="M${f1(ex1 - 6)} ${f1(ey + 2)} Q${f1(ex1)} ${f1(ey - 5)} ${f1(ex1 + 6)} ${f1(ey + 2)}"/><path d="M${f1(ex2 - 6)} ${f1(ey + 2)} Q${f1(ex2)} ${f1(ey - 5)} ${f1(ex2 + 6)} ${f1(ey + 2)}"/></g>
    <g class="tears" fill="#7FB7FF"><path class="tear a" d="M${f1(ex1 - 4.5)} ${f1(ey + 7)} q2.2 3.6 0 5.4 q-2.2 -1.8 0 -5.4z"/><path class="tear b" d="M${f1(ex2 + 4.5)} ${f1(ey + 7)} q2.2 3.6 0 5.4 q-2.2 -1.8 0 -5.4z"/></g>
  </g>
  <g class="mouth zone" data-zone="mouth">
    <path class="m smile" d="M${f1(50 - mw)} ${f1(my - 1)} Q50 ${f1(my + p.smile)} ${f1(50 + mw)} ${f1(my - 1)}" stroke="var(--ink)" stroke-width="2.4" fill="none" stroke-linecap="round"/>
    <g class="m grin"><path d="M${f1(50 - mw - 2)} ${f1(my - 3.5)} Q50 ${f1(my - 3.5)} ${f1(50 + mw + 2)} ${f1(my - 3.5)} Q${f1(50 + mw + 1)} ${f1(my + 8)} 50 ${f1(my + 9)} Q${f1(50 - mw - 1)} ${f1(my + 8)} ${f1(50 - mw - 2)} ${f1(my - 3.5)}Z" fill="#2A1F2E"/><path d="M${f1(50 - 5)} ${f1(my + 3.5)} Q50 ${f1(my + .5)} ${f1(50 + 5)} ${f1(my + 3.5)} Q${f1(50 + 3.5)} ${f1(my + 7.5)} 50 ${f1(my + 7.7)} Q${f1(50 - 3.5)} ${f1(my + 7.5)} ${f1(50 - 5)} ${f1(my + 3.5)}Z" fill="#FF6B81" opacity=".9"/></g>
    <g class="m open"><ellipse cx="50" cy="${f1(my + 1.5)}" rx="4.2" ry="5" fill="#2A1F2E"/><ellipse cx="50" cy="${f1(my + 4)}" rx="2.5" ry="1.6" fill="#FF6B81" opacity=".9"/></g>
    <g class="m half"><path d="M${f1(50 - mw + 1)} ${f1(my - .5)} Q50 ${f1(my + 3)} ${f1(50 + mw - 1)} ${f1(my - .5)} Q${f1(50 + mw - 2)} ${f1(my + 4)} 50 ${f1(my + 4.5)} Q${f1(50 - mw + 2)} ${f1(my + 4)} ${f1(50 - mw + 1)} ${f1(my - .5)}Z" fill="#2A1F2E"/></g>
    <path class="m flat" d="M${f1(50 - mw + 1)} ${f1(my + 1)} L${f1(50 + mw - 1)} ${f1(my + 1)}" stroke="var(--ink)" stroke-width="2.4" fill="none" stroke-linecap="round"/>
    <path class="m frown" d="M${f1(50 - mw)} ${f1(my + 3.5)} Q50 ${f1(my - 2)} ${f1(50 + mw)} ${f1(my + 3.5)}" stroke="var(--ink)" stroke-width="2.4" fill="none" stroke-linecap="round"/>
    <ellipse class="m o" cx="50" cy="${f1(my + 1.5)}" rx="3.2" ry="4.2" fill="#2A1F2E"/>
    <path class="m grit" d="M${f1(50 - mw + 1)} ${f1(my + .5)} h${f1(mw * 2 - 2)} M${f1(50 - 3.5)} ${f1(my - 1.7)} v4.4 M50 ${f1(my - 1.7)} v4.4 M${f1(50 + 3.5)} ${f1(my - 1.7)} v4.4" stroke="var(--ink)" stroke-width="2" fill="none" stroke-linecap="round"/>
    <path class="m smirk" d="M${f1(50 - mw + 1)} ${f1(my + .5)} Q50 ${f1(my + 2.5)} ${f1(50 + mw)} ${f1(my - 2)}" stroke="var(--ink)" stroke-width="2.4" fill="none" stroke-linecap="round"/>
  </g>
  <g class="drop" fill="#7FB7FF"><path d="M${f1(50 + rx - 9)} 48 q2.8 4.6 0 7 q-2.8 -2.4 0 -7z"/></g>
</g>`;
  }

  function svg(age) {
    const p = params(age);
    return `<svg viewBox="-5 -12 110 130" aria-hidden="true">${defs(p)}
<ellipse class="shadow" cx="50" cy="${f1(p.bodyBot + 6)}" rx="${f1(p.bodyRx * .78 * p.scale)}" ry="3.6" fill="#1B1F3B" opacity=".14" filter="url(#soft)"/>
<g class="rig"><g transform="translate(50 ${f1(p.bodyBot + 6)}) scale(${p.scale.toFixed(3)}) translate(-50 ${f1(-(p.bodyBot + 6))})">${p.lev ? maneLev(p) : lampMyslik(p)}${bodySvg(p)}</g></g></svg>`;
  }

  /* ---------- настроения, реплики, зоны ---------- */
  const MOODS = ['idle', 'think', 'yay', 'party', 'sad', 'angry', 'surprised', 'sleepy', 'wave', 'love', 'shy'];
  const ALIAS = { oops: 'sad', celebrate: 'party', happy: 'yay', hi: 'wave' };
  const MOUTH = { idle: 'smile', think: 'flat', yay: 'grin', party: 'grin', sad: 'frown', angry: 'grit', surprised: 'o', sleepy: 'half', wave: 'smile', love: 'grin', shy: 'smile' };
  const MOUTH_LEV = { ...MOUTH, idle: 'smirk', yay: 'half', wave: 'smirk', love: 'half' };
  const HAPPY_EYES = new Set(['yay', 'party', 'love']);
  const SHUT_EYES = new Set(['sleepy']);
  const TALK = ['open', 'half', 'smile', 'open', 'o', 'half'];

  const REACT = {
    junior: {
      hello: { mood: 'wave', say: ['Привет! Я Мыслик!', 'Привет-привет!', 'Ура, ты пришёл!'] },
      correct: { mood: 'yay', say: ['Ура, верно!', 'Правильно!', 'Вот это да!', 'Молодец!'] },
      wrong: { mood: 'sad', say: ['Ой, не то.', 'Почти! Ещё разок.', 'Не сходится. Попробуй снова.'] },
      thinking: { mood: 'think', say: ['Хм-м…', 'Думаю…', 'Так-так…'] },
      idea: { mood: 'think', say: ['Есть идея!', 'Знаю, знаю!', 'А если начать с конца?'] },
      bye: { mood: 'wave', say: ['Пока-пока!', 'До завтра!', 'Ты молодец!'] },
      streak: { mood: 'party', say: ['Три подряд! Ура!', 'Ты просто чемпион!'] },
      surprise: { mood: 'surprised', say: ['Ого!', 'Вот это да!'] },
      tired: { mood: 'sleepy', say: ['Устал? Давай отдохнём.', 'Пять минуток перерыв.'] },
      love: { mood: 'love', say: ['Ты мне нравишься!', 'Обожаю, когда получается!'] },
      angry: { mood: 'angry', say: ['Эй! Так нечестно!', 'Не списывай!'] },
      shy: { mood: 'shy', say: ['Ой!', 'Щекотно!'] },
    },
    middle: {
      hello: { mood: 'wave', say: ['Привет. Я Мыслик.', 'Здравствуй. Готов к уроку?', 'Привет. Что сегодня решаем?'] },
      correct: { mood: 'yay', say: ['Верно.', 'Точно.', 'Да, именно так.', 'Правильно.', 'С первого раза.'] },
      wrong: { mood: 'sad', say: ['Пока не то.', 'Почти, но нет.', 'Не сходится. Проверь ещё раз.', 'Попробуй иначе.'] },
      thinking: { mood: 'think', say: ['Дай подумать…', 'Так, смотрим на условие…', 'Хм…'] },
      idea: { mood: 'think', say: ['Есть идея.', 'А что, если начать с конца?', 'Знаю, с чего начать.'] },
      bye: { mood: 'wave', say: ['Пока. Заходи завтра.', 'До встречи.', 'Молодец сегодня.'] },
      streak: { mood: 'party', say: ['Три подряд.', 'Серия. Так держать.'] },
      surprise: { mood: 'surprised', say: ['Ого.', 'Ничего себе.'] },
      tired: { mood: 'sleepy', say: ['Может, перерыв?', 'Пять минут отдыха, и продолжим.'] },
      love: { mood: 'love', say: ['Люблю, когда получается.', 'Ты молодец.'] },
      angry: { mood: 'angry', say: ['Эй. Так нечестно.', 'Не списывай.'] },
      shy: { mood: 'shy', say: ['Ой.', 'Хватит.'] },
    },
    lev: {
      hello: { mood: 'wave', say: ['Привет. Я Лев.', 'Здравствуй. Начнём?', 'Привет. Что разбираем?'] },
      correct: { mood: 'yay', say: ['Верно.', 'Так и есть.', 'Точно.', 'Хорошо.'] },
      wrong: { mood: 'sad', say: ['Нет. Посмотри ещё раз.', 'Не сходится.', 'Проверь знак.'] },
      thinking: { mood: 'think', say: ['Думаю…', 'Смотрю условие…'] },
      idea: { mood: 'think', say: ['Есть ход.', 'Попробуй от обратного.'] },
      bye: { mood: 'wave', say: ['До завтра.', 'Хорошая работа.'] },
      streak: { mood: 'party', say: ['Три подряд. Держи темп.', 'Серия.'] },
      surprise: { mood: 'surprised', say: ['Неожиданно.', 'Ого.'] },
      tired: { mood: 'sleepy', say: ['Перерыв. Десять минут.', 'Отдохни, потом вернёмся.'] },
      love: { mood: 'love', say: ['Красиво решено.'] },
      angry: { mood: 'angry', say: ['Списывать не будем.'] },
      shy: { mood: 'shy', say: ['Хватит.'] },
    },
  };
  const ZONE = { lamp: ['idea', 'thinking'], eyes: ['surprise'], mouth: ['hello', 'bye'], arm: ['hello'], face: ['shy', 'love'], body: ['correct', 'streak', 'tired'] };

  class MyslikFace extends HTMLElement {
    static get observedAttributes() { return ['mood', 'size', 'class', 'talking', 'who', 'age']; }
    constructor() {
      super();
      const root = this.attachShadow({ mode: 'open' });
      const style = document.createElement('style'); style.textContent = CSS;
      this._stage = document.createElement('div'); this._stage.className = 'stage';
      this._bubble = document.createElement('div'); this._bubble.className = 'bubble';
      this._hint = document.createElement('div'); this._hint.className = 'hint'; this._hint.textContent = 'перетащи меня';
      this._help = document.createElement('button'); this._help.className = 'help'; this._help.type = 'button';
      this._help.textContent = '?'; this._help.title = 'Помощь'; this._help.setAttribute('aria-label', 'Помощь');
      this._help.addEventListener('pointerdown', e => e.stopPropagation());
      this._help.addEventListener('pointerup', e => e.stopPropagation());
      this._help.addEventListener('click', e => { e.stopPropagation(); this.dispatchEvent(new CustomEvent('myslik-help', { bubbles: true })); });
      root.append(style, this._stage);
      this._current = 'idle'; this._timers = {}; this._age = 5;
      this._build();
    }
    get age() { return this._age; }
    set age(v) { this.setAttribute('age', v); }
    get lev() { return this._age >= 9; }
    get band() { return this.lev ? 'lev' : this._age < 4 ? 'junior' : 'middle'; }
    _readAge() {
      const a = parseFloat(this.getAttribute('age'));
      if (!isNaN(a)) return clamp(a, 1, 11);
      return (this.getAttribute('who') || '').toLowerCase() === 'lev' ? 10 : 5;
    }
    _build() {
      this._age = this._readAge();
      this._stage.innerHTML = svg(this._age);
      this._stage.append(this._bubble, this._hint, this._help);
      this._stage.querySelectorAll('.zone').forEach(z => {
        z.addEventListener('pointerup', e => { if (!this._moved) { e.stopPropagation(); this._zone(z.dataset.zone); } });
      });
      this._applyFace();
    }
    connectedCallback() {
      this._applySize(); this._applyClasses(this.classList.length ? 'class' : 'mood'); this._scheduleBlink(); this._glance();
      this._followBound = this._follow.bind(this);
      window.addEventListener('pointermove', this._followBound, { passive: true });
      if (this.hasAttribute('float')) this._setupFloat();
    }
    disconnectedCallback() {
      Object.values(this._timers).forEach(t => { clearTimeout(t); clearInterval(t); });
      window.removeEventListener('pointermove', this._followBound);
      window.removeEventListener('resize', this._resizeBound);
    }
    attributeChangedCallback(n, o, v) {
      if (this._syncing) return;
      if (n === 'size') this._applySize();
      if (n === 'mood') this._applyClasses('mood');
      if (n === 'class') this._applyClasses('class');
      if (n === 'talking') this._talking(this.hasAttribute('talking'));
      if ((n === 'who' || n === 'age') && o !== v) { this._build(); this._applyClasses('mood'); }
    }
    _applySize() {
      const s = this.getAttribute('size');
      if (s && !this.hasAttribute('float')) { this.style.width = s + 'px'; this.style.height = s + 'px'; }
    }
    _applyClasses(source) {
      let m = this.getAttribute('mood') || 'idle';
      if (source === 'class') for (const c of this.classList) { if (MOODS.includes(c) || ALIAS[c]) m = ALIAS[c] || c; }
      m = ALIAS[m] || m; if (!MOODS.includes(m)) m = 'idle';
      this._syncing = true;
      for (const x of MOODS) this.classList.toggle(x, x === m);
      if (this.getAttribute('mood') !== m) this.setAttribute('mood', m);
      this._syncing = false;
      this._current = m;
      this._applyFace();
      clearTimeout(this._timers.mood);
      const once = { yay: 1700, wave: 2300, surprised: 1500, angry: 1700, shy: 1800 }[m];
      if (once) this._timers.mood = setTimeout(() => { if (this._current === m) this.mood('idle'); }, once);
    }
    _applyFace() {
      const m = this._current;
      this._setMouth((this.lev ? MOUTH_LEV : MOUTH)[m]);
      const eyes = this._stage.querySelector('.eyes'); if (!eyes) return;
      eyes.querySelector('.happy').classList.toggle('on', HAPPY_EYES.has(m));
      eyes.querySelector('.shut').classList.toggle('on', SHUT_EYES.has(m));
      eyes.querySelectorAll('.eye, .pupils').forEach(e => e.style.opacity = HAPPY_EYES.has(m) || SHUT_EYES.has(m) ? 0 : 1);
      this._stage.querySelector('.brows').style.opacity = HAPPY_EYES.has(m) ? 0 : 1;
    }
    _setMouth(kind) { this._stage.querySelectorAll('.mouth .m').forEach(e => e.classList.toggle('on', e.classList.contains(kind))); }
    _scheduleBlink() {
      clearTimeout(this._timers.blink);
      this._timers.blink = setTimeout(() => {
        const eyes = this._stage.querySelector('.eyes');
        const b = () => { if (!eyes) return; eyes.classList.remove('blink'); void eyes.getBoundingClientRect(); eyes.classList.add('blink'); setTimeout(() => eyes.classList.remove('blink'), 320); };
        b(); if (Math.random() < .08) setTimeout(b, 480);
        this._scheduleBlink();
      }, 4200 + Math.random() * 4600);
    }
    _glance() {
      clearTimeout(this._timers.glance);
      this._timers.glance = setTimeout(() => {
        if (!this._pointerNear && this._current === 'idle') {
          this._pupil((Math.random() * 4 - 2).toFixed(1), (Math.random() * 2.4 - 1.2).toFixed(1));
          setTimeout(() => this._pupil(0, 0), 800 + Math.random() * 900);
        }
        this._glance();
      }, 2800 + Math.random() * 3800);
    }
    _pupil(x, y) {
      if (!['idle', 'wave', 'shy'].includes(this._current) && !(x === 0 && y === 0)) return;
      const p = this._stage.querySelector('.pupils'); if (p) p.style.transform = `translate(${x}px,${y}px)`;
    }
    _follow(e) {
      if (this._current !== 'idle' && this._current !== 'wave') return;
      const r = this.getBoundingClientRect(); if (!r.width) return;
      const cx = r.left + r.width / 2, cy = r.top + r.height * .45;
      const dx = e.clientX - cx, dy = e.clientY - cy, d = Math.hypot(dx, dy);
      this._pointerNear = d < r.width * 3;
      if (!this._pointerNear) { this._pupil(0, 0); return; }
      const k = Math.min(1, d / (r.width * 1.5));
      this._pupil((dx / d * 2.6 * k).toFixed(2), (dy / d * 2 * k).toFixed(2));
    }
    _talking(on) {
      clearInterval(this._timers.talk);
      if (!on) { this._setMouth((this.lev ? MOUTH_LEV : MOUTH)[this._current]); return; }
      let i = 0;
      this._timers.talk = setInterval(() => this._setMouth(TALK[i++ % TALK.length]), 105 + Math.random() * 40);
    }
    _zone(zone) {
      const list = ZONE[zone] || ['hello'];
      const kind = list[Math.floor(Math.random() * list.length)];
      this.react(kind, { voice: this.hasAttribute('voice'), profile: this.getAttribute('voice') || undefined });
      this.dispatchEvent(new CustomEvent('myslik-tap', { detail: { zone, kind }, bubbles: true }));
    }
    /* ---------- рост ---------- */
    grow(toAge, ms = 3000) {
      toAge = clamp(+toAge, 1, 11);
      const from = this._age, dir = toAge > from ? 1 : -1;
      cancelAnimationFrame(this._growRaf);
      const crosses = (from < 9 && toAge >= 9) || (from >= 9 && toAge < 9);
      const start = performance.now();
      const step = now => {
        let k = clamp((now - start) / ms, 0, 1);
        k = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
        let a = lerp(from, toAge, k);
        if (crosses && dir > 0 && a >= 9 && !this._morphed) { this._morphed = true; this._morph(() => { this.setAttribute('age', f1(a)); this._growRaf = requestAnimationFrame(step); }); return; }
        if (crosses && dir < 0 && a < 9 && !this._morphed) { this._morphed = true; this._morph(() => { this.setAttribute('age', f1(a)); this._growRaf = requestAnimationFrame(step); }, true); return; }
        this.setAttribute('age', f1(a));
        if (k < 1) this._growRaf = requestAnimationFrame(step);
        else { this._morphed = false; this.dispatchEvent(new CustomEvent('myslik-grown', { detail: { age: toAge }, bubbles: true })); }
      };
      this._growRaf = requestAnimationFrame(step);
      return this;
    }
    _morph(done, back) {
      // вспышка света: лампа разлетается, гаснет тело, появляется Лев с гривой
      this.classList.add('morph-out'); this.hush();
      setTimeout(() => {
        this.classList.remove('morph-out'); this.classList.add('morph-in');
        done();
        this.react('hello', { text: back ? 'Снова Мыслик.' : 'Теперь я Лев.' });
        setTimeout(() => this.classList.remove('morph-in'), 900);
      }, 700);
    }
    /* ---------- плавающий помощник ---------- */
    _setupFloat() {
      const KEY = 'smk_float_pos';
      const place = (x, y) => {
        const w = this.offsetWidth || 150, h = this.offsetHeight || 150;
        x = Math.max(6, Math.min(window.innerWidth - w - 6, x)); y = Math.max(6, Math.min(window.innerHeight - h - 6, y));
        this.style.left = x + 'px'; this.style.top = y + 'px'; this.style.right = 'auto'; this.style.bottom = 'auto';
        this._bubble.classList.toggle('left', x > window.innerWidth * .55); this._bubble.classList.toggle('below', y < 140);
        return [x, y];
      };
      let saved = null; try { saved = JSON.parse(localStorage.getItem(KEY) || 'null'); } catch (e) {}
      const w = this.offsetWidth || 150;
      if (saved && saved.x != null) place(saved.x * window.innerWidth, saved.y * window.innerHeight);
      else if (window.innerWidth < 640) place(window.innerWidth - w - 10, window.innerHeight - w - 24);
      else place(window.innerWidth - w - 18, window.innerHeight - w - 18);
      this._resizeBound = () => place(parseFloat(this.style.left), parseFloat(this.style.top));
      window.addEventListener('resize', this._resizeBound);
      let sx = 0, sy = 0, ox = 0, oy = 0;
      this.addEventListener('pointerdown', e => { this._moved = false; sx = e.clientX; sy = e.clientY; ox = parseFloat(this.style.left); oy = parseFloat(this.style.top); this.setPointerCapture(e.pointerId); this.setAttribute('dragging', ''); });
      this.addEventListener('pointermove', e => {
        if (!this.hasAttribute('dragging')) return;
        const dx = e.clientX - sx, dy = e.clientY - sy;
        if (!this._moved && Math.hypot(dx, dy) < 6) return;
        this._moved = true; this.hush(); place(ox + dx, oy + dy);
      });
      const end = () => {
        if (!this.hasAttribute('dragging')) return;
        this.removeAttribute('dragging');
        if (this._moved) {
          const x = parseFloat(this.style.left), y = parseFloat(this.style.top), w = this.offsetWidth;
          const [nx, ny] = place(x + w / 2 < window.innerWidth / 2 ? 10 : window.innerWidth - w - 10, y);
          this.style.transition = 'left .25s ease, top .25s ease'; setTimeout(() => this.style.transition = '', 300);
          try { localStorage.setItem(KEY, JSON.stringify({ x: nx / window.innerWidth, y: ny / window.innerHeight })); } catch (err) {}
        }
        setTimeout(() => this._moved = false, 0);
      };
      this.addEventListener('pointerup', end); this.addEventListener('pointercancel', end);
      if (!saved) { this._hint.classList.add('on'); setTimeout(() => this._hint.classList.remove('on'), 4000); }
    }
    /* ---------- публичный API ---------- */
    mood(m) { this.setAttribute('mood', m); return this; }
    say(text, opts = {}) {
      const b = this._bubble; clearTimeout(this._timers.say);
      if (opts.left != null) b.classList.toggle('left', !!opts.left);
      else this._fitBubble();
      b.innerHTML = ''; b.classList.add('on');
      const cur = document.createElement('span'); cur.className = 'cur';
      const span = document.createElement('span'); b.append(span, cur);
      let i = 0; const speed = opts.speed ?? 26;
      const tick = () => {
        if (i < text.length) { span.textContent = text.slice(0, ++i); this._timers.say = setTimeout(tick, speed); }
        else { cur.remove(); this._timers.say = setTimeout(() => b.classList.remove('on'), opts.ms ?? Math.max(2200, text.length * 70)); }
      };
      tick(); return this;
    }
    _fitBubble() {
      // облачко не вылезает за край экрана: справа, слева или над головой по центру
      const b = this._bubble, r = this.getBoundingClientRect(), vw = document.documentElement.clientWidth || window.innerWidth;
      if (!r.width || this.hasAttribute('float')) return;
      b.classList.remove('top'); b.style.left = ''; b.style.right = ''; b.style.maxWidth = '';
      const right = vw - (r.left + r.width * .74) - 10, left = r.left + r.width * .26 - 10;
      if (right >= 190) { b.classList.remove('left'); b.style.maxWidth = Math.min(300, right) + 'px'; return; }
      if (left >= 190) { b.classList.add('left'); b.style.maxWidth = Math.min(300, left) + 'px'; return; }
      const w = Math.min(280, vw - 20);
      const x = Math.max(10 - r.left, Math.min((r.width - w) / 2, vw - 10 - w - r.left));
      b.classList.remove('left'); b.classList.add('top');
      b.style.left = x + 'px'; b.style.right = 'auto'; b.style.maxWidth = w + 'px';
      b.style.setProperty('--tail', Math.max(14, Math.min(w - 28, r.width / 2 - x - 7)) + 'px');
    }
    hush() { clearTimeout(this._timers.say); this._bubble.classList.remove('on'); return this; }
    react(kind, opts = {}) {
      const r = REACT[this.band][kind]; if (!r) return this;
      this.mood(r.mood);
      const phrase = opts.text || r.say[Math.floor(Math.random() * r.say.length)];
      if (opts.bubble !== false) this.say(phrase, opts);
      if (opts.voice) this.speak(phrase, opts.profile, { bubble: false });
      return this;
    }
    speak(text, profile, opts = {}) {
      if (!('speechSynthesis' in window)) return this;
      const P = typeof profile === 'string' ? Myslik.profiles[profile] : (profile || Myslik.profiles[this.lev ? 'lev' : 'boy']);
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
    MOODS, REACT, params,
    profiles: {
      boy:    { label: 'Мыслик, для мальчика', prefer: ['Pavel', 'Dmitry', 'Yuri', 'Google русский'], pitch: 1.18, rate: 1.0 },
      girl:   { label: 'Мыслик, для девочки',  prefer: ['Svetlana', 'Irina', 'Milena', 'Katya', 'Google русский'], pitch: 1.14, rate: 1.02 },
      parent: { label: 'Мыслик, для родителя', prefer: ['Irina', 'Svetlana', 'Pavel', 'Google русский'], pitch: 1.0, rate: 0.96 },
      lev:    { label: 'Лев', prefer: ['Pavel', 'Dmitry', 'Yuri', 'Google русский'], pitch: 0.92, rate: 0.98 },
    },
    voices() { return (window.speechSynthesis?.getVoices() || []).filter(v => /^ru/i.test(v.lang)); },
    pick(P) {
      const vs = Myslik.voices(); if (!vs.length) return null;
      if (P.voiceURI) { const f = vs.find(v => v.voiceURI === P.voiceURI || v.name === P.voiceURI); if (f) return f; }
      for (const name of P.prefer || []) { const f = vs.find(v => v.name.toLowerCase().includes(name.toLowerCase())); if (f) return f; }
      const nat = vs.find(v => /natural|neural|premium|enhanced/i.test(v.name)); if (nat) return nat;
      return vs[0];
    },
    clean(t) { return String(t).replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu, '').replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim(); },
  };
  window.Myslik = Myslik;
  if (!customElements.get('myslik-face')) customElements.define('myslik-face', MyslikFace);
  if (window.speechSynthesis) window.speechSynthesis.onvoiceschanged = () => document.dispatchEvent(new Event('myslik-voices'));
})();
