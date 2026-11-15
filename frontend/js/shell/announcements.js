/* ---- 공지사항 (알림과 따로) ----
   · 알림 = 내 일정·초대·소식 (종 모양)    · 공지사항 = 서비스 전체 안내 (확성기 모양)
   · 운영자가 올리면 접속 중인 사람에게는 실시간으로 '새 공지' 팝업이 한 번 뜨고, 확성기 단추에 빨간 점이 생긴다.
   · 공지사항을 열어 보면 '여기까지 확인했어요'가 서버에 저장돼 웹·설치한 앱·다른 기기에서 같이 사라진다. */
var AN = { toast: null, items: [], unseen: 0, known: null, busy: false, tok: null, shownNew: {}, openIds: {} };
function anDate(iso){ return ntDate(iso); }
function anWhen(iso){
  var d = anDate(iso); if(!d) return '';
  var rel = ntRel(iso);
  return /전$|^방금$|^어제$/.test(rel) ? rel : (d.getFullYear() + '.' + (d.getMonth() + 1) + '.' + d.getDate());
}
function anBadge(){
  var el = document.getElementById('annCount'); if(!el) return;
  el.style.display = AN.unseen > 0 ? 'flex' : 'none'; el.textContent = AN.unseen > 9 ? '9+' : AN.unseen;
  var pill = document.getElementById('annPill'); if(pill){ pill.hidden = AN.unseen === 0; pill.textContent = AN.unseen + '개 새 공지'; }
}
function anRender(){
  var box = document.getElementById('annList'); if(!box) return;
  box.innerHTML = '';
  if(!AN.items.length){
    var e = document.createElement('div'); e.className = 'nt-empty';
    e.innerHTML = '<div class="nt-empty-ic">' + ntIcon('notice', 26) + '</div><b>아직 공지가 없어요</b><span>서비스 소식과 점검 안내가 올라오면 여기에 모여요.</span>';
    box.appendChild(e); return;
  }
  AN.items.forEach(function(a){
    var isOpen = !!AN.openIds[a.id];
    var it = document.createElement('div'); it.className = 'ann-item' + (a.new ? ' new' : '') + (isOpen ? ' open' : '');
    var h = document.createElement('button'); h.type = 'button'; h.className = 'ann-h'; h.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    var t = document.createElement('span'); t.className = 'ann-t'; t.textContent = a.title;
    var nw = document.createElement('i'); nw.className = 'ann-new'; nw.textContent = 'NEW';
    var d = document.createElement('span'); d.className = 'ann-d'; d.textContent = anWhen(a.created_at);
    var ch = document.createElement('span'); ch.className = 'ann-chev'; ch.innerHTML = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>';
    h.appendChild(nw); h.appendChild(t); h.appendChild(d); h.appendChild(ch);
    var b = document.createElement('div'); b.className = 'ann-b';
    var p = document.createElement('p'); p.textContent = a.message; b.appendChild(p);
    if(a.link){ var go = document.createElement('button'); go.type = 'button'; go.className = 'ann-go'; go.textContent = '자세히 보기'; go.onclick = function(){ closeMenus(); if(typeof openNotifLink === 'function') openNotifLink(a.link); }; b.appendChild(go); }
    h.onclick = function(){ var on = !it.classList.contains('open'); it.classList.toggle('open', on); h.setAttribute('aria-expanded', on ? 'true' : 'false'); AN.openIds[a.id] = on; };
    it.appendChild(h); it.appendChild(b); box.appendChild(it);
  });
}
async function loadAnnouncements(announce){
  if(!authToken){ AN.items = []; AN.unseen = 0; AN.known = null; anBadge(); anRender(); return; }
  if(AN.tok !== authToken){ AN.tok = authToken; AN.known = null; }
  if(AN.busy) return; AN.busy = true;
  try {
    var res = await fetch(API_BASE + '/api/announcements', { headers: { 'Authorization': 'Bearer ' + authToken } });
    if(res.ok){
      var d = await res.json(), items = d.items || [];
      var fresh = items.filter(function(a){ return a.new && AN.known && !AN.known[a.id]; });
      AN.known = AN.known || {}; items.forEach(function(a){ AN.known[a.id] = 1; });
      var open = document.getElementById('annPanel') && document.getElementById('annPanel').classList.contains('open');
      if(open) items.forEach(function(a){ if(AN.shownNew[a.id]) a.new = true; });          // 열려 있는 동안은 NEW 표시를 그대로 둔다
      AN.items = items; AN.unseen = open ? 0 : (d.unseen || 0);
      anBadge(); anRender();
      if(open && d.unseen) annSeen();
      if(announce && fresh.length && !open){            // 새 공지는 팝업 하나로만 (여러 개여도 한 번)
        var top = fresh[0], cnt = Math.max(fresh.length, d.unseen || 0);
        if(AN.toast && AN.toast.isConnected) dismissToast(AN.toast);                // 이미 떠 있는 '새 공지' 팝업은 하나로 합친다
        pushToast(null, cnt > 1 ? '새 공지 ' + cnt + '개' : '새 공지가 올라왔어요', top.title, { category: 'notice', duration: 8000, onclick: function(){ var b = document.getElementById('annBtn'); if(b) b.click(); } });
        var stk = document.getElementById('toastStack'); AN.toast = stk ? stk.querySelector('.toast:last-of-type:not(.out)') : null;
      }
    }
  } catch(e){}
  AN.busy = false;
}
function annSeen(){
  if(!authToken) return;
  fetch(API_BASE + '/api/announcements/seen', { method: 'POST', headers: { 'Authorization': 'Bearer ' + authToken } }).catch(function(){});
}
function anFit(){ var p = document.getElementById('annPanel'); if(!p) return; if(window.matchMedia && matchMedia('(max-width:640px)').matches){ p.style.right = ''; p.style.left = ''; return; } fitPopover('annPanel', -6); }      // 폰에서는 화면 너비에 맞춰 꽉 차게 (CSS)
function toggleAnn(e){
  e.stopPropagation();
  var p = document.getElementById('annPanel'), wasOpen = p.classList.contains('open');
  closeMenus();
  if(!wasOpen){
    p.classList.add('open'); anFit();
    AN.shownNew = {}; AN.items.forEach(function(a){ if(a.new) AN.shownNew[a.id] = 1; });
    AN.openIds = {}; var fn = AN.items.filter(function(a){ return a.new; })[0]; if(fn) AN.openIds[fn.id] = true;      // 가장 새 공지는 펼쳐서 보여준다
    anRender();
    if(AN.unseen){ AN.unseen = 0; anBadge(); annSeen(); }        // 열어 본 순간 확인한 것으로 (이번에 연 화면에서는 NEW 표시가 남아 있다)
    loadAnnouncements(false);
  }
}
window.addEventListener('resize', function(){ var p = document.getElementById('annPanel'); if(p && p.classList.contains('open')) anFit(); });
