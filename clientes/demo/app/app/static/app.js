/* OrçaFácil · demo PWA por Antonio Rocha. Dados ficam no localStorage do aparelho. */
(function () {
  'use strict';
  var KEY = 'orcafacil:v1', LKEY = 'demo-lang';
  var I = {
    pt: {
      demo: '📱 <b>Demonstração</b> de app PWA: instale, use sem internet. Os dados ficam só no seu aparelho. · <a href="/">← Portfólio de Antonio Rocha</a>',
      online: 'Online', offline: 'Sem internet · tudo salvo no aparelho', instalar: '⬇ Instalar', inicio: 'Início', orcs: 'Orçamentos', agenda: 'Agenda', ajustes: 'Ajustes',
      ola: 'Olá! 👋', receber: 'Aprovado este mês', pend: 'Em aberto', aprov: 'Aprovados', prox: 'Próximos compromissos', recentes: 'Orçamentos recentes', verTodos: 'Ver todos',
      semAg: 'Nenhum compromisso agendado.', semOrc: 'Nenhum orçamento ainda.', toqueMais: 'Toque em + para criar.', buscar: 'Buscar cliente ou serviço…',
      todos: 'Todos', pendente: 'Pendente', aprovado: 'Aprovado', recusado: 'Recusado', exemplo: 'EXEMPLO',
      novoOrc: 'Novo orçamento', editOrc: 'Editar orçamento', cliente: 'Cliente', telefone: 'Telefone', itens: 'Itens', desc: 'Descrição', qtd: 'Qtd', valor: 'Valor', addItem: '+ Adicionar item',
      desconto: 'Desconto (%)', validade: 'Válido até', obs: 'Observações', status: 'Status', total: 'Total', subtotal: 'Subtotal', salvar: 'Salvar', cancelar: 'Cancelar', excluir: 'Excluir',
      compartilhar: 'Compartilhar', imprimir: 'PDF / Imprimir', editar: 'Editar', duplicar: 'Duplicar', confirmaExc: 'Excluir este item?', salvo: 'Salvo ✓', excluido: 'Excluído', copiado: 'Texto copiado ✓',
      novoAg: 'Novo compromisso', editAg: 'Editar compromisso', titulo: 'O que vai fazer', data: 'Data', hora: 'Hora', hoje: 'Hoje', amanha: 'Amanhã', nota: 'Anotação',
      preencha: 'Preencha o nome do cliente e pelo menos um item.', preenchaAg: 'Preencha o título e a data.',
      seuNome: 'Seu nome ou empresa (sai no orçamento)', backup: 'Backup', exportar: 'Exportar dados (.json)', importar: 'Importar backup', limparEx: 'Remover dados de exemplo', apagarTudo: 'Apagar tudo',
      sobre: 'Sobre este app', sobreTxt: 'App web progressivo (PWA): instala no Android, iPhone e computador, abre sem internet e guarda os dados no próprio aparelho. Feito por Antonio Rocha como demonstração.',
      iosDica: 'No iPhone: toque em Compartilhar ⬆️ e depois em “Adicionar à Tela de Início”.', instalado: 'App instalado ✓', importado: 'Backup importado ✓', importErro: 'Arquivo inválido',
      confirmaTudo: 'Apagar todos os dados deste aparelho?', orcTxt: 'Orçamento', validoAte: 'Válido até', de: 'de', semData: 'sem data', venceu: 'vencido', itensN: 'itens', item1: 'item'
    },
    en: {
      demo: '📱 <b>PWA demo</b>: install it and use it offline. Data stays on your device only. · <a href="/">← Antonio Rocha\'s portfolio</a>',
      online: 'Online', offline: 'Offline · everything saved on device', instalar: '⬇ Install', inicio: 'Home', orcs: 'Quotes', agenda: 'Schedule', ajustes: 'Settings',
      ola: 'Hello! 👋', receber: 'Approved this month', pend: 'Open', aprov: 'Approved', prox: 'Upcoming appointments', recentes: 'Recent quotes', verTodos: 'See all',
      semAg: 'No appointments scheduled.', semOrc: 'No quotes yet.', toqueMais: 'Tap + to create one.', buscar: 'Search client or service…',
      todos: 'All', pendente: 'Pending', aprovado: 'Approved', recusado: 'Declined', exemplo: 'SAMPLE',
      novoOrc: 'New quote', editOrc: 'Edit quote', cliente: 'Client', telefone: 'Phone', itens: 'Items', desc: 'Description', qtd: 'Qty', valor: 'Price', addItem: '+ Add item',
      desconto: 'Discount (%)', validade: 'Valid until', obs: 'Notes', status: 'Status', total: 'Total', subtotal: 'Subtotal', salvar: 'Save', cancelar: 'Cancel', excluir: 'Delete',
      compartilhar: 'Share', imprimir: 'PDF / Print', editar: 'Edit', duplicar: 'Duplicate', confirmaExc: 'Delete this item?', salvo: 'Saved ✓', excluido: 'Deleted', copiado: 'Text copied ✓',
      novoAg: 'New appointment', editAg: 'Edit appointment', titulo: 'What', data: 'Date', hora: 'Time', hoje: 'Today', amanha: 'Tomorrow', nota: 'Note',
      preencha: 'Fill in the client name and at least one item.', preenchaAg: 'Fill in the title and date.',
      seuNome: 'Your name or company (shown on quotes)', backup: 'Backup', exportar: 'Export data (.json)', importar: 'Import backup', limparEx: 'Remove sample data', apagarTudo: 'Erase everything',
      sobre: 'About this app', sobreTxt: 'Progressive web app (PWA): installs on Android, iPhone and desktop, opens offline and keeps data on the device. Built by Antonio Rocha as a demo.',
      iosDica: 'On iPhone: tap Share ⬆️ then “Add to Home Screen”.', instalado: 'App installed ✓', importado: 'Backup imported ✓', importErro: 'Invalid file',
      confirmaTudo: 'Erase all data on this device?', orcTxt: 'Quote', validoAte: 'Valid until', de: 'from', semData: 'no date', venceu: 'expired', itensN: 'items', item1: 'item'
    }
  };
  var lang = (new URLSearchParams(location.search).get('lang')) || ls(LKEY) || 'pt'; if (lang !== 'en') lang = 'pt';
  function t(k) { return I[lang][k] || k; }
  function ls(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function $(q) { return document.querySelector(q); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function uid() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 7); }
  function brl(v) { return (Number(v) || 0).toLocaleString(lang === 'en' ? 'en-US' : 'pt-BR', { style: 'currency', currency: 'BRL' }); }
  function iso(d) { var z = new Date(d.getTime() - d.getTimezoneOffset() * 60000); return z.toISOString().slice(0, 10); }
  function addDias(n) { var d = new Date(); d.setDate(d.getDate() + n); return iso(d); }
  function fmtData(s) {
    if (!s) return t('semData');
    if (s === addDias(0)) return t('hoje'); if (s === addDias(1)) return t('amanha');
    var d = new Date(s + 'T12:00:00'); return d.toLocaleDateString(lang === 'en' ? 'en-US' : 'pt-BR', { weekday: 'short', day: '2-digit', month: 'short' });
  }

  // ---------- dados ----------
  var db;
  function carregar() { try { db = JSON.parse(ls(KEY)); } catch (e) { db = null; } if (!db || !db.orcs) { db = semente(); salvar(); } }
  function salvar() { try { localStorage.setItem(KEY, JSON.stringify(db)); } catch (e) { toast('⚠️ localStorage'); } }
  function semente() {
    return {
      cfg: { nome: '' },
      orcs: [
        { id: uid(), ex: 1, cliente: 'Padaria Pão Dourado', tel: '(11) 98888-1111', status: 'aprovado', criado: addDias(-3), validade: addDias(12), desconto: 0, obs: 'Entrega em 7 dias.', itens: [{ d: 'Site institucional', q: 1, v: 1200 }, { d: 'Cardápio digital', q: 1, v: 350 }] },
        { id: uid(), ex: 1, cliente: 'Studio Bella Unhas', tel: '(11) 97777-2222', status: 'pendente', criado: addDias(-1), validade: addDias(6), desconto: 10, obs: '', itens: [{ d: 'Logo + identidade visual', q: 1, v: 480 }, { d: 'Posts para Instagram', q: 8, v: 35 }] },
        { id: uid(), ex: 1, cliente: 'Oficina Rápida', tel: '', status: 'recusado', criado: addDias(-9), validade: addDias(-2), desconto: 0, obs: '', itens: [{ d: 'Sistema de agendamento', q: 1, v: 2400 }] }
      ],
      agenda: [
        { id: uid(), ex: 1, titulo: 'Reunião de briefing', cliente: 'Studio Bella Unhas', data: addDias(0), hora: '15:00', nota: 'Levar exemplos de logo', feito: false },
        { id: uid(), ex: 1, titulo: 'Entregar primeira versão', cliente: 'Padaria Pão Dourado', data: addDias(1), hora: '10:00', nota: '', feito: false },
        { id: uid(), ex: 1, titulo: 'Ligar para retorno', cliente: 'Oficina Rápida', data: addDias(3), hora: '09:30', nota: '', feito: false },
        { id: uid(), ex: 1, titulo: 'Enviar orçamento', cliente: 'Padaria Pão Dourado', data: addDias(-1), hora: '11:00', nota: '', feito: true }
      ]
    };
  }
  function totais(o) { var s = (o.itens || []).reduce(function (a, i) { return a + (Number(i.q) || 0) * (Number(i.v) || 0); }, 0); var d = s * (Number(o.desconto) || 0) / 100; return { sub: s, desc: d, total: s - d }; }

  // ---------- UI base ----------
  var aba = new URLSearchParams(location.search).get('aba') || 'inicio', filtro = 'todos', busca = '';
  var TABS = [['inicio', '🏠'], ['orcs', '🧾'], ['agenda', '📅'], ['ajustes', '⚙️']];
  function toast(m) { var e = $('#toast'); e.textContent = m; e.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(function () { e.hidden = true; }, 2200); }
  function textosFixos() {
    document.documentElement.lang = lang === 'en' ? 'en' : 'pt-BR';
    $('#demoBar').innerHTML = t('demo'); $('#lang').textContent = lang === 'en' ? 'PT' : 'EN'; $('#install').textContent = t('instalar');
    $('#tabs').innerHTML = TABS.map(function (x) { return '<button data-tab="' + x[0] + '" class="' + (aba === x[0] ? 'on' : '') + '"><span>' + x[1] + '</span>' + t(x[0]) + '</button>'; }).join('');
    rede();
  }
  function rede() { var n = $('#net'); n.textContent = navigator.onLine ? t('online') : t('offline'); n.className = navigator.onLine ? '' : 'off'; }
  function render() {
    textosFixos();
    var v = $('#view');
    v.innerHTML = aba === 'orcs' ? vOrcs() : aba === 'agenda' ? vAgenda() : aba === 'ajustes' ? vAjustes() : vInicio();
    $('#fab').hidden = aba === 'ajustes';
    window.scrollTo(0, 0);
  }
  function itemOrc(o) {
    var tt = totais(o), n = (o.itens || []).length;
    return '<div class="item" data-ver="' + o.id + '"><div class="ic">🧾</div><div class="mid"><b>' + esc(o.cliente) + '</b><span>' + (o.ex ? '<span class="ex">' + t('exemplo') + '</span> ' : '') + n + ' ' + (n === 1 ? t('item1') : t('itensN')) + ' · ' + fmtData(o.criado) + '</span></div><div class="rt">' + brl(tt.total) + '<br><span class="badge b-' + o.status + '">' + t(o.status) + '</span></div></div>';
  }
  function itemAg(a) {
    return '<div class="item ' + (a.feito ? 'done' : '') + '" data-ag="' + a.id + '"><button class="chk" data-feito="' + a.id + '" aria-label="ok">' + (a.feito ? '✓' : '') + '</button><div class="mid"><b>' + esc(a.titulo) + '</b><span>' + (a.ex ? '<span class="ex">' + t('exemplo') + '</span> ' : '') + esc(a.cliente || '') + (a.nota ? ' · ' + esc(a.nota) : '') + '</span></div><div class="rt">' + esc(a.hora || '') + '</div></div>';
  }
  function vInicio() {
    var mes = iso(new Date()).slice(0, 7);
    var aprovMes = db.orcs.filter(function (o) { return o.status === 'aprovado' && (o.criado || '').slice(0, 7) === mes; }).reduce(function (a, o) { return a + totais(o).total; }, 0);
    var pend = db.orcs.filter(function (o) { return o.status === 'pendente'; });
    var aprov = db.orcs.filter(function (o) { return o.status === 'aprovado'; });
    var hoje = addDias(0);
    var prox = db.agenda.filter(function (a) { return !a.feito && a.data >= hoje; }).sort(ordAg).slice(0, 3);
    var rec = db.orcs.slice().sort(function (a, b) { return (b.criado || '').localeCompare(a.criado || ''); }).slice(0, 3);
    return '<h2>' + (db.cfg.nome ? esc(db.cfg.nome) : t('ola')) + '</h2>' +
      '<div class="hero"><small>' + t('receber') + '</small><div class="big">' + brl(aprovMes) + '</div><div class="row"><div><b>' + pend.length + '</b><span>' + t('pend') + ' · ' + brl(pend.reduce(function (a, o) { return a + totais(o).total; }, 0)) + '</span></div><div><b>' + aprov.length + '</b><span>' + t('aprov') + '</span></div></div></div>' +
      '<h3>' + t('prox') + '</h3><div class="list">' + (prox.length ? prox.map(function (a) { return itemAg(a).replace('<div class="rt">', '<div class="rt"><small style="color:var(--p);font-weight:800">' + fmtData(a.data) + '</small><br>'); }).join('') : '<div class="empty" style="padding:16px">' + t('semAg') + '</div>') + '</div>' +
      '<h3>' + t('recentes') + '</h3><div class="list">' + (rec.length ? rec.map(itemOrc).join('') : vazio(t('semOrc'))) + '</div>';
  }
  function vazio(m) { return '<div class="empty"><div>🗂️</div><b>' + m + '</b><br>' + t('toqueMais') + '</div>'; }
  function vOrcs() {
    var q = busca.toLowerCase();
    var l = db.orcs.filter(function (o) { return (filtro === 'todos' || o.status === filtro) && (!q || (o.cliente + ' ' + o.itens.map(function (i) { return i.d; }).join(' ')).toLowerCase().indexOf(q) >= 0); })
      .sort(function (a, b) { return (b.criado || '').localeCompare(a.criado || ''); });
    return '<h2>' + t('orcs') + '</h2><input class="search" id="busca" placeholder="' + t('buscar') + '" value="' + esc(busca) + '">' +
      '<div class="filters">' + ['todos', 'pendente', 'aprovado', 'recusado'].map(function (f) { return '<button data-filtro="' + f + '" class="' + (filtro === f ? 'on' : '') + '">' + t(f) + '</button>'; }).join('') + '</div>' +
      '<div class="list">' + (l.length ? l.map(itemOrc).join('') : vazio(t('semOrc'))) + '</div>';
  }
  function ordAg(a, b) { return (a.data + (a.hora || '')).localeCompare(b.data + (b.hora || '')); }
  function vAgenda() {
    var l = db.agenda.slice().sort(ordAg), html = '', dia = null, hoje = addDias(0);
    l.forEach(function (a) { if (a.data !== dia) { dia = a.data; html += '<div class="day ' + (dia === hoje ? 'today' : '') + '">' + fmtData(dia) + '</div>'; } html += itemAg(a); });
    return '<h2>' + t('agenda') + '</h2><div class="list">' + (html || vazio(t('semAg'))) + '</div>';
  }
  function vAjustes() {
    return '<h2>' + t('ajustes') + '</h2><div class="card"><label style="margin-top:0">' + t('seuNome') + '</label><input class="in" id="cfgNome" value="' + esc(db.cfg.nome) + '" maxlength="60"></div>' +
      '<div class="card"><b>' + t('backup') + '</b><div class="row2"><button class="btn bs" id="exp">' + t('exportar') + '</button><label class="btn bs" style="margin:0;text-align:center;color:var(--p);font-size:inherit">' + t('importar') + '<input type="file" id="imp" accept="application/json,.json" hidden></label></div>' +
      '<div class="row2"><button class="btn bs" id="limpEx">' + t('limparEx') + '</button><button class="btn bd" id="apagar">' + t('apagarTudo') + '</button></div></div>' +
      '<div class="card"><b>' + t('sobre') + '</b><p>' + t('sobreTxt') + '</p><p id="iosHint" hidden>' + t('iosDica') + '</p><p style="font-size:12px">v' + esc(window.VERSAO) + '</p></div>';
  }

  // ---------- folhas (formularios) ----------
  function abrirSheet(html) { var s = $('#sheet'); s.innerHTML = '<div class="grab"></div>' + html; s.hidden = false; $('#sheetBg').hidden = false; document.body.style.overflow = 'hidden'; }
  function fecharSheet() { $('#sheet').hidden = true; $('#sheetBg').hidden = true; document.body.style.overflow = ''; }
  function linhaItem(i) { return '<div class="it"><input class="in" data-k="d" placeholder="' + t('desc') + '" value="' + esc(i.d) + '"><input class="in" data-k="q" type="number" min="0" step="1" inputmode="numeric" placeholder="' + t('qtd') + '" value="' + esc(i.q) + '"><input class="in" data-k="v" type="number" min="0" step="0.01" inputmode="decimal" placeholder="' + t('valor') + '" value="' + esc(i.v) + '"><button type="button" class="rm" data-rm>×</button></div>'; }
  function formOrc(id, copia) {
    var o = id ? JSON.parse(JSON.stringify(db.orcs.find(function (x) { return x.id === id; }))) : null;
    if (copia && o) { o.id = null; o.status = 'pendente'; o.ex = 0; o.criado = addDias(0); }
    o = o || { cliente: '', tel: '', status: 'pendente', validade: addDias(15), desconto: 0, obs: '', itens: [{ d: '', q: 1, v: '' }] };
    abrirSheet('<h2>' + (o.id ? t('editOrc') : t('novoOrc')) + '</h2><form id="fOrc" data-id="' + (o.id || '') + '">' +
      '<label>' + t('cliente') + '</label><input class="in" name="cliente" required maxlength="80" value="' + esc(o.cliente) + '">' +
      '<label>' + t('telefone') + '</label><input class="in" name="tel" inputmode="tel" maxlength="30" value="' + esc(o.tel) + '">' +
      '<label>' + t('itens') + '</label><div class="its" id="its">' + o.itens.map(linhaItem).join('') + '</div><button type="button" class="add" id="addIt">' + t('addItem') + '</button>' +
      '<div class="g2"><div><label>' + t('desconto') + '</label><input class="in" name="desconto" type="number" min="0" max="100" step="1" value="' + esc(o.desconto) + '"></div><div><label>' + t('validade') + '</label><input class="in" name="validade" type="date" value="' + esc(o.validade) + '"></div></div>' +
      '<label>' + t('status') + '</label><div class="seg" id="seg">' + ['pendente', 'aprovado', 'recusado'].map(function (s) { return '<button type="button" data-st="' + s + '" class="' + (o.status === s ? 'on' : '') + '">' + t(s) + '</button>'; }).join('') + '</div>' +
      '<label>' + t('obs') + '</label><textarea class="in" name="obs" rows="2" maxlength="500">' + esc(o.obs) + '</textarea>' +
      '<div class="tot" id="tot"></div>' +
      '<div class="acts"><button type="button" class="btn bs" data-fechar>' + t('cancelar') + '</button><button class="btn bp">' + t('salvar') + '</button></div></form>');
    var f = $('#fOrc'); f._status = o.status; f._criado = o.criado || addDias(0); f._ex = o.ex || 0;
    atualizaTot();
  }
  function lerOrc() {
    var f = $('#fOrc');
    var itens = Array.prototype.map.call(f.querySelectorAll('.it'), function (r) { return { d: r.querySelector('[data-k=d]').value.trim(), q: Number(r.querySelector('[data-k=q]').value) || 0, v: Number(r.querySelector('[data-k=v]').value) || 0 }; }).filter(function (i) { return i.d; });
    return { id: f.dataset.id || uid(), ex: f._ex, cliente: f.cliente.value.trim(), tel: f.tel.value.trim(), status: f._status, criado: f._criado, validade: f.validade.value, desconto: Math.min(100, Math.max(0, Number(f.desconto.value) || 0)), obs: f.obs.value.trim(), itens: itens };
  }
  function atualizaTot() { var tt = totais(lerOrc()); $('#tot').innerHTML = '<div><small>' + t('subtotal') + ' ' + brl(tt.sub) + (tt.desc ? ' · −' + brl(tt.desc) : '') + '</small>' + t('total') + '</div><div>' + brl(tt.total) + '</div>'; }
  function verOrc(id) {
    var o = db.orcs.find(function (x) { return x.id === id; }); if (!o) return; var tt = totais(o);
    var venc = o.validade && o.validade < addDias(0) && o.status === 'pendente';
    abrirSheet('<h2>' + esc(o.cliente) + ' <span class="badge b-' + o.status + '">' + t(o.status) + '</span></h2>' + (o.tel ? '<div style="color:var(--mut)">📞 ' + esc(o.tel) + '</div>' : '') +
      '<div class="list" style="margin-top:12px">' + o.itens.map(function (i) { return '<div class="item" style="cursor:default"><div class="mid"><b>' + esc(i.d) + '</b><span>' + i.q + ' × ' + brl(i.v) + '</span></div><div class="rt">' + brl(i.q * i.v) + '</div></div>'; }).join('') + '</div>' +
      '<div class="tot"><div><small>' + t('subtotal') + ' ' + brl(tt.sub) + (tt.desc ? ' · −' + o.desconto + '%' : '') + '</small>' + t('total') + '</div><div>' + brl(tt.total) + '</div></div>' +
      '<p style="color:' + (venc ? 'var(--bad)' : 'var(--mut)') + ';font-size:13px">' + t('validoAte') + ' ' + fmtData(o.validade) + (venc ? ' · ' + t('venceu') : '') + (o.obs ? '<br>' + esc(o.obs) : '') + '</p>' +
      '<div class="seg" id="segVer" data-id="' + o.id + '">' + ['pendente', 'aprovado', 'recusado'].map(function (s) { return '<button type="button" data-st2="' + s + '" class="' + (o.status === s ? 'on' : '') + '">' + t(s) + '</button>'; }).join('') + '</div>' +
      '<div class="acts"><button class="btn bp" data-share="' + o.id + '">' + t('compartilhar') + '</button><button class="btn bs" data-print="' + o.id + '">' + t('imprimir') + '</button></div>' +
      '<div class="acts" style="margin-top:8px"><button class="btn bs" data-edit="' + o.id + '">' + t('editar') + '</button><button class="btn bs" data-dup="' + o.id + '">' + t('duplicar') + '</button><button class="btn bd" data-del="' + o.id + '">' + t('excluir') + '</button></div>');
  }
  function textoOrc(o) {
    var tt = totais(o);
    return '*' + t('orcTxt') + (db.cfg.nome ? ' · ' + db.cfg.nome : '') + '*\n' + t('cliente') + ': ' + o.cliente + '\n\n' +
      o.itens.map(function (i) { return '• ' + i.d + ' (' + i.q + ' × ' + brl(i.v) + ') = ' + brl(i.q * i.v); }).join('\n') +
      (tt.desc ? '\n' + t('desconto') + ': −' + brl(tt.desc) : '') + '\n*' + t('total') + ': ' + brl(tt.total) + '*\n' + t('validoAte') + ' ' + (o.validade || '-') + (o.obs ? '\n\n' + o.obs : '');
  }
  function imprimir(o) {
    var tt = totais(o);
    $('#print').innerHTML = '<h1 style="margin:0">' + t('orcTxt') + '</h1><p>' + esc(db.cfg.nome || 'OrçaFácil') + ' · ' + new Date().toLocaleDateString(lang === 'en' ? 'en-US' : 'pt-BR') + '</p><p><b>' + t('cliente') + ':</b> ' + esc(o.cliente) + (o.tel ? ' · ' + esc(o.tel) : '') + '</p>' +
      '<table><tr><th>' + t('desc') + '</th><th class="r">' + t('qtd') + '</th><th class="r">' + t('valor') + '</th><th class="r">' + t('total') + '</th></tr>' + o.itens.map(function (i) { return '<tr><td>' + esc(i.d) + '</td><td class="r">' + i.q + '</td><td class="r">' + brl(i.v) + '</td><td class="r">' + brl(i.q * i.v) + '</td></tr>'; }).join('') +
      (tt.desc ? '<tr><td colspan="3" class="r">' + t('desconto') + '</td><td class="r">−' + brl(tt.desc) + '</td></tr>' : '') + '<tr><th colspan="3" class="r">' + t('total') + '</th><th class="r">' + brl(tt.total) + '</th></tr></table>' +
      '<p>' + t('validoAte') + ' ' + esc(o.validade || '-') + '</p>' + (o.obs ? '<p>' + esc(o.obs) + '</p>' : '');
    setTimeout(function () { window.print(); }, 50);
  }
  function formAg(id) {
    var a = id ? db.agenda.find(function (x) { return x.id === id; }) : { titulo: '', cliente: '', data: addDias(0), hora: '', nota: '' };
    abrirSheet('<h2>' + (id ? t('editAg') : t('novoAg')) + '</h2><form id="fAg" data-id="' + (id || '') + '">' +
      '<label>' + t('titulo') + '</label><input class="in" name="titulo" maxlength="80" required value="' + esc(a.titulo) + '">' +
      '<label>' + t('cliente') + '</label><input class="in" name="cliente" maxlength="80" list="clis" value="' + esc(a.cliente) + '"><datalist id="clis">' + Array.from(new Set(db.orcs.map(function (o) { return o.cliente; }))).map(function (c) { return '<option value="' + esc(c) + '">'; }).join('') + '</datalist>' +
      '<div class="g2"><div><label>' + t('data') + '</label><input class="in" name="data" type="date" required value="' + esc(a.data) + '"></div><div><label>' + t('hora') + '</label><input class="in" name="hora" type="time" value="' + esc(a.hora) + '"></div></div>' +
      '<label>' + t('nota') + '</label><input class="in" name="nota" maxlength="200" value="' + esc(a.nota) + '">' +
      '<div class="acts">' + (id ? '<button type="button" class="btn bd" data-delag="' + id + '">' + t('excluir') + '</button>' : '<button type="button" class="btn bs" data-fechar>' + t('cancelar') + '</button>') + '<button class="btn bp">' + t('salvar') + '</button></div></form>');
  }

  // ---------- eventos ----------
  document.addEventListener('click', function (e) {
    var el = e.target.closest('button,[data-ver],[data-ag],label'); if (!el) { if (e.target.id === 'sheetBg') fecharSheet(); return; }
    var d = el.dataset;
    if (d.tab) { aba = d.tab; busca = ''; render(); }
    else if (d.filtro) { filtro = d.filtro; render(); }
    else if (d.feito) { e.stopPropagation(); var a = db.agenda.find(function (x) { return x.id === d.feito; }); a.feito = !a.feito; salvar(); render(); }
    else if (d.ver) verOrc(d.ver);
    else if (d.ag) formAg(d.ag);
    else if (d.fechar !== undefined) fecharSheet();
    else if (d.rm !== undefined) { if ($('#its').children.length > 1) el.parentNode.remove(); atualizaTot(); }
    else if (el.id === 'addIt') { $('#its').insertAdjacentHTML('beforeend', linhaItem({ d: '', q: 1, v: '' })); $('#its').lastChild.querySelector('input').focus(); }
    else if (d.st) { $('#fOrc')._status = d.st; el.parentNode.querySelectorAll('button').forEach(function (b) { b.classList.toggle('on', b === el); }); }
    else if (d.st2) { var o = db.orcs.find(function (x) { return x.id === el.parentNode.dataset.id; }); o.status = d.st2; salvar(); verOrc(o.id); render(); toast(t('salvo')); }
    else if (d.edit) formOrc(d.edit);
    else if (d.dup) formOrc(d.dup, true);
    else if (d.del) { if (confirm(t('confirmaExc'))) { db.orcs = db.orcs.filter(function (x) { return x.id !== d.del; }); salvar(); fecharSheet(); render(); toast(t('excluido')); } }
    else if (d.delag) { if (confirm(t('confirmaExc'))) { db.agenda = db.agenda.filter(function (x) { return x.id !== d.delag; }); salvar(); fecharSheet(); render(); toast(t('excluido')); } }
    else if (d.share) { var so = db.orcs.find(function (x) { return x.id === d.share; }), txt = textoOrc(so); if (navigator.share) navigator.share({ title: t('orcTxt') + ' · ' + so.cliente, text: txt }).catch(function () {}); else if (navigator.clipboard) navigator.clipboard.writeText(txt).then(function () { toast(t('copiado')); }); }
    else if (d.print) imprimir(db.orcs.find(function (x) { return x.id === d.print; }));
    else if (el.id === 'fab') { if (aba === 'agenda') formAg(); else formOrc(); }
    else if (el.id === 'lang') { lang = lang === 'en' ? 'pt' : 'en'; try { localStorage.setItem(LKEY, lang); } catch (x) {} render(); }
    else if (el.id === 'exp') { var b = new Blob([JSON.stringify(db, null, 2)], { type: 'application/json' }), u = URL.createObjectURL(b), l = document.createElement('a'); l.href = u; l.download = 'orcafacil-backup-' + addDias(0) + '.json'; l.click(); setTimeout(function () { URL.revokeObjectURL(u); }, 1000); }
    else if (el.id === 'limpEx') { db.orcs = db.orcs.filter(function (x) { return !x.ex; }); db.agenda = db.agenda.filter(function (x) { return !x.ex; }); salvar(); toast(t('salvo')); }
    else if (el.id === 'apagar') { if (confirm(t('confirmaTudo'))) { db = { cfg: { nome: '' }, orcs: [], agenda: [] }; salvar(); render(); } }
    else if (el.id === 'install') instalar();
  });
  $('#sheetBg').addEventListener('click', fecharSheet);
  document.addEventListener('input', function (e) {
    if (e.target.closest && e.target.closest('#fOrc')) atualizaTot();
    if (e.target.id === 'busca') { busca = e.target.value; var p = e.target.selectionStart; render(); var b = $('#busca'); b.focus(); b.setSelectionRange(p, p); }
    if (e.target.id === 'cfgNome') { db.cfg.nome = e.target.value; salvar(); }
  });
  document.addEventListener('change', function (e) {
    if (e.target.id !== 'imp' || !e.target.files[0]) return;
    var r = new FileReader(); r.onload = function () { try { var x = JSON.parse(r.result); if (!Array.isArray(x.orcs) || !Array.isArray(x.agenda)) throw 0; db = { cfg: x.cfg || { nome: '' }, orcs: x.orcs, agenda: x.agenda }; salvar(); render(); toast(t('importado')); } catch (er) { toast(t('importErro')); } }; r.readAsText(e.target.files[0]);
  });
  document.addEventListener('submit', function (e) {
    e.preventDefault();
    if (e.target.id === 'fOrc') {
      var o = lerOrc(); if (!o.cliente || !o.itens.length) { toast(t('preencha')); return; }
      var i = db.orcs.findIndex(function (x) { return x.id === o.id; }); if (i >= 0) db.orcs[i] = o; else db.orcs.unshift(o);
      salvar(); fecharSheet(); if (aba === 'ajustes' || aba === 'agenda') aba = 'orcs'; render(); toast(t('salvo'));
    } else if (e.target.id === 'fAg') {
      var f = e.target, id = f.dataset.id, a = { id: id || uid(), titulo: f.titulo.value.trim(), cliente: f.cliente.value.trim(), data: f.data.value, hora: f.hora.value, nota: f.nota.value.trim(), feito: false };
      if (!a.titulo || !a.data) { toast(t('preenchaAg')); return; }
      var j = db.agenda.findIndex(function (x) { return x.id === id; }); if (j >= 0) { a.feito = db.agenda[j].feito; a.ex = db.agenda[j].ex; db.agenda[j] = a; } else db.agenda.push(a);
      salvar(); fecharSheet(); render(); toast(t('salvo'));
    }
  });
  window.addEventListener('online', rede); window.addEventListener('offline', rede);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') fecharSheet(); });

  // ---------- instalacao (PWA) ----------
  var promptInstal = null;
  var standalone = window.matchMedia('(display-mode: standalone)').matches || navigator.standalone;
  window.addEventListener('beforeinstallprompt', function (e) { e.preventDefault(); promptInstal = e; $('#install').hidden = false; });
  window.addEventListener('appinstalled', function () { $('#install').hidden = true; toast(t('instalado')); });
  var ios = /iphone|ipad|ipod/i.test(navigator.userAgent) && !standalone;
  if (ios) $('#install').hidden = false;
  function instalar() {
    if (promptInstal) { promptInstal.prompt(); promptInstal.userChoice.then(function () { promptInstal = null; $('#install').hidden = true; }); }
    else if (ios) toast(t('iosDica'));
  }
  if ('serviceWorker' in navigator) window.addEventListener('load', function () { navigator.serviceWorker.register(window.BASE + '/sw.js', { scope: window.BASE + '/' }).catch(function () {}); });

  carregar(); render();
  if (new URLSearchParams(location.search).get('novo') === 'orcamento') formOrc();
})();
