/* ==========================================================================
   Smart Warehouse Monitor — dashboard logic
   Polls the Flask API every 5 s and renders KPIs, inventory, charts and logs.
   Use ?api=http://<server-ip>:5000 to point at a different backend.
   ========================================================================== */

const API = new URLSearchParams(location.search).get("api") || "";
const POLL_MS = 5000;
const HISTORY_POINTS = 60;

// Thresholds (mirror backend/app.py and firmware config.h)
const T = { distAlert: 15, distWarn: 25, gas: 2000, gasWarn: 1500, tempHigh: 30, tempCrit: 35, humHigh: 80, binDepth: 60 };

const PRODUCT_COLORS = { P001: "#4f8cff", P002: "#22d3ee", P003: "#f59e0b" };

const state = { products: [], forecast: {}, latest: null, online: false };
const charts = {};

// ------------------------------------------------------------------ helpers
const $ = (id) => document.getElementById(id);

async function api(path, opts = {}) {
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.message || `HTTP ${res.status}`);
  return body;
}

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtTime = (ts) => (ts ? new Date(ts).toLocaleTimeString([], { hour12: false }) : "—");

function ago(ts) {
  if (!ts) return "never";
  const s = Math.max(0, Math.round((Date.now() - new Date(ts).getTime()) / 1000));
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}

function toast(msg, isErr = false) {
  const t = $("toast");
  t.textContent = msg;
  t.className = "toast" + (isErr ? " err" : "");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.add("hidden"), 3000);
}

function setKpi(key, value, digits, chipText, level) {
  $("v" + key).textContent = value == null || isNaN(value) ? "--" : Number(value).toFixed(digits);
  const chip = $("s" + key);
  chip.textContent = chipText;
  chip.className = "chip " + level;
  const tile = chip.closest(".kpi");
  tile.classList.remove("ok", "warn", "crit");
  if (level === "ok" || level === "warn" || level === "crit") tile.classList.add(level);
}

const occupancy = (d) => (d == null ? null : Math.max(0, Math.min(100, (1 - d / T.binDepth) * 100)));

// ------------------------------------------------------------------- charts
Chart.defaults.color = "#8b97b3";
Chart.defaults.font.family = "Inter, system-ui, sans-serif";
Chart.defaults.borderColor = "rgba(35,48,79,.6)";

function lineChart(canvasId, datasets, scales) {
  return new Chart($(canvasId), {
    type: "line",
    data: { labels: [], datasets },
    options: {
      responsive: true, maintainAspectRatio: false, animation: { duration: 300 },
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { labels: { boxWidth: 10, boxHeight: 10, usePointStyle: true } } },
      elements: { point: { radius: 0, hoverRadius: 4 }, line: { tension: 0.35, borderWidth: 2 } },
      scales: { x: { ticks: { maxTicksLimit: 6 }, grid: { display: false } }, ...scales },
    },
  });
}

function ds(label, color, yAxisID = "y", fill = false) {
  return { label, data: [], borderColor: color, backgroundColor: color + "22", yAxisID, fill };
}

function initCharts() {
  charts.env = lineChart("chartEnv",
    [ds("Temperature (°C)", "#f97316", "y", true), ds("Humidity (%)", "#22d3ee", "y1")],
    { y: { position: "left", title: { display: true, text: "°C" } },
      y1: { position: "right", grid: { drawOnChartArea: false }, title: { display: true, text: "%" } } });

  charts.occ = lineChart("chartOcc",
    [ds("Distance (cm)", "#4f8cff", "y", true), ds("Gas (ADC)", "#ef4444", "y1")],
    { y: { position: "left", min: 0, title: { display: true, text: "cm" } },
      y1: { position: "right", min: 0, max: 4095, grid: { drawOnChartArea: false }, title: { display: true, text: "ADC" } } });

  charts.light = lineChart("chartLight",
    [ds("Light (%)", "#facc15", "y", true)],
    { y: { min: 0, max: 100 } });

  charts.pred = lineChart("chartPred", [], {
    y: { min: 0, max: 20, title: { display: true, text: "Units / 24 h" } },
  });
  charts.pred.options.elements.point.radius = 3;
  charts.pred.options.spanGaps = true;

  charts.fi = new Chart($("chartFI"), {
    type: "bar",
    data: { labels: [], datasets: [{ data: [], backgroundColor: "#4f8cff", borderRadius: 6 }] },
    options: {
      indexAxis: "y", responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { grid: { display: false } }, y: { grid: { display: false } } },
    },
  });
}

// ------------------------------------------------------------------ status
async function refreshStatus() {
  try {
    const s = await api("/api/status");
    state.online = true;
    $("totalLogs").textContent = s.total_logs;
    $("lastSeen").textContent = ago(s.last_device_contact);

    const fresh = s.last_device_contact && Date.now() - new Date(s.last_device_contact) < 30000;
    const pill = $("connPill");
    pill.className = "pill " + (fresh ? "pill-on" : "pill-idle");
    $("connText").textContent = fresh ? "Device online" : "API online · device idle";

    const n = s.active_alerts_10min;
    $("vAlerts").textContent = n;
    const lvl = n === 0 ? "ok" : n > 5 ? "crit" : "warn";
    setKpi("Alerts", n, 0, n === 0 ? "All clear" : "Attention", lvl);
  } catch (e) {
    state.online = false;
    $("connPill").className = "pill pill-off";
    $("connText").textContent = "Backend offline";
  }
}

// ----------------------------------------------------------------- history
async function refreshHistory() {
  const { data } = await api(`/api/history?limit=${HISTORY_POINTS}`);
  if (!data.length) return;
  const latest = data[data.length - 1];
  state.latest = latest;

  // KPI tiles
  const t = latest.temperature;
  setKpi("Temp", t, 1, t > T.tempCrit ? "Critical" : t > T.tempHigh ? "High" : "Normal",
    t > T.tempCrit ? "crit" : t > T.tempHigh ? "warn" : "ok");

  const h = latest.humidity;
  setKpi("Hum", h, 0, h > T.humHigh ? "High" : h < 30 ? "Dry" : "Normal", h > T.humHigh ? "warn" : "ok");

  const d = latest.distance_cm;
  setKpi("Dist", d, 1, d < T.distAlert ? "Bin full" : d < T.distWarn ? "Filling" : "Normal",
    d < T.distAlert ? "crit" : d < T.distWarn ? "warn" : "ok");
  const occ = occupancy(d);
  $("vOcc").textContent = `Occupancy ${occ == null ? "--" : occ.toFixed(0)}%`;

  const g = latest.mq_analog;
  const gasHigh = latest.gas_alert || g > T.gas;
  setKpi("Gas", g, 0, gasHigh ? "Gas alert" : g > T.gasWarn ? "Elevated" : "Clean",
    gasHigh ? "crit" : g > T.gasWarn ? "warn" : "ok");

  const l = latest.light_pct;
  setKpi("Light", l, 0, l > 75 ? "Bright" : l >= 40 ? "Medium" : "Dark", l > 75 ? "ok" : l >= 40 ? "info" : "warn");

  // Charts
  const labels = data.map((r) => fmtTime(r.ts));
  const set = (chart, ...series) => {
    chart.data.labels = labels;
    series.forEach((s, i) => (chart.data.datasets[i].data = s));
    chart.update("none");
  };
  set(charts.env, data.map((r) => r.temperature), data.map((r) => r.humidity));
  set(charts.occ, data.map((r) => r.distance_cm), data.map((r) => r.mq_analog));
  set(charts.light, data.map((r) => r.light_pct));
}

// --------------------------------------------------------------- inventory
async function refreshInventory() {
  const promo = $("promoToggle").checked ? 1 : 0;
  const [inv, fc] = await Promise.all([
    api("/api/inventory"),
    api(`/api/forecast?promo=${promo}`).catch(() => ({ data: [] })),
  ]);
  state.products = inv.data;
  state.forecast = Object.fromEntries(fc.data.map((f) => [f.product_id, f]));
  renderInventory();
}

function renderInventory() {
  $("inventory").innerHTML = state.products.map((p) => {
    const f = state.forecast[p.id] || {};
    const scaleMax = Math.max(p.reorder_point * 5, p.stock, 1);
    const pct = Math.min(100, (p.stock / scaleMax) * 100);
    const rpPct = (p.reorder_point / scaleMax) * 100;
    const exp = p.days_to_expiry;
    const expChip = exp == null ? "" :
      exp < 0 ? `<span class="chip crit">Expired</span>` :
      exp <= 3 ? `<span class="chip crit">Expires in ${exp}d</span>` :
      exp <= 14 ? `<span class="chip warn">Expires in ${exp}d</span>` :
      `<span class="chip ok">Exp. ${exp}d</span>`;
    const stockChip = p.low_stock ? `<span class="chip warn">Low stock</span>` : `<span class="chip ok">In stock</span>`;
    const runsOut = f.predicted_demand != null && f.stock_after_demand < p.reorder_point;

    return `
    <div class="card product ${p.low_stock ? "low" : ""}">
      <div class="p-head">
        <div><div class="p-name">${esc(p.name)}</div><div class="p-id">${esc(p.id)} · RFID ${esc(p.rfid_uid)}</div></div>
        <div class="p-badges">${stockChip}${expChip}</div>
      </div>
      <div>
        <div class="p-stock"><b>${p.stock}</b><span>units on hand</span></div>
        <div class="bar" style="margin-top:10px">
          <div class="bar-fill" style="width:${pct}%"></div>
          <div class="bar-marker" style="left:${rpPct}%" title="Reorder point"></div>
        </div>
        <div class="bar-legend"><span>0</span><span style="color:var(--crit)">Reorder point: ${p.reorder_point}</span><span>${scaleMax}</span></div>
      </div>
      <div class="p-stats">
        <div class="p-stat"><span>Forecast 24 h</span><b>${f.predicted_demand ?? "—"}</b></div>
        <div class="p-stat"><span>Suggested order</span><b>${f.restock_recommendation ?? "—"}</b></div>
        <div class="p-stat"><span>After demand</span><b style="color:${runsOut ? "var(--warn)" : "inherit"}">${f.stock_after_demand ?? "—"}</b></div>
      </div>
      <div class="p-actions">
        <button class="btn ghost" onclick="adjustStock('${p.id}', -5)">Dispatch −5</button>
        <button class="btn ghost" onclick="adjustStock('${p.id}', 20)">Receive +20</button>
      </div>
    </div>`;
  }).join("");
}

async function adjustStock(pid, delta) {
  const p = state.products.find((x) => x.id === pid);
  if (!p) return;
  try {
    await api(`/api/inventory/${pid}`, { method: "POST", body: JSON.stringify({ stock: Math.max(0, p.stock + delta) }) });
    toast(`${p.name}: stock ${delta > 0 ? "+" : ""}${delta}`);
    await Promise.all([refreshInventory(), refreshAlerts()]);
  } catch (e) {
    toast(e.message, true);
  }
}
window.adjustStock = adjustStock;

// ------------------------------------------------------------ alerts/events
async function refreshAlerts() {
  const { data } = await api("/api/alerts?limit=50");
  $("alertCount").textContent = `${data.length} alerts`;
  $("alertBody").innerHTML = data.length ? data.map((a) => `
    <tr>
      <td class="mono">${fmtTime(a.ts)}</td>
      <td><span class="chip ${a.level === "critical" ? "crit" : "warn"}">${esc(a.level)}</span></td>
      <td>${esc(a.type)}</td>
      <td>${esc(a.message)}</td>
    </tr>`).join("") : `<tr><td colspan="4" class="empty">No alerts yet</td></tr>`;

  // Critical banner for alerts in the last 30 s
  const recent = data.find((a) => a.level === "critical" && Date.now() - new Date(a.ts) < 30000);
  $("criticalBanner").classList.toggle("hidden", !recent);
  if (recent) $("criticalText").textContent = `CRITICAL: ${recent.message} (${ago(recent.ts)})`;
}

const EVENT_STYLE = { ORDER: ["info", "📦"], RESTOCK: ["ok", "🚚"], EMERGENCY: ["crit", "🚨"], SCAN: ["info", "🏷️"] };

async function refreshEvents() {
  const { data } = await api("/api/events?limit=25");
  const names = Object.fromEntries(state.products.map((p) => [p.id, p.name]));
  $("eventList").innerHTML = data.length ? data.map((e) => {
    const [cls, icon] = EVENT_STYLE[String(e.event).toUpperCase()] || ["info", "•"];
    const what = e.product_id ? `${names[e.product_id] || e.product_id}` : (e.card_uid || "System");
    return `<li>
      <div class="ev-main"><b>${icon} ${esc(e.event)} · ${esc(what)}</b>
        <span class="mono">${e.card_uid ? "UID " + esc(e.card_uid) : ""}${e.stock_level != null ? " · stock " + e.stock_level : ""}</span></div>
      <span class="chip ${cls}">${fmtTime(e.ts)}</span>
    </li>`;
  }).join("") : `<li class="empty">No events yet</li>`;
}

// ------------------------------------------------------------- predictions
async function refreshPredictions() {
  const { data } = await api("/api/predictions?limit=40");
  const labels = data.map((p) => fmtTime(p.ts));
  const ids = [...new Set(data.map((p) => p.product_id || "manual"))].sort();
  const names = Object.fromEntries(state.products.map((p) => [p.id, p.name]));
  charts.pred.data.labels = labels;
  charts.pred.data.datasets = ids.map((id) => {
    const color = PRODUCT_COLORS[id] || "#a78bfa";
    return {
      label: names[id] ? `${names[id]} (${id})` : "Manual",
      data: data.map((p) => ((p.product_id || "manual") === id ? p.predicted_demand : null)),
      borderColor: color, backgroundColor: color, spanGaps: true,
    };
  });
  charts.pred.update("none");
}

async function loadModel() {
  try {
    const m = await api("/api/model");
    $("mR2").textContent = m.r2?.toFixed(3) ?? "—";
    $("mMAE").textContent = m.mae?.toFixed(2) ?? "—";
    $("mRMSE").textContent = m.rmse?.toFixed(2) ?? "—";
    $("mWithin").textContent = m.within_2_units_pct != null ? m.within_2_units_pct.toFixed(0) + "%" : "—";
    $("mTrained").textContent = `Trained ${new Date(m.trained_at).toLocaleString()} · ${m.n_train} train / ${m.n_test} test samples (75/25 split)`;
    const fi = Object.entries(m.feature_importance || {}).sort((a, b) => b[1] - a[1]);
    charts.fi.data.labels = fi.map(([k]) => k);
    charts.fi.data.datasets[0].data = fi.map(([, v]) => +(v * 100).toFixed(1));
    charts.fi.update();
  } catch (e) {
    $("mTrained").textContent = "Model not loaded — run backend/train_model.py";
  }
}

// --------------------------------------------------------- prediction form
const FIELDS = ["orders", "avg_temp_c", "occupancy_pct", "ambient_light_adc", "promo_flag", "day_of_week", "stock_on_hand", "reorder_point"];

function fillProduct() {
  const p = state.products.find((x) => x.id === $("fProduct").value);
  if (!p) return;
  $("f_stock_on_hand").value = p.stock;
  $("f_reorder_point").value = p.reorder_point;
}

function fillLive() {
  const l = state.latest;
  if (l) {
    if (l.temperature != null) $("f_avg_temp_c").value = l.temperature;
    const occ = occupancy(l.distance_cm);
    if (occ != null) $("f_occupancy_pct").value = occ.toFixed(1);
    if (l.light_adc != null) $("f_ambient_light_adc").value = l.light_adc;
  }
  $("f_day_of_week").value = (new Date().getDay() + 6) % 7; // JS Sunday=0 -> spec Monday=0
  $("f_promo_flag").value = $("promoToggle").checked ? 1 : 0;
  fillProduct();
  toast(l ? "Filled from latest sensor data" : "No sensor data yet — used defaults");
}

async function submitPrediction(ev) {
  ev.preventDefault();
  const body = { product_id: $("fProduct").value };
  FIELDS.forEach((f) => (body[f] = Number($("f_" + f).value)));
  const t0 = performance.now();
  try {
    const r = await api("/api/predict", { method: "POST", body: JSON.stringify(body) });
    const ms = performance.now() - t0;
    $("rDemand").textContent = `${r.predicted_demand} units`;
    $("rRestock").textContent = `${r.restock_recommendation} units`;
    $("rLatency").textContent = `${ms.toFixed(0)} ms`;
    refreshPredictions();
  } catch (e) {
    toast(e.message, true);
  }
}

// -------------------------------------------------------------------- main
async function tick() {
  await refreshStatus();
  if (!state.online) return;
  const jobs = [refreshHistory(), refreshInventory(), refreshAlerts(), refreshPredictions()];
  await Promise.allSettled(jobs);
  await refreshEvents().catch(() => {});
}

function startClock() {
  const upd = () => ($("clock").textContent = new Date().toLocaleTimeString([], { hour12: false }));
  upd();
  setInterval(upd, 1000);
}

document.addEventListener("DOMContentLoaded", async () => {
  initCharts();
  startClock();
  $("predictForm").addEventListener("submit", submitPrediction);
  $("btnLive").addEventListener("click", fillLive);
  $("fProduct").addEventListener("change", fillProduct);
  $("promoToggle").addEventListener("change", refreshInventory);
  await tick();
  fillProduct();
  loadModel();
  setInterval(tick, POLL_MS);
});
