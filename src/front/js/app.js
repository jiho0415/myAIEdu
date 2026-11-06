const $app = document.getElementById("app");
const $nav = document.getElementById("authNav");
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const tag = (stage) => `<span class="tag ${stage}">${STAGES[stage]}</span>`;
const STATUS = { applied: "신청완료", active: "수강중", completed: "수료", canceled: "취소됨" };
const errBox = (m) => `<div class="msg err">${esc(m)}</div>`;
const needLogin = (msg) => `<h2>로그인이 필요합니다</h2><p class="muted">${msg}</p><a class="btn" href="#/login">로그인 / 회원가입</a>`;

function renderNav() {
  const u = session.user;
  $nav.innerHTML = u
    ? `<span class="muted">${esc(u.name)}님</span><a href="#" id="logout">로그아웃</a>`
    : `<a href="#/login">로그인</a>`;
  const lo = document.getElementById("logout");
  if (lo) lo.onclick = (e) => { e.preventDefault(); session.clear(); location.hash = "#/"; render(); };
}

const views = {
  async home() {
    return `
      <section class="hero">
        <h1>AI, 어렵지 않게 시작해서<br>내일 당장 내 일에 씁니다</h1>
        <p>중간관리자·자영업자·프리랜서를 위한 8주 실전 클래스</p>
        <a class="btn light" href="#/enroll">수강신청 하기</a>
        <a class="btn ghost" style="color:#fff;border-color:#fff" href="#/curriculum">커리큘럼 보기</a>
      </section>
      <h2>이런 과정입니다</h2>
      <div class="grid">
        ${Object.entries(STAGES).map(([k, v], i) => `<div class="card">${tag(k)}<h3>${["1~2주", "3~6주", "7~8주"][i]} ${v}</h3>
          <p class="muted">${["AI 개념과 질문하는 법", "업무 문서·홍보 콘텐츠 실전 적용", "자동화 루틴 설계와 프로젝트 발표"][i]}</p></div>`).join("")}
      </div>
      <h2>API 실습</h2>
      <p class="muted">서버 API 명세를 보고 직접 호출해 볼 수 있습니다.</p>
      <a class="btn ghost" href="#/apidocs">API 문서·실습 대시보드 열기</a>`;
  },

  apidocs: () => apiDocs.view(),

  async curriculum() {
    const c = await api(`/courses/${COURSE_ID}`);
    return `<h2>${esc(c.title)}</h2><p class="muted">${esc(c.description)}</p>
      <div class="grid" style="grid-template-columns:1fr">
        ${c.weeks.map((w) => `<a class="card week" href="#/week/${w.week_no}">
          <div class="no">${w.week_no}주</div>
          <div>${tag(w.stage)}<h3>${esc(w.title)}</h3><span class="muted">${esc(w.summary)}</span></div></a>`).join("")}
      </div>`;
  },

  async week(no) {
    const w = await api(`/courses/${COURSE_ID}/weeks/${Number(no)}`);
    return `<a href="#/curriculum">← 커리큘럼으로</a>
      <h2>${w.week_no}주차 · ${esc(w.title)}</h2>${tag(w.stage)}
      <p>${esc(w.summary)}</p>
      ${w.practices.map((p) => `<div class="card"><h3>핵심 실습: ${esc(p.title)}</h3>
        <ol class="steps">${p.steps.map((s) => `<li>${esc(s)}</li>`).join("")}</ol></div>`).join("")}
      <p style="margin-top:24px"><a class="btn" href="#/enroll">수강신청 하기</a></p>`;
  },

  async login() {
    return `<h2>로그인 / 회원가입</h2>
      <div class="grid">
        <form id="loginForm" class="card"><h3>로그인</h3>
          <label>이메일</label><input name="email" type="email" required>
          <label>비밀번호</label><input name="password" type="password" required>
          <p><button class="btn" type="submit">로그인</button></p><div class="out"></div></form>
        <form id="signupForm" class="card"><h3>회원가입</h3>
          <label>이름</label><input name="name" required maxlength="50">
          <label>이메일</label><input name="email" type="email" required>
          <label>비밀번호 (8자 이상)</label><input name="password" type="password" required minlength="8" maxlength="64">
          <label>구분</label>
          <select name="user_type"><option value="manager">중간관리자 직장인</option><option value="self_employed">자영업자</option><option value="freelancer">프리랜서</option></select>
          <p><button class="btn" type="submit">가입하기</button></p><div class="out"></div></form>
      </div>`;
  },

  async enroll() {
    const cohorts = await api("/cohorts?status=open");
    const loggedIn = !!session.user;
    return `<h2>수강신청</h2>
      <div class="grid">${cohorts.map((c) => `<div class="card"><h3>${esc(c.name)}</h3>
        <p class="muted">개강 ${c.start_date} · 잔여 ${c.seats_left}/${c.capacity}석</p>
        ${c.seats_left > 0 ? `<button class="btn" data-enroll="${c.id}">이 기수 신청하기</button>` : "<b>마감되었습니다</b>"}</div>`).join("")}</div>
      ${loggedIn ? "" : `<p class="muted" style="margin-top:16px">신청하려면 <a href="#/login">로그인</a>이 필요합니다.</p>`}
      <div id="result"></div>`;
  },

  async my() {
    if (!session.user) return needLogin("내 수강현황을 보려면 로그인해 주세요.");
    const list = await api("/enrollments/me");
    if (!list.length) return `<h2>내 수강현황</h2><p class="muted">아직 신청 내역이 없습니다.</p><a class="btn" href="#/enroll">수강신청 하기</a>`;
    return `<h2>내 수강현황</h2><div class="grid">${list.map((e) => `<div class="card"><h3>${esc(e.cohort_name)}</h3>
      <p class="muted">개강 ${e.start_date}</p>
      <div class="bar"><i style="width:${(e.current_week / 8) * 100}%"></i></div>
      <p class="muted">진행 ${e.current_week} / 8주 · 상태: ${STATUS[e.status] || e.status}</p>
      ${e.status === "canceled" ? "" : `<button class="btn ghost" data-cancel="${e.id}">신청 취소</button>`}</div>`).join("")}</div>
      <div id="result"></div>`;
  },
};

function show(el, msg, ok = false) { el.innerHTML = ok ? `<div class="msg">${msg}</div>` : errBox(msg); }

function bind() {
  apiDocs.bind();
  for (const [id, path] of [["loginForm", "/auth/login"], ["signupForm", "/auth/signup"]]) {
    const f = document.getElementById(id);
    if (!f) continue;
    f.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const out = f.querySelector(".out");
      try {
        session.save(await api(path, { method: "POST", body: Object.fromEntries(new FormData(f)) }));
        location.hash = "#/enroll"; render();
      } catch (e) { show(out, e.message); }
    });
  }
  document.querySelectorAll("[data-enroll]").forEach((b) => b.addEventListener("click", async () => {
    const out = document.getElementById("result");
    if (!session.user) { location.hash = "#/login"; return; }
    try {
      await api("/enrollments", { method: "POST", body: { cohort_id: Number(b.dataset.enroll) } });
      show(out, `신청이 완료되었습니다. <a href="#/my">내 수강현황 보기</a>`, true);
      setTimeout(render, 1500);
    } catch (e) { show(out, e.message); render().then(() => show(document.getElementById("result"), e.message)); }
  }));
  document.querySelectorAll("[data-cancel]").forEach((b) => b.addEventListener("click", async () => {
    if (!confirm("신청을 취소하시겠습니까?")) return;
    try { await api(`/enrollments/${b.dataset.cancel}/cancel`, { method: "PATCH" }); render(); }
    catch (e) { show(document.getElementById("result"), e.message); }
  }));
}

async function render() {
  renderNav();
  const [, name = "", arg] = location.hash.split("/");
  const view = views[name || "home"] || views.home;
  $app.innerHTML = `<p class="muted">불러오는 중...</p>`;
  try { $app.innerHTML = await view(arg); }
  catch (e) { $app.innerHTML = errBox(e.message); }
  bind();
  window.scrollTo(0, 0);
}
window.addEventListener("hashchange", render);
render();
