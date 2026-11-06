// 실습 미션 컴포넌트: 버튼 하나로 API를 호출하고, 기대 결과와 비교해 통과/실패를 즉시 보여 준다.
// 서버 통신은 api.js(apiRaw)만 사용하고, esc/renderNav는 app.js, apiDocs는 apidocs.js의 전역을 쓴다.
const practice = (() => {
  const state = { results: {}, ctx: {}, running: false };

  const pass = (msg) => ({ ok: true, msg });
  const fail = (msg, hint) => ({ ok: false, msg, hint });
  // 토큰은 화면에 노출하지 않는다
  const mask = (d) => (d && d.access_token ? { ...d, access_token: "(저장됨 · 화면에는 표시하지 않음)" } : d);
  const saveSession = (res) => { session.save(res.data); renderNav(); apiDocs.refreshAuth(); };

  const NEEDS = {
    token: "4단계 회원가입 또는 5단계 로그인",
    cohortId: "7단계 모집 중인 기수 찾기",
    enrollmentId: "8단계 수강신청",
  };
  const STATUS_HINTS = {
    401: "토큰이 없거나 만료되었습니다. 회원가입·로그인 단계를 먼저 실행하세요.",
    422: "입력 형식이 맞지 않습니다. 응답의 detail에서 어떤 필드가 문제인지 확인하세요.",
    500: "서버 내부 오류입니다. 백엔드 터미널의 로그를 확인하세요.",
  };

  // 각 미션: request로 호출 내용을 만들고, verdict로 기대 결과와 비교한다.
  const STEPS = [
    {
      id: "health", title: "1. 서버 상태 확인", key: "GET /health",
      desc: "백엔드가 켜져 있는지 확인합니다. 기대 결과: 200, status가 ok",
      request: () => ({ path: "/health" }),
      verdict: (res) => (res.status === 200 && res.data.status === "ok"
        ? pass("서버가 정상 동작 중입니다.")
        : fail("서버 응답이 예상과 다릅니다.", "백엔드를 --port 8000으로 실행했는지 확인하세요.")),
    },
    {
      id: "courses", title: "2. 강의 목록 조회 (공개 API)", key: "GET /courses",
      desc: "로그인 없이 호출됩니다. 기대 결과: 200, 강의가 1개 이상",
      request: () => ({ path: "/courses" }),
      verdict: (res) => (res.ok && Array.isArray(res.data) && res.data.length
        ? pass(`강의 ${res.data.length}개를 조회했습니다.`)
        : fail("강의 목록을 받지 못했습니다.", "초기 데이터(seed)가 들어갔는지 확인하세요.")),
    },
    {
      id: "noauth", title: "3. 토큰 없이 내 정보 호출 (예외 케이스)", key: "GET /users/me",
      desc: "일부러 토큰 없이 호출합니다. 기대 결과: 401 (실패해야 정상)",
      request: () => ({ path: "/users/me", auth: false }),
      verdict: (res) => (res.status === 401
        ? pass("401을 받았습니다. 보호된 API는 토큰이 없으면 거절됩니다.")
        : fail(`401이 아니라 ${res.status}를 받았습니다.`, "인증이 필요한 API가 열려 있으면 보안 문제입니다.")),
    },
    {
      id: "signup", title: "4. 회원가입", key: "POST /auth/signup",
      desc: "위 입력칸의 값으로 가입합니다. 기대 결과: 201, 토큰 발급 및 자동 로그인",
      pre: (inp) => (inp.password.length < 8 ? "비밀번호는 8자 이상이어야 합니다." : ""),
      request: (_, inp) => ({
        path: "/auth/signup", method: "POST",
        body: { name: inp.name, email: inp.email, password: inp.password, user_type: "manager" },
      }),
      verdict: (res, ctx, inp) => {
        if (res.status === 201 && res.data.access_token) { saveSession(res); ctx.token = true; ctx.email = inp.email; return pass("가입이 완료되어 로그인되었습니다."); }
        if (res.status === 409) return fail("이미 가입된 이메일입니다.", "이메일을 바꾸거나 5단계 로그인으로 넘어가세요.");
        if (res.status === 400) return fail("비밀번호가 너무 깁니다.", "영문·숫자는 72자, 한글은 24자 이내로 입력하세요.");
        return fail(`가입에 실패했습니다. (HTTP ${res.status})`, STATUS_HINTS[res.status]);
      },
    },
    {
      id: "login", title: "5. 로그인", key: "POST /auth/login",
      desc: "가입한 계정으로 로그인합니다. 기대 결과: 200, 토큰 발급",
      request: (_, inp) => ({ path: "/auth/login", method: "POST", body: { email: inp.email, password: inp.password } }),
      verdict: (res, ctx, inp) => {
        if (res.ok && res.data.access_token) { saveSession(res); ctx.token = true; ctx.email = inp.email; return pass("로그인되었습니다."); }
        return fail("로그인에 실패했습니다.", res.status === 401 ? "이메일·비밀번호를 확인하거나 4단계 가입을 먼저 하세요." : STATUS_HINTS[res.status]);
      },
    },
    {
      id: "me", title: "6. 내 정보 확인", key: "GET /users/me", needs: ["token"],
      desc: "토큰이 올바른지 확인합니다. 기대 결과: 200, 내 이메일이 응답에 포함",
      request: () => ({ path: "/users/me" }),
      verdict: (res, ctx) => (res.ok && res.data.email === String(ctx.email).toLowerCase()
        ? pass(`${res.data.name}님으로 인증되었습니다.`)
        : fail("내 정보가 예상과 다릅니다.", STATUS_HINTS[res.status])),
    },
    {
      id: "cohorts", title: "7. 모집 중인 기수 찾기", key: "GET /cohorts", needs: ["token"],
      desc: "status=open인 기수 중 자리가 남은 기수를 고릅니다. 기대 결과: 200, 잔여석 1 이상",
      request: () => ({ path: "/cohorts?status=open" }),
      verdict: (res, ctx) => {
        const open = res.ok && Array.isArray(res.data) ? res.data.find((c) => c.seats_left > 0) : null;
        if (!open) return fail("신청 가능한 기수가 없습니다.", "모두 마감되었거나 모집 중인 기수가 없습니다.");
        ctx.cohortId = open.id;
        return pass(`'${open.name}' 기수를 선택했습니다. (잔여 ${open.seats_left}석)`);
      },
    },
    {
      id: "enroll", title: "8. 수강신청", key: "POST /enrollments", needs: ["token", "cohortId"],
      desc: "선택한 기수에 신청합니다. 기대 결과: 201, 신청 내역 생성",
      request: (ctx) => ({ path: "/enrollments", method: "POST", body: { cohort_id: ctx.cohortId } }),
      verdict: (res, ctx) => {
        if (res.status === 201) { ctx.enrollmentId = res.data.id; return pass("수강신청이 완료되었습니다."); }
        const known = { 409: "이미 신청했거나 정원이 마감되었습니다.", 400: "모집 중인 기수가 아닙니다.", 404: "기수를 찾을 수 없습니다." };
        return fail(`신청에 실패했습니다. (HTTP ${res.status})`, known[res.status] || STATUS_HINTS[res.status]);
      },
    },
    {
      id: "mine", title: "9. 내 수강현황 확인", key: "GET /enrollments/me", needs: ["token", "enrollmentId"],
      desc: "방금 한 신청이 목록에 있는지 확인합니다. 기대 결과: 200, 신청 내역 포함",
      request: () => ({ path: "/enrollments/me" }),
      verdict: (res, ctx) => (res.ok && res.data.some((e) => e.id === ctx.enrollmentId)
        ? pass("신청 내역이 목록에 보입니다.")
        : fail("신청 내역을 찾지 못했습니다.", STATUS_HINTS[res.status])),
    },
    {
      id: "admin", title: "10. 관리자 API를 수강생이 호출 (예외 케이스)", key: "PATCH /enrollments/{enrollment_id}/progress",
      needs: ["token", "enrollmentId"],
      desc: "진도 변경은 관리자 전용입니다. 기대 결과: 403 (실패해야 정상)",
      request: (ctx) => ({ path: `/enrollments/${ctx.enrollmentId}/progress`, method: "PATCH", body: { current_week: 1 } }),
      verdict: (res) => (res.status === 403
        ? pass("403을 받았습니다. 수강생은 관리자 API를 쓸 수 없습니다.")
        : fail(`403이 아니라 ${res.status}를 받았습니다.`, "권한 검사가 빠져 있다면 보안 문제입니다.")),
    },
    {
      id: "cancel", title: "11. 신청 취소 (정리)", key: "PATCH /enrollments/{enrollment_id}/cancel",
      needs: ["token", "enrollmentId"],
      desc: "실습으로 차지한 자리를 돌려놓습니다. 기대 결과: 200, status가 canceled",
      request: (ctx) => ({ path: `/enrollments/${ctx.enrollmentId}/cancel`, method: "PATCH" }),
      verdict: (res) => (res.ok && res.data.status === "canceled"
        ? pass("신청이 취소되어 자리가 반환되었습니다.")
        : fail("취소에 실패했습니다.", STATUS_HINTS[res.status])),
    },
  ];

  const readInputs = () => {
    const get = (n) => document.querySelector(`#mission [name="${n}"]`).value.trim();
    return { name: get("name"), email: get("email").toLowerCase(), password: document.querySelector('#mission [name="password"]').value };
  };

  async function execute(step) {
    // 이미 로그인된 상태(이전 실습 등)도 인정한다
    if (session.token) { state.ctx.token = true; state.ctx.email ??= session.user?.email; }
    const missing = (step.needs || []).find((k) => state.ctx[k] == null);
    if (missing) { state.results[step.id] = fail("앞 단계를 먼저 통과해야 합니다.", `필요한 단계: ${NEEDS[missing]}`); return; }
    const inp = readInputs();
    const problem = step.pre?.(inp);
    if (problem) { state.results[step.id] = fail(problem); return; }
    const { path, method, body, auth } = step.request(state.ctx, inp);
    try {
      const res = await apiRaw(path, { method, body, auth });
      state.results[step.id] = { ...step.verdict(res, state.ctx, inp), status: res.status, data: mask(res.data) };
    } catch (e) {
      state.results[step.id] = fail(e.message, "백엔드가 실행 중인지, API_BASE 주소가 맞는지 확인하세요.");
    }
  }

  function resultHtml(r) {
    if (!r) return "";
    return `<p class="mi-msg">${esc(r.msg)}</p>${r.hint ? `<p class="muted">힌트: ${esc(r.hint)}</p>` : ""}
      ${r.data === undefined ? "" : `<details><summary>응답 보기 (HTTP ${esc(r.status)})</summary><pre class="out-pre">${esc(JSON.stringify(r.data, null, 2))}</pre></details>`}`;
  }

  function listHtml() {
    return STEPS.map((s) => {
      const r = state.results[s.id];
      const cls = r ? (r.ok ? "pass" : "fail") : "";
      return `<li class="mi ${cls}"><div class="mi-h"><b>${esc(s.title)}</b>
          <span class="badge ${r ? (r.ok ? "" : "admin") : "user"}">${r ? (r.ok ? "통과" : "실패") : "대기"}</span>
          <button class="btn ghost sm" type="button" data-run="${s.id}" ${state.running ? "disabled" : ""}>실행</button>
          <button class="btn ghost sm" type="button" data-goto="${esc(s.key)}">명세 보기</button></div>
        <div class="muted">${esc(s.desc)}</div>${resultHtml(r)}</li>`;
    }).join("");
  }

  function paint() {
    const passed = STEPS.filter((s) => state.results[s.id]?.ok).length;
    document.getElementById("missionList").innerHTML = listHtml();
    document.getElementById("missionProgress").innerHTML =
      `<p><b>${passed} / ${STEPS.length}</b> 통과${passed === STEPS.length ? " — 모든 미션을 완료했습니다!" : ""}</p>
       <div class="bar"><i style="width:${(passed / STEPS.length) * 100}%"></i></div>`;
    document.querySelectorAll("#mission [data-all], #mission [data-reset]").forEach((b) => { b.disabled = state.running; });
  }

  async function runSteps(steps, stopOnFail) {
    state.running = true;
    paint();
    for (const s of steps) {
      await execute(s);
      paint();
      if (stopOnFail && !state.results[s.id].ok) {
        // 중간에 멈춰도 실습으로 잡은 자리는 반드시 돌려놓는다
        const cancel = STEPS.find((x) => x.id === "cancel");
        if (state.ctx.enrollmentId && s !== cancel) { await execute(cancel); paint(); }
        break;
      }
    }
    state.running = false;
    paint();
  }

  function view() {
    const guest = `student${Math.floor(1000 + Math.random() * 9000)}@example.com`;
    return `<h2>실습 미션</h2>
      <p class="muted">버튼을 눌러 위에서부터 차례로 실행하세요. 호출 결과가 기대와 같으면 통과로 표시됩니다.
        실습으로 만든 계정은 서버에 남고, 수강신청은 11단계에서 취소됩니다.</p>
      <div id="mission" class="card">
        <div class="grid">
          <div><label>이름</label><input name="name" value="홍길동" maxlength="50"></div>
          <div><label>이메일</label><input name="email" value="${guest}"></div>
          <div><label>비밀번호 (8자 이상, 영문·숫자 권장)</label><input name="password" type="password" maxlength="64" autocomplete="off"></div>
        </div>
        <p><button class="btn" type="button" data-all="1">처음부터 모두 실행</button>
          <button class="btn ghost" type="button" data-reset="1">결과 초기화</button></p>
        <div id="missionProgress" aria-live="polite"></div>
        <ol id="missionList" class="mission" aria-live="polite">${listHtml()}</ol>
      </div>`;
  }

  function bind() {
    const root = document.getElementById("mission");
    if (!root) return;
    paint();
    root.addEventListener("click", async (e) => {
      const btn = e.target.closest("button");
      if (!btn || state.running) return;
      if (btn.dataset.run) await runSteps([STEPS.find((s) => s.id === btn.dataset.run)], false);
      else if (btn.dataset.all) { state.results = {}; state.ctx = {}; await runSteps(STEPS, true); }
      else if (btn.dataset.reset) { state.results = {}; state.ctx = {}; paint(); }
    });
  }

  return { view, bind };
})();
