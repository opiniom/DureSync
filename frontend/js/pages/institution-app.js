/* ---- 기관용 로그인 (/institution/login) · 기관용 첫 화면 (/institution/app) ----
   기관용 계정은 비즈니스 계정과 완전히 따로다 (서버: routers/inst.py · 별도 DB 파일 · 별도 토큰 종류 / 화면: 로그인 정보도 따로 저장한다).
     · 선생님(교수 · 교사 · 기관 담당자): 구글 로그인 → 처음이면 기관을 만들고(기관 코드 발급) 학생을 등록한다
     · 학생: 기관 코드 + 아이디 + 비밀번호로 로그인 (선생님이 등록, 첫 로그인에서 비밀번호를 바꾼다)
   ★ 지금은 '기본 틀'이다: 로그인 · 기관 만들기 · 학생 등록 · 비밀번호 바꾸기만 실제로 동작하고, 나머지 메뉴는 소개 페이지(js/pages/institution.js)에
     적어 둔 구상대로 화면의 구성(표의 칸)만 잡아 두었다. 선생님 화면과 학생 화면은 메뉴가 다르다 (소개 페이지의 '역할별' 카드와 같은 구성). */

var INST_TK = 'sync_inst_token';
var instToken = null, instUser = null, INST_ERR = '';
try { instToken = localStorage.getItem(INST_TK) || null; } catch(e){}
/* 구글 로그인을 다녀오면 주소에 itoken(성공) 또는 inst_error(실패)가 붙어 온다 — 한 번 읽고 주소에서 지운다 */
(function(){ try {
  var q = new URLSearchParams(location.search);
  if(q.has('itoken')){ instToken = q.get('itoken'); try { localStorage.setItem(INST_TK, instToken); } catch(e){} history.replaceState({}, '', location.pathname); }
  if(q.has('inst_error')){ INST_ERR = q.get('inst_error') || 'failed'; history.replaceState({}, '', location.pathname); }
} catch(e){} })();
var INST_ERRORS = { cancelled: '로그인을 취소했어요.', google_keys_missing: '구글 로그인 설정이 아직 없어요.', state: '로그인 확인이 만료됐어요. 다시 시도해 주세요.', inactive: '사용할 수 없는 계정이에요.', no_email: '구글 계정에서 이메일을 받지 못했어요.' };
if(INST_ERR) setTimeout(function(){ if(typeof pushToast === 'function') pushToast('⚠️', '기관용 로그인을 못 했어요', INST_ERRORS[INST_ERR] || '잠시 뒤에 다시 시도해 주세요. (' + INST_ERR + ')'); }, 700);

var IA = { tab: 'teams' };
function instRole(){ return instUser && instUser.role === 'student' ? 'student' : 'teacher'; }

/* ---------- 서버 호출 · 로그인 정보 ---------- */
async function instFetch(path, opts){
  opts = opts || {};
  var h = { 'Content-Type': 'application/json' }; if(instToken) h.Authorization = 'Bearer ' + instToken;
  var r = await fetch(API_BASE + '/api/inst' + path, Object.assign({}, opts, { headers: Object.assign(h, opts.headers || {}) }));
  var j = null; try { j = await r.json(); } catch(e){}
  if(r.status === 401 && instToken){ instClear(); goView('instlogin'); }          // 로그인이 만료됐다
  if(!r.ok){
    var msg = (j && typeof j.detail === 'string') ? j.detail : (r.status === 422 ? '입력한 내용을 확인해 주세요.' : r.status === 429 ? '너무 자주 했어요. 잠시 뒤에 다시 해 주세요.' : '요청에 실패했어요 (' + r.status + ')');
    var err = new Error(msg); err.status = r.status; throw err;
  }
  return j;
}
function instClear(){ instToken = null; instUser = null; try { localStorage.removeItem(INST_TK); } catch(e){} }
function instSetSession(d){
  instToken = d.access_token; instUser = d.user;
  try { localStorage.setItem(INST_TK, instToken); } catch(e){}
  goView('instapp');
}
function instLogout(){ instClear(); goView('institution'); }                 // 기관용 로그아웃은 비즈니스 로그인에 영향이 없다

/* ---------- 소개 페이지 버튼 · 로그인 화면 ---------- */
function instEnter(){ goView(instToken ? 'instapp' : 'instlogin'); }
function instLoginTab(k){
  var t = k === 'student';
  document.getElementById('inTabTeacher').classList.toggle('on', !t); document.getElementById('inTabTeacher').setAttribute('aria-selected', String(!t));
  document.getElementById('inTabStudent').classList.toggle('on', t); document.getElementById('inTabStudent').setAttribute('aria-selected', String(t));
  document.getElementById('inPaneTeacher').hidden = t; document.getElementById('inPaneStudent').hidden = !t;
  var f = document.getElementById(t ? 'inOrg' : null); if(f) f.focus();
}
async function instTeacherLogin(){
  try {
    var c = await fetch(API_BASE + '/api/inst/config').then(function(r){ return r.ok ? r.json() : {}; });
    if(c.dev_auto_login){ instSetSession(await instFetch('/auth/dev-auto', { method: 'POST' })); return; }         // 임시(로컬) 서버: 구글을 거치지 않고 바로
    if(!c.google_enabled){ pushToast('ℹ️', '구글 로그인 설정이 아직 없어요', '서버에 구글 로그인 키가 등록되어야 해요.'); return; }
    window.location.href = API_BASE + '/api/inst/auth/google/login';
  } catch(e){ pushToast('⚠️', '로그인을 시작하지 못했어요', e.message || ''); }
}
async function instStudentLogin(ev){
  if(ev && ev.preventDefault) ev.preventDefault();
  var err = document.getElementById('inStuErr'), btn = document.getElementById('inStuBtn');
  err.hidden = true; btn.disabled = true;
  try {
    var d = await instFetch('/auth/student-login', { method: 'POST', body: JSON.stringify({ org_code: document.getElementById('inOrg').value.trim(), login_id: document.getElementById('inLid').value.trim(), password: document.getElementById('inPw').value }) });
    document.getElementById('inPw').value = '';
    instSetSession(d);
  } catch(e){ err.textContent = e.message; err.hidden = false; }
  finally { btn.disabled = false; }
  return false;
}

/* ---------- 역할별 메뉴 (소개 페이지의 '메뉴 묶음 · 역할별 카드'와 같은 구성) ---------- */
var IA_MENU = {
  teacher: [{ g: '팀별', ks: ['teams', 'accts', 'sheet'] }, { g: '워크스페이스 · 소통', ks: ['files', 'chat'] }, { g: '프로젝트', ks: ['settings'] }],
  student: [{ g: '워크스페이스 · 소통', ks: ['files', 'chat'] }, { g: '사람', ks: ['profile', 'community'] }]
};
var IA_HELLO = { teacher: '수업 속 팀 프로젝트를 한눈에 살피고, 공정하게 이끌어요.', student: '내 파일에 집중하고, 팀과 소통해요.' };
/* 표 모양 틀: cols = 칸 이름, w = 칸 너비(grid), n = 빈 줄 수 */
function iaTable(cols, w, n){
  var rows = ''; for(var r = 0; r < n; r++){ rows += '<div class="ia-tr">' + cols.map(function(c, i){ return '<span><i style="--w:' + (46 + ((r * 3 + i * 5) % 5) * 11) + '%"></i></span>'; }).join('') + '</div>'; }
  return '<div class="ia-tb" style="--cols:' + w + '" aria-hidden="true"><div class="ia-tr ia-th">' + cols.map(function(c){ return '<span>' + c + '</span>'; }).join('') + '</div>' + rows + '</div>';
}
function iaChips(list, on){ return '<div class="ia-chips" aria-hidden="true">' + list.map(function(c, i){ return '<span class="chip' + (i === (on || 0) ? ' on' : '') + '">' + c + '</span>'; }).join('') + '</div>'; }
function iaStats(list){ return '<div class="ia-stats" aria-hidden="true">' + list.map(function(s){ return '<div><small>' + s + '</small><b>—</b></div>'; }).join('') + '</div>'; }

var IA_TABS = {
  teams: { ic: 'flag', c: '#3B82F6', t: '팀별 진행 현황', d: '팀마다 진행률과 최근 활동을 한눈에 보고, 지연 주의 팀을 바로 찾아요.',
    body: function(){ return iaStats(['전체 진행', '이번 주 활동', '지연 주의']) + iaChips(['전체', '진행 중', '지연 주의', '완료']) + iaTable(['팀', '진행률', '상태', '팀원', '최근 활동'], '1.6fr 1.4fr .9fr 1fr 1fr', 3); } },
  accts: { ic: 'users', c: '#8B5CF6', t: '계정 일괄 관리', d: '수강생 명단으로 학생 계정을 한 번에 등록해요. 학생은 기관 코드와 아이디, 비밀번호로 로그인해요.', real: true,
    body: function(){ return '<div id="iaAccts"><p class="ia-hint">불러오는 중…</p></div>'; } },
  sheet: { ic: 'board', c: '#F59E0B', t: '과제 스프레드시트', d: '과제 제출이 필요하면 스프레드시트로 받고, AI가 기본 채점을 해 주면 평가자가 수정해서 확정해요.',
    body: function(){ return iaTable(['이름', '제출물', '기준 1', '기준 2', 'AI 점수', '확정'], '1fr 1.4fr .7fr .7fr .9fr .9fr', 4) + '<p class="ia-hint"><b>AI는 기본 채점</b>까지만 해요. 점수는 <b>평가자가 수정하고 확정</b>해요.</p>'; } },
  files: { ic: 'code', c: '#22C55E', t: '파일 자동 생성 · 권한', d: '인원별 폴더와 파일이 자동으로 만들어져요. 교수 · 교사는 모두 열고, 학생은 내 파일만 열어요.',
    body: function(role){
      return role === 'student'
        ? '<div class="ia-files" aria-hidden="true"><div class="ia-f on"><b>내 폴더</b><span>열기</span></div><div class="ia-f lock"><b>다른 사람 폴더</b><span>접근 제한</span></div><div class="ia-f lock"><b>다른 사람 폴더</b><span>접근 제한</span></div></div><p class="ia-hint">학생은 <b>내 폴더와 파일</b> 중심으로 써요.</p>'
        : '<div class="ia-files" aria-hidden="true"><div class="ia-f"><b>인원별 폴더</b><span>열기</span></div><div class="ia-f"><b>인원별 폴더</b><span>열기</span></div><div class="ia-f"><b>인원별 폴더</b><span>열기</span></div></div><p class="ia-hint">교수 · 교사는 <b>모든 파일</b>을 볼 수 있어요.</p>'; } },
  chat: { ic: 'chat', c: '#EC4899', t: '팀 채팅 · 1:1 톡방', d: '통화는 빼고 채팅은 그대로. 팀장(교수 · 교사 · 기관 담당자)과 1:1 톡방으로 물어볼 수 있어요.',
    body: function(role){ return '<div class="ia-chat" aria-hidden="true"><div class="ia-cl"><div class="on"><b>팀 채팅</b><small>팀원</small></div><div><b>' + (role === 'student' ? '팀장과 1:1 톡방' : '팀장 · 학생 1:1 톡방') + '</b><small>1:1</small></div></div><div class="ia-cm"><i style="--w:60%"></i><i class="me" style="--w:48%"></i><i style="--w:72%"></i></div></div><p class="ia-hint">기관용에는 <b>통화가 없어요.</b> 채팅으로 소통해요.</p>'; } },
  profile: { ic: 'cap', c: '#06B6D4', t: '내 프로필', d: '학교 · 소속 · 학년과 참여 중인 프로젝트가 담긴 프로필이에요.',
    body: function(){
      var u = instUser || {}, org = u.org || {};
      var kv = function(l, v){ return '<div><small>' + l + '</small><b>' + (v ? instaEsc(v) : '—') + '</b></div>'; };
      return '<div class="ia-kv">' + kv('이름', u.name) + kv('기관', org.name) + kv('아이디', u.login_id) + '</div><h4 class="ia-sub">참여 중인 프로젝트</h4>' + iaTable(['프로젝트', '수업 · 모임', '역할'], '1.6fr 1.2fr .8fr', 3); } },
  community: { ic: 'trophy', c: '#EF4444', t: '커뮤니티', d: '글쓴이의 이름 옆에 학교 마크가 함께 보여요.',
    body: function(){ return iaChips(['전체', '질문', '스터디', '팀원 구해요']) + iaTable(['학교', '글', '태그'], '1.3fr 2fr .9fr', 3); } },
  settings: { ic: 'spark', c: '#14B8A6', t: '프로젝트 설정', d: '기관용 프로젝트를 만드는 팀장은 수업에 맞게 원하는 대로 편하게 커스텀할 수 있어요.',
    body: function(){ return iaTable(['설정 항목', '현재 값'], '1.6fr 1.4fr', 3); } }
};

/* ---------- 기관용 첫 화면 ---------- */
async function instaEnter(){
  window.scrollTo(0, 0);
  var m = document.getElementById('iaMain'); if(!m) return;
  if(!instUser){
    m.innerHTML = '<div class="ia-wrap"><p class="ia-hint">불러오는 중…</p></div>';
    try { instUser = await instFetch('/me'); } catch(e){ if(instToken) m.innerHTML = '<div class="ia-wrap"><p class="ia-hint">' + instaEsc(e.message) + '</p></div>'; return; }
  }
  instaBuild();
}
function instaHead(){
  var u = instUser || {};
  var el = document.getElementById('iaUser'); if(el) el.textContent = u.name || '';
  var c = document.getElementById('iaChip'); if(c) c.textContent = u.role === 'student' ? '기관용 · 학생' : '기관용 · 선생님';
}
function instaBuild(){
  var m = document.getElementById('iaMain'); if(!m || !instUser) return;
  instaHead();
  var role = instRole(), banner = '<div class="in-banner" role="status"><span class="chip">개발 중</span><span>기관용은 현재 개발 중이에요. 로그인 · 기관 · 학생 등록만 지금 쓸 수 있고, 나머지는 기본 틀이에요.</span></div>';
  if(role === 'student' && instUser.must_change_password){ m.innerHTML = banner + instaPwCard(); return; }
  if(role === 'teacher' && !instUser.org){ m.innerHTML = banner + instaOrgCard(); return; }
  var org = instUser.org;
  m.innerHTML = banner +
    '<div class="ia-wrap">' +
      '<div class="ia-hello"><div><span class="view-eyebrow">Institution</span><h2>' + instaEsc(instUser.name) + '님, 환영해요</h2><p class="sub">' + (org ? instaEsc(org.name) + ' · ' : '') + (role === 'teacher' ? '교수 · 교사 · 기관 담당자' : '학생') + '</p><p class="sub">' + IA_HELLO[role] + '</p></div>' +
      (role === 'teacher' && org ? '<div class="ia-code"><small>기관 코드 (학생이 로그인할 때 써요)</small><div><b id="iaCode">' + instaEsc(org.code) + '</b><button type="button" class="btn ghost ia-btn" onclick="instaCopy(\'' + instaEsc(org.code) + '\', this)">복사</button></div></div>' : '') + '</div>' +
      '<div class="ia-body"><nav class="ia-nav" id="iaNav" aria-label="기관용 메뉴"></nav><section class="ia-panel card" id="iaPanel" aria-live="polite"></section></div>' +
    '</div>';
  var groups = IA_MENU[role], first = groups[0].ks[0];
  document.getElementById('iaNav').innerHTML = groups.map(function(g){
    return '<div class="ia-g"><span class="ia-gh">' + g.g + '</span>' + g.ks.map(function(k){ var t = IA_TABS[k]; return '<button type="button" data-k="' + k + '" onclick="instaTab(\'' + k + '\')">' + hbIco(t.ic, t.c) + '<span>' + iaLabel(k, role) + '</span></button>'; }).join('') + '</div>';
  }).join('');
  var has = groups.some(function(g){ return g.ks.indexOf(IA.tab) >= 0; });
  instaTab(has ? IA.tab : first);
}
function iaLabel(k, role){ return k === 'files' ? (role === 'student' ? '내 파일' : '파일 · 권한') : (k === 'accts' ? '계정 관리' : IA_TABS[k].t); }
function instaTab(k){
  var role = instRole(), t = IA_TABS[k] || IA_TABS.teams; if(!IA_TABS[k]) k = 'teams'; IA.tab = k;
  document.querySelectorAll('#iaNav button').forEach(function(b){ b.classList.toggle('on', b.dataset.k === k); });
  var nv = document.getElementById('iaNav'), on = nv && nv.querySelector('button.on');
  if(on && nv.scrollWidth > nv.clientWidth) nv.scrollLeft = on.offsetLeft - (nv.clientWidth - on.offsetWidth) / 2;          // 좁은 화면(메뉴가 가로로 길어질 때)에서는 고른 항목이 보이게
  var p = document.getElementById('iaPanel'); if(!p) return;
  var title = k === 'files' ? iaLabel(k, role) : t.t;
  var desc = (k === 'files' && role === 'student') ? '내 폴더와 파일에 집중해요. 다른 사람의 파일은 접근이 제한돼요.' : t.d;
  p.innerHTML = '<div class="ia-ph">' + hbIco(t.ic, t.c, true) + '<div><h3>' + title + '</h3><p>' + desc + '</p></div>' + (t.real ? '' : '<span class="chip ia-soon">준비 중</span>') + '</div>' +
    '<div class="ia-frame">' + t.body(role) + '</div>' +
    (t.real ? '' : '<p class="ia-note">이 화면은 기본 틀이에요. 소개 페이지에서 안내한 기능이 하나씩 채워질 예정이에요.</p>');
  if(k === 'accts') instaLoadStudents();
}

/* ---------- 학생: 첫 로그인 비밀번호 바꾸기 ---------- */
function instaPwCard(){
  return '<div class="ia-wrap"><form class="ia-card card" onsubmit="return instaChangePw(event)"><h3>비밀번호를 바꿔 주세요</h3><p class="ia-hint">선생님이 만들어 준 비밀번호예요. 나만 아는 새 비밀번호로 바꾸면 쓸 수 있어요. (8자 이상)</p>' +
    '<label>지금 비밀번호<input type="password" id="iaOldPw" autocomplete="current-password" required></label>' +
    '<label>새 비밀번호<input type="password" id="iaNewPw" minlength="8" autocomplete="new-password" required></label>' +
    '<label>새 비밀번호 확인<input type="password" id="iaNewPw2" minlength="8" autocomplete="new-password" required></label>' +
    '<p class="in-err" id="iaPwErr" role="alert" hidden></p><button type="submit" class="btn primary" id="iaPwBtn">바꾸기</button></form></div>';
}
async function instaChangePw(ev){
  ev.preventDefault();
  var err = document.getElementById('iaPwErr'), n1 = document.getElementById('iaNewPw').value;
  err.hidden = true;
  if(n1 !== document.getElementById('iaNewPw2').value){ err.textContent = '새 비밀번호가 서로 달라요.'; err.hidden = false; return false; }
  var btn = document.getElementById('iaPwBtn'); btn.disabled = true;
  try { await instFetch('/auth/change-password', { method: 'POST', body: JSON.stringify({ old_password: document.getElementById('iaOldPw').value, new_password: n1 }) }); instUser.must_change_password = false; instaBuild(); pushToast('✅', '비밀번호를 바꿨어요', '다음부터는 새 비밀번호로 로그인해요.'); }
  catch(e){ err.textContent = e.message; err.hidden = false; btn.disabled = false; }
  return false;
}

/* ---------- 선생님: 기관 만들기 · 학생 등록 ---------- */
function instaOrgCard(){
  return '<div class="ia-wrap"><form class="ia-card card" onsubmit="return instaCreateOrg(event)"><h3>기관을 만들어 주세요</h3><p class="ia-hint">학교 · 학원 · 수업 이름을 정하면 학생이 로그인할 때 쓰는 <b>기관 코드</b>가 만들어져요.</p>' +
    '<label>기관 이름<input type="text" id="iaOrgName" maxlength="100" placeholder="예: 한빛대학교 컴퓨터공학과" required></label>' +
    '<p class="in-err" id="iaOrgErr" role="alert" hidden></p><button type="submit" class="btn primary" id="iaOrgBtn">기관 만들기</button></form></div>';
}
async function instaCreateOrg(ev){
  ev.preventDefault();
  var err = document.getElementById('iaOrgErr'), btn = document.getElementById('iaOrgBtn'); err.hidden = true; btn.disabled = true;
  try { var d = await instFetch('/org', { method: 'POST', body: JSON.stringify({ name: document.getElementById('iaOrgName').value.trim() }) }); instToken = d.access_token; instUser = d.user; try { localStorage.setItem(INST_TK, instToken); } catch(e){} instaBuild(); }
  catch(e){ err.textContent = e.message; err.hidden = false; btn.disabled = false; }
  return false;
}
function instaCopy(text, btn){
  var done = function(){ if(btn){ var o = btn.textContent; btn.textContent = '복사했어요'; setTimeout(function(){ btn.textContent = o; }, 1400); } };
  try { navigator.clipboard.writeText(text).then(done, function(){ pushToast('ℹ️', '복사하지 못했어요', '직접 선택해서 복사해 주세요.'); }); } catch(e){ pushToast('ℹ️', '복사하지 못했어요', '직접 선택해서 복사해 주세요.'); }
}
var IA_STU = [], IA_NEW = null;                 // 학생 목록 · 방금 만든 초기 비밀번호(이 화면에서만 보여 준다)
async function instaLoadStudents(){
  var box = document.getElementById('iaAccts'); if(!box) return;
  try { IA_STU = (await instFetch('/students')).students; } catch(e){ box.innerHTML = '<p class="ia-hint">' + instaEsc(e.message) + '</p>'; return; }
  instaRenderAccts();
}
function instaRenderAccts(){
  var box = document.getElementById('iaAccts'); if(!box) return;
  var newBox = '';
  if(IA_NEW && IA_NEW.rows.length){
    newBox = '<div class="ia-newpw"><div class="ia-newpw-h"><b>초기 비밀번호</b><button type="button" class="btn ghost ia-btn" onclick="instaCopyNew(this)">표 복사</button></div>' +
      '<p class="ia-hint">이 비밀번호는 <b>지금만</b> 보여요. 학생에게 전달해 주세요. 학생은 첫 로그인에서 바꿔요.</p>' +
      '<div class="ia-tb" style="--cols:1.2fr 1fr 1fr">' + '<div class="ia-tr ia-th"><span>아이디</span><span>이름</span><span>초기 비밀번호</span></div>' + IA_NEW.rows.map(function(r){ return '<div class="ia-tr"><span>' + instaEsc(r[0]) + '</span><span>' + instaEsc(r[1]) + '</span><span class="ia-pw">' + instaEsc(r[2]) + '</span></div>'; }).join('') + '</div></div>';
  }
  if(IA_NEW && IA_NEW.skipped && IA_NEW.skipped.length) newBox += '<p class="in-err">건너뜀: ' + IA_NEW.skipped.map(function(s){ return instaEsc(s.login_id) + ' (' + instaEsc(s.reason) + ')'; }).join(', ') + '</p>';
  var list = IA_STU.length
    ? '<div class="ia-tb ia-stu" style="--cols:1.1fr 1fr .9fr 1.2fr 1.4fr"><div class="ia-tr ia-th"><span>아이디</span><span>이름</span><span>상태</span><span>마지막 로그인</span><span></span></div>' +
      IA_STU.map(function(s){ return '<div class="ia-tr"><span>' + instaEsc(s.login_id) + '</span><span>' + instaEsc(s.name) + '</span><span>' + (s.must_change_password ? '<em class="ia-st w">비밀번호 변경 전</em>' : '<em class="ia-st">사용 중</em>') + '</span><span>' + (s.last_login_at ? instaEsc(new Date(s.last_login_at).toLocaleString('ko-KR', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })) : '—') + '</span><span class="ia-ac"><button type="button" class="btn ghost ia-btn" onclick="instaResetPw(' + s.id + ')">비밀번호 다시 만들기</button><button type="button" class="btn ghost ia-btn" onclick="instaDelStudent(' + s.id + ')">삭제</button></span></div>'; }).join('') + '</div>'
    : '<p class="ia-hint">아직 등록한 학생이 없어요. 위 칸에 명단을 붙여 넣어 등록해 보세요.</p>';
  box.innerHTML =
    '<form class="ia-add" onsubmit="return instaAddStudents(event)"><label for="iaList">명단 — 한 줄에 한 명, <b>아이디, 이름</b> (엑셀에서 복사해 붙여 넣어도 돼요)</label>' +
    '<textarea id="iaList" rows="5" placeholder="20260101, 김민수&#10;20260102, 이지은&#10;3-2-15, 박수현" spellcheck="false"></textarea>' +
    '<div class="ia-add-r"><button type="submit" class="btn primary" id="iaAddBtn">학생 등록</button><span class="ia-hint">대학은 학번, 중 · 고등학교는 3-2-15 처럼 학년-반-번호 등 선생님이 정한 아이디를 쓰면 돼요. 엑셀 파일 올리기는 준비 중이에요.</span></div></form>' +
    newBox + '<h4 class="ia-sub">등록한 학생 (' + IA_STU.length + '명)</h4>' + list;
}
async function instaAddStudents(ev){
  ev.preventDefault();
  var rows = [], lines = document.getElementById('iaList').value.split(/\r?\n/);
  lines.forEach(function(l){ l = l.trim(); if(!l) return; var m = l.split(/\t|,/); var id = (m[0] || '').trim(), nm = m.slice(1).join(',').trim(); if(id) rows.push({ login_id: id, name: nm || id }); });
  if(!rows.length){ pushToast('ℹ️', '명단이 비어 있어요', '한 줄에 "아이디, 이름" 형식으로 적어 주세요.'); return false; }
  var btn = document.getElementById('iaAddBtn'); btn.disabled = true;
  try {
    var d = await instFetch('/students', { method: 'POST', body: JSON.stringify({ students: rows }) });
    IA_NEW = { rows: d.created.map(function(s){ return [s.login_id, s.name, s.initial_password]; }), skipped: d.skipped };
    await instaLoadStudents();
    if(d.created.length) pushToast('✅', d.created.length + '명을 등록했어요', '초기 비밀번호를 학생에게 전달해 주세요.');
  } catch(e){ pushToast('⚠️', '등록하지 못했어요', e.message); btn.disabled = false; }
  return false;
}
function instaCopyNew(btn){ if(IA_NEW) instaCopy(IA_NEW.rows.map(function(r){ return r.join('\t'); }).join('\n'), btn); }
async function instaResetPw(id){
  var s = IA_STU.filter(function(x){ return x.id === id; })[0]; if(!s || !confirm(s.name + '(' + s.login_id + ') 학생의 비밀번호를 새로 만들까요? 예전 비밀번호는 쓸 수 없게 돼요.')) return;
  try { var d = await instFetch('/students/' + id + '/reset-password', { method: 'POST' }); IA_NEW = { rows: [[d.login_id, s.name, d.initial_password]], skipped: [] }; await instaLoadStudents(); }
  catch(e){ pushToast('⚠️', '다시 만들지 못했어요', e.message); }
}
async function instaDelStudent(id){
  var s = IA_STU.filter(function(x){ return x.id === id; })[0]; if(!s || !confirm(s.name + '(' + s.login_id + ') 학생을 삭제할까요? 되돌릴 수 없어요.')) return;
  try { await instFetch('/students/' + id, { method: 'DELETE' }); await instaLoadStudents(); }
  catch(e){ pushToast('⚠️', '삭제하지 못했어요', e.message); }
}
function instaEsc(s){ return String(s).replace(/[&<>"']/g, function(c){ return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
