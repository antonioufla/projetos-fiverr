/*! Chatbot widget · Antonio Rocha · instala com: <script src=".../widget.js" defer></script>
 * Opcoes (atributos do <script>): data-titulo, data-cor, data-lang (pt|en), data-abrir="1" */
(function () {
  if (window.__chatWidget) return; window.__chatWidget = true;
  var s = document.currentScript || document.querySelector('script[src*="widget.js"]');
  var API = s.src.replace(/widget\.js(\?.*)?$/, '') + 'api/chat';
  var COR = s.getAttribute('data-cor') || '#0ea5e9';
  var TITULO = s.getAttribute('data-titulo') || 'Clínica Sorriso';
  function lang() { var l = s.getAttribute('data-lang') || document.documentElement.lang || 'pt'; return /^en/i.test(l) ? 'en' : 'pt'; }
  var T = {
    pt: { on: 'Online agora', ph: 'Digite sua pergunta…', ola: 'Olá! 😊 Sou a assistente virtual da ' + TITULO + '. Pergunte sobre preços, horários, convênios ou agendamento.', sug: ['Preços', 'Horário', 'Convênios', 'Agendar avaliação'], err: 'Ops, não consegui responder agora. Tente de novo em instantes.', by: 'Demonstração · chatbot por Antonio Rocha', tip: 'Olá! 👋 Posso ajudar com preços e horários?', abrir: 'Abrir chat', fechar: 'Fechar chat', env: 'Enviar' },
    en: { on: 'Online now', ph: 'Type your question…', ola: 'Hi! 😊 I\'m ' + TITULO + '\'s virtual assistant. Ask me about prices, opening hours, insurance or booking.', sug: ['Prices', 'Opening hours', 'Insurance', 'Book a check-up'], err: 'Oops, I couldn\'t answer right now. Please try again.', by: 'Demo · chatbot by Antonio Rocha', tip: 'Hi! 👋 Need help with prices or hours?', abrir: 'Open chat', fechar: 'Close chat', env: 'Send' }
  };
  var host = document.createElement('div'); host.id = 'chat-widget-ar';
  var root = host.attachShadow({ mode: 'open' });
  root.innerHTML = '<style>' +
    ':host{all:initial}[hidden]{display:none!important}*{box-sizing:border-box;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}' +
    '.bub{position:fixed;right:22px;bottom:22px;width:62px;height:62px;border-radius:50%;border:0;background:' + COR + ';color:#fff;cursor:pointer;box-shadow:0 12px 30px -6px rgba(0,0,0,.35);display:grid;place-items:center;z-index:2147483000;transition:transform .2s}' +
    '.bub:hover{transform:scale(1.07)}.bub svg{width:28px;height:28px}' +
    '.ping{position:absolute;top:2px;right:2px;width:16px;height:16px;border-radius:50%;background:#ef4444;border:2px solid #fff;font-size:10px;color:#fff;display:grid;place-items:center;font-weight:700}' +
    '.tip{position:fixed;right:96px;bottom:34px;background:#fff;color:#0f172a;padding:10px 14px;border-radius:14px 14px 4px 14px;font-size:14px;box-shadow:0 10px 30px rgba(0,0,0,.18);z-index:2147483000;max-width:240px;animation:in .4s ease}' +
    '.box{position:fixed;right:22px;bottom:98px;width:370px;max-width:calc(100vw - 24px);height:560px;max-height:calc(100vh - 120px);background:#fff;border-radius:20px;box-shadow:0 30px 80px -20px rgba(15,23,42,.45);display:flex;flex-direction:column;overflow:hidden;z-index:2147483000;transform-origin:bottom right;animation:in .25s ease}' +
    '@keyframes in{from{opacity:0;transform:translateY(10px) scale(.97)}to{opacity:1;transform:none}}' +
    '.hd{background:' + COR + ';color:#fff;padding:16px 18px;display:flex;align-items:center;gap:12px}' +
    '.av{width:40px;height:40px;border-radius:50%;background:rgba(255,255,255,.25);display:grid;place-items:center;font-size:20px}' +
    '.hd b{display:block;font-size:15px}.hd small{font-size:12px;opacity:.9;display:flex;align-items:center;gap:6px}.hd small:before{content:"";width:8px;height:8px;border-radius:50%;background:#4ade80}' +
    '.x{margin-left:auto;background:transparent;border:0;color:#fff;font-size:22px;cursor:pointer;line-height:1;opacity:.85}' +
    '.ms{flex:1;overflow-y:auto;padding:16px;background:#f8fafc;display:flex;flex-direction:column;gap:10px}' +
    '.m{max-width:85%;padding:10px 14px;border-radius:16px;font-size:14px;line-height:1.45;white-space:pre-line;color:#0f172a;word-wrap:break-word}' +
    '.b{background:#fff;border:1px solid #e2e8f0;border-bottom-left-radius:4px;align-self:flex-start}' +
    '.u{background:' + COR + ';color:#fff;border-bottom-right-radius:4px;align-self:flex-end}' +
    '.sg{display:flex;flex-wrap:wrap;gap:6px}.sg button{border:1px solid ' + COR + ';background:#fff;color:' + COR + ';border-radius:999px;padding:6px 12px;font-size:13px;cursor:pointer}.sg button:hover{background:' + COR + ';color:#fff}' +
    '.ty{display:flex;gap:4px;padding:14px}.ty i{width:7px;height:7px;border-radius:50%;background:#94a3b8;animation:b 1s infinite}.ty i:nth-child(2){animation-delay:.15s}.ty i:nth-child(3){animation-delay:.3s}' +
    '@keyframes b{0%,60%,100%{transform:none;opacity:.5}30%{transform:translateY(-4px);opacity:1}}' +
    'form{display:flex;gap:8px;padding:12px;border-top:1px solid #e2e8f0;background:#fff}' +
    'input{flex:1;border:1px solid #e2e8f0;border-radius:12px;padding:11px 14px;font-size:14px;outline:none;color:#0f172a}input:focus{border-color:' + COR + '}' +
    '.sd{width:44px;border:0;border-radius:12px;background:' + COR + ';color:#fff;cursor:pointer;display:grid;place-items:center}.sd svg{width:18px;height:18px}' +
    '.ft{font-size:11px;text-align:center;color:#94a3b8;padding:0 0 8px;background:#fff}' +
    '@media (max-width:480px){.box{right:0;bottom:0;width:100vw;max-width:100vw;height:100%;max-height:100%;border-radius:0}.tip{display:none}.box:not([hidden])~.bub{display:none}}' +
    '</style>' +
    '<div class="tip" hidden></div>' +
    '<div class="box" hidden><div class="hd"><div class="av">🦷</div><div><b></b><small class="on"></small></div><button class="x" type="button">×</button></div>' +
    '<div class="ms" role="log" aria-live="polite"></div>' +
    '<form><input maxlength="500" autocomplete="off"><button class="sd" type="submit"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4 20-7z"/></svg></button></form><div class="ft"></div></div>' +
    '<button class="bub" type="button"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg><span class="ping">1</span></button>';
  var $ = function (q) { return root.querySelector(q); };
  var box = $('.box'), ms = $('.ms'), inp = $('input'), bub = $('.bub'), tip = $('.tip'), ping = $('.ping');
  var hist = [], aberto = false, iniciado = false, ocupado = false;
  $('.hd b').textContent = TITULO;
  function textos() { var t = T[lang()]; $('.on').textContent = t.on; inp.placeholder = t.ph; $('.ft').textContent = t.by; bub.setAttribute('aria-label', aberto ? t.fechar : t.abrir); $('.sd').setAttribute('aria-label', t.env); tip.textContent = t.tip; }
  function add(txt, cls) { var d = document.createElement('div'); d.className = 'm ' + cls; d.textContent = txt; ms.appendChild(d); ms.scrollTop = ms.scrollHeight; return d; }
  function sugs(lista) { if (!lista || !lista.length) return; var d = document.createElement('div'); d.className = 'sg'; lista.forEach(function (x) { var b = document.createElement('button'); b.type = 'button'; b.textContent = x; b.onclick = function () { d.remove(); enviar(x); }; d.appendChild(b); }); ms.appendChild(d); ms.scrollTop = ms.scrollHeight; }
  function abrir(v) {
    aberto = v; box.hidden = !v; tip.hidden = true; ping.style.display = 'none'; textos();
    bub.innerHTML = v ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>' : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>';
    if (v && !iniciado) { iniciado = true; var t = T[lang()]; add(t.ola, 'b'); sugs(t.sug); }
    if (v) setTimeout(function () { inp.focus(); }, 50);
  }
  function enviar(txt) {
    txt = (txt || '').trim(); if (!txt || ocupado) return; ocupado = true;
    root.querySelectorAll('.sg').forEach(function (e) { e.remove(); });
    add(txt, 'u'); inp.value = '';
    var ty = document.createElement('div'); ty.className = 'm b ty'; ty.innerHTML = '<i></i><i></i><i></i>'; ms.appendChild(ty); ms.scrollTop = ms.scrollHeight;
    var t0 = Date.now();
    fetch(API, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mensagem: txt, idioma: lang(), historico: hist.slice(-6) }) })
      .then(function (r) { return r.json(); })
      .then(function (d) { return new Promise(function (ok) { setTimeout(function () { ok(d); }, Math.max(0, 550 - (Date.now() - t0))); }); })
      .then(function (d) { ty.remove(); add(d.resposta, 'b'); sugs(d.sugestoes); hist.push({ role: 'user', content: txt }, { role: 'assistant', content: d.resposta }); })
      .catch(function () { ty.remove(); add(T[lang()].err, 'b'); })
      .then(function () { ocupado = false; });
  }
  bub.onclick = function () { abrir(!aberto); };
  $('.x').onclick = function () { abrir(false); };
  $('form').onsubmit = function (e) { e.preventDefault(); enviar(inp.value); };
  window.addEventListener('chatwidget:abrir', function (e) { abrir(true); if (e.detail) enviar(e.detail); });
  new MutationObserver(textos).observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
  function montar() { document.body.appendChild(host); textos(); if (s.getAttribute('data-abrir') === '1') abrir(true); else setTimeout(function () { if (!aberto && !iniciado) tip.hidden = false; }, 2500); }
  if (document.body) montar(); else document.addEventListener('DOMContentLoaded', montar);
})();
