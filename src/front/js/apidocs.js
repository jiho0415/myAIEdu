// API 문서·실습 대시보드 컴포넌트.
// /openapi.json을 실시간으로 읽어 엔드포인트 문서와 실행 폼을 그린다.
// 서버 통신은 api.js(fetchOpenApi, apiRaw)만 사용하고, esc/renderNav는 app.js의 전역을 쓴다.
const apiDocs = (() => {
  const HTTP_METHODS = ["get", "post", "put", "patch", "delete"];
  const TAG_LABELS = { auth: "인증", courses: "강의", enrollments: "수강신청", etc: "기타" };
  const LEVEL_LABELS = { public: "공개", user: "로그인", admin: "관리자" };
  const SAMPLE_BY_NAME = { email: "student@example.com", name: "홍길동" };

  // openapi.json에 없는 정보(한글 설명, 관리자 전용 여부, 도메인 에러)만 보완한다.
  // 서비스 코드와 /make-api-doc 결과(docs/api.md)가 바뀌면 이 표도 함께 갱신한다.
  const API_NOTES = {
    "GET /health": { desc: "서버 상태 확인" },
    "POST /auth/signup": { desc: "회원가입 후 토큰 발급", errors: [[400, "비밀번호가 너무 깁니다. 영문·숫자는 72자, 한글은 24자 이내로 입력해 주세요."], [409, "이미 가입된 이메일입니다."]] },
    "POST /auth/login": { desc: "로그인 후 토큰 발급", errors: [[401, "이메일 또는 비밀번호가 올바르지 않습니다."]] },
    "GET /users/me": { desc: "내 정보 조회" },
    "GET /courses": { desc: "강의(과정) 목록 조회" },
    "GET /courses/{course_id}": { desc: "강의 상세와 주차 목록 조회", errors: [[404, "과정을 찾을 수 없습니다."]] },
    "GET /courses/{course_id}/weeks/{week_no}": { desc: "주차별 실습 내용 조회", errors: [[404, "주차를 찾을 수 없습니다."]] },
    "GET /cohorts": { desc: "기수 목록 조회 (status로 필터)" },
    "POST /enrollments": {
      desc: "수강신청",
      errors: [[404, "기수를 찾을 수 없습니다."], [400, "모집 중인 기수가 아닙니다."],
        [409, "이미 신청한 기수입니다."], [409, "정원이 마감되었습니다."]],
    },
    "GET /enrollments/me": { desc: "내 수강현황 조회" },
    "PATCH /enrollments/{enrollment_id}/cancel": { desc: "수강신청 취소", errors: [[404, "신청 내역을 찾을 수 없습니다."]] },
    "PATCH /enrollments/{enrollment_id}/progress": {
      desc: "진도 변경 (관리자)", admin: true, errors: [[404, "신청 내역을 찾을 수 없습니다."]],
    },
  };

  let spec = null;
  let ops = [];

  const deref = (s) => (s && s.$ref ? spec.components.schemas[s.$ref.split("/").pop()] : s) || {};

  function typeLabel(s) {
    if (!s) return "any";
    if (s.$ref) return s.$ref.split("/").pop();
    if (s.anyOf) {
      const types = s.anyOf.filter((x) => x.type !== "null").map(typeLabel).join(" | ");
      return s.anyOf.some((x) => x.type === "null") ? `${types} (null 허용)` : types;
    }
    if (s.enum) return s.enum.map((v) => `"${v}"`).join(" | ");
    if (s.type === "array") return `${typeLabel(s.items)}[]`;
    return s.type || "any";
  }

  function constraints(s) {
    const c = [];
    if (s.minLength != null) c.push(`최소 ${s.minLength}자`);
    if (s.maxLength != null) c.push(`최대 ${s.maxLength}자`);
    if (s.minimum != null) c.push(`${s.minimum} 이상`);
    if (s.maximum != null) c.push(`${s.maximum} 이하`);
    if (s.pattern) c.push(`패턴 ${s.pattern}`);
    if (s.default !== undefined && s.default !== null) c.push(`기본값 ${s.default}`);
    return c.join(", ");
  }

  function sampleOf(schema, name = "") {
    const s = deref(schema);
    if (s.default !== undefined) return s.default;
    if (s.anyOf) return sampleOf(s.anyOf.find((x) => x.type !== "null"), name);
    if (s.enum) return s.enum[0];
    switch (s.type) {
      case "object": return Object.fromEntries(Object.entries(s.properties || {}).map(([k, v]) => [k, sampleOf(v, k)]));
      case "array": return [];
      case "integer": case "number": return s.minimum ?? 1;
      case "boolean": return false;
      default: return SAMPLE_BY_NAME[name] ?? "";
    }
  }

  function successOf(op) {
    const code = Object.keys(op.responses || {}).find((c) => c.startsWith("2"));
    return { code, schema: op.responses?.[code]?.content?.["application/json"]?.schema };
  }

  function errorsOf(note, level, hasInput) {
    const list = [...(note.errors || [])];
    if (level !== "public") list.push([401, "로그인이 필요합니다."], [401, "인증이 만료되었습니다. 다시 로그인해 주세요."]);
    if (level === "admin") list.push([403, "관리자만 사용할 수 있습니다."]);
    if (hasInput) list.push([422, "요청 형식이 올바르지 않습니다. (FastAPI 자동 검증, detail은 배열)"]);
    return list.sort((a, b) => a[0] - b[0]);
  }

  function parseOps() {
    ops = [];
    for (const [path, item] of Object.entries(spec.paths)) {
      for (const method of HTTP_METHODS) {
        const op = item[method];
        if (!op) continue;
        const key = `${method.toUpperCase()} ${path}`;
        const note = API_NOTES[key] || {};
        const all = op.parameters || [];
        // 인증은 Authorization 헤더 파라미터 유무로 판별한다 (관리자 여부만 note로 보완)
        const needsAuth = all.some((p) => p.in === "header" && p.name.toLowerCase() === "authorization");
        const level = !needsAuth ? "public" : note.admin ? "admin" : "user";
        const params = all.filter((p) => p.in === "path" || p.in === "query");
        const body = op.requestBody?.content?.["application/json"]?.schema || null;
        ops.push({
          key, method: method.toUpperCase(), path, level, params, body,
          tag: op.tags?.[0] || "etc", desc: note.desc || op.summary || "",
          success: successOf(op), errors: errorsOf(note, level, params.length > 0 || !!body),
        });
      }
    }
  }

  const table = (head, rows) => (rows.length
    ? `<table class="tbl"><thead><tr>${head.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${
      rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table>`
    : "");

  function schemaTable(schema, withRequired) {
    let s = deref(schema);
    let label = typeLabel(schema);
    if (s.type === "array") { label = `${typeLabel(s.items)} 배열`; s = deref(s.items); }
    const required = s.required || [];
    const rows = Object.entries(s.properties || {}).map(([name, p]) => {
      const cells = [`<code>${esc(name)}</code>`, esc(typeLabel(p))];
      if (withRequired) cells.push(required.includes(name) ? "예" : "아니오");
      cells.push(esc(constraints(deref(p).anyOf ? deref(p.anyOf[0]) : deref(p))));
      return cells;
    });
    const head = withRequired ? ["필드", "타입", "필수", "제약"] : ["필드", "타입", "제약"];
    return `<p class="muted">${esc(label)}</p>${table(head, rows) || `<p class="muted">필드 정보 없음</p>`}`;
  }

  function paramTable(op) {
    const rows = op.params.map((p) => [`<code>${esc(p.name)}</code>`, p.in === "path" ? "경로" : "쿼리",
      esc(typeLabel(p.schema)), p.required ? "예" : "아니오"]);
    return table(["이름", "위치", "타입", "필수"], rows);
  }

  function tryForm(op, i) {
    const inputs = op.params.map((p) => `<label>${esc(p.name)} <span class="muted">(${p.in === "path" ? "경로" : "쿼리"}${p.required ? ", 필수" : ""})</span></label>
      <input data-param="${esc(p.name)}" data-in="${p.in}" ${p.required ? "required" : ""}>`).join("");
    const sample = op.body ? JSON.stringify(sampleOf(op.body), null, 2) : "";
    const body = op.body
      ? `<label>요청 본문 (JSON)</label><textarea name="body" rows="${sample.split("\n").length + 1}">${esc(sample)}</textarea>`
      : "";
    return `<form class="try" data-op="${i}"><h4>실습하기</h4>${inputs}${body}
      <p><button class="btn" type="submit">실행</button></p><pre class="out-pre" hidden></pre></form>`;
  }

  function endpointCard(op, i) {
    const section = (title, html) => (html ? `<h4>${title}</h4>${html}` : "");
    return `<details class="card ep" id="ep-${i}">
      <summary><span class="method ${op.method}">${op.method}</span> <code>${esc(op.path)}</code>
        <span class="badge ${op.level}">${LEVEL_LABELS[op.level]}</span> <span class="muted">${esc(op.desc)}</span></summary>
      ${section("경로·쿼리 파라미터", paramTable(op))}
      ${op.body ? section("요청 본문", schemaTable(op.body, true)) : ""}
      ${section(`응답 ${esc(op.success.code || "")}`, op.success.schema ? schemaTable(op.success.schema, false) : "")}
      ${section("에러", table(["코드", "메시지"], op.errors.map(([c, m]) => [c, esc(m)])))}
      ${tryForm(op, i)}
    </details>`;
  }

  const authStateText = () => {
    const u = session.user;
    return u ? `로그인 상태: ${u.name} (${u.role})` : "비로그인 상태입니다. 로그인이 필요한 API는 먼저 회원가입·로그인 단계를 실행하세요.";
  };

  async function view() {
    spec = await fetchOpenApi();
    parseOps();
    const tags = [...new Set(ops.map((o) => o.tag))];
    const count = (level) => ops.filter((o) => o.level === level).length;
    return `<div id="apiDocs">
      <h2>API 문서 · 실습 대시보드</h2>
      <p class="muted">${esc(spec.info.title)} · /openapi.json 실시간 기준</p>
      <p id="apiAuthState" class="msg">${esc(authStateText())}</p>
      <div class="grid stats">
        <div class="card"><b>${ops.length}</b><br><span class="muted">전체 엔드포인트</span></div>
        <div class="card"><b>${count("public")}</b><br><span class="muted">공개</span></div>
        <div class="card"><b>${count("user")}</b><br><span class="muted">로그인 필요</span></div>
        <div class="card"><b>${count("admin")}</b><br><span class="muted">관리자 전용</span></div>
      </div>
      ${practice.view()}
      ${tags.map((t) => `<h2>${esc(TAG_LABELS[t] || t)}</h2>${ops.map((o, i) => (o.tag === t ? endpointCard(o, i) : "")).join("")}`).join("")}
      <p class="muted" style="margin-top:32px">정적 문서가 필요하면 Claude Code에서 <code>/make-api-doc</code>을 실행해 <code>docs/api.md</code>를 만드세요.</p>
    </div>`;
  }

  function print(out, text) { out.hidden = false; out.textContent = text; }

  async function run(form) {
    const op = ops[Number(form.dataset.op)];
    const out = form.querySelector(".out-pre");
    let path = op.path;
    const query = new URLSearchParams();
    form.querySelectorAll("[data-param]").forEach((input) => {
      const v = input.value.trim();
      if (input.dataset.in === "path") path = path.replace(`{${input.dataset.param}}`, encodeURIComponent(v));
      else if (v) query.set(input.dataset.param, v);
    });
    let body;
    if (op.body) {
      try { body = JSON.parse(form.elements.body.value); }
      catch { return print(out, "요청 본문이 올바른 JSON이 아닙니다."); }
    }
    try {
      const qs = query.toString();
      const res = await apiRaw(path + (qs ? "?" + qs : ""), { method: op.method, body });
      let shown = res.data;
      if (res.ok && res.data?.access_token) {
        // 토큰은 세션에만 저장하고 화면에는 노출하지 않는다
        session.save(res.data);
        renderNav();
        document.getElementById("apiAuthState").textContent = authStateText();
        shown = { ...res.data, access_token: "(저장됨 · 화면에는 표시하지 않음)" };
      }
      print(out, `${res.status} ${res.ok ? "성공" : "실패"}\n${JSON.stringify(shown, null, 2)}`);
    } catch (e) { print(out, e.message); }
  }

  // render()마다 #apiDocs가 새로 만들어지므로 리스너가 중복되지 않는다
  function bind() {
    const root = document.getElementById("apiDocs");
    if (!root) return;
    root.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-goto]");
      if (!btn) return;
      const card = document.getElementById("ep-" + ops.findIndex((o) => o.key === btn.dataset.goto));
      if (!card) return;
      card.open = true;
      card.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    practice.bind();
    root.addEventListener("submit", (e) => {
      const form = e.target.closest("form.try");
      if (!form) return;
      e.preventDefault();
      run(form);
    });
  }

  function refreshAuth() {
    const el = document.getElementById("apiAuthState");
    if (el) el.textContent = authStateText();
  }

  return { view, bind, refreshAuth };
})();
