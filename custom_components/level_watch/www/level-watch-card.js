/* Level Watch card: water gauge or tank with thresholds, trend and forecast.
 *
 * Reads everything from the Level Watch "level" sensor; any other entity of
 * the same Level Watch device works too and is resolved to that sensor.
 */

const CARD_VERSION = "0.7.5";
const STYLES = ["forecast", "classic", "ring", "compact"];
const NORMAL_WATER = "#2b8fd6";

const TEXT = {
  de: {
    rising: "steigend", falling: "fallend", stable: "stabil", unknown: "Tendenz offen",
    normal: "Normal", next: "Nächste Schwelle", in: "in", reached: "erreicht", level_now: "Pegel",
    left: "Reicht noch", per_day: "pro Tag", full_in: "Voll in", of: "von",
    min: "Min", max: "Max", change: "24 h", stale: "Daten veraltet",
    unavailable: "Sensor nicht verfügbar", no_data: "Noch keine Daten",
    not_found: "Entität nicht gefunden", not_level_watch: "Keine Level-Watch-Entität",
    day: "Tag", days: "Tage", h: "h", min_u: "min", history: "Verlauf",
    entity: "Entität", title: "Titel", mode: "Darstellung", history_hours: "Verlauf (Stunden)", show_history: "Verlauf anzeigen",
    mode_auto: "Automatisch", mode_water: "Wasserpegel", mode_tank: "Tank",
    style: "Stil", style_forecast: "Prognose", style_classic: "Klassisch (Pegellatte / Tank)",
    style_ring: "Ring", style_compact: "Kompakt", forecast_hours: "Prognose (Stunden)",
    now: "jetzt", expected: "voraussichtlich", today: "heute", tomorrow: "morgen",
    until: "bis", refilled: "Getankt", in_short: "in",
    edit_thresholds: "Schwellen bearbeiten", add_threshold: "Schwelle hinzufügen",
    save: "Speichern", cancel: "Abbrechen", saving: "Speichert …", delete: "Löschen",
    f_name: "Name", f_value: "Wert", f_above: "steigt auf/über", f_below: "fällt auf/unter",
    f_hysteresis: "Hysterese", f_notify: "Meldung senden", f_targets: "Melden über",
    f_critical: "Kritisch (Companion App, klingelt auch lautlos)", f_clear: "Entwarnung senden",
    f_repeat: "Wiederholen alle (min, 0 = einmal)", f_message: "Eigener Meldungstext",
    f_message_hint: "Leer für den Standardtext. Platzhalter: {name} {threshold} {value} {level} {trend} {rate}",
    more: "Meldung und mehr", no_thresholds: "Noch keine Schwellen. Leg die erste an.",
    new_threshold: "Neue Schwelle", err_name: "Jede Schwelle braucht einen Namen.",
    err_value: "Jede Schwelle braucht einen Wert.", err_targets: "Wähle für jede Schwelle mit Meldung mindestens ein Ziel.",
    err_save: "Speichern fehlgeschlagen", no_targets: "Keine Meldewege gefunden.", preview: "Vorschau",
  },
  en: {
    rising: "rising", falling: "falling", stable: "stable", unknown: "trend pending",
    normal: "Normal", next: "Next threshold", in: "in", reached: "reached", level_now: "Level",
    left: "Lasts", per_day: "per day", full_in: "Full in", of: "of",
    min: "Min", max: "Max", change: "24 h", stale: "Data stale",
    unavailable: "Sensor unavailable", no_data: "No data yet",
    not_found: "Entity not found", not_level_watch: "Not a Level Watch entity",
    day: "day", days: "days", h: "h", min_u: "min", history: "History",
    entity: "Entity", title: "Title", mode: "Display", history_hours: "History (hours)", show_history: "Show history",
    mode_auto: "Automatic", mode_water: "Water level", mode_tank: "Tank",
    style: "Style", style_forecast: "Forecast", style_classic: "Classic (gauge / tank)",
    style_ring: "Ring", style_compact: "Compact", forecast_hours: "Forecast (hours)",
    now: "now", expected: "expected", today: "today", tomorrow: "tomorrow",
    until: "until", refilled: "Refilled", in_short: "in",
    edit_thresholds: "Edit thresholds", add_threshold: "Add threshold",
    save: "Save", cancel: "Cancel", saving: "Saving …", delete: "Delete",
    f_name: "Name", f_value: "Value", f_above: "rises to/above", f_below: "falls to/below",
    f_hysteresis: "Hysteresis", f_notify: "Send notification", f_targets: "Notify via",
    f_critical: "Critical (Companion app, sounds even when silent)", f_clear: "Send all-clear",
    f_repeat: "Repeat every (min, 0 = once)", f_message: "Custom message",
    f_message_hint: "Empty for the default text. Placeholders: {name} {threshold} {value} {level} {trend} {rate}",
    more: "Notification and more", no_thresholds: "No thresholds yet. Add the first one.",
    new_threshold: "New threshold", err_name: "Every threshold needs a name.",
    err_value: "Every threshold needs a value.", err_targets: "Choose at least one target for every threshold that notifies.",
    err_save: "Saving failed", no_targets: "No notify targets found.", preview: "Preview",
  },
};

const ICON = {
  pencil: "M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z",
  trash: "M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z",
  chevron: "M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z",
  plus: "M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z",
  close: "M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z",
  bell: "M21,19V20H3V19L5,17V11C5,7.9 7.03,5.17 10,4.29C10,4.19 10,4.1 10,4A2,2 0 0,1 12,2A2,2 0 0,1 14,4C14,4.1 14,4.19 14,4.29C16.97,5.17 19,7.9 19,11V17L21,19M14,21A2,2 0 0,1 12,23A2,2 0 0,1 10,21",
};

const icon = (name, cls = "") => `<svg class="mdi ${cls}" viewBox="0 0 24 24" aria-hidden="true"><path d="${ICON[name]}"/></svg>`;

const toHex = (rgb) => `#${(rgb || [245, 124, 0]).map((v) => Number(v).toString(16).padStart(2, "0")).join("")}`;
const toRgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));

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
    // The card body is rebuilt on every update; the editor dialog lives beside
    // it so a new sensor value does not close or reset it.
    this.shadowRoot.innerHTML = `${STYLE}${EDITOR_STYLE}<div id="card"></div><dialog id="editor"></dialog>`;
    this._cardEl = this.shadowRoot.getElementById("card");
    this._dialog = this.shadowRoot.getElementById("editor");
    this._editor = null;
    this._bindEditor();
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
          name: "style",
          selector: { select: { mode: "dropdown", options: STYLES.map((v) => ({ value: v, label: t[`style_${v}`] })) } },
        },
        {
          name: "mode",
          selector: { select: { mode: "dropdown", options: ["auto", "water", "tank"].map((v) => ({ value: v, label: t[`mode_${v}`] })) } },
        },
        { name: "show_history", selector: { boolean: {} } },
        { name: "history_hours", selector: { number: { min: 1, max: 168, mode: "box" } } },
        { name: "forecast_hours", selector: { number: { min: 1, max: 168, mode: "box" } } },
      ],
      computeLabel: (schema) => t[schema.name] || schema.name,
    };
  }

  setConfig(config) {
    if (!config || !config.entity) throw new Error("entity is required");
    this._config = {
      style: "forecast", mode: "auto", show_history: true, history_hours: 24, forecast_hours: 12, ...config,
    };
    if (!STYLES.includes(this._config.style)) this._config.style = "forecast";
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
    const style = this._config?.style || "forecast";
    if (style === "compact") return 2;
    if (style === "ring") return 3;
    return this._historyHours() || style === "forecast" ? 6 : 4;
  }

  getGridOptions() {
    const style = this._config?.style || "forecast";
    // "auto" lets the dashboard size the card to its content, so nothing
    // spills into the card below whatever the style shows.
    if (style === "compact") return { columns: 6, rows: "auto", min_columns: 3, min_rows: 2 };
    if (style === "ring") return { columns: 12, rows: "auto", min_columns: 6, min_rows: 3 };
    if (style === "forecast") return { columns: 12, rows: "auto", min_columns: 6, min_rows: 4 };
    return { columns: 12, rows: "auto", min_columns: 6, min_rows: 3 };
  }

  // -- data ---------------------------------------------------------------------

  /** Hours of history to show; 0 when switched off (also the old "0 = off"). */
  _historyHours() {
    const c = this._config || {};
    if (c.show_history === false) return 0;
    const hours = Number(c.history_hours ?? 24);
    return Number.isFinite(hours) && hours > 0 ? hours : 0;
  }

  async _fetchHistory(entityId) {
    const hours = this._historyHours();
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
      this._cardEl.innerHTML = `<ha-card><div class="warn">${esc(msg)}: ${esc(this._config.entity)}</div></ha-card>`;
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

    const c = { a, level, hasLevel, mode, color, title, fmt, t, quality, qualityNote,
      dim: quality === "ok" ? "" : "dim" };
    const style = this._config.style;
    const content = style === "classic" ? this._classic(c)
      : style === "ring" ? this._ring(c)
        : style === "compact" ? this._compact(c)
          : this._forecast(c);
    this._entityId = entityId;
    this._lastCtx = c;
    this._cardEl.innerHTML = `
      <ha-card class="${style}" style="--lw-color:${esc(color)}">${content}</ha-card>`;
    this._cardEl.querySelector("ha-card").addEventListener("click", (event) => {
      if (event.target.closest(".edit")) {
        event.stopPropagation();
        this._openEditor();
        return;
      }
      const ev = new Event("hass-more-info", { bubbles: true, composed: true });
      ev.detail = { entityId };
      this.dispatchEvent(ev);
    });
  }

  _head(c) {
    const edit = this._hass?.user?.is_admin
      ? `<button class="edit" title="${esc(c.t.edit_thresholds)}" aria-label="${esc(c.t.edit_thresholds)}">${icon("pencil")}</button>`
      : "";
    return `<div class="head"><div class="title">${esc(c.title)}</div><div class="headright">${this._stageChip(c.a, c.t)}${edit}</div></div>`;
  }

  // -- threshold editor -----------------------------------------------------------

  async _openEditor() {
    const t = TEXT[lang(this._hass)];
    try {
      const res = await this._hass.callWS({ type: "level_watch/thresholds", entity_id: this._entityId });
      this._editor = {
        draft: res.thresholds.map((th) => ({ ...th, color: toHex(th.color) })),
        targets: res.targets || {},
        open: new Set(),
        error: "",
        saving: false,
      };
    } catch (err) {
      this._editor = { draft: [], targets: {}, open: new Set(), error: `${t.err_save}: ${err.message || err}`, saving: false };
    }
    this._renderEditor();
    if (!this._dialog.open) this._dialog.showModal();
  }

  _closeEditor() {
    this._dialog.close();
    this._editor = null;
  }

  _bindEditor() {
    const dlg = this._dialog;
    dlg.addEventListener("click", (ev) => {
      if (ev.target === dlg) { this._closeEditor(); return; }
      const btn = ev.target.closest("[data-act]");
      if (!btn || !this._editor) return;
      const idx = Number(btn.dataset.idx);
      const ed = this._editor;
      const t = TEXT[lang(this._hass)];
      switch (btn.dataset.act) {
        case "close": this._closeEditor(); return;
        case "add": {
          const level = this._lastCtx?.hasLevel ? Math.round(this._lastCtx.level) : 0;
          ed.draft.push({ name: t.new_threshold, value: level, direction: "above", hysteresis: 2,
            color: "#f57c00", notify: false, targets: [], critical: false, message: "", clear_message: true, repeat: 0 });
          ed.open.add(ed.draft.length - 1);
          break;
        }
        case "delete": {
          ed.draft.splice(idx, 1);
          ed.open = new Set([...ed.open].filter((i) => i !== idx).map((i) => (i > idx ? i - 1 : i)));
          break;
        }
        case "toggle": if (ed.open.has(idx)) ed.open.delete(idx); else ed.open.add(idx); break;
        case "dir": ed.draft[idx].direction = btn.dataset.dir; break;
        case "save": this._saveEditor(); return;
        default: return;
      }
      this._renderEditor();
    });
    dlg.addEventListener("input", (ev) => this._editorInput(ev, false));
    dlg.addEventListener("change", (ev) => this._editorInput(ev, true));
    dlg.addEventListener("cancel", () => { this._editor = null; });
  }

  _editorInput(ev, structural) {
    const el = ev.target;
    const field = el.dataset?.field;
    if (!field || !this._editor) return;
    const th = this._editor.draft[Number(el.dataset.idx)];
    if (!th) return;
    if (field === "target") {
      const set = new Set(th.targets);
      if (el.checked) set.add(el.value); else set.delete(el.value);
      th.targets = [...set];
    } else if (el.type === "checkbox") {
      th[field] = el.checked;
    } else if (el.type === "number") {
      th[field] = el.value === "" ? null : Number(el.value);
    } else {
      th[field] = el.value;
    }
    this._editor.error = "";
    // Re-render only for switches; typing keeps focus and just refreshes the preview.
    if (structural && el.type === "checkbox" && field === "notify") this._renderEditor();
    else this._renderPreview();
  }

  _draftThresholds() {
    return (this._editor?.draft || [])
      .filter((th) => Number.isFinite(th.value))
      .map((th) => ({ name: th.name, value: th.value, direction: th.direction, color: th.color, active: false }));
  }

  _renderPreview() {
    const box = this._dialog.querySelector(".pv");
    if (!box || !this._lastCtx) return;
    const c = { ...this._lastCtx, a: { ...this._lastCtx.a, thresholds: this._draftThresholds() } };
    box.innerHTML = this._zoneBar(c);
  }

  _renderEditor() {
    const ed = this._editor;
    if (!ed) return;
    const t = TEXT[lang(this._hass)];
    const targetEntries = Object.entries(ed.targets);
    const u = unitOf(this._lastCtx?.a);
    const rows = ed.draft.map((th, i) => {
      const open = ed.open.has(i);
      const targets = targetEntries.length
        ? targetEntries.map(([id, label]) => `<label class="chk"><input type="checkbox" data-field="target" data-idx="${i}" value="${esc(id)}" ${th.targets.includes(id) ? "checked" : ""}><span>${esc(label)}</span></label>`).join("")
        : `<div class="hint">${esc(t.no_targets)}</div>`;
      const details = open ? `
        <div class="details">
          <label class="fld"><span>${t.f_hysteresis}</span><span class="num"><input type="number" step="0.5" min="0" data-field="hysteresis" data-idx="${i}" value="${esc(th.hysteresis)}"><em>${esc(u)}</em></span></label>
          <label class="sw"><input type="checkbox" data-field="notify" data-idx="${i}" ${th.notify ? "checked" : ""}><span class="track"></span><span>${t.f_notify}</span></label>
          ${th.notify ? `
            <div class="fld"><span>${t.f_targets}</span><div class="targets">${targets}</div></div>
            <label class="sw"><input type="checkbox" data-field="critical" data-idx="${i}" ${th.critical ? "checked" : ""}><span class="track"></span><span>${t.f_critical}</span></label>
            <label class="sw"><input type="checkbox" data-field="clear_message" data-idx="${i}" ${th.clear_message ? "checked" : ""}><span class="track"></span><span>${t.f_clear}</span></label>
            <label class="fld"><span>${t.f_repeat}</span><span class="num"><input type="number" step="1" min="0" data-field="repeat" data-idx="${i}" value="${esc(th.repeat)}"><em>min</em></span></label>
            <label class="fld"><span>${t.f_message}</span><textarea rows="2" data-field="message" data-idx="${i}">${esc(th.message)}</textarea><small>${esc(t.f_message_hint)}</small></label>
          ` : ""}
        </div>` : "";
      return `
        <div class="row ${open ? "open" : ""}" style="--th:${esc(th.color)}">
          <div class="main">
            <input class="swatch" type="color" data-field="color" data-idx="${i}" value="${esc(th.color)}" aria-label="Farbe">
            <input class="name" type="text" data-field="name" data-idx="${i}" value="${esc(th.name)}" aria-label="${t.f_name}">
            <div class="seg" role="group">
              <button data-act="dir" data-dir="above" data-idx="${i}" class="${th.direction === "above" ? "on" : ""}" title="${t.f_above}">≥</button>
              <button data-act="dir" data-dir="below" data-idx="${i}" class="${th.direction === "below" ? "on" : ""}" title="${t.f_below}">≤</button>
            </div>
            <span class="num val"><input type="number" step="0.5" data-field="value" data-idx="${i}" value="${esc(th.value ?? "")}" aria-label="${t.f_value}"><em>${esc(u)}</em></span>
            <button class="ib ${th.notify ? "bell" : "bell off"}" data-act="toggle" data-idx="${i}" title="${t.more}">${icon("bell")}</button>
            <button class="ib" data-act="toggle" data-idx="${i}" title="${t.more}">${icon("chevron", open ? "up" : "")}</button>
            <button class="ib del" data-act="delete" data-idx="${i}" title="${t.delete}">${icon("trash")}</button>
          </div>
          ${details}
        </div>`;
    }).join("");
    this._dialog.innerHTML = `
      <div class="dlg">
        <div class="dhead">
          <div><div class="dtitle">${t.edit_thresholds}</div><div class="dsub">${esc(this._lastCtx?.title || "")}</div></div>
          <button class="ib" data-act="close" aria-label="${t.cancel}">${icon("close")}</button>
        </div>
        <div class="pvlabel">${t.preview}</div>
        <div class="pv"></div>
        <div class="rows">${rows || `<div class="empty">${t.no_thresholds}</div>`}</div>
        <button class="add" data-act="add">${icon("plus")}<span>${t.add_threshold}</span></button>
        ${ed.error ? `<div class="err">${esc(ed.error)}</div>` : ""}
        <div class="dfoot">
          <button class="btn" data-act="close">${t.cancel}</button>
          <button class="btn primary" data-act="save" ${ed.saving ? "disabled" : ""}>${ed.saving ? t.saving : t.save}</button>
        </div>
      </div>`;
    this._renderPreview();
  }

  async _saveEditor() {
    const ed = this._editor;
    const t = TEXT[lang(this._hass)];
    if (ed.draft.some((th) => !String(th.name || "").trim())) ed.error = t.err_name;
    else if (ed.draft.some((th) => !Number.isFinite(th.value))) ed.error = t.err_value;
    else if (ed.draft.some((th) => th.notify && !th.targets.length)) ed.error = t.err_targets;
    if (ed.error) { this._renderEditor(); return; }
    ed.saving = true;
    this._renderEditor();
    try {
      await this._hass.callWS({
        type: "level_watch/thresholds/save",
        entity_id: this._entityId,
        thresholds: ed.draft.map((th) => ({
          ...th,
          name: String(th.name).trim(),
          color: toRgb(th.color),
          hysteresis: Number(th.hysteresis) || 0,
          repeat: Number(th.repeat) || 0,
        })),
      });
      this._closeEditor();
    } catch (err) {
      ed.saving = false;
      ed.error = `${t.err_save}: ${err.message || err.code || err}`;
      this._renderEditor();
    }
  }

  // -- style: classic -----------------------------------------------------------

  _classic(c) {
    const { a, level, hasLevel, mode, color, fmt, t } = c;
    const visual = mode === "tank" ? this._tankSvg(a, level, color) : this._waterSvg(a, level, color);
    const stats = mode === "tank"
      ? this._tankStats(a, level, hasLevel, fmt, t)
      : this._waterStats(a, level, hasLevel, fmt, t);
    return `${this._head(c)}
      <div class="body ${c.dim}">
        <div class="visual">${visual}</div>
        <div class="stats">${stats}</div>
      </div>
      ${c.qualityNote}
      ${this._sparkline(a, color)}`;
  }

  // -- style: forecast (zone bar + history with projection) ---------------------

  _range(c) {
    const { a, level, mode } = c;
    if (mode === "tank") {
      const top = Number.isFinite(a.top) && a.top > 0 ? a.top
        : Math.max(level || 0, ...(a.thresholds || []).map((x) => x.value), 1) * 1.1;
      return [Math.min(0, a.reference_min ?? 0), top];
    }
    if (Number.isFinite(a.reference_min) && Number.isFinite(a.reference_max)) {
      // Fixed references give clean ends; widen only if a value lies outside.
      const values = [level, ...(a.thresholds || []).map((x) => x.value)].filter(Number.isFinite);
      return [Math.min(a.reference_min, ...values), Math.max(a.reference_max, ...values)];
    }
    return this._waterRange(a, level);
  }

  _bigValue(c) {
    const { a, level, hasLevel, mode, fmt } = c;
    if (mode === "tank" && Number.isFinite(a.percent)) return `${fmt(a.percent, 0)}<span class="unit">%</span>`;
    return hasLevel ? `${fmt(level)}<span class="unit">${esc(unitOf(a))}</span>` : "–";
  }

  _forecast(c) {
    const { a, mode, fmt, t } = c;
    const rows = [];
    const next = a.next_threshold && Number.isFinite(a.hours_to_next)
      ? (a.thresholds || []).find((x) => x.name === a.next_threshold) : null;
    if (next) {
      rows.push(`<div class="line"><span class="dot" style="background:${esc(next.color)}"></span>${esc(next.name)} ${t.expected} <b>${esc(this._when(a.hours_to_next, t))}</b></div>`);
    }
    if (mode === "tank") {
      if (Number.isFinite(a.days_left)) {
        rows.push(`<div class="line">${t.left} <b>${esc(this._duration(a.days_left * 24, t, fmt))}</b> <span class="small">(${t.until} ${esc(this._date(a.days_left * 24))})</span></div>`);
      }
      const parts = [];
      if (Number.isFinite(a.volume)) parts.push(`${fmt(a.volume, 0)} L${Number.isFinite(a.capacity) ? ` ${t.of} ${fmt(a.capacity, 0)} L` : ""}`);
      if (Number.isFinite(a.consumption)) parts.push(`${fmt(a.consumption)} ${a.unit === "%" ? "%" : "L"} ${t.per_day}`);
      if (Number.isFinite(a.hours_to_full)) parts.push(`${t.full_in} ${this._duration(a.hours_to_full, t, fmt)}`);
      if (parts.length) rows.push(`<div class="small">${esc(parts.join(" · "))}</div>`);
    } else {
      const parts = [
        Number.isFinite(a.min_24h) ? `${t.min} ${fmt(a.min_24h)}` : "",
        Number.isFinite(a.max_24h) ? `${t.max} ${fmt(a.max_24h)}` : "",
        Number.isFinite(a.change_24h) ? `${t.change} ${a.change_24h > 0 ? "+" : ""}${fmt(a.change_24h)}` : "",
      ].filter(Boolean);
      if (parts.length) rows.push(`<div class="small">${esc(parts.join(" · "))} ${esc(unitOf(a))}</div>`);
    }
    return `${this._head(c)}
      <div class="fc ${c.dim}">
        <div class="valrow"><div class="big">${this._bigValue(c)}</div>${this._trendLine(a, fmt, t)}</div>
        ${this._zoneBar(c)}
        ${this._forecastChart(c)}
        ${rows.join("")}
      </div>
      ${c.qualityNote}`;
  }

  _zoneBar(c) {
    const { a, level, hasLevel, fmt } = c;
    const ths = a.thresholds || [];
    const [lo, hi] = this._range(c);
    const w = 300;
    const x = (v) => Math.max(0, Math.min(w, ((v - lo) / (hi - lo)) * w));
    const bounds = [lo, ...ths.map((th) => th.value).filter((v) => v > lo && v < hi), hi]
      .sort((p, q) => p - q);
    // Every zone keeps its full color (dimming turns colors muddy on dark
    // themes); the zone holding the level is drawn taller instead.
    let rects = "";
    let hereDone = false;
    for (let i = 0; i < bounds.length - 1; i += 1) {
      const mid = (bounds[i] + bounds[i + 1]) / 2;
      const stage = stageAt(ths, mid);
      const col = stage ? stage.color : NORMAL_ZONE;
      const tip = `${stage ? stage.name : c.t.normal} · ${fmt(bounds[i], 0)}–${fmt(bounds[i + 1], 0)} ${unitOf(c.a)}`;
      const here = hasLevel && !hereDone && level >= bounds[i] && level <= bounds[i + 1];
      if (here) hereDone = true;
      const x0 = x(bounds[i]) + (i ? 1 : 0);
      const x1 = x(bounds[i + 1]) - (i < bounds.length - 2 ? 1 : 0);
      const [y0, hgt] = here ? [12, 16] : [16, 8];
      // An invisible full-height strip makes the thin zones easy to hover.
      rects += `<g class="zone"><title>${esc(tip)}</title>`
        + `<rect x="${x0}" y="4" width="${Math.max(0, x1 - x0)}" height="32" fill="transparent"/>`
        + `<rect x="${x0}" y="${y0}" width="${Math.max(0, x1 - x0)}" height="${hgt}" rx="${here ? 4 : 3}" fill="${esc(col)}" class="zfill${here ? "" : " zoneoff"}"/></g>`;
    }
    let marker = "";
    if (hasLevel) {
      const lx = x(level);
      marker = `<line x1="${lx}" x2="${lx}" y1="9" y2="31" class="mark"/><polygon points="${lx - 5},3 ${lx + 5},3 ${lx},9" class="markfill"/>`;
      if (Number.isFinite(a.rate) && (a.trend === "rising" || a.trend === "falling")) {
        const fh = Number(this._config.forecast_hours) || 12;
        const target = level + a.rate * Math.min(fh, Number.isFinite(a.hours_to_next) ? a.hours_to_next : fh);
        const tx = x(target);
        if (Math.abs(tx - lx) > 4) {
          marker += `<line x1="${lx}" x2="${tx}" y1="20" y2="20" class="proj"/>`
            + `<circle cx="${tx}" cy="20" r="3" class="projdot"/>`;
        }
      }
    }
    let labels = "";
    let lastX = -100;
    for (const v of bounds) {
      const lx = x(v);
      if (lx - lastX < 30 && v !== hi) continue;
      if (v === hi && lx - lastX < 30) continue;
      const anchor = lx < 10 ? "start" : lx > w - 10 ? "end" : "middle";
      labels += `<text x="${lx}" y="44" text-anchor="${anchor}" class="zl">${esc(fmt(v, 0))}</text>`;
      lastX = lx;
    }
    return `<svg class="zones" viewBox="0 0 ${w} 48" aria-hidden="true">
      ${rects}${marker}${labels}</svg>`;
  }

  _forecastChart(c) {
    const { a, level, hasLevel, color, t } = c;
    const hist = this._historyHours();
    const fh = Number(this._config.forecast_hours) || 12;
    const pts = hist ? this._history || [] : [];
    const now = Date.now();
    const t0 = now - (hist || 6) * 3600e3;
    const t1 = now + fh * 3600e3;
    let proj = null;
    if (hasLevel && Number.isFinite(a.rate) && (a.trend === "rising" || a.trend === "falling")) {
      const reach = Number.isFinite(a.hours_to_next) && a.hours_to_next <= fh;
      const h = reach ? a.hours_to_next : fh;
      proj = { h, v: level + a.rate * h, reach };
    }
    const values = pts.map((p) => p.v);
    if (hasLevel) values.push(level);
    if (proj) values.push(proj.v);
    if (!values.length) return "";
    let lo = Math.min(...values);
    let hi = Math.max(...values);
    if (hi - lo < 10) { const m = (hi + lo) / 2; lo = m - 5; hi = m + 5; }
    const span = hi - lo;
    const ths = a.thresholds || [];
    const next = ths.find((th) => th.name === a.next_threshold);
    for (const th of ths) {
      if (th === next || (th.value >= lo - span * 0.5 && th.value <= hi + span * 0.5)) {
        lo = Math.min(lo, th.value);
        hi = Math.max(hi, th.value);
      }
    }
    lo -= (hi - lo) * 0.08;
    hi += (hi - lo) * 0.08;
    const w = 300;
    const h = 110;
    const x = (ms) => ((ms - t0) / (t1 - t0)) * w;
    const y = (v) => h - 14 - ((v - lo) / (hi - lo)) * (h - 22);
    const nx = x(now);
    let d = "";
    pts.filter((p) => p.t >= t0).forEach((p, i) => {
      d += i ? ` H${x(p.t).toFixed(1)} V${y(p.v).toFixed(1)}` : `M${x(p.t).toFixed(1)} ${y(p.v).toFixed(1)}`;
    });
    if (hasLevel) d += d ? ` H${nx.toFixed(1)} V${y(level).toFixed(1)}` : `M${nx.toFixed(1)} ${y(level).toFixed(1)}`;
    const area = d ? `${d} V${h - 14} H${x(Math.max(t0, pts[0]?.t ?? now)).toFixed(1)} Z` : "";
    const lines = ths.filter((th) => th.value >= lo && th.value <= hi).map((th) => {
      const ty = y(th.value);
      return hoverLine(this._thrTip(th, a), 0, ty, w, ty,
        `<line x1="0" x2="${w}" y1="${ty}" y2="${ty}" stroke="${esc(th.color)}" class="thr ${th.active ? "on" : ""}"/>`
        + `<text x="3" y="${ty - 3}" class="zl" fill="${esc(th.color)}">${esc(th.name)}</text>`);
    }).join("");
    let projSvg = "";
    if (proj) {
      const px = x(now + proj.h * 3600e3);
      const py = y(proj.v);
      projSvg = `<line x1="${nx}" y1="${y(level)}" x2="${px}" y2="${py}" stroke="${esc(color)}" class="projline"/>`;
      if (proj.reach && next) {
        projSvg += `<circle cx="${px}" cy="${py}" r="4" fill="var(--card-background-color, #fff)" stroke="${esc(next.color)}" stroke-width="2"/>`;
      }
    }
    return `<svg class="chart" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true">
      ${area ? `<path d="${area}" fill="${esc(color)}" opacity="0.12"/>` : ""}
      ${lines}
      <line x1="${nx}" x2="${nx}" y1="4" y2="${h - 14}" class="nowline"/>
      ${d ? `<path d="${d}" fill="none" stroke="${esc(color)}" stroke-width="2" vector-effect="non-scaling-stroke"/>` : ""}
      ${projSvg}
      ${hasLevel ? `<circle cx="${nx}" cy="${y(level)}" r="3.5" fill="${esc(color)}"/>` : ""}
      <text x="0" y="${h - 2}" class="zl">−${hist || 6} h</text>
      <text x="${nx}" y="${h - 2}" class="zl" text-anchor="middle">${esc(t.now)}</text>
      <text x="${w}" y="${h - 2}" class="zl" text-anchor="end">+${fh} h</text>
    </svg>`;
  }

  _when(hours, t) {
    if (hours < 1) return `${t.in_short} ${Math.max(1, Math.round(hours * 60))} ${t.min_u}`;
    const at = new Date(Date.now() + hours * 3600e3);
    const loc = this._hass.locale?.language || "en";
    const time = at.toLocaleTimeString(loc, { hour: "2-digit", minute: "2-digit" });
    const today = new Date();
    const days = Math.round((new Date(at.toDateString()) - new Date(today.toDateString())) / 86400e3);
    if (days === 0) return `${t.today} ${time}`;
    if (days === 1) return `${t.tomorrow} ${time}`;
    return `${at.toLocaleDateString(loc, { weekday: "short", day: "numeric", month: "short" })} ${time}`;
  }

  _date(hours) {
    const at = new Date(Date.now() + hours * 3600e3);
    return at.toLocaleDateString(this._hass.locale?.language || "en", { day: "numeric", month: "short", year: hours > 24 * 300 ? "numeric" : undefined });
  }

  // -- style: ring ----------------------------------------------------------------

  _fraction(c, v) {
    const { a, mode } = c;
    if (mode === "tank" && a.shape === "horizontal_cylinder" && Number.isFinite(a.tank_diameter)) {
      const vol = (h) => segmentArea(a.tank_diameter, h);
      const bottom = vol(a.reference_min ?? 0);
      const full = vol(a.top) - bottom;
      return full > 0 ? clamp01((vol(v) - bottom) / full) : 0;
    }
    const [lo, hi] = mode === "tank"
      ? [a.reference_min ?? 0, this._range(c)[1]]
      : [a.reference_min ?? this._range(c)[0], a.reference_max ?? this._range(c)[1]];
    return clamp01((v - lo) / (hi - lo));
  }

  _ring(c) {
    const { a, level, hasLevel, mode, color, fmt, t } = c;
    const frac = mode === "tank" && Number.isFinite(a.percent) ? a.percent / 100
      : hasLevel ? this._fraction(c, level) : 0;
    const r = 48;
    const len = 2 * Math.PI * r;
    const ticks = (a.thresholds || []).map((th) => {
      const ang = this._fraction(c, th.value) * 360;
      return `<g class="hov" transform="rotate(${ang} 60 60)"><title>${esc(this._thrTip(th, a))}</title>`
        + `<line x1="60" y1="0" x2="60" y2="24" class="hit"/>`
        + `<line x1="60" y1="4" x2="60" y2="20" stroke="${esc(th.color)}" stroke-width="2.5"/></g>`;
    }).join("");
    const center = mode === "tank" && Number.isFinite(a.percent)
      ? `${fmt(a.percent, 0)} %` : (hasLevel ? `${fmt(level, 0)}` : "–");
    const sub = mode === "tank" && Number.isFinite(a.volume) ? `${fmt(a.volume, 0)} L` : (hasLevel ? unitOf(a) : "");
    const lines = [this._trendLine(a, fmt, t)];
    if (Number.isFinite(a.days_left)) lines.push(`<div class="line">${t.left} <b>${esc(this._duration(a.days_left * 24, t, fmt))}</b></div>`);
    if (Number.isFinite(a.consumption)) lines.push(`<div class="small">${fmt(a.consumption)} ${a.unit === "%" ? "%" : "L"} ${t.per_day}</div>`);
    if (Number.isFinite(a.hours_to_full)) lines.push(`<div class="line">${t.full_in} <b>${esc(this._duration(a.hours_to_full, t, fmt))}</b></div>`);
    lines.push(this._nextLine(a, t, fmt));
    if (a.last_refill) {
      lines.push(`<div class="small">${t.refilled} ${esc(new Date(a.last_refill).toLocaleDateString(this._hass.locale?.language || "en", { day: "numeric", month: "short" }))}</div>`);
    }
    return `${this._head(c)}
      <div class="body ${c.dim}">
        <svg class="ringsvg" viewBox="0 0 120 120" aria-hidden="true">
          <circle cx="60" cy="60" r="${r}" class="ringbg"/>
          ${frac > 0.005 ? `<circle cx="60" cy="60" r="${r}" fill="none" stroke="${esc(color)}" stroke-width="12" stroke-linecap="round"
            stroke-dasharray="${(len * frac).toFixed(1)} ${len.toFixed(1)}" transform="rotate(-90 60 60)"/>` : ""}
          ${ticks}
          <text x="60" y="62" text-anchor="middle" class="ringval">${esc(center)}</text>
          <text x="60" y="80" text-anchor="middle" class="zl">${esc(sub)}</text>
        </svg>
        <div class="stats">${lines.join("")}</div>
      </div>
      ${c.qualityNote}`;
  }

  // -- style: compact ---------------------------------------------------------------

  _compact(c) {
    const { a, level, hasLevel, mode, color, fmt, t } = c;
    const frac = mode === "tank" && Number.isFinite(a.percent) ? a.percent / 100
      : hasLevel ? this._fraction(c, level) : 0;
    const stage = a.stage
      ? `<div class="cstage" style="color:${esc(a.color)}">${esc(a.stage)}</div>`
      : `<div class="cstage">${esc(t.normal)}</div>`;
    let hint = "";
    if (a.next_threshold && Number.isFinite(a.hours_to_next)) {
      hint = `${a.next_threshold} ${t.in_short} ${this._duration(a.hours_to_next, t, fmt)}`;
    } else if (Number.isFinite(a.days_left)) {
      hint = this._duration(a.days_left * 24, t, fmt);
    } else if (Number.isFinite(a.hours_to_full)) {
      hint = `${t.full_in} ${this._duration(a.hours_to_full, t, fmt)}`;
    }
    const icon = TREND_ICON[a.trend]
      ? `<svg class="ticon ${a.trend}" viewBox="0 0 24 24"><path d="${TREND_ICON[a.trend]}"/></svg>` : "";
    return `<div class="cbox ${c.dim}">
        <div class="cbar"><div style="height:${(frac * 100).toFixed(1)}%;background:${esc(color)}"></div></div>
        <div class="cinfo">
          <div class="ctitle">${esc(c.title)}</div>
          <div class="cval">${this._bigValue(c)}</div>
          ${stage}
          ${hint || icon ? `<div class="chint">${icon}<span>${esc(hint)}</span></div>` : ""}
        </div>
      </div>`;
  }

  /** Tooltip text of a threshold line, e.g. "Meldestufe 2 · ≥ 350 cm (erreicht)". */
  _thrTip(th, a) {
    const t = TEXT[lang(this._hass)];
    const fmt = new Intl.NumberFormat(this._hass?.locale?.language || "en", { maximumFractionDigits: 1 });
    const sign = th.direction === "below" ? "≤" : "≥";
    return `${th.name} · ${sign} ${fmt.format(th.value)} ${unitOf(a)}${th.active ? ` (${t.reached})` : ""}`;
  }

  _levelTip(a, level) {
    const t = TEXT[lang(this._hass)];
    if (!Number.isFinite(level)) return t.level_now;
    const fmt = new Intl.NumberFormat(this._hass?.locale?.language || "en", { maximumFractionDigits: 1 });
    return `${t.level_now} ${fmt.format(level)} ${unitOf(a)}`;
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
      rate = ` · ${sign}${Math.abs(a.rate) < 0.05 ? "0" : shown} ${unitOf(a)}/h`;
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
    const big = hasLevel ? `${fmt(level)}<span class="unit">${esc(unitOf(a))}</span>` : "–";
    const extremes = [
      Number.isFinite(a.min_24h) ? `${t.min} ${fmt(a.min_24h)}` : "",
      Number.isFinite(a.max_24h) ? `${t.max} ${fmt(a.max_24h)}` : "",
      Number.isFinite(a.change_24h) ? `${t.change} ${a.change_24h > 0 ? "+" : ""}${fmt(a.change_24h)}` : "",
    ].filter(Boolean).join(" · ");
    return `
      <div class="big">${big}</div>
      ${this._trendLine(a, fmt, t)}
      ${this._nextLine(a, t, fmt)}
      ${extremes ? `<div class="small">${esc(extremes)} ${esc(unitOf(a))}</div>` : ""}`;
  }

  _tankStats(a, level, hasLevel, fmt, t) {
    const pct = Number.isFinite(a.percent) ? a.percent : null;
    const big = pct !== null
      ? `${fmt(pct, 0)}<span class="unit">%</span>`
      : (hasLevel ? `${fmt(level)}<span class="unit">${esc(unitOf(a))}</span>` : "–");
    const lines = [];
    if (Number.isFinite(a.volume)) {
      const cap = Number.isFinite(a.capacity) ? ` ${t.of} ${fmt(a.capacity, 0)} L` : "";
      lines.push(`<div class="line"><b>${fmt(a.volume, 0)} L</b>${cap}</div>`);
    } else if (pct !== null && hasLevel) {
      lines.push(`<div class="line">${fmt(level)} ${esc(unitOf(a))}</div>`);
    }
    if (Number.isFinite(a.days_left)) {
      lines.push(`<div class="line">${t.left} <b>${esc(this._duration(a.days_left * 24, t, fmt))}</b></div>`);
    }
    if (Number.isFinite(a.consumption)) {
      lines.push(`<div class="small">${fmt(a.consumption)} ${a.unit === "%" ? "%" : "L"} ${t.per_day}</div>`);
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
      return hoverLine(this._thrTip(th, a), 8, ty, 158, ty,
        `<line x1="8" x2="152" y1="${ty}" y2="${ty}" stroke="${esc(th.color)}" class="thr ${th.active ? "on" : ""}"/>`
        + `<polygon points="152,${ty} 158,${ty - 4} 158,${ty + 4}" fill="${esc(th.color)}"/>`);
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
        ${hoverLine(this._levelTip(a, level), 4, ly, 152, ly, `<line x1="4" x2="152" y1="${ly}" y2="${ly}" class="surface"/>`)}
      </svg>`;
  }

  // -- tank ---------------------------------------------------------------------

  _tankSvg(a, level, color) {
    const topH = Number.isFinite(a.top) && a.top > 0 ? a.top
      : Math.max(level || 0, ...(a.thresholds || []).map((x) => x.value), 1) * 1.1;
    // A tank in % reports its content; in a horizontal cylinder that is not
    // the fill height, so draw at the height that holds that share.
    const byVolume = unitOf(a) === "%" && a.shape === "horizontal_cylinder";
    const frac = (v) => {
      const f = clamp01(v / topH);
      return byVolume ? heightForVolume(f) : f;
    };
    let outline;
    let box;
    if (a.shape === "horizontal_cylinder") {
      box = { x: 44, y: 40, w: 140, h: 140 };
      outline = `<circle cx="114" cy="110" r="70"/>`;
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
      return hoverLine(this._thrTip(th, a), box.x - 2, ty, box.x + box.w + 8, ty,
        `<line x1="${box.x - 2}" x2="${box.x + box.w + 8}" y1="${ty}" y2="${ty}" stroke="${esc(th.color)}" class="thr ${th.active ? "on" : ""}"/>`);
    }).join("");
    // Scale beside the tank, in the unit of the level (cm or %).
    const step = niceStep(topH / 5);
    let scale = `<line x1="${box.x - 6}" x2="${box.x - 6}" y1="${box.y}" y2="${box.y + box.h}" class="tick minor"/>`;
    for (let v = 0; v <= topH + step * 0.01; v += step) {
      const ty = y(v);
      scale += `<line x1="${box.x - 10}" x2="${box.x - 6}" y1="${ty}" y2="${ty}" class="tick"/>`
        + `<text x="${box.x - 13}" y="${ty + 3}" text-anchor="end" class="tlabel">${Math.round(v)}</text>`;
      const half = y(v + step / 2);
      if (v + step / 2 <= topH) scale += `<line x1="${box.x - 8}" x2="${box.x - 6}" y1="${half}" y2="${half}" class="tick minor"/>`;
    }
    scale += `<text x="${box.x - 13}" y="${box.y - 8}" text-anchor="end" class="tlabel">${esc(unitOf(a))}</text>`;
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
        ${scale}
        ${lines}
        <g class="rim">${outline}</g>
      </svg>`;
  }

  // -- history ------------------------------------------------------------------

  _sparkline(a, color) {
    if (!this._historyHours()) return "";
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
      .map((th) => hoverLine(this._thrTip(th, a), 0, y(th.value), w, y(th.value),
        `<line x1="0" x2="${w}" y1="${y(th.value)}" y2="${y(th.value)}" stroke="${esc(th.color)}" class="thr"/>`))
      .join("");
    return `
      <svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true">
        <path d="${area}" fill="${esc(color)}" opacity="0.15"/>
        ${lines}
        <path d="${d}" fill="none" stroke="${esc(color)}" stroke-width="2" vector-effect="non-scaling-stroke"/>
      </svg>`;
  }
}

const NORMAL_ZONE = "#26a69a";

const EDITOR_STYLE = `<style>
  .headright { display: flex; align-items: center; gap: 4px; flex: none; }
  .edit { border: none; background: none; padding: 4px; margin: -4px -6px -4px 0; border-radius: 50%;
    color: var(--secondary-text-color); cursor: pointer; display: flex; }
  .edit:hover { background: color-mix(in srgb, var(--primary-text-color) 8%, transparent); }
  .mdi { width: 20px; height: 20px; fill: currentColor; display: block; }
  dialog { border: none; padding: 0; border-radius: 20px; width: min(600px, calc(100vw - 24px));
    max-height: calc(100vh - 48px); background: var(--card-background-color, #fff); color: var(--primary-text-color);
    box-shadow: 0 12px 40px rgba(0,0,0,.3); font-family: var(--paper-font-body1_-_font-family, inherit); }
  dialog::backdrop { background: rgba(0,0,0,.45); }
  .dlg { padding: 20px; display: flex; flex-direction: column; gap: 12px; }
  .dhead { display: flex; justify-content: space-between; align-items: flex-start; }
  .dtitle { font-size: 1.25em; font-weight: 500; }
  .dsub { color: var(--secondary-text-color); font-size: 0.9em; }
  .pvlabel { font-size: 0.75em; text-transform: uppercase; letter-spacing: .06em; color: var(--secondary-text-color); margin-bottom: -6px; }
  .pv { padding: 2px 4px; }
  .rows { display: flex; flex-direction: column; gap: 8px; }
  .row { border: 1px solid var(--divider-color, #e0e0e0); border-left: 4px solid var(--th); border-radius: 12px;
    padding: 8px 8px 8px 10px; background: color-mix(in srgb, var(--th) 5%, transparent); }
  .main { display: flex; align-items: center; gap: 6px; }
  .swatch { width: 28px; height: 28px; padding: 0; border: none; border-radius: 50%; background: none; cursor: pointer; flex: none; }
  .swatch::-webkit-color-swatch-wrapper { padding: 0; }
  .swatch::-webkit-color-swatch { border: 2px solid var(--card-background-color, #fff); border-radius: 50%;
    box-shadow: 0 0 0 1px var(--divider-color, #ccc); }
  .swatch::-moz-color-swatch { border: none; border-radius: 50%; }
  .dlg input[type=text], .dlg input[type=number], .dlg textarea { font: inherit; color: inherit; background: transparent;
    border: 1px solid var(--divider-color, #ccc); border-radius: 8px; padding: 6px 8px; min-width: 0; box-sizing: border-box; }
  .dlg input:focus, .dlg textarea:focus { outline: 2px solid var(--primary-color, #03a9f4); outline-offset: -1px; border-color: transparent; }
  .name { flex: 1; }
  .num { display: inline-flex; align-items: center; gap: 4px; }
  .num input { width: 80px; text-align: right; }
  .num em { font-style: normal; color: var(--secondary-text-color); font-size: 0.85em; }
  .seg { display: inline-flex; border: 1px solid var(--divider-color, #ccc); border-radius: 8px; overflow: hidden; flex: none; }
  .seg button { border: none; background: none; color: var(--secondary-text-color); padding: 5px 9px; cursor: pointer; font: inherit; }
  .seg button.on { background: var(--th); color: #fff; }
  .ib { border: none; background: none; color: var(--secondary-text-color); padding: 5px; border-radius: 50%; cursor: pointer; display: flex; flex: none; }
  .ib:hover { background: color-mix(in srgb, var(--primary-text-color) 8%, transparent); }
  .ib.bell { color: var(--th); }
  .ib.bell.off { opacity: .35; }
  .ib.del:hover { color: var(--error-color, #db4437); }
  .mdi.up { transform: rotate(180deg); }
  .details { display: flex; flex-direction: column; gap: 10px; padding: 10px 4px 4px 34px; }
  .fld { display: flex; flex-direction: column; gap: 4px; font-size: 0.9em; }
  .fld > span:first-child { color: var(--secondary-text-color); }
  .fld small, .hint { color: var(--secondary-text-color); font-size: 0.8em; }
  .targets { display: flex; flex-wrap: wrap; gap: 6px; }
  .chk { display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--divider-color, #ccc);
    border-radius: 16px; padding: 4px 10px 4px 6px; cursor: pointer; font-size: 0.9em; }
  .chk:has(input:checked) { border-color: var(--th); background: color-mix(in srgb, var(--th) 12%, transparent); }
  .sw { display: flex; align-items: center; gap: 10px; cursor: pointer; font-size: 0.9em; }
  .sw input { position: absolute; opacity: 0; pointer-events: none; }
  .track { width: 34px; height: 20px; border-radius: 10px; background: var(--divider-color, #ccc); position: relative; flex: none; transition: background .2s; }
  .track::after { content: ""; position: absolute; top: 2px; left: 2px; width: 16px; height: 16px; border-radius: 50%; background: #fff; transition: transform .2s; box-shadow: 0 1px 2px rgba(0,0,0,.3); }
  .sw input:checked + .track { background: var(--th); }
  .sw input:checked + .track::after { transform: translateX(14px); }
  .sw input:focus-visible + .track { outline: 2px solid var(--primary-color, #03a9f4); outline-offset: 2px; }
  .add { display: flex; align-items: center; justify-content: center; gap: 6px; border: 1px dashed var(--divider-color, #bbb);
    border-radius: 12px; background: none; color: var(--primary-color, #03a9f4); padding: 10px; cursor: pointer; font: inherit; }
  .add:hover { background: color-mix(in srgb, var(--primary-color, #03a9f4) 6%, transparent); }
  .empty { color: var(--secondary-text-color); text-align: center; padding: 12px; }
  .err { color: var(--error-color, #db4437); font-size: 0.9em; }
  .dfoot { display: flex; justify-content: flex-end; gap: 8px; padding-top: 4px; }
  .btn { font: inherit; font-weight: 500; border-radius: 18px; padding: 8px 18px; cursor: pointer; border: 1px solid var(--divider-color, #ccc);
    background: none; color: var(--primary-color, #03a9f4); }
  .btn.primary { background: var(--primary-color, #03a9f4); color: var(--text-primary-color, #fff); border-color: transparent; }
  .btn[disabled] { opacity: .6; cursor: default; }
  @media (max-width: 480px) {
    .main { flex-wrap: wrap; }
    .name { flex-basis: calc(100% - 40px); }
    .details { padding-left: 4px; }
  }
</style>`;

/** A line with a tooltip and a wider invisible strip that is easy to hover. */
function hoverLine(tip, x1, y1, x2, y2, visible) {
  return `<g class="hov"><title>${esc(tip)}</title>`
    + `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="hit"/>${visible}</g>`;
}

function unitOf(a) {
  return (a && a.unit) || "cm";
}

function clamp01(v) {
  return Math.max(0, Math.min(1, Number.isFinite(v) ? v : 0));
}

/** Filled cross-section of a horizontal cylinder of diameter d up to height h. */
function segmentArea(d, h) {
  const r = d / 2;
  const hh = Math.max(0, Math.min(d, h));
  return r * r * Math.acos((r - hh) / r) - (r - hh) * Math.sqrt(Math.max(0, 2 * r * hh - hh * hh));
}

/** The stage that would be active at value v (hysteresis ignored), or null. */
function stageAt(ths, v) {
  const above = ths.filter((x) => x.direction === "above" && v >= x.value);
  if (above.length) return above.reduce((m, x) => (x.value > m.value ? x : m));
  const below = ths.filter((x) => x.direction === "below" && v <= x.value);
  if (below.length) return below.reduce((m, x) => (x.value < m.value ? x : m));
  return null;
}

/** Fill height (0-1) of a horizontal cylinder that holds the share f (0-1). */
function heightForVolume(f) {
  const full = Math.PI / 4; // cross-section of diameter 1
  let lo = 0;
  let hi = 1;
  for (let i = 0; i < 30; i += 1) {
    const mid = (lo + hi) / 2;
    if (segmentArea(1, mid) / full < f) lo = mid; else hi = mid;
  }
  return (lo + hi) / 2;
}

/** Color of the stage that would be active at value v (hysteresis ignored). */
function stageColorAt(ths, v, normal) {
  const above = ths.filter((x) => x.direction === "above" && v >= x.value);
  if (above.length) return above.reduce((m, x) => (x.value > m.value ? x : m)).color;
  const below = ths.filter((x) => x.direction === "below" && v <= x.value);
  if (below.length) return below.reduce((m, x) => (x.value < m.value ? x : m)).color;
  return normal;
}

function niceStep(raw) {
  const pow = 10 ** Math.floor(Math.log10(Math.max(raw, 1e-6)));
  const n = raw / pow;
  return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10) * pow;
}

/**
 * Water body from `surface` down to `bottom`: a taller, slower swell behind,
 * a quicker wave in front with a light crest, both drifting in opposite
 * directions. Each drifts by exactly one wavelength, so the loop is seamless.
 */
function waves(surface, x, width, bottom, fill) {
  const crest = (len, amp, lift) => {
    let d = `M${x - len * 2} ${surface - lift}`;
    for (let i = -2; i * len < width + len * 2; i += 1) {
      d += ` q${len / 4} ${-amp} ${len / 2} 0 t${len / 2} 0`;
    }
    return d;
  };
  const body = (len, amp, lift) => `${crest(len, amp, lift)} V${bottom} H${x - len * 2} Z`;
  return `
    <g class="bob"><path d="${body(70, 8.5, 2.5)}" fill="${fill}" class="wave b" style="--len:70px" opacity="0.5"/></g>
    <path d="${body(50, 6.5, 0)}" fill="${fill}" class="wave a" style="--len:50px"/>
    <path d="${crest(50, 6.5, 0)}" class="wave a crest" style="--len:50px"/>`;
}

const STYLE = `<style>
  :host { display: block; height: 100%; }
  #card { height: 100%; }
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
  .wave.a { animation: lw-drift 3.6s linear infinite; }
  .wave.b { animation: lw-drift 6s linear infinite reverse; }
  .wave.crest { fill: none; stroke: #fff; stroke-opacity: 0.4; stroke-width: 1.75; }
  .bob { animation: lw-bob 3.8s ease-in-out infinite; }
  @keyframes lw-drift { from { transform: translateX(0); } to { transform: translateX(var(--len, 40px)); } }
  @keyframes lw-bob { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(2.5px); } }
  @media (prefers-reduced-motion: reduce) { .wave.a, .wave.b, .bob { animation: none; } }
  .fc { display: flex; flex-direction: column; gap: 6px; }
  .fc.dim, .cbox.dim { opacity: 0.55; filter: grayscale(0.6); }
  .valrow { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
  .zones { width: 100%; height: auto; display: block; overflow: visible; }
  .zl { font-size: 9px; fill: var(--secondary-text-color); }
  .zoneoff { opacity: 0.85; }
  .zone { cursor: help; }
  .hov { cursor: help; }
  .hov .hit { stroke: transparent; stroke-width: 10; pointer-events: stroke; vector-effect: non-scaling-stroke; }
  .hov:hover .thr { opacity: 1; stroke-width: 2.5; }
  .zone .zfill { transition: opacity .15s, filter .15s; }
  .zone:hover .zfill { opacity: 1; filter: brightness(1.15); }
  .mark { stroke: var(--primary-text-color); stroke-width: 2; }
  .markfill { fill: var(--primary-text-color); }
  .proj { stroke: var(--primary-text-color); stroke-width: 1.5; stroke-dasharray: 3 2; }
  .projdot { fill: var(--card-background-color, #fff); stroke: var(--primary-text-color); stroke-width: 1.5; }
  .chart { width: 100%; height: 120px; display: block; }
  .projline { stroke-width: 2; stroke-dasharray: 5 4; vector-effect: non-scaling-stroke; }
  .nowline { stroke: var(--divider-color, #ccc); stroke-width: 1; vector-effect: non-scaling-stroke; }
  .ringsvg { flex: 0 0 120px; width: 120px; height: 120px; }
  .ringbg { fill: none; stroke: var(--divider-color, #e0e0e0); stroke-width: 12; }
  .ringval { font-size: 22px; font-weight: 500; fill: var(--primary-text-color); }
  ha-card.compact { padding: 12px; }
  .cbox { display: flex; gap: 12px; height: 100%; align-items: stretch; }
  .cbar { width: 10px; border-radius: 5px; background: var(--divider-color, #e0e0e0); position: relative;
    overflow: hidden; flex: none; }
  .cbar div { position: absolute; left: 0; right: 0; bottom: 0; transition: height 0.8s ease; }
  .cinfo { min-width: 0; display: flex; flex-direction: column; gap: 2px; }
  .ctitle { font-size: 0.9em; color: var(--secondary-text-color); white-space: nowrap; overflow: hidden;
    text-overflow: ellipsis; }
  .cval { font-size: 1.7em; font-weight: 500; line-height: 1.1; color: var(--primary-text-color); }
  .cstage { font-size: 0.85em; color: var(--secondary-text-color); }
  .chint { display: flex; align-items: center; gap: 4px; font-size: 0.85em; color: var(--secondary-text-color); }
  .chint .ticon { width: 16px; height: 16px; }
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
