/* Level Watch card: water gauge or tank with thresholds, trend and forecast.
 *
 * Reads everything from the Level Watch "level" sensor; any other entity of
 * the same Level Watch device works too and is resolved to that sensor.
 */

const CARD_VERSION = "0.4.0";
const NORMAL_WATER = "#2b8fd6";

const TEXT = {
  de: {
    rising: "steigend", falling: "fallend", stable: "stabil", unknown: "Tendenz offen",
    normal: "Normal", next: "Nächste Schwelle", in: "in", reached: "erreicht",
    left: "Reicht noch", per_day: "pro Tag", full_in: "Voll in", of: "von",
    min: "Min", max: "Max", change: "24 h", stale: "Daten veraltet",
    unavailable: "Sensor nicht verfügbar", no_data: "Noch keine Daten",
    not_found: "Entität nicht gefunden", not_level_watch: "Keine Level-Watch-Entität",
    day: "Tag", days: "Tage", h: "h", min_u: "min", history: "Verlauf",
    entity: "Entität", title: "Titel", mode: "Darstellung", history_hours: "Verlauf (Stunden, 0 = aus)",
    mode_auto: "Automatisch", mode_water: "Wasserpegel", mode_tank: "Tank",
  },
  en: {
    rising: "rising", falling: "falling", stable: "stable", unknown: "trend pending",
    normal: "Normal", next: "Next threshold", in: "in", reached: "reached",
    left: "Lasts", per_day: "per day", full_in: "Full in", of: "of",
    min: "Min", max: "Max", change: "24 h", stale: "Data stale",
    unavailable: "Sensor unavailable", no_data: "No data yet",
    not_found: "Entity not found", not_level_watch: "Not a Level Watch entity",
    day: "day", days: "days", h: "h", min_u: "min", history: "History",
    entity: "Entity", title: "Title", mode: "Display", history_hours: "History (hours, 0 = off)",
    mode_auto: "Automatic", mode_water: "Water level", mode_tank: "Tank",
  },
};

const TREND_ICON = {
  rising: "M4 18 L11 11 L14 14 L20 8 M15 8 H20 V13",
  falling: "M4 6 L11 13 L14 10 L20 16 M15 16 H20 V11",
  stable: "M4 12 H19 M15 8 L19 12 L15 16",
};

function lang(hass) {
  const l = (hass && (hass.locale?.language || hass.language)) || "en";
  return l.startsWith("de") ? "de" : "en";
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

function isLevelState(state) {
  return Boolean(state && state.attributes && "source_entity" in state.attributes
    && "thresholds" in state.attributes);
}

/** Find the Level Watch level sensor for any entity of the same device. */
function resolveLevelEntity(hass, entityId) {
  const state = hass.states[entityId];
  if (isLevelState(state)) return entityId;
  const device = hass.entities?.[entityId]?.device_id;
  if (!device) return null;
  for (const [id, entry] of Object.entries(hass.entities)) {
    if (entry.device_id === device && isLevelState(hass.states[id])) return id;
  }
  return null;
}

class LevelWatchCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._history = null;
    this._historyFetched = 0;
    this._renderKey = "";
  }

  static getStubConfig(hass) {
    const id = Object.keys(hass.states).find((e) => isLevelState(hass.states[e]));
    return { entity: id || "" };
  }

  static getConfigForm() {
    const t = TEXT[document.documentElement.lang?.startsWith("de") ? "de" : "en"];
    return {
      schema: [
        { name: "entity", required: true, selector: { entity: { filter: { integration: "level_watch" } } } },
        { name: "title", selector: { text: {} } },
        {
          name: "mode",
          selector: { select: { mode: "dropdown", options: ["auto", "water", "tank"].map((v) => ({ value: v, label: t[`mode_${v}`] })) } },
        },
        { name: "history_hours", selector: { number: { min: 0, max: 168, mode: "box" } } },
      ],
      computeLabel: (schema) => t[schema.name] || schema.name,
    };
  }

  setConfig(config) {
    if (!config || !config.entity) throw new Error("entity is required");
    this._config = { mode: "auto", history_hours: 24, ...config };
    this._renderKey = "";
    this._history = null;
    this._historyFetched = 0;
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return this._config?.history_hours ? 5 : 4;
  }

  getGridOptions() {
    return { columns: 12, rows: this._config?.history_hours ? 5 : 4, min_columns: 6, min_rows: 3 };
  }

  // -- data ---------------------------------------------------------------------

  async _fetchHistory(entityId) {
    const hours = Number(this._config.history_hours) || 0;
    if (!hours || !this._hass.callWS) return;
    const now = Date.now();
    if (now - this._historyFetched < 5 * 60 * 1000) return;
    this._historyFetched = now;
    try {
      const result = await this._hass.callWS({
        type: "history/history_during_period",
        start_time: new Date(now - hours * 3600 * 1000).toISOString(),
        end_time: new Date(now).toISOString(),
        entity_ids: [entityId],
        minimal_response: true,
        no_attributes: true,
      });
      const rows = result[entityId] || [];
      this._history = rows
        .map((r) => ({ t: (r.lu ?? r.last_updated) * 1000, v: parseFloat(r.s ?? r.state) }))
        .filter((p) => Number.isFinite(p.v) && Number.isFinite(p.t));
      this._renderKey = "";
      this._render();
    } catch (err) {
      console.warn("level-watch-card: history unavailable", err);
    }
  }

  // -- rendering ----------------------------------------------------------------

  _render() {
    if (!this._config || !this._hass) return;
    const hass = this._hass;
    const t = TEXT[lang(hass)];
    const entityId = resolveLevelEntity(hass, this._config.entity);
    const state = entityId && hass.states[entityId];
    const key = [entityId, state?.last_updated, state?.state, lang(hass), this._history?.length,
      hass.themes?.darkMode].join("|");
    if (key === this._renderKey) return;
    this._renderKey = key;

    if (!state) {
      const msg = hass.states[this._config.entity] ? t.not_level_watch : t.not_found;
      this.shadowRoot.innerHTML = `${STYLE}<ha-card><div class="warn">${esc(msg)}: ${esc(this._config.entity)}</div></ha-card>`;
      return;
    }
    this._fetchHistory(entityId);

    const a = state.attributes;
    const level = parseFloat(state.state);
    const hasLevel = Number.isFinite(level);
    const mode = this._config.mode === "auto" || !this._config.mode
      ? (a.kind === "tank" ? "tank" : "water")
      : this._config.mode;
    const color = a.stage ? a.color : NORMAL_WATER;
    const title = this._config.title ?? (hass.devices?.[hass.entities?.[entityId]?.device_id]?.name
      || (a.friendly_name || "").replace(/\s+(Pegel|Level)$/i, ""));
    const fmt = (v, d = 1) => new Intl.NumberFormat(hass.locale?.language || "en", {
      maximumFractionDigits: d, minimumFractionDigits: 0,
    }).format(v);

    const quality = a.quality || (hasLevel ? "ok" : "no_data");
    const qualityNote = quality === "ok" ? "" : `<div class="quality">${esc(t[quality] || quality)}</div>`;

    const visual = mode === "tank" ? this._tankSvg(a, level, color) : this._waterSvg(a, level, color);
    const stats = mode === "tank"
      ? this._tankStats(a, level, hasLevel, fmt, t)
      : this._waterStats(a, level, hasLevel, fmt, t);
    const spark = this._sparkline(a, color);

    this.shadowRoot.innerHTML = `${STYLE}
      <ha-card style="--lw-color:${esc(color)}">
        <div class="head">
          <div class="title">${esc(title)}</div>
          ${this._stageChip(a, t)}
        </div>
        <div class="body ${quality === "ok" ? "" : "dim"}">
          <div class="visual">${visual}</div>
          <div class="stats">${stats}</div>
        </div>
        ${qualityNote}
        ${spark}
      </ha-card>`;
    this.shadowRoot.querySelector("ha-card").addEventListener("click", () => {
      const ev = new Event("hass-more-info", { bubbles: true, composed: true });
      ev.detail = { entityId };
      this.dispatchEvent(ev);
    });
  }

  _stageChip(a, t) {
    const name = a.stage || t.normal;
    const color = a.stage ? a.color : "var(--secondary-text-color)";
    return `<div class="chip" style="--chip:${esc(color)}">${esc(name)}</div>`;
  }

  _trendLine(a, fmt, t) {
    if (a.quality === "unavailable" || a.quality === "no_data") return "";
    const trend = a.trend || "unknown";
    const path = TREND_ICON[trend];
    const icon = path
      ? `<svg class="ticon ${trend}" viewBox="0 0 24 24"><path d="${path}"/></svg>` : "";
    let rate = "";
    if (Number.isFinite(a.rate)) {
      const shown = fmt(Math.abs(a.rate));
      const sign = Math.abs(a.rate) < 0.05 ? "±" : a.rate > 0 ? "+" : "−";
      rate = ` · ${sign}${Math.abs(a.rate) < 0.05 ? "0" : shown} cm/h`;
    }
    return `<div class="trend">${icon}<span>${esc(t[trend] || trend)}${rate}</span></div>`;
  }

  _duration(hours, t, fmt) {
    if (!Number.isFinite(hours)) return "";
    if (hours < 1) return `${Math.max(1, Math.round(hours * 60))} ${t.min_u}`;
    if (hours < 48) {
      const h = Math.floor(hours);
      const m = Math.round((hours - h) * 60);
      return m ? `${h} ${t.h} ${m} ${t.min_u}` : `${h} ${t.h}`;
    }
    const d = hours / 24;
    return `${fmt(d, 0)} ${Math.round(d) === 1 ? t.day : t.days}`;
  }

  _nextLine(a, t, fmt) {
    if (!a.next_threshold || !Number.isFinite(a.hours_to_next)) return "";
    const th = (a.thresholds || []).find((x) => x.name === a.next_threshold);
    const dot = th ? `<span class="dot" style="background:${esc(th.color)}"></span>` : "";
    return `<div class="line">${dot}${esc(a.next_threshold)} ${t.in} <b>${esc(this._duration(a.hours_to_next, t, fmt))}</b></div>`;
  }

  _waterStats(a, level, hasLevel, fmt, t) {
    const big = hasLevel ? `${fmt(level)}<span class="unit">cm</span>` : "–";
    const extremes = [
      Number.isFinite(a.min_24h) ? `${t.min} ${fmt(a.min_24h)}` : "",
      Number.isFinite(a.max_24h) ? `${t.max} ${fmt(a.max_24h)}` : "",
      Number.isFinite(a.change_24h) ? `${t.change} ${a.change_24h > 0 ? "+" : ""}${fmt(a.change_24h)}` : "",
    ].filter(Boolean).join(" · ");
    return `
      <div class="big">${big}</div>
      ${this._trendLine(a, fmt, t)}
      ${this._nextLine(a, t, fmt)}
      ${extremes ? `<div class="small">${esc(extremes)} cm</div>` : ""}`;
  }

  _tankStats(a, level, hasLevel, fmt, t) {
    const pct = Number.isFinite(a.percent) ? a.percent : null;
    const big = pct !== null
      ? `${fmt(pct, 0)}<span class="unit">%</span>`
      : (hasLevel ? `${fmt(level)}<span class="unit">cm</span>` : "–");
    const lines = [];
    if (Number.isFinite(a.volume)) {
      const cap = Number.isFinite(a.capacity) ? ` ${t.of} ${fmt(a.capacity, 0)} L` : "";
      lines.push(`<div class="line"><b>${fmt(a.volume, 0)} L</b>${cap}</div>`);
    } else if (pct !== null && hasLevel) {
      lines.push(`<div class="line">${fmt(level)} cm</div>`);
    }
    if (Number.isFinite(a.days_left)) {
      lines.push(`<div class="line">${t.left} <b>${esc(this._duration(a.days_left * 24, t, fmt))}</b></div>`);
    }
    if (Number.isFinite(a.consumption)) {
      lines.push(`<div class="small">${fmt(a.consumption)} L ${t.per_day}</div>`);
    }
    if (Number.isFinite(a.hours_to_full)) {
      lines.push(`<div class="line">${t.full_in} <b>${esc(this._duration(a.hours_to_full, t, fmt))}</b></div>`);
    }
    return `
      <div class="big">${big}</div>
      ${this._trendLine(a, fmt, t)}
      ${lines.join("")}
      ${this._nextLine(a, t, fmt)}`;
  }

  // -- water gauge --------------------------------------------------------------

  _waterRange(a, level) {
    const values = [a.reference_min, a.reference_max, a.min_24h, a.max_24h, level,
      ...(a.thresholds || []).map((x) => x.value)].filter(Number.isFinite);
    if (!values.length) return [0, 100];
    let lo = Math.min(...values);
    let hi = Math.max(...values);
    const span = Math.max(hi - lo, 10);
    lo -= span * 0.12;
    hi += span * 0.12;
    if (Number.isFinite(a.reference_min) && a.reference_min >= lo - span * 0.2) lo = Math.min(lo, a.reference_min);
    return [lo, hi];
  }

  _waterSvg(a, level, color) {
    const [lo, hi] = this._waterRange(a, level);
    const top = 12;
    const bottom = 208;
    const y = (v) => bottom - ((v - lo) / (hi - lo)) * (bottom - top);
    const ly = Number.isFinite(level) ? Math.max(top, Math.min(bottom, y(level))) : bottom;

    // Gauge staff: alternating blocks like a real gauge board, labels at nice steps.
    const step = niceStep((hi - lo) / 6);
    let ticks = "";
    for (let v = Math.ceil(lo / step) * step; v <= hi; v += step) {
      const ty = y(v);
      ticks += `<line x1="8" x2="30" y1="${ty}" y2="${ty}" class="tick"/>`
        + `<text x="34" y="${ty + 3}" class="tlabel">${Math.round(v)}</text>`;
      const half = y(v + step / 2);
      if (half > top) ticks += `<line x1="8" x2="18" y1="${half}" y2="${half}" class="tick minor"/>`;
    }
    const lines = (a.thresholds || []).map((th) => {
      const ty = y(th.value);
      if (ty < top - 1 || ty > bottom + 1) return "";
      return `<line x1="8" x2="152" y1="${ty}" y2="${ty}" stroke="${esc(th.color)}" class="thr ${th.active ? "on" : ""}"/>`
        + `<polygon points="152,${ty} 158,${ty - 4} 158,${ty + 4}" fill="${esc(th.color)}"/>`;
    }).join("");
    return `
      <svg viewBox="0 0 160 220" class="gauge" aria-hidden="true">
        <defs>
          <linearGradient id="lwWater" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" stop-color="${esc(color)}" stop-opacity="0.85"/>
            <stop offset="1" stop-color="${esc(color)}" stop-opacity="0.45"/>
          </linearGradient>
          <clipPath id="lwBasin"><rect x="54" y="${top}" width="98" height="${bottom - top}" rx="4"/></clipPath>
        </defs>
        <rect x="54" y="${top}" width="98" height="${bottom - top}" rx="4" class="basin"/>
        <g clip-path="url(#lwBasin)">
          ${waves(ly, 54, 98, bottom, "url(#lwWater)")}
        </g>
        <rect x="6" y="${top}" width="26" height="${bottom - top}" rx="2" class="staff"/>
        ${ticks}
        ${lines}
        <line x1="4" x2="152" y1="${ly}" y2="${ly}" class="surface"/>
      </svg>`;
  }

  // -- tank ---------------------------------------------------------------------

  _tankSvg(a, level, color) {
    const topH = Number.isFinite(a.top) && a.top > 0 ? a.top
      : Math.max(level || 0, ...(a.thresholds || []).map((x) => x.value), 1) * 1.1;
    const frac = (v) => Math.max(0, Math.min(1, v / topH));
    let outline;
    let box;
    if (a.shape === "horizontal_cylinder") {
      box = { x: 30, y: 40, w: 140, h: 140 };
      outline = `<circle cx="100" cy="110" r="70"/>`;
    } else if (a.shape === "vertical_cylinder") {
      box = { x: 45, y: 24, w: 110, h: 180 };
      outline = `<path d="M45 34 a55 10 0 0 1 110 0 V194 a55 10 0 0 1 -110 0 Z"/>`;
    } else {
      box = { x: 40, y: 20, w: 120, h: 186 };
      outline = `<rect x="40" y="20" width="120" height="186" rx="8"/>`;
    }
    const y = (v) => box.y + box.h * (1 - frac(v));
    const ly = Number.isFinite(level) ? y(level) : box.y + box.h;
    const lines = (a.thresholds || []).map((th) => {
      const ty = y(th.value);
      return `<line x1="${box.x - 10}" x2="${box.x + box.w + 10}" y1="${ty}" y2="${ty}" stroke="${esc(th.color)}" class="thr ${th.active ? "on" : ""}"/>`;
    }).join("");
    return `
      <svg viewBox="0 0 200 220" class="tank" aria-hidden="true">
        <defs>
          <linearGradient id="lwFill" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0" stop-color="${esc(color)}" stop-opacity="0.95"/>
            <stop offset="0.5" stop-color="${esc(color)}" stop-opacity="0.7"/>
            <stop offset="1" stop-color="${esc(color)}" stop-opacity="0.9"/>
          </linearGradient>
          <clipPath id="lwTank">${outline}</clipPath>
        </defs>
        <g class="shell">${outline}</g>
        <g clip-path="url(#lwTank)">
          ${waves(ly, box.x, box.w, box.y + box.h + 12, "url(#lwFill)")}
        </g>
        ${lines}
        <g class="rim">${outline}</g>
      </svg>`;
  }

  // -- history ------------------------------------------------------------------

  _sparkline(a, color) {
    if (!Number(this._config.history_hours)) return "";
    const pts = this._history || [];
    if (pts.length < 2) return `<div class="spark empty"></div>`;
    const w = 300;
    const h = 56;
    const t0 = pts[0].t;
    const t1 = Date.now();
    const values = pts.map((p) => p.v);
    const ths = (a.thresholds || []).map((x) => x.value);
    let lo = Math.min(...values);
    let hi = Math.max(...values);
    // At least 10 cm tall, so sensor noise does not look like waves.
    if (hi - lo < 10) {
      const mid = (hi + lo) / 2;
      lo = mid - 5;
      hi = mid + 5;
    }
    // Show nearby thresholds, but do not flatten the curve for far away ones.
    const pad = hi - lo;
    for (const v of ths) if (v >= lo - pad && v <= hi + pad) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
    lo -= pad * 0.1;
    hi += pad * 0.1;
    const x = (t) => ((t - t0) / Math.max(t1 - t0, 1)) * w;
    const y = (v) => h - 4 - ((v - lo) / (hi - lo)) * (h - 8);
    let d = "";
    pts.forEach((p, i) => {
      // Step line: a value holds until the next one.
      d += i ? ` H${x(p.t).toFixed(1)} V${y(p.v).toFixed(1)}` : `M${x(p.t).toFixed(1)} ${y(p.v).toFixed(1)}`;
    });
    d += ` H${w}`;
    const area = `${d} V${h} H0 Z`;
    const lines = (a.thresholds || []).filter((th) => th.value >= lo && th.value <= hi)
      .map((th) => `<line x1="0" x2="${w}" y1="${y(th.value)}" y2="${y(th.value)}" stroke="${esc(th.color)}" class="thr"/>`)
      .join("");
    return `
      <svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true">
        <path d="${area}" fill="${esc(color)}" opacity="0.15"/>
        ${lines}
        <path d="${d}" fill="none" stroke="${esc(color)}" stroke-width="2" vector-effect="non-scaling-stroke"/>
      </svg>`;
  }
}

function niceStep(raw) {
  const pow = 10 ** Math.floor(Math.log10(Math.max(raw, 1e-6)));
  const n = raw / pow;
  return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10) * pow;
}

/** Water body from `surface` down to `bottom`, with two drifting waves on top. */
function waves(surface, x, width, bottom, fill) {
  const amp = 3;
  const len = 40;
  const wave = (offset) => {
    let d = `M${x - len * 2} ${surface}`;
    for (let i = -2; i * len < width + len * 2; i += 1) {
      d += ` q${len / 4} ${-amp + offset} ${len / 2} 0 t${len / 2} 0`;
    }
    return `${d} V${bottom} H${x - len * 2} Z`;
  };
  return `
    <path d="${wave(0)}" fill="${fill}" class="wave a"/>
    <path d="${wave(1)}" fill="${fill}" class="wave b" opacity="0.6"/>`;
}

const STYLE = `<style>
  :host { display: block; }
  ha-card { padding: 16px; cursor: pointer; overflow: hidden; height: 100%; box-sizing: border-box;
    display: flex; flex-direction: column; gap: 8px; }
  .head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
  .title { font-size: 1.15em; font-weight: 500; color: var(--primary-text-color);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .chip { flex: none; font-size: 0.85em; font-weight: 500; padding: 3px 10px; border-radius: 12px;
    color: var(--chip); background: color-mix(in srgb, var(--chip) 15%, transparent);
    border: 1px solid color-mix(in srgb, var(--chip) 40%, transparent); }
  .body { display: flex; gap: 16px; align-items: center; flex: 1; min-height: 0; }
  .body.dim { opacity: 0.55; filter: grayscale(0.6); }
  .visual { flex: 0 0 42%; max-width: 180px; align-self: stretch; display: flex; align-items: center; }
  .visual svg { width: 100%; height: auto; max-height: 220px; }
  .stats { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 6px; }
  .big { font-size: 2.6em; font-weight: 400; line-height: 1; color: var(--primary-text-color); }
  .unit { font-size: 0.45em; margin-left: 4px; color: var(--secondary-text-color); }
  .trend { display: flex; align-items: center; gap: 6px; color: var(--secondary-text-color); }
  .ticon { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 2.2;
    stroke-linecap: round; stroke-linejoin: round; flex: none; }
  .ticon.rising { color: var(--lw-color); }
  .ticon.falling { color: var(--lw-color); }
  .line { color: var(--primary-text-color); line-height: 1.35; }
  .line b { font-weight: 500; white-space: nowrap; }
  .small { font-size: 0.85em; color: var(--secondary-text-color); }
  .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px;
    vertical-align: 1px; }
  .quality { font-size: 0.85em; color: var(--warning-color, #ff9800); }
  .warn { color: var(--error-color, #db4437); }
  .basin { fill: color-mix(in srgb, var(--primary-text-color) 4%, transparent);
    stroke: var(--divider-color, #ccc); }
  .staff { fill: var(--card-background-color, #fff); stroke: var(--secondary-text-color); stroke-width: 1; }
  .tick { stroke: var(--primary-text-color); stroke-width: 1.4; }
  .tick.minor { stroke-width: 1; opacity: 0.6; }
  .tlabel { font-size: 9px; fill: var(--secondary-text-color); }
  .thr { stroke-width: 1.5; stroke-dasharray: 4 3; opacity: 0.75; }
  .thr.on { stroke-dasharray: none; stroke-width: 2; opacity: 1; }
  .surface { stroke: var(--lw-color); stroke-width: 1.5; opacity: 0.9; }
  .shell * { fill: color-mix(in srgb, var(--primary-text-color) 5%, transparent); }
  .rim * { fill: none; stroke: var(--secondary-text-color); stroke-width: 2; }
  .wave { transition: d 0.8s ease; }
  .wave.a { animation: lw-drift 6s linear infinite; }
  .wave.b { animation: lw-drift 9s linear infinite reverse; }
  @keyframes lw-drift { from { transform: translateX(0); } to { transform: translateX(40px); } }
  @media (prefers-reduced-motion: reduce) { .wave.a, .wave.b { animation: none; } }
  .spark { width: 100%; height: 56px; display: block; }
  .spark.empty { height: 56px; }
</style>`;

customElements.define("level-watch-card", LevelWatchCard);

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "level-watch-card")) {
  window.customCards.push({
    type: "level-watch-card",
    name: "Level Watch",
    description: "Wasserpegel oder Tank mit Schwellen, Tendenz und Prognose",
    preview: true,
    documentationURL: "https://github.com/berwil84afk/ha-level-watch",
  });
}

console.info(`%c LEVEL-WATCH-CARD %c ${CARD_VERSION} `, "background:#2b8fd6;color:#fff", "");
