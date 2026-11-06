const API_BASE = "http://localhost:8000";
const COURSE_ID = 1;

const session = {
  get token() { return localStorage.getItem("token"); },
  get user() { return JSON.parse(localStorage.getItem("user") || "null"); },
  save(data) { localStorage.setItem("token", data.access_token); localStorage.setItem("user", JSON.stringify(data.user)); },
  clear() { localStorage.removeItem("token"); localStorage.removeItem("user"); },
};

// 상태 코드와 본문을 그대로 돌려주는 저수준 호출 (API 실습 화면용, 세션을 건드리지 않는다)
async function apiRaw(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth && session.token) headers.Authorization = "Bearer " + session.token;
  let res;
  try {
    res = await fetch(API_BASE + path, { method, headers, body: body ? JSON.stringify(body) : undefined });
  } catch {
    throw new Error("서버에 연결할 수 없습니다. 백엔드가 실행 중인지 확인해 주세요.");
  }
  const data = await res.json().catch(() => ({}));
  return { status: res.status, ok: res.ok, data };
}

async function api(path, options) {
  const { ok, status, data } = await apiRaw(path, options);
  if (!ok) {
    if (status === 401 && session.token) { session.clear(); }
    const d = data.detail;
    throw new Error(typeof d === "string" ? d : "입력값을 확인해 주세요.");
  }
  return data;
}

async function fetchOpenApi() {
  const { ok, data } = await apiRaw("/openapi.json");
  if (!ok) throw new Error("API 명세를 불러오지 못했습니다.");
  return data;
}
