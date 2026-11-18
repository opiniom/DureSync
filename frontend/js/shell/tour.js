/* ---- 사용 안내: 두레가 말풍선으로 알려 줘요 ----
   · 설명서는 아무도 안 읽으니, 실제 화면의 버튼을 두레(로고)가 말풍선으로 하나씩 가리키며 알려 준다.
   · 전체 투어(6단계)는 첫 로그인 때 한 번만, 화면별 힌트(워크스페이스·회의록·캘린더)는 그 화면에 처음 들어갔을 때 한 번만 뜬다.
   · 자동으로 뜬 순간 서버(users.tour_seen · users.hints_seen)에 저장돼 웹·앱·다른 기기에서도 다시 뜨지 않는다.
   · 다시 보기: 아바타 메뉴 > 사용 안내(전체) / 이 화면 안내(지금 보는 화면의 힌트)
   · 전체 투어 내용이 크게 바뀌면 TOUR_VERSION 을 올려 한 번 더 보여준다. */
var TOUR_VERSION = 1;
var TOUR = { on: false, i: 0, key: 'main', manual: false, steps: null, raf: 0, state: null, loading: null };
var TOUR_BIT = { workspace: 1, notes: 2, calendar: 4 };
var TOUR_LABEL = { workspace: '워크스페이스', notes: '회의록', calendar: '캘린더' };
var TOUR_IC = {
  plus: '<path d="M12 5v14M5 12h14"/>',
  code: '<path d="m9 8-4 4 4 4M15 8l4 4-4 4M13.5 5 10.5 19"/>',
  note: '<path d="M6 4h9l3 3v13H6z"/><path d="M9 12h6M9 16h6M9 8h3"/>',
  bell: '<path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6Z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
  user: '<circle cx="12" cy="8" r="3.4"/><path d="M5 20c1-3.8 3.6-5.7 7-5.7s6 1.9 7 5.7"/>',
  folder: '<path d="M3.5 7.5A2.5 2.5 0 0 1 6 5h3.3l2 2.2H18A2.5 2.5 0 0 1 20.5 9.7v7.8A2.5 2.5 0 0 1 18 20H6a2.5 2.5 0 0 1-2.5-2.5Z"/>',
  users: '<circle cx="9" cy="8.5" r="3.2"/><path d="M3 19c.4-3.2 2.7-5 6-5s5.6 1.8 6 5"/><path d="M16.5 5.6a3.2 3.2 0 0 1 0 5.8M18 14.4c1.7.6 2.7 2.1 3 4.6"/>',
  cal: '<rect x="4" y="5.5" width="16" height="14.5" rx="3"/><path d="M4 10h16M9 3.5v4M15 3.5v4"/>'
};
function tourSteps(key){
  if(key === 'workspace') return [
    { ic: 'folder', title: '프로젝트를 골라요', text: '작업할 프로젝트를 여기서 고르거나 새로 만들어요. 프로젝트마다 파일과 채팅, 팀원이 따로 있어요.', sel: ['#wsSelBtn'] },
    { ic: 'users', title: '팀원을 불러와요', text: '<b>팀원 초대</b>로 친구를 부르면 같은 파일을 실시간으로 함께 보고 고칠 수 있어요.', sel: ['#wsInviteBtn'] },
    { ic: 'code', title: '내 컴퓨터의 언어로 실행해요', text: '내 컴퓨터에 설치한 언어로 실행하고 싶다면 <b>내 PC</b>를 눌러 러너를 설치해요. 안내에 나온 한 줄을 터미널에 붙여넣으면 연결돼요. <b>PC에서만</b> 쓸 수 있어요.', sel: ['#wsRunnerBtnTop'] },
    { ic: 'code', title: '파일을 열고 실행해요', text: '왼쪽에서 파일을 만들고 열어요. 열린 파일은 바로 실행할 수 있고, <b>줄 번호 옆</b>을 누르면 한 줄씩 따라가는 디버거를 쓸 수 있어요. 채팅에서 <b>“두레야”</b>도 불러 보세요.', sel: ['#wsFileTree'], last: true }
  ];
  if(key === 'notes') return [
    { ic: 'folder', title: '프로젝트별로 봐요', text: '전체 프로젝트의 회의록을 한 번에 보거나, 프로젝트 하나만 골라서 볼 수 있어요.', sel: ['#noteSelBtn'] },
    { ic: 'note', title: '새 회의록은 여기서', text: '회의 내용을 적어 저장하면, 날짜가 들어 있는 일정을 AI가 찾아 <b>캘린더</b>에 넣어 줘요.', sel: ['[data-view="notes"] .btn.primary[onclick="openComposeModal()"]'], last: true }
  ];
  if(key === 'calendar') return [
    { ic: 'folder', title: '프로젝트 캘린더', text: '프로젝트를 골라 그 팀의 일정만 보거나, 전체를 한꺼번에 볼 수 있어요.', sel: ['#calSelBtn'] },
    { ic: 'plus', title: '일정을 추가해요', text: '직접 일정을 추가할 수 있어요. 회의록에서 AI가 찾은 일정도 이 캘린더에 함께 모여요.', sel: ['[data-view="calendar"] .btn.primary[onclick="openAddEvent()"]'] },
    { ic: 'cal', title: '달을 빠르게 옮겨요', text: '달 이름을 누르면 원하는 달로 바로 이동해요.', sel: ['#calMonthBtn'], last: true }
  ];
  return [
    { ic: 'mark', title: '두레에 오신 걸 환영해요', text: '처음이어도 막히지 않게, 꼭 알아야 할 곳만 30초 안에 보여 드릴게요.', center: true },
    { ic: 'plus', title: '프로젝트로 시작해요', text: '<b>새 프로젝트 만들기</b>로 내 공간을 만들고, <b>팀원 초대하기</b>로 친구와 팀원을 불러요. 혼자 시작해도 나중에 팀으로 이어져요.', sel: ['.home-cta'] },
    { ic: 'code', title: '코드는 워크스페이스에서', text: '설치 없이 코드를 쓰고 실행해요. 에러가 나면 AI가 어디가 왜 틀렸는지 쉬운 말로 알려 줘요. 채팅에서 <b>“두레야”</b>라고 부르면 AI가 도와줘요.', sel: ['#tabnav [data-view="workspace"]', '#mnav [data-view="workspace"]'] },
    { ic: 'note', title: '회의록과 캘린더', text: '회의 내용을 적으면 날짜가 들어 있는 일정을 AI가 찾아서 <b>캘린더</b>에 넣어 줘요. 팀 일정도 한곳에서 봐요.', sel: ['#tabnav [data-view="notes"]', '#mnav [data-view="notes"]'] },
    { ic: 'bell', title: '알림과 공지사항', text: '<b>종</b>은 내 일정·초대·소식, <b>확성기</b>는 운영자의 공지사항이에요. 떠오른 알림 팝업은 화면 아무 곳이나 누르면 사라지고, 기록은 알림함에 남아 있어요.', sel: ['#annBtn', '#bellBtn'], union: true },
    { ic: 'user', title: '내 메뉴와 문의하기', text: '마이페이지·설정 옆에 <b>문의하기</b>가 있어요. 불편한 점은 운영자에게 바로 남겨 주세요. 이 안내는 <b>사용 안내</b>에서 언제든 다시 볼 수 있어요.', sel: ['#avatarBtn'], last: true }
  ];
}
function tourVis(sel){
  var list = document.querySelectorAll(sel);
  for(var i = 0; i < list.length; i++){ var r = list[i].getBoundingClientRect(); if(r.width > 0 && r.height > 0) return list[i]; }
  return null;
}
function tourRect(step){
  if(!step.sel) return null;
  var els = [];
  if(step.union){ step.sel.forEach(function(s){ var e = tourVis(s); if(e) els.push(e); }); }
  else { for(var k = 0; k < step.sel.length; k++){ var e1 = tourVis(step.sel[k]); if(e1){ els.push(e1); break; } } }
  if(!els.length) return null;
  var l = 1e9, t = 1e9, r = -1e9, b = -1e9;
  els.forEach(function(e){ var q = e.getBoundingClientRect(); l = Math.min(l, q.left); t = Math.min(t, q.top); r = Math.max(r, q.right); b = Math.max(b, q.bottom); });
  return { left: l, top: t, width: r - l, height: b - t, el: els[0] };
}
function tourBuild(){
  var root = document.getElementById('tour'); if(root) return root;
  root = document.createElement('div'); root.id = 'tour'; root.className = 'tour'; root.setAttribute('role', 'dialog'); root.setAttribute('aria-modal', 'true'); root.setAttribute('aria-label', '사용 안내');
  root.innerHTML = '<div class="tour-dim"></div><div class="tour-spot"></div><div class="tour-bubble" id="tourBubble"></div>';
  document.body.appendChild(root); return root;
}
function tourIcon(name){
  if(name === 'mark') return '<span class="bm tour-mark" role="img" aria-hidden="true"></span>';
  return '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + TOUR_IC[name] + '</svg>';
}
function tourRender(){
  var step = TOUR.steps[TOUR.i], root = tourBuild(), bub = document.getElementById('tourBubble'), spot = root.querySelector('.tour-spot');
  var n = TOUR.steps.length, main = TOUR.key === 'main';
  var nodes = ''; for(var k = 0; k < n; k++) nodes += '<i class="' + (k < TOUR.i ? 'done' : (k === TOUR.i ? 'on' : '')) + '"></i>';
  var primary = main ? (TOUR.i === 0 ? '안내 보기' : (step.last ? '시작하기' : '다음')) : (step.last ? '알겠어요' : '다음');
  var skip = main ? (TOUR.i === 0 ? '건너뛰기' : '그만 보기') : '닫기';
  bub.innerHTML = '<span class="tour-badge"><i class="tour-ring"></i><span class="bm tour-mark" role="img" aria-hidden="true"></span></span>' +
    '<div class="tour-top"><span class="tour-who">' + (main ? '두레가 안내해요' : '두레 팁 · ' + TOUR_LABEL[TOUR.key]) + '</span><span class="tour-count">' + (TOUR.i + 1) + '<s>/</s>' + n + '</span></div>' +
    '<h4><span class="tour-ic">' + (step.ic === 'mark' ? '' : tourIcon(step.ic)) + '</span>' + step.title + '</h4>' +
    '<p>' + step.text + '</p>' +
    '<div class="tour-nodes" aria-hidden="true">' + nodes + '</div>' +
    '<div class="tour-act"><button type="button" class="tour-skip" data-a="skip">' + skip + '</button><span class="tour-sp"></span>' +
    (TOUR.i > 0 ? '<button type="button" class="tour-prev" data-a="prev">이전</button>' : '') +
    '<button type="button" class="tour-next" data-a="next">' + primary + '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></button></div>' +
    '<i class="tour-trail a"></i><i class="tour-trail b"></i>';
  Array.prototype.forEach.call(bub.querySelectorAll('button'), function(b){ b.onclick = function(){ var a = b.getAttribute('data-a'); if(a === 'next') tourNext(); else if(a === 'prev') tourPrev(); else tourEnd(); }; });
  root.classList.toggle('center', !!step.center);
  var tgt = tourRect(step);
  if(tgt && tgt.el && tgt.el.scrollIntoView){ var q = tgt.el.getBoundingClientRect(); if(q.top < 0 || q.bottom > window.innerHeight) tgt.el.scrollIntoView({ block: 'center' }); tgt = tourRect(step); }
  root.classList.toggle('no-target', !tgt);
  if(tgt){
    var pad = 7;
    spot.style.cssText = 'left:' + (tgt.left - pad) + 'px; top:' + (tgt.top - pad) + 'px; width:' + (tgt.width + pad * 2) + 'px; height:' + (tgt.height + pad * 2) + 'px;';
  }
  tourPlace(tgt);
  var nx = bub.querySelector('.tour-next'); if(nx) nx.focus({ preventScroll: true });
}
function tourPlace(tgt){
  var bub = document.getElementById('tourBubble'); if(!bub) return;
  var vw = document.documentElement.clientWidth, vh = window.innerHeight;
  bub.style.left = bub.style.top = '0px';
  var bw = bub.offsetWidth, bh = bub.offsetHeight, m = 12, ab = bub.querySelector('.tour-trail.a'), bb = bub.querySelector('.tour-trail.b');
  if(!tgt){ bub.style.left = Math.max(m, (vw - bw) / 2) + 'px'; bub.style.top = Math.max(m, (vh - bh) / 2) + 'px'; bub.classList.remove('up', 'down'); return; }
  var below = tgt.top + tgt.height + 18 + bh + m <= vh, top = below ? tgt.top + tgt.height + 26 : Math.max(m, tgt.top - bh - 26);
  var cx = tgt.left + tgt.width / 2, left = Math.min(Math.max(m, cx - bw / 2), vw - bw - m);
  bub.style.left = left + 'px'; bub.style.top = top + 'px';
  bub.classList.toggle('up', below); bub.classList.toggle('down', !below);        // up: 말풍선이 대상 아래 → 꼬리 점이 위로
  var x = Math.min(Math.max(26, cx - left), bw - 26);
  if(ab) ab.style.left = x + 'px'; if(bb) bb.style.left = (x + (cx - left > x ? 0 : (cx - left - x) * 0.3)) + 'px';
}
function tourReflow(){ if(!TOUR.on) return; cancelAnimationFrame(TOUR.raf); TOUR.raf = requestAnimationFrame(function(){ tourRender(); }); }
function tourNext(){
  if(TOUR.i >= TOUR.steps.length - 1){ tourEnd(true); return; }
  TOUR.i++; if(typeof closeMenus === 'function') closeMenus(); tourRender();
}
function tourPrev(){ if(TOUR.i > 0){ TOUR.i--; if(typeof closeMenus === 'function') closeMenus(); tourRender(); } }
function startTour(manual, key){
  if(TOUR.on) return;
  key = key || 'main';
  if(typeof closeMenus === 'function') closeMenus();
  if(key === 'main'){ var v0 = document.querySelector('.view.active'); if(!v0 || v0.dataset.view !== 'home') goView('home'); }
  setTimeout(function(){
    var steps = tourSteps(key).filter(function(s){ return s.center || tourRect(s); });       // 지금 화면에 없는 버튼을 가리키는 단계는 건너뛴다
    if(steps.length && key !== 'main') steps[steps.length - 1].last = true;
    if(!steps.length || TOUR.on) return;
    TOUR.manual = !!manual; TOUR.key = key; TOUR.steps = steps; TOUR.i = 0; TOUR.on = true;
    document.documentElement.classList.add('tour-on');
    if(!manual) tourMark(key);          // 자동으로 뜬 순간 '봤어요' 저장 (탭을 그냥 닫아도 다시 뜨지 않게)
    tourRender();
  }, key === 'main' ? 120 : 0);
}
/* '봤어요'를 저장한다. 자동으로 뜬 순간 바로 저장하므로, 끝까지 안 보고 탭을 닫아도 다음에 또 뜨지 않는다. */
function tourMark(key){
  var uid = (currentUser && currentUser.id) || 'x';
  if(key === 'main'){
    try { localStorage.setItem('sync_tour_v_' + uid, String(TOUR_VERSION)); } catch(e){}
    if(TOUR.state) TOUR.state.tour_seen = TOUR_VERSION;
    if(authToken) apiFetch('/api/onboarding/tour', { method: 'POST', body: JSON.stringify({ version: TOUR_VERSION }) }).catch(function(){});
  } else {
    var bit = TOUR_BIT[key] || 0;
    try { localStorage.setItem('sync_hints_' + uid, String((parseInt(localStorage.getItem('sync_hints_' + uid), 10) || 0) | bit)); } catch(e){}
    if(TOUR.state) TOUR.state.hints_seen = (TOUR.state.hints_seen || 0) | bit;
    if(authToken) apiFetch('/api/onboarding/hint', { method: 'POST', body: JSON.stringify({ key: key }) }).catch(function(){});
  }
}
function tourEnd(){
  if(!TOUR.on) return;
  var key = TOUR.key; TOUR.on = false; document.documentElement.classList.remove('tour-on');
  var root = document.getElementById('tour'); if(root) root.remove();
  tourMark(key);                       // (이미 저장돼 있어도 한 번 더 — 직접 '다시 보기'로 본 경우 포함)
}
/* 서버에 저장된 '봤어요' 상태 (한 번만 불러온다) */
function tourState(){
  if(TOUR.state) return Promise.resolve(TOUR.state);
  if(!authToken || !currentUser) return Promise.resolve(null);
  if(!TOUR.loading){
    var uid = currentUser.id;
    TOUR.loading = apiFetch('/api/onboarding').then(function(d){
      var lt = 0, lh = 0; try { lt = parseInt(localStorage.getItem('sync_tour_v_' + uid), 10) || 0; lh = parseInt(localStorage.getItem('sync_hints_' + uid), 10) || 0; } catch(e){}
      TOUR.state = { tour_seen: Math.max(d.tour_seen || 0, lt), hints_seen: (d.hints_seen || 0) | lh }; return TOUR.state;
    }).catch(function(){ TOUR.loading = null; return null; });
  }
  return TOUR.loading;
}
async function tourAuto(){
  if(TOUR.on || !authToken || !currentUser) return;
  var st = await tourState(); if(!st || st.tour_seen >= TOUR_VERSION) return;
  setTimeout(function(){
    var v = document.querySelector('.view.active');
    if(!v || v.dataset.view !== 'home' || document.querySelector('.modal-backdrop.open') || TOUR.on) return;       // 다른 화면·창을 쓰는 중이면 다음 기회에
    startTour(false);
  }, 1200);
}
/* 화면별 첫 방문 힌트: 그 화면에 처음 들어갔을 때 한 번만 (전체 투어를 먼저 본 사람에게만) */
async function tourViewHint(view){
  if(!TOUR_BIT[view] || TOUR.on || !authToken || !currentUser) return;
  var st = await tourState(); if(!st || st.tour_seen < TOUR_VERSION || (st.hints_seen & TOUR_BIT[view])) return;
  setTimeout(function(){
    var v = document.querySelector('.view.active');
    if(!v || v.dataset.view !== view || TOUR.on || document.querySelector('.modal-backdrop.open') || (TOUR.state.hints_seen & TOUR_BIT[view])) return;
    startTour(false, view);
  }, 900);
}
/* 아바타 메뉴: 지금 보는 화면에 힌트가 있으면 '이 화면 안내'를 보여준다 */
function tourMenuSync(){
  var b = document.getElementById('avatarHintBtn'); if(!b) return;
  var v = document.querySelector('.view.active'), k = v && v.dataset.view;
  b.hidden = !TOUR_BIT[k]; b.setAttribute('data-k', k || '');
}
function tourHintHere(){ var b = document.getElementById('avatarHintBtn'); var k = b && b.getAttribute('data-k'); if(k && TOUR_BIT[k]) startTour(true, k); }
window.addEventListener('resize', tourReflow);
window.addEventListener('scroll', tourReflow, { passive: true, capture: true });
document.addEventListener('keydown', function(e){
  if(!TOUR.on) return;
  if(e.key === 'Escape'){ e.preventDefault(); tourEnd(); }
  else if(e.key === 'ArrowRight'){ e.preventDefault(); tourNext(); }
  else if(e.key === 'ArrowLeft'){ e.preventDefault(); tourPrev(); }
}, true);
