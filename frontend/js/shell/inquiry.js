/* ---- 1:1 문의 (사용자 → 관리자) ----
   · 아바타 메뉴 > 문의하기. 앱 안에서 바로 남기고, 관리자 페이지 '문의' 탭에 실시간으로 올라간다.
   · 어느 화면에서 남겼는지 · 웹/앱 · 브라우저 · 화면 크기가 자동으로 함께 간다(내용을 길게 설명하지 않아도 원인을 찾기 쉽게).
   · 관리자가 답하면 알림으로 오고, 누르면 이 창의 그 문의가 열린다. 같은 문의 안에서 이어서 대화할 수 있다. */
var INQ = { items: [], unread: 0, cur: null, view: 'list', cat: 'bug', busy: false };
var INQ_CATS = [['bug', '오류 · 불편'], ['idea', '건의 · 아이디어'], ['account', '계정'], ['etc', '기타']];
var INQ_ST = { open: '접수', progress: '처리 중', done: '완료' };
function inqEl(tag, cls, text){ var e = document.createElement(tag); if(cls) e.className = cls; if(text != null) e.textContent = text; return e; }
function inqApi(path, opts){ return apiFetch('/api/inquiries' + path, opts); }
function inqWhen(iso){ var d = ntDate(iso); if(!d) return ''; var r = ntRel(iso); return /전$|^방금$|^어제$/.test(r) ? r : (d.getMonth() + 1) + '월 ' + d.getDate() + '일'; }
function inqClient(){
  var ua = navigator.userAgent || '', br = /Edg\//.test(ua) ? 'Edge' : /OPR\//.test(ua) ? 'Opera' : /Chrome\//.test(ua) ? 'Chrome' : /Safari\//.test(ua) ? 'Safari' : /Firefox\//.test(ua) ? 'Firefox' : '브라우저';
  var os = /Android/.test(ua) ? 'Android' : /iPhone|iPad|iPod/.test(ua) ? 'iOS' : /Mac/.test(ua) ? 'Mac' : /Windows/.test(ua) ? 'Windows' : /Linux/.test(ua) ? 'Linux' : '';
  return ((typeof pwaStandalone === 'function' && pwaStandalone()) ? '설치한 앱' : '웹') + ' · ' + br + (os ? ' · ' + os : '') + ' · ' + window.innerWidth + '×' + window.innerHeight;
}
function inqPage(){ var v = document.querySelector('.view.active'); var k = v && v.dataset.view; return (typeof PAGE_TITLES !== 'undefined' && PAGE_TITLES[k]) || k || ''; }
function inqBadge(){
  var n = INQ.unread;
  var d = document.getElementById('inqAvatarDot'); if(d) d.hidden = !n;
  var b = document.getElementById('inqMenuBadge'); if(b){ b.hidden = !n; b.textContent = n > 9 ? '9+' : n; }
}
async function loadInquiries(){
  if(!authToken){ INQ.items = []; INQ.unread = 0; inqBadge(); return; }
  try { var d = await inqApi(''); INQ.items = d.items || []; INQ.unread = d.unread || 0; } catch(e){}
  inqBadge();
}
function inqOpen(){ var m = document.getElementById('inqModal'); return !!(m && m.classList.contains('open')); }
function inqLive(){                                         // 관리자가 답했거나 상태가 바뀜(알림 신호와 함께 온다)
  loadInquiries().then(function(){
    if(!inqOpen()) return;
    if(INQ.view === 'list') inqShowList();
    else if(INQ.view === 'thread' && INQ.cur) inqShowThread(INQ.cur, true);
  });
}
function openInquiry(id){
  if(!authToken){ if(typeof openLogin === 'function') openLogin(); return; }
  if(typeof closeMenus === 'function') closeMenus();
  var m = document.getElementById('inqModal'); if(!m) return;
  m.classList.add('open');
  if(id) inqShowThread(id); else inqShowList();
  loadInquiries().then(function(){ if(!id && INQ.view === 'list') inqShowList(); });
}
function closeInquiry(){ var m = document.getElementById('inqModal'); if(m) m.classList.remove('open'); }
function inqHead(title, back){
  var h = document.getElementById('inqHead'); h.innerHTML = '';
  if(back){ var b = inqEl('button', 'icon-btn inq-back'); b.type = 'button'; b.setAttribute('aria-label', '목록으로'); b.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 6-6 6 6 6"/></svg>'; b.onclick = back; h.appendChild(b); }
  h.appendChild(inqEl('h3', '', title));
  var x = inqEl('button', 'icon-btn'); x.type = 'button'; x.setAttribute('aria-label', '닫기'); x.innerHTML = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M18 6 6 18"/></svg>'; x.onclick = closeInquiry; h.appendChild(x);
}
function inqStatusChip(st){ return inqEl('span', 'inq-chip st-' + st, INQ_ST[st] || st); }
function inqShowList(){
  INQ.view = 'list'; INQ.cur = null; inqHead('1:1 문의');
  var body = document.getElementById('inqBody'); body.innerHTML = '';
  body.appendChild(inqEl('p', 'inq-lead', '불편한 점이나 바라는 점을 운영자에게 바로 남겨 주세요. 답변이 오면 알림으로 알려 드려요.'));
  var nb = inqEl('button', 'btn primary inq-new', '새 문의 남기기'); nb.type = 'button'; nb.onclick = inqShowForm; body.appendChild(nb);
  var list = inqEl('div', 'inq-list');
  if(!INQ.items.length){ list.appendChild(inqEl('div', 'inq-empty', '아직 남긴 문의가 없어요.')); }
  INQ.items.forEach(function(q){
    var it = inqEl('button', 'inq-item' + (q.unread ? ' unread' : '')); it.type = 'button';
    var top = inqEl('div', 'inq-item-top'); top.appendChild(inqEl('b', '', q.title)); if(q.unread) top.appendChild(inqEl('i', 'inq-new-dot', '새 답변'));
    var meta = inqEl('div', 'inq-item-meta'); meta.appendChild(inqStatusChip(q.status)); meta.appendChild(inqEl('span', '', q.category_label)); meta.appendChild(inqEl('span', 'inq-time', inqWhen(q.updated_at)));
    it.appendChild(top); it.appendChild(meta); it.onclick = function(){ inqShowThread(q.id); }; list.appendChild(it);
  });
  body.appendChild(list);
}
function inqShowForm(){
  INQ.view = 'form'; inqHead('새 문의', inqShowList);
  var body = document.getElementById('inqBody'); body.innerHTML = '';
  var chips = inqEl('div', 'inq-cats');
  INQ_CATS.forEach(function(c){ var b = inqEl('button', 'inq-cat' + (INQ.cat === c[0] ? ' on' : ''), c[1]); b.type = 'button'; b.onclick = function(){ INQ.cat = c[0]; Array.prototype.forEach.call(chips.children, function(x, i){ x.classList.toggle('on', INQ_CATS[i][0] === INQ.cat); }); }; chips.appendChild(b); });
  var t = inqEl('input', 'inq-input'); t.type = 'text'; t.maxLength = 120; t.placeholder = '제목 (예: 저장 버튼이 눌리지 않아요)'; t.id = 'inqTitle';
  var m = inqEl('textarea', 'inq-input inq-ta'); m.rows = 6; m.maxLength = 2000; m.placeholder = '어떤 상황인지 적어 주세요. (무엇을 하려고 했고, 어떻게 됐는지)'; m.id = 'inqMsg';
  var info = inqEl('p', 'inq-info', '문의를 남긴 화면과 사용 환경(웹/앱 · 브라우저 · 화면 크기)이 함께 전달돼요: ' + inqPage() + ' · ' + inqClient());
  var send = inqEl('button', 'btn primary inq-send', '문의 남기기'); send.type = 'button';
  send.onclick = async function(){
    var title = t.value.trim(), msg = m.value.trim();
    if(!title || !msg){ pushToast('⚠️', '제목과 내용을 입력해 주세요', ''); return; }
    if(INQ.busy) return; INQ.busy = true; send.disabled = true;
    try {
      var r = await inqApi('', { method: 'POST', body: JSON.stringify({ category: INQ.cat, title: title, message: msg, page: inqPage(), client: inqClient() }) });
      pushToast('✅', '문의를 남겼어요', '답변이 오면 알림으로 알려 드릴게요.');
      await loadInquiries(); inqShowThread(r.id);
    } catch(e){ pushToast('⚠️', '문의를 남기지 못했어요', (e && e.message) || ''); }
    INQ.busy = false; send.disabled = false;
  };
  [chips, t, m, info, send].forEach(function(e){ body.appendChild(e); });
  setTimeout(function(){ t.focus(); }, 60);
}
async function inqShowThread(id, quiet){
  var body = document.getElementById('inqBody');
  var keepScroll = quiet && body ? body.scrollTop : null;
  var draft = document.getElementById('inqReply'); var draftVal = draft ? draft.value : '';
  var q;
  try { q = await inqApi('/' + id); } catch(e){ pushToast('⚠️', '문의를 열지 못했어요', (e && e.message) || ''); inqShowList(); return; }
  INQ.view = 'thread'; INQ.cur = id; inqHead(q.title, function(){ loadInquiries().then(inqShowList); });
  body.innerHTML = '';
  var meta = inqEl('div', 'inq-thread-meta'); meta.appendChild(inqStatusChip(q.status)); meta.appendChild(inqEl('span', '', q.category_label)); meta.appendChild(inqEl('span', 'inq-time', inqWhen(q.created_at))); body.appendChild(meta);
  var thread = inqEl('div', 'inq-thread');
  q.messages.forEach(function(msg){
    var b = inqEl('div', 'inq-msg ' + (msg.sender === 'admin' ? 'admin' : 'me'));
    b.appendChild(inqEl('span', 'inq-who', msg.sender === 'admin' ? '운영자' : '나')); b.appendChild(inqEl('p', '', msg.text)); b.appendChild(inqEl('time', '', inqWhen(msg.created_at))); thread.appendChild(b);
  });
  body.appendChild(thread);
  if(q.status === 'done') body.appendChild(inqEl('p', 'inq-done', '완료된 문의예요. 더 궁금한 점이 있으면 아래에 이어서 적어 주세요.'));
  var box = inqEl('div', 'inq-replybox');
  var ta = inqEl('textarea', 'inq-input inq-ta'); ta.rows = 3; ta.maxLength = 2000; ta.id = 'inqReply'; ta.placeholder = '이어서 적기…'; ta.value = draftVal;
  var sb = inqEl('button', 'btn primary', '보내기'); sb.type = 'button';
  sb.onclick = async function(){
    var text = ta.value.trim(); if(!text) return; sb.disabled = true;
    try { await inqApi('/' + id + '/messages', { method: 'POST', body: JSON.stringify({ text: text }) }); await loadInquiries(); inqShowThread(id); }
    catch(e){ pushToast('⚠️', '보내지 못했어요', (e && e.message) || ''); sb.disabled = false; }
  };
  box.appendChild(ta); box.appendChild(sb); body.appendChild(box);
  body.scrollTop = keepScroll !== null ? keepScroll : body.scrollHeight;
  loadInquiries();
}
document.addEventListener('keydown', function(e){ if(e.key === 'Escape' && inqOpen()) closeInquiry(); });
