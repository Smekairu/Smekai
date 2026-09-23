/* Персонажи Смекай: Мыслик (1–8 класс) и Лев (9–11 класс).
 *
 * Подключение:  <script src="assets/myslik.js"></script>
 *               <myslik-face mood="idle" size="240"></myslik-face>
 *               <myslik-face who="lev" size="240"></myslik-face>
 *               <myslik-face float></myslik-face>      плавающий помощник, его можно таскать
 *
 * Настроения: idle, think, yay, party, sad, angry, surprised, sleepy, wave, love, shy
 * Совместимость с викториной: oops = sad, celebrate = party.
 *
 * API:  el.mood('yay')   el.say('Текст', {ms})   el.speak('Текст', 'girl')
 *       el.react('correct' | 'wrong' | 'hello' | 'thinking' | 'bye' | 'streak' | 'idea')
 *       Myslik.voices()  Myslik.profiles  Myslik.clean()
 *
 * Клик по частям тела даёт разные реакции: лампа, глаза, рот, руки, живот.
 */
(function () {
  const CSS = `
:host{display:inline-block;position:relative;line-height:0;touch-action:none;user-select:none;-webkit-user-select:none;
  --sun:#FFC933;--ink:#1B1F3B;--face:#F7F9FF}
:host([hidden]){display:none}
:host([float]){position:fixed;z-index:9000;width:104px;height:104px;cursor:grab;filter:drop-shadow(0 10px 18px rgba(27,31,59,.22))}
:host([float][dragging]){cursor:grabbing;transition:none!important}
:host([float]) .hint{position:absolute;left:50%;bottom:-6px;transform:translateX(-50%);font:600 11px/1 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
  color:#fff;background:var(--ink);padding:4px 8px;border-radius:999px;white-space:nowrap;opacity:0;transition:opacity .3s;pointer-events:none}
:host([float]) .hint.on{opacity:.92}
@media(max-width:640px){:host([float]){width:78px;height:78px}}
.stage{position:relative;width:100%;height:100%}
svg{width:100%;height:100%;overflow:visible;display:block}
.rig{transform-box:fill-box;transform-origin:50% 100%;animation:sway 6s ease-in-out infinite}
.body{transform-box:fill-box;transform-origin:50% 100%;animation:breathe 3.8s ease-in-out infinite}
.shadow{transform-box:fill-box;transform-origin:center;animation:shadow 3.8s ease-in-out infinite}
.eye{transform-box:fill-box;transform-origin:center;transition:transform .2s}
.eyes.blink .eye{animation:blink .14s ease-in-out}
.pupils{transition:transform .28s ease}
.brow{transform-box:fill-box;transform-origin:center;transition:transform .3s ease,opacity .2s}
.m{opacity:0;transition:opacity .1s}.m.on{opacity:1}
.arm{transform-box:fill-box;transform-origin:50% 0;transition:transform .4s cubic-bezier(.2,.8,.3,1.2)}
.glow{fill:var(--sun);opacity:.14;transform-box:fill-box;transform-origin:center;animation:idleglow 5s ease-in-out infinite}
.rays{opacity:0;transform-box:fill-box;transform-origin:center;transition:opacity .25s}
.bulb{transition:fill .3s}
.fil{transition:opacity .3s;opacity:.35}
.mane{transform-box:fill-box;transform-origin:center;animation:maneidle 6s ease-in-out infinite}
.sparks,.hearts,.tears,.steam,.zzz,.drop,.wow{opacity:0;transition:opacity .25s}
.spark{transform-box:fill-box;transform-origin:center}
.cheek{transition:opacity .3s}
.zone{cursor:pointer}
.hint{display:none}
:host([float]) .hint{display:block}
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
:host(.party) .arm.l{animation:wave 1.1s ease-in-out infinite}
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
:host(.surprised) .eye{transform:scale(1.18)}
:host(.surprised) .brow.l,:host(.surprised) .brow.r{transform:translate(0,-3.2px)}
:host(.surprised) .wow{opacity:1;animation:wow .5s ease}
:host(.surprised) .glow{animation:none;opacity:.5;transform:scale(1.2)}
:host(.sleepy) .rig{animation:sway 7.5s ease-in-out infinite}
:host(.sleepy) .eye{transform:scaleY(.3)}
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
  box-shadow:0 10px 28px rgba(27,31,59,.16);opacity:0;transform:translateY(8px) scale(.94);transform-origin:0 100%;
  transition:opacity .22s,transform .22s;pointer-events:none;z-index:2;white-space:pre-wrap;text-align:left}
.bubble::after{content:"";position:absolute;left:14px;bottom:-9px;width:14px;height:14px;background:#fff;
  border-left:1.5px solid rgba(27,31,59,.22);border-bottom:1.5px solid rgba(27,31,59,.22);transform:rotate(-45deg);border-radius:0 0 0 3px}
.bubble.on{opacity:1;transform:translateY(0) scale(1)}
.bubble.left{left:auto;right:74%;transform-origin:100% 100%}
.bubble.left::after{left:auto;right:14px;transform:rotate(-135deg)}
.bubble.below{bottom:auto;top:96%;transform-origin:0 0}
.bubble.below::after{bottom:auto;top:-9px;transform:rotate(135deg)}
.bubble.below.left::after{transform:rotate(45deg)}
.bubble .cur{display:inline-block;width:2px;height:1em;background:var(--ink);vertical-align:-2px;margin-left:1px;animation:cur .8s step-end infinite}
/* --- ключевые кадры --- */
@keyframes sway{0%,100%{transform:rotate(-1deg)}50%{transform:rotate(1deg)}}
@keyframes breathe{0%,100%{transform:scale(1,1)}50%{transform:scale(1.008,1.022)}}
@keyframes shadow{0%,100%{transform:scale(1)}50%{transform:scale(1.04)}}
@keyframes blink{0%,100%{transform:scaleY(1)}50%{transform:scaleY(.08)}}
@keyframes idleglow{0%,100%{opacity:.12;transform:scale(1)}50%{opacity:.3;transform:scale(1.07)}}
@keyframes thinkglow{0%,100%{opacity:.2;transform:scale(1)}50%{opacity:.7;transform:scale(1.22)}}
@keyframes maneidle{0%,100%{transform:scale(1) rotate(0)}50%{transform:scale(1.02) rotate(.6deg)}}
@keyframes manethink{0%,100%{transform:scale(1)}50%{transform:scale(1.06)}}
@keyframes maneyay{0%,100%{transform:scale(1.04) rotate(-1.5deg)}50%{transform:scale(1.1) rotate(1.5deg)}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes tw{0%,100%{transform:scale(.6) rotate(0);opacity:.4}50%{transform:scale(1.1) rotate(20deg);opacity:1}}
@keyframes hop{0%{transform:translateY(0)}30%{transform:translateY(-9px)}55%{transform:translateY(0)}75%{transform:translateY(-3px)}100%{transform:translateY(0)}}
@keyframes squash{0%{transform:scale(1,1)}18%{transform:scale(1.05,.94)}40%{transform:scale(.96,1.05)}65%{transform:scale(1.02,.98)}100%{transform:scale(1,1)}}
@keyframes bounce{0%,100%{transform:translateY(0) rotate(-2deg)}50%{transform:translateY(-6px) rotate(2deg)}}
@keyframes wave{0%,100%{transform:rotate(-60deg)}50%{transform:rotate(-118deg)}}
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
@media (prefers-reduced-motion:reduce){.rig,.body,.shadow,.glow,.mane{animation:none!important}}
`;

  /* Общий каркас. Голова у обоих, лампа у Мыслика, грива у Льва. */
  const DEFS = `
<defs>
  <radialGradient id="gBody" cx="36%" cy="28%" r="78%"><stop offset="0" stop-color="#5E93FF"/><stop offset=".6" stop-color="#3E7BFA"/><stop offset="1" stop-color="#2853C4"/></radialGradient>
  <radialGradient id="gBodyLev" cx="36%" cy="28%" r="78%"><stop offset="0" stop-color="#3D5BD6"/><stop offset=".6" stop-color="#2743A8"/><stop offset="1" stop-color="#1B2C70"/></radialGradient>
  <radialGradient id="gFace" cx="50%" cy="40%" r="70%"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#EEF2FB"/></radialGradient>
  <radialGradient id="gBulb" cx="42%" cy="34%" r="66%"><stop offset="0" stop-color="#FFFBEA"/><stop offset=".7" stop-color="#F6E7B1"/><stop offset="1" stop-color="#E5CF86"/></radialGradient>
  <radialGradient id="gBulbOn" cx="42%" cy="34%" r="66%"><stop offset="0" stop-color="#FFFDF0"/><stop offset=".6" stop-color="#FFE270"/><stop offset="1" stop-color="#F5B91E"/></radialGradient>
  <radialGradient id="gBulbOff" cx="42%" cy="34%" r="66%"><stop offset="0" stop-color="#E9ECF4"/><stop offset="1" stop-color="#C3C8D8"/></radialGradient>
  <radialGradient id="gIris" cx="40%" cy="36%" r="66%"><stop offset="0" stop-color="#4A5AA8"/><stop offset=".55" stop-color="#26306B"/><stop offset="1" stop-color="#151A3D"/></radialGradient>
  <radialGradient id="gIrisLev" cx="40%" cy="36%" r="66%"><stop offset="0" stop-color="#C9962B"/><stop offset=".55" stop-color="#7A5A12"/><stop offset="1" stop-color="#3A2A06"/></radialGradient>
  <linearGradient id="gMane" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFD966"/><stop offset="1" stop-color="#E9A825"/></linearGradient>
  <linearGradient id="gMetal" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#B8BFD4"/><stop offset="1" stop-color="#7E86A3"/></linearGradient>
</defs>`;

  const HEAD_MYSLIK = `
<g class="lamp zone" data-zone="lamp">
  <g class="sparks" fill="var(--sun)">
    <path class="spark" d="M4 30l1.8 4.6 4.6 1.8-4.6 1.8-1.8 4.6-1.8-4.6-4.6-1.8 4.6-1.8z"/>
    <path class="spark" d="M94 42l1.4 3.6 3.6 1.4-3.6 1.4-1.4 3.6-1.4-3.6-3.6-1.4 3.6-1.4z"/>
    <path class="spark" d="M90 6l1.1 2.8 2.8 1.1-2.8 1.1-1.1 2.8-1.1-2.8-2.8-1.1 2.8-1.1z"/>
  </g>
  <g class="rays" stroke="var(--sun)" stroke-width="2.2" stroke-linecap="round">
    <line x1="50" y1="-7" x2="50" y2="-2"/><line x1="36" y1="-1" x2="39.5" y2="2.5"/><line x1="64" y1="-1" x2="60.5" y2="2.5"/>
    <line x1="30" y1="12" x2="35.5" y2="12"/><line x1="70" y1="12" x2="64.5" y2="12"/>
  </g>
  <circle class="glow" cx="50" cy="12" r="15"/>
  <path d="M48.6 30 L48.6 23.2 M51.4 30 L51.4 23.2" stroke="url(#gMetal)" stroke-width="1.8" stroke-linecap="round"/>
  <circle class="bulb" cx="50" cy="12" r="8" fill="url(#gBulb)"/>
  <path class="fil" d="M46.5 15 q1.2 -6 3.5 -2 q2.3 -4 3.5 2" stroke="#D9A21B" stroke-width="1" fill="none" stroke-linecap="round"/>
  <path d="M45.4 9.4 q1.8 -3.6 5.2 -3.4" stroke="#fff" stroke-width="1.6" fill="none" stroke-linecap="round" opacity=".85"/>
  <rect x="45.4" y="19.2" width="9.2" height="4" rx="1.4" fill="url(#gMetal)"/>
  <rect x="45.4" y="20.6" width="9.2" height="1.1" fill="#fff" opacity=".35"/>
  <g class="steam" fill="#B9C0D6"><circle class="puff a" cx="38" cy="26" r="2.8"/><circle class="puff b" cx="62" cy="24" r="3.3"/><circle class="puff c" cx="50" cy="-2" r="2.4"/></g>
  <g class="zzz" fill="var(--ink)" font-family="Arial,sans-serif" font-weight="700"><text class="z a" x="70" y="30" font-size="8">z</text><text class="z b" x="74" y="24" font-size="10">z</text><text class="z c" x="79" y="18" font-size="12">Z</text></g>
  <g class="hearts" fill="#FF6B81"><path class="heart a" d="M22 40c-3-4-9-1-6 4l6 6 6-6c3-5-3-8-6-4z"/><path class="heart b" d="M78 34c-2.4-3.2-7.2-.8-4.8 3.2l4.8 4.8 4.8-4.8c2.4-4-2.4-6.4-4.8-3.2z"/><path class="heart c" d="M50 -4c-2-2.6-6-.6-4 2.6l4 4 4-4c2-3.2-2-5.2-4-2.6z"/></g>
  <g class="wow"><text x="80" y="22" font-size="11" font-weight="800" fill="var(--sun)" font-family="Arial,sans-serif">!</text></g>
</g>`;

  function manePath(cx, cy, rOut, rIn, n, phase) {
    // грива: кольцо из мягких лепестков, как у льва, а не корона
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
  const HEAD_LEV = `
<g class="lamp zone" data-zone="lamp">
  <g class="sparks" fill="var(--sun)">
    <path class="spark" d="M0 36l1.8 4.6 4.6 1.8-4.6 1.8-1.8 4.6-1.8-4.6-4.6-1.8 4.6-1.8z"/>
    <path class="spark" d="M98 50l1.4 3.6 3.6 1.4-3.6 1.4-1.4 3.6-1.4-3.6-3.6-1.4 3.6-1.4z"/>
    <path class="spark" d="M92 4l1.1 2.8 2.8 1.1-2.8 1.1-1.1 2.8-1.1-2.8-2.8-1.1 2.8-1.1z"/>
  </g>
  <g class="mane">
    <circle class="glow" cx="50" cy="54" r="30"/>
    <path d="${manePath(50, 55, 46, 38, 18, -Math.PI / 2)}" fill="url(#gMane)"/>
    <path d="${manePath(50, 55, 40, 34, 18, -Math.PI / 2 + .17)}" fill="#FFE59A" opacity=".5"/>
    <path d="${manePath(50, 55, 35, 31, 18, -Math.PI / 2)}" fill="#E9A825" opacity=".35"/>
  </g>
  <g class="rays" stroke="var(--sun)" stroke-width="2" stroke-linecap="round"><line x1="50" y1="-2" x2="50" y2="3"/><line x1="22" y1="12" x2="26" y2="15"/><line x1="78" y1="12" x2="74" y2="15"/></g>
  <g class="ears"><ellipse cx="29" cy="31" rx="6.4" ry="6.8" fill="url(#gBodyLev)"/><ellipse cx="29" cy="31.6" rx="3.4" ry="3.8" fill="#8EA6FF" opacity=".5"/>
     <ellipse cx="71" cy="31" rx="6.4" ry="6.8" fill="url(#gBodyLev)"/><ellipse cx="71" cy="31.6" rx="3.4" ry="3.8" fill="#8EA6FF" opacity=".5"/></g>
  <circle class="bulb" cx="50" cy="12" r="0" fill="none"/>
  <g class="steam" fill="#B9C0D6"><circle class="puff a" cx="36" cy="18" r="2.8"/><circle class="puff b" cx="64" cy="16" r="3.3"/><circle class="puff c" cx="50" cy="-2" r="2.4"/></g>
  <g class="zzz" fill="var(--sun)" font-family="Arial,sans-serif" font-weight="700"><text class="z a" x="78" y="26" font-size="8">z</text><text class="z b" x="82" y="20" font-size="10">z</text><text class="z c" x="87" y="14" font-size="12">Z</text></g>
  <g class="hearts" fill="#FF6B81"><path class="heart a" d="M14 46c-3-4-9-1-6 4l6 6 6-6c3-5-3-8-6-4z"/><path class="heart b" d="M88 40c-2.4-3.2-7.2-.8-4.8 3.2l4.8 4.8 4.8-4.8c2.4-4-2.4-6.4-4.8-3.2z"/><path class="heart c" d="M50 -6c-2-2.6-6-.6-4 2.6l4 4 4-4c2-3.2-2-5.2-4-2.6z"/></g>
  <g class="wow"><text x="86" y="30" font-size="11" font-weight="800" fill="var(--sun)" font-family="Arial,sans-serif">!</text></g>
</g>`;

  function body(lev) {
    const fill = lev ? 'url(#gBodyLev)' : 'url(#gBody)';
    const iris = lev ? 'url(#gIrisLev)' : 'url(#gIris)';
    const armC = lev ? '#22398F' : '#2F63D6';
    // Лев выше и уже, лицо спокойнее: глаза чуть уже, брови прямее, рот короче
    const eyeRy = lev ? 6.4 : 7.4, eyeRx = lev ? 6.2 : 6.6;
    const browL = lev ? 'M33 46 Q39 44.2 45 46' : 'M32.5 45.5 Q39 42.8 45.5 45.5';
    const browR = lev ? 'M55 46 Q61 44.2 67 46' : 'M54.5 45.5 Q61 42.8 67.5 45.5';
    const cheekOp = lev ? .28 : .42;
    return `
<g class="arm l zone" data-zone="arm"><path d="M21 70 Q9 74 11 84" stroke="${armC}" stroke-width="6.5" fill="none" stroke-linecap="round"/></g>
<g class="arm r zone" data-zone="arm"><path d="M79 70 Q91 74 89 84" stroke="${armC}" stroke-width="6.5" fill="none" stroke-linecap="round"/></g>
<g class="body">
  <path class="zone" data-zone="body" d="${lev ? 'M20 66 C20 40 33 28 50 28 C67 28 80 40 80 66 C80 90 67 104 50 104 C33 104 20 90 20 66Z' : 'M18 67 C18 41 32 29 50 29 C68 29 82 41 82 67 C82 89 68 103 50 103 C32 103 18 89 18 67Z'}" fill="${fill}"/>
  <path d="M26 58 C26 44 36 36 50 36 C64 36 74 44 74 58" stroke="#fff" stroke-width="1.2" fill="none" opacity=".12"/>
  <ellipse cx="37" cy="40" rx="8" ry="4.2" fill="#fff" opacity=".13" transform="rotate(-24 37 40)"/>
  <path class="zone" data-zone="face" d="${lev ? 'M31 74 C31 63 39 57 50 57 C61 57 69 63 69 74 C69 88 61 96 50 96 C39 96 31 88 31 74Z' : 'M30 76 C30 64 38 58 50 58 C62 58 70 64 70 76 C70 90 62 98 50 98 C38 98 30 90 30 76Z'}" fill="url(#gFace)" opacity=".97"/>
  <g class="cheeks"><ellipse class="cheek" cx="31.5" cy="71" rx="4.2" ry="2.8" fill="#FF8FA3" opacity="${cheekOp}"/><ellipse class="cheek" cx="68.5" cy="71" rx="4.2" ry="2.8" fill="#FF8FA3" opacity="${cheekOp}"/></g>
  <g class="brows" stroke="var(--ink)" stroke-width="2.2" stroke-linecap="round" fill="none"><path class="brow l" d="${browL}"/><path class="brow r" d="${browR}"/></g>
  <g class="eyes zone" data-zone="eyes">
    <g class="eye l"><ellipse cx="39.5" cy="55" rx="${eyeRx}" ry="${eyeRy}" fill="#fff"/></g>
    <g class="eye r"><ellipse cx="60.5" cy="55" rx="${eyeRx}" ry="${eyeRy}" fill="#fff"/></g>
    <g class="pupils">
      <circle cx="40.3" cy="55.8" r="4" fill="${iris}"/><circle cx="61.3" cy="55.8" r="4" fill="${iris}"/>
      <circle cx="40.3" cy="55.8" r="1.9" fill="#0E1230"/><circle cx="61.3" cy="55.8" r="1.9" fill="#0E1230"/>
      <circle cx="41.8" cy="54" r="1.3" fill="#fff"/><circle cx="62.8" cy="54" r="1.3" fill="#fff"/>
      <circle cx="39" cy="57.4" r=".6" fill="#fff" opacity=".7"/><circle cx="60" cy="57.4" r=".6" fill="#fff" opacity=".7"/>
    </g>
    <g class="happy m" stroke="var(--ink)" stroke-width="2.8" fill="none" stroke-linecap="round"><path d="M33.5 57 Q39.5 50 45.5 57"/><path d="M54.5 57 Q60.5 50 66.5 57"/></g>
    <g class="tears" fill="#7FB7FF"><path class="tear a" d="M35 62 q2.2 3.6 0 5.4 q-2.2 -1.8 0 -5.4z"/><path class="tear b" d="M65 62 q2.2 3.6 0 5.4 q-2.2 -1.8 0 -5.4z"/></g>
  </g>
  <g class="mouth zone" data-zone="mouth">
    <path class="m smile on" d="${lev ? 'M44 75 Q50 79.5 56 75' : 'M43 74.5 Q50 80.5 57 74.5'}" stroke="var(--ink)" stroke-width="2.4" fill="none" stroke-linecap="round"/>
    <g class="m grin"><path d="M41.5 72 Q50 72 58.5 72 Q57.5 83.5 50 84.5 Q42.5 83.5 41.5 72Z" fill="#2A1F2E"/><path d="M45 79 Q50 76 55 79 Q53.5 83 50 83.2 Q46.5 83 45 79Z" fill="#FF6B81" opacity=".9"/></g>
    <g class="m open"><ellipse cx="50" cy="77" rx="4.2" ry="5" fill="#2A1F2E"/><ellipse cx="50" cy="79.6" rx="2.5" ry="1.6" fill="#FF6B81" opacity=".9"/></g>
    <g class="m half"><path d="M44 75 Q50 78.5 56 75 Q55 79.5 50 80 Q45 79.5 44 75Z" fill="#2A1F2E"/></g>
    <path class="m flat" d="M44.5 76.5 L55.5 76.5" stroke="var(--ink)" stroke-width="2.4" fill="none" stroke-linecap="round"/>
    <path class="m frown" d="M43.5 79 Q50 73.5 56.5 79" stroke="var(--ink)" stroke-width="2.4" fill="none" stroke-linecap="round"/>
    <ellipse class="m o" cx="50" cy="77" rx="3.2" ry="4.2" fill="#2A1F2E"/>
    <path class="m grit" d="M43 76 h14 M46.5 73.8 v4.4 M50 73.8 v4.4 M53.5 73.8 v4.4" stroke="var(--ink)" stroke-width="2" fill="none" stroke-linecap="round"/>
    <path class="m smirk" d="M44 76 Q50 78 57 73.5" stroke="var(--ink)" stroke-width="2.4" fill="none" stroke-linecap="round"/>
  </g>
  <g class="drop" fill="#7FB7FF"><path d="M73 48 q2.8 4.6 0 7 q-2.8 -2.4 0 -7z"/></g>
</g>`;
  }

  function svg(lev) {
    return `<svg viewBox="-12 -16 124 136" aria-hidden="true">${DEFS}
<ellipse class="shadow" cx="50" cy="109" rx="25" ry="3.6" fill="#1B1F3B" opacity=".09"/>
<g class="rig">${lev ? HEAD_LEV : HEAD_MYSLIK}${body(lev)}</g></svg>`;
  }

  const MOODS = ['idle', 'think', 'yay', 'party', 'sad', 'angry', 'surprised', 'sleepy', 'wave', 'love', 'shy'];
  const ALIAS = { oops: 'sad', celebrate: 'party', happy: 'yay', hi: 'wave' };
  const MOUTH = { idle: 'smile', think: 'flat', yay: 'grin', party: 'grin', sad: 'frown', angry: 'grit',
                  surprised: 'o', sleepy: 'half', wave: 'smile', love: 'grin', shy: 'smile' };
  const MOUTH_LEV = { ...MOUTH, idle: 'smirk', yay: 'half', wave: 'smirk', shy: 'smile', love: 'half' };
  const HAPPY_EYES = new Set(['yay', 'party', 'love']);
  const TALK = ['open', 'half', 'smile', 'open', 'o', 'half'];

  const REACT = {
    hello:    { mood: 'wave',      say: ['Привет! Я Мыслик.', 'Здравствуй. Готов к уроку?', 'Привет. Что сегодня решаем?'] },
    correct:  { mood: 'yay',       say: ['Верно.', 'Точно.', 'Да, именно так.', 'Правильно.', 'С первого раза!'] },
    wrong:    { mood: 'sad',       say: ['Пока не то.', 'Почти, но нет.', 'Не сходится. Проверь ещё раз.', 'Попробуй иначе.'] },
    thinking: { mood: 'think',     say: ['Дай подумать…', 'Так, смотрим на условие…', 'Хм…'] },
    idea:     { mood: 'think',     say: ['Есть идея!', 'А что, если начать с конца?', 'Знаю, с чего начать.'] },
    bye:      { mood: 'wave',      say: ['Пока. Заходи завтра.', 'До встречи.', 'Молодец сегодня.'] },
    streak:   { mood: 'party',     say: ['Три подряд!', 'Серия. Так держать.'] },
    surprise: { mood: 'surprised', say: ['Ого!', 'Ничего себе.'] },
    tired:    { mood: 'sleepy',    say: ['Может, перерыв?', 'Пять минут отдыха, и продолжим.'] },
    love:     { mood: 'love',      say: ['Люблю, когда получается.', 'Ты молодец.'] },
    angry:    { mood: 'angry',     say: ['Эй. Так нечестно.', 'Не списывай.'] },
    shy:      { mood: 'shy',       say: ['Ой.', 'Щекотно.'] },
  };
  const REACT_LEV = {
    hello:    { mood: 'wave',      say: ['Привет. Я Лев.', 'Здравствуй. Начнём?', 'Привет. Что разбираем?'] },
    correct:  { mood: 'yay',       say: ['Верно.', 'Так и есть.', 'Точно.', 'Хорошо.'] },
    wrong:    { mood: 'sad',       say: ['Нет. Посмотри ещё раз.', 'Не сходится.', 'Проверь знак.'] },
    thinking: { mood: 'think',     say: ['Думаю…', 'Смотрю условие…'] },
    idea:     { mood: 'think',     say: ['Есть ход.', 'Попробуй от обратного.'] },
    bye:      { mood: 'wave',      say: ['До завтра.', 'Хорошая работа.'] },
    streak:   { mood: 'party',     say: ['Три подряд. Держи темп.', 'Серия.'] },
    surprise: { mood: 'surprised', say: ['Неожиданно.', 'Ого.'] },
    tired:    { mood: 'sleepy',    say: ['Перерыв. Десять минут.', 'Отдохни, потом вернёмся.'] },
    love:     { mood: 'love',      say: ['Красиво решено.'] },
    angry:    { mood: 'angry',     say: ['Списывать не будем.'] },
    shy:      { mood: 'shy',       say: ['Хватит.'] },
  };
  const ZONE = {
    lamp:  ['idea', 'thinking'],
    eyes:  ['surprise'],
    mouth: ['hello', 'bye'],
    arm:   ['hello'],
    face:  ['shy', 'love'],
    body:  ['correct', 'streak', 'tired'],
  };

  class MyslikFace extends HTMLElement {
    static get observedAttributes() { return ['mood', 'size', 'class', 'talking', 'who']; }
    constructor() {
      super();
      const root = this.attachShadow({ mode: 'open' });
      const style = document.createElement('style'); style.textContent = CSS;
      this._stage = document.createElement('div'); this._stage.className = 'stage';
      this._bubble = document.createElement('div'); this._bubble.className = 'bubble';
      this._hint = document.createElement('div'); this._hint.className = 'hint'; this._hint.textContent = 'перетащи меня';
      root.append(style, this._stage);
      this._current = 'idle'; this._timers = {};
      this._build();
    }
    get lev() { return (this.getAttribute('who') || '').toLowerCase() === 'lev'; }
    _build() {
      this._stage.innerHTML = svg(this.lev);
      this._stage.append(this._bubble, this._hint);
      this._stage.querySelectorAll('.zone').forEach(z => {
        z.addEventListener('pointerup', e => { if (!this._moved) { e.stopPropagation(); this._zone(z.dataset.zone); } });
      });
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
      if (n === 'who' && o !== v) { this._build(); this._applyClasses('mood'); }
    }
    _applySize() {
      const s = this.getAttribute('size');
      if (s && !this.hasAttribute('float')) { this.style.width = s + 'px'; this.style.height = s + 'px'; }
    }
    _applyClasses(source) {
      let m = this.getAttribute('mood') || 'idle';
      if (source === 'class') {
        // викторина управляет настроением через классы: idle, think, yay, oops, party
        for (const c of this.classList) { if (MOODS.includes(c) || ALIAS[c]) m = ALIAS[c] || c; }
      }
      m = ALIAS[m] || m; if (!MOODS.includes(m)) m = 'idle';
      this._syncing = true;
      for (const x of MOODS) this.classList.toggle(x, x === m);
      if (this.getAttribute('mood') !== m) this.setAttribute('mood', m);
      this._syncing = false;
      this._current = m;
      this._setMouth((this.lev ? MOUTH_LEV : MOUTH)[m]);
      const eyes = this._stage.querySelector('.eyes');
      eyes.querySelector('.happy').classList.toggle('on', HAPPY_EYES.has(m));
      eyes.querySelectorAll('.eye, .pupils').forEach(e => e.style.opacity = HAPPY_EYES.has(m) ? 0 : 1);
      this._stage.querySelector('.brows').style.opacity = HAPPY_EYES.has(m) ? 0 : 1;
      clearTimeout(this._timers.mood);
      const once = { yay: 1700, wave: 2300, surprised: 1500, angry: 1700, shy: 1800 }[m];
      if (once) this._timers.mood = setTimeout(() => { if (this._current === m) this.mood('idle'); }, once);
    }
    _setMouth(kind) {
      this._stage.querySelectorAll('.mouth .m').forEach(e => e.classList.toggle('on', e.classList.contains(kind)));
    }
    _scheduleBlink() {
      clearTimeout(this._timers.blink);
      this._timers.blink = setTimeout(() => {
        const eyes = this._stage.querySelector('.eyes');
        const b = () => { eyes.classList.add('blink'); setTimeout(() => eyes.classList.remove('blink'), 150); };
        b(); if (Math.random() < .22) setTimeout(b, 240);
        this._scheduleBlink();
      }, 2800 + Math.random() * 3400);
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
      this._stage.querySelector('.pupils').style.transform = `translate(${x}px,${y}px)`;
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
    /* ---------- плавающий помощник ---------- */
    _setupFloat() {
      const KEY = 'smk_float_pos';
      const place = (x, y) => {
        const w = this.offsetWidth || 104, h = this.offsetHeight || 104;
        x = Math.max(6, Math.min(window.innerWidth - w - 6, x));
        y = Math.max(6, Math.min(window.innerHeight - h - 6, y));
        this.style.left = x + 'px'; this.style.top = y + 'px'; this.style.right = 'auto'; this.style.bottom = 'auto';
        this._bubble.classList.toggle('left', x > window.innerWidth * .55);
        this._bubble.classList.toggle('below', y < 140);
        return [x, y];
      };
      let saved = null;
      try { saved = JSON.parse(localStorage.getItem(KEY) || 'null'); } catch (e) {}
      const w = this.offsetWidth || 104;
      if (saved && saved.x != null) place(saved.x * window.innerWidth, saved.y * window.innerHeight);
      else if (window.innerWidth < 640) place(window.innerWidth - w - 10, 84);     // на телефоне сверху, чтобы не спорить с плашками
      else place(window.innerWidth - w - 18, window.innerHeight - w - 18);
      this._resizeBound = () => { const x = parseFloat(this.style.left), y = parseFloat(this.style.top); place(x, y); };
      window.addEventListener('resize', this._resizeBound);

      let sx = 0, sy = 0, ox = 0, oy = 0;
      this.addEventListener('pointerdown', e => {
        this._moved = false; sx = e.clientX; sy = e.clientY;
        ox = parseFloat(this.style.left); oy = parseFloat(this.style.top);
        this.setPointerCapture(e.pointerId); this.setAttribute('dragging', '');
      });
      this.addEventListener('pointermove', e => {
        if (!this.hasAttribute('dragging')) return;
        const dx = e.clientX - sx, dy = e.clientY - sy;
        if (!this._moved && Math.hypot(dx, dy) < 6) return;
        this._moved = true; this.hush(); place(ox + dx, oy + dy);
      });
      const end = e => {
        if (!this.hasAttribute('dragging')) return;
        this.removeAttribute('dragging');
        if (this._moved) {
          // прилипает к ближайшему краю по горизонтали, как кнопка в мессенджерах
          const x = parseFloat(this.style.left), y = parseFloat(this.style.top), w = this.offsetWidth;
          const [nx, ny] = place(x + w / 2 < window.innerWidth / 2 ? 10 : window.innerWidth - w - 10, y);
          this.style.transition = 'left .25s ease, top .25s ease';
          setTimeout(() => this.style.transition = '', 300);
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
    hush() { clearTimeout(this._timers.say); this._bubble.classList.remove('on'); return this; }
    react(kind, opts = {}) {
      const r = (this.lev ? REACT_LEV : REACT)[kind]; if (!r) return this;
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
    MOODS, REACT, REACT_LEV,
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
