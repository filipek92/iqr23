/**
 * Lovelace card for the iQ R23 heating controller, served by the iqr23 integration.
 *
 * Entities are looked up by their translation key on the selected device,
 * so renamed entity IDs keep working.
 */

const DOMAIN = "iqr23";
// Setpoint presses are collected and sent as one number.set_value after this pause.
const SEND_DELAY = 1200;

const TRANSLATIONS = {
  en: {
    subtitle: "Heating controller",
    outdoor: "Outdoor temperature",
    min: "min",
    max: "max",
    mean: "Ø",
    tank: "Storage tank",
    upper: "Upper",
    middle: "Middle",
    lower: "Lower",
    heating: "Heating",
    idle: "Idle",
    tank_base: "Base temperature",
    circuit_1: "Circuit 1",
    circuit_2: "Circuit 2",
    pump_running: "Pump running",
    pump_stopped: "Pump stopped",
    demand: "Demand",
    no_demand: "No demand",
    setback: "Setback",
    mixing: "Mixing",
    shift: "Curve shift",
    fireplace: "Fireplace",
    solar: "Solar",
    pool: "Pool",
    cooling: "Cooling",
    pump: "pump",
    range: "Range {min} to {max}",
    pending: "Sending shortly",
    sending: "Sending to controller…",
    failed: "Failed: {error}",
    decrease: "Decrease {name}",
    increase: "Increase {name}",
    safety_thermostat: "Safety thermostat",
    system_pressure: "System pressure",
    tank_upper_overcurrent: "Upper coil overcurrent",
    tank_lower_overcurrent: "Lower coil overcurrent",
    pool_error: "Pool error",
    alarm: "Fault reported",
    no_device: "No iQ R23 device found.",
    device: "Device",
    title: "Title",
    show_controls: "Setpoint -/+ buttons",
    card_description: "Tank, heating circuits and setpoints of the iQ R23 controller.",
  },
  cs: {
    subtitle: "Regulace vytápění",
    outdoor: "Venkovní teplota",
    min: "min",
    max: "max",
    mean: "Ø",
    tank: "Zásobník",
    upper: "Horní",
    middle: "Střed",
    lower: "Dolní",
    heating: "Ohřev",
    idle: "Neohřívá",
    tank_base: "Základní teplota",
    circuit_1: "Okruh 1",
    circuit_2: "Okruh 2",
    pump_running: "Čerpadlo běží",
    pump_stopped: "Čerpadlo stojí",
    demand: "Požadavek",
    no_demand: "Bez požadavku",
    setback: "Útlum",
    mixing: "Směšování",
    shift: "Posun křivky",
    fireplace: "Krb",
    solar: "Solár",
    pool: "Bazén",
    cooling: "Chlazení",
    pump: "čerp.",
    range: "Rozsah {min} až {max}",
    pending: "Odešle se po chvíli",
    sending: "Odesílám do regulátoru…",
    failed: "Chyba: {error}",
    decrease: "Snížit: {name}",
    increase: "Zvýšit: {name}",
    safety_thermostat: "Bezpečnostní termostat",
    system_pressure: "Tlak v systému",
    tank_upper_overcurrent: "Nadproud horní spirály",
    tank_lower_overcurrent: "Nadproud dolní spirály",
    pool_error: "Porucha bazénu",
    alarm: "Hlášena porucha",
    no_device: "Nenalezeno žádné zařízení iQ R23.",
    device: "Zařízení",
    title: "Nadpis",
    show_controls: "Tlačítka -/+ pro žádané hodnoty",
    card_description: "Zásobník, topné okruhy a žádané hodnoty regulátoru iQ R23.",
  },
};

const PROBLEMS = [
  "safety_thermostat",
  "system_pressure",
  "tank_upper_overcurrent",
  "tank_lower_overcurrent",
  "pool_error",
];

const ICONS = {
  thermometer: '<path d="M14 4v10.5a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0z"/>',
  alert:
    '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  flame:
    '<path d="M12 22c4 0 7-3 7-7 0-3-2-5.5-3.5-7-.4 2-1.5 3-2.5 3 .5-3-1-6.5-4-9 0 3-1.5 5-3 6.5S5 12 5 15c0 4 3 7 7 7z"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  waves:
    '<path d="M2 8c2 0 2-1.5 4-1.5S8 8 10 8s2-1.5 4-1.5S16 8 18 8s2-1.5 4-1.5"/><path d="M2 13c2 0 2-1.5 4-1.5S8 13 10 13s2-1.5 4-1.5 2 1.5 4 1.5 2-1.5 4-1.5"/><path d="M2 18c2 0 2-1.5 4-1.5S8 18 10 18s2-1.5 4-1.5 2 1.5 4 1.5 2-1.5 4-1.5"/>',
  snowflake: '<path d="M12 2v20M4.9 7l14.2 10M4.9 17 19.1 7"/><path d="m9 4 3 2 3-2M9 20l3-2 3 2"/>',
  minus: '<path d="M5 12h14"/>',
  plus: '<path d="M5 12h14"/><path d="M12 5v14"/>',
};

const icon = (name, size = 20) =>
  `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name]}</svg>`;

const escape = (value) =>
  String(value).replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]
  );

const STYLES = `
  :host { display: block; }
  ha-card { overflow: hidden; }
  section { padding: 12px 20px 16px; border-top: 1px solid var(--divider-color); }
  h2 { margin: 0; font-size: 20px; font-weight: 500; }
  h3 {
    margin: 0; font-size: 12px; font-weight: 500; letter-spacing: .06em;
    text-transform: uppercase; color: var(--secondary-text-color);
  }
  button { font: inherit; color: inherit; }
  .secondary { font-size: 13px; color: var(--secondary-text-color); }
  .small { font-size: 12px; color: var(--secondary-text-color); }
  .value { font-size: 22px; font-weight: 500; font-variant-numeric: tabular-nums; }
  .target { font-size: 13px; font-weight: 400; color: var(--secondary-text-color); }
  .linkish { background: none; border: 0; padding: 0; cursor: pointer; text-align: inherit; }
  .header {
    display: flex; align-items: flex-start; justify-content: space-between;
    gap: 16px; padding: 20px 20px 16px;
  }
  .header-title { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
  .outdoor { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
  .outdoor-value { display: flex; align-items: center; gap: 6px; font-size: 24px; font-weight: 500; }
  .alarm {
    display: flex; align-items: center; gap: 12px; margin: 0 16px 12px; padding: 12px 14px;
    border-radius: 8px; color: var(--error-color);
    background: color-mix(in srgb, var(--error-color) 12%, transparent);
  }
  .alarm div { display: flex; flex-direction: column; gap: 2px; }
  .alarm strong { font-size: 14px; font-weight: 500; }
  .tank { display: flex; gap: 20px; align-items: stretch; margin-top: 12px; }
  .vessel {
    width: 64px; flex-shrink: 0; display: flex; flex-direction: column; min-height: 168px;
    border-radius: 22px; overflow: hidden; border: 2px solid var(--divider-color);
  }
  .vessel div { flex: 1; }
  .zones { flex: 1; display: flex; flex-direction: column; justify-content: space-between; gap: 12px; min-width: 0; }
  .zone { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
  .zone .linkish { display: flex; flex-direction: column; gap: 2px; }
  .chip {
    display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px;
    font-size: 12px; font-weight: 500; white-space: nowrap;
    background: var(--secondary-background-color); color: var(--secondary-text-color);
  }
  .chip.heat {
    color: var(--state-climate-heat-color, #ff8100);
    background: color-mix(in srgb, var(--state-climate-heat-color, #ff8100) 14%, transparent);
  }
  .chip.on {
    color: var(--primary-color);
    background: color-mix(in srgb, var(--primary-color) 14%, transparent);
  }
  .dot { width: 6px; height: 6px; border-radius: 50%; box-sizing: border-box; border: 1px solid currentColor; }
  .chip.on .dot { background: currentColor; }
  .circuit-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0 12px; }
  .mixing { display: flex; align-items: center; gap: 12px; }
  .mixing .secondary { width: 84px; flex-shrink: 0; }
  .bar { flex: 1; height: 6px; border-radius: 3px; background: var(--secondary-background-color); overflow: hidden; }
  .bar div { height: 100%; border-radius: 3px; background: var(--primary-color); }
  .mixing .pct { font-size: 13px; width: 44px; text-align: right; font-variant-numeric: tabular-nums; }
  .stepper {
    display: flex; align-items: center; justify-content: space-between; gap: 12px;
    margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--divider-color);
  }
  .stepper-label { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
  .stepper-label .name { font-size: 14px; }
  .stepper-label .small.active { color: var(--primary-color); }
  .stepper-label .small.error { color: var(--error-color); }
  .stepper-controls { display: flex; align-items: center; gap: 4px; }
  .round {
    width: 44px; height: 44px; border-radius: 50%; padding: 0; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    border: 1px solid var(--divider-color); background: none;
  }
  .round:disabled { opacity: .38; cursor: default; }
  .stepper-value {
    min-width: 76px; text-align: center; font-size: 20px; font-weight: 500;
    font-variant-numeric: tabular-nums;
  }
  .stepper-value.active { color: var(--primary-color); }
  .tiles {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(88px, 1fr)); gap: 8px;
    padding: 12px 16px 16px; border-top: 1px solid var(--divider-color);
  }
  .tile {
    display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 12px 4px;
    border-radius: 10px; border: 0; cursor: pointer; background: var(--secondary-background-color);
  }
  .tile .active { color: var(--state-climate-heat-color, #ff8100); }
  .tile-value { font-size: 15px; font-weight: 500; }
  .empty { padding: 16px 20px; }
`;

class IQR23Card extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    // entity_id -> { value, sending, error, timer }
    this._steps = {};
    this._html = "";
    this.shadowRoot.addEventListener("click", (ev) => this._onClick(ev));
  }

  static getConfigElement() {
    return document.createElement("iqr23-card-editor");
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    this._config = config || {};
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 12;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  disconnectedCallback() {
    Object.values(this._steps).forEach((step) => clearTimeout(step.timer));
  }

  _t(key, params = {}) {
    const lang = this._hass?.locale?.language || this._hass?.language || "en";
    const table = TRANSLATIONS[lang.split("-")[0]] || TRANSLATIONS.en;
    return (table[key] ?? TRANSLATIONS.en[key] ?? key).replace(/\{(\w+)\}/g, (_, k) => params[k] ?? "");
  }

  _deviceId() {
    if (this._config.device_id) return this._config.device_id;
    const entity = Object.values(this._hass.entities || {}).find(
      (e) => e.platform === DOMAIN && e.device_id
    );
    return entity?.device_id;
  }

  _entityMap(deviceId) {
    const map = {};
    for (const entity of Object.values(this._hass.entities || {})) {
      if (entity.platform === DOMAIN && entity.device_id === deviceId && entity.translation_key) {
        // Per-output entities share a translation key; the card does not use them.
        map[entity.translation_key] ??= entity.entity_id;
      }
    }
    return map;
  }

  _state(key) {
    const entityId = this._entities[key];
    const state = entityId && this._hass.states[entityId];
    return state && state.state !== "unavailable" && state.state !== "unknown" ? state : undefined;
  }

  _has(key) {
    return Boolean(this._entities[key] && this._hass.states[this._entities[key]]);
  }

  _isOn(key) {
    return this._state(key)?.state === "on";
  }

  _format(key) {
    const state = this._state(key);
    if (!state) return "—";
    return this._hass.formatEntityState ? this._hass.formatEntityState(state) : `${state.state} ${state.attributes.unit_of_measurement ?? ""}`;
  }

  _number(key) {
    const value = parseFloat(this._state(key)?.state);
    return Number.isNaN(value) ? undefined : value;
  }

  _formatNumber(value, unit, signed) {
    const lang = this._hass.locale?.language || this._hass.language;
    const text = new Intl.NumberFormat(lang, { signDisplay: signed ? "exceptZero" : "auto" }).format(value);
    return unit ? `${text} ${unit}` : text;
  }

  _tempColor(key) {
    const value = this._number(key);
    if (value === undefined) return "var(--disabled-color, #bdbdbd)";
    const cold = [74, 144, 217];
    const hot = [228, 87, 46];
    const k = Math.max(0, Math.min(1, (value - 20) / 50));
    return `rgb(${cold.map((c, i) => Math.round(c + (hot[i] - c) * k)).join(",")})`;
  }

  _moreInfo(key) {
    const entityId = this._entities[key];
    return entityId ? `data-more-info="${escape(entityId)}"` : "";
  }

  _onClick(ev) {
    const target = ev.composedPath().find((el) => el.dataset && (el.dataset.moreInfo || el.dataset.step));
    if (!target) return;
    if (target.dataset.moreInfo) {
      this.dispatchEvent(
        new CustomEvent("hass-more-info", {
          detail: { entityId: target.dataset.moreInfo },
          bubbles: true,
          composed: true,
        })
      );
    } else {
      this._press(target.dataset.step, Number(target.dataset.delta));
    }
  }

  _press(entityId, delta) {
    const state = this._hass.states[entityId];
    if (!state) return;
    const step = (this._steps[entityId] ??= {});
    if (step.sending) return;
    const { min, max, step: increment = 1 } = state.attributes;
    const current = parseFloat(state.state);
    const base = step.value ?? current;
    const next = Math.max(min, Math.min(max, base + delta * increment));
    clearTimeout(step.timer);
    step.error = undefined;
    if (next === current) {
      step.value = undefined;
    } else {
      step.value = next;
      step.timer = setTimeout(() => this._send(entityId), SEND_DELAY);
    }
    this._render();
  }

  async _send(entityId) {
    const step = this._steps[entityId];
    step.sending = true;
    this._render();
    try {
      await this._hass.callService("number", "set_value", { entity_id: entityId, value: step.value });
    } catch (err) {
      step.error = err?.message || String(err);
    }
    step.sending = false;
    step.value = undefined;
    this._render();
  }

  _stepper(key, label, signed) {
    if (this._config.show_controls === false || !this._has(key)) return "";
    const entityId = this._entities[key];
    const state = this._hass.states[entityId];
    const unit = state.attributes.unit_of_measurement;
    const { min, max } = state.attributes;
    const step = this._steps[entityId] || {};
    const current = this._number(key);
    const value = step.value ?? current;
    const pending = step.value !== undefined;
    let status = this._t("range", {
      min: this._formatNumber(min, unit, signed),
      max: this._formatNumber(max, unit, signed),
    });
    let statusClass = "";
    if (step.sending) {
      status = this._t("sending");
      statusClass = "active";
    } else if (pending) {
      status = this._t("pending");
      statusClass = "active";
    } else if (step.error) {
      status = this._t("failed", { error: step.error });
      statusClass = "error";
    }
    const disabled = value === undefined || step.sending;
    const id = escape(entityId);
    return `
      <div class="stepper">
        <div class="stepper-label">
          <span class="name">${escape(label)}</span>
          <span class="small ${statusClass}" aria-live="polite">${escape(status)}</span>
        </div>
        <div class="stepper-controls">
          <button type="button" class="round" data-step="${id}" data-delta="-1"
            aria-label="${escape(this._t("decrease", { name: label }))}"
            ${disabled || value <= min ? "disabled" : ""}>${icon("minus", 18)}</button>
          <span class="stepper-value ${pending ? "active" : ""}">${value === undefined ? "—" : escape(this._formatNumber(value, unit, signed))}</span>
          <button type="button" class="round" data-step="${id}" data-delta="1"
            aria-label="${escape(this._t("increase", { name: label }))}"
            ${disabled || value >= max ? "disabled" : ""}>${icon("plus", 18)}</button>
        </div>
      </div>`;
  }

  _header() {
    const title = this._config.title ?? "iQ R23";
    const extremes = [
      ["min", "outdoor_temperature_min"],
      ["max", "outdoor_temperature_max"],
      ["mean", "outdoor_temperature_mean"],
    ]
      .filter(([, key]) => this._state(key))
      .map(([label, key]) => `${this._t(label)} ${escape(this._format(key))}`)
      .join(" · ");
    const outdoor = this._has("outdoor_temperature")
      ? `<button type="button" class="linkish outdoor" ${this._moreInfo("outdoor_temperature")}
          aria-label="${escape(this._t("outdoor"))}">
          <span class="outdoor-value">${icon("thermometer")}${escape(this._format("outdoor_temperature"))}</span>
          <span class="small">${extremes}</span>
        </button>`
      : "";
    return `
      <div class="header">
        <div class="header-title">
          <h2>${escape(title)}</h2>
          <span class="secondary">${escape(this._t("subtitle"))}</span>
        </div>
        ${outdoor}
      </div>`;
  }

  _alarm() {
    const active = PROBLEMS.filter((key) => this._isOn(key));
    if (!active.length) return "";
    return `
      <div class="alarm" role="alert">
        ${icon("alert")}
        <div>
          <strong>${active.map((key) => escape(this._t(key))).join(", ")}</strong>
          <span class="small" style="color: inherit">${escape(this._t("alarm"))}</span>
        </div>
      </div>`;
  }

  _zone(label, key, targetKey, heatingKey) {
    if (!this._has(key)) return "";
    const target = this._state(targetKey) ? ` <span class="target">→ ${escape(this._format(targetKey))}</span>` : "";
    let chip = "";
    if (this._has(heatingKey)) {
      chip = this._isOn(heatingKey)
        ? `<span class="chip heat">${icon("flame", 14)}${escape(this._t("heating"))}</span>`
        : `<span class="chip">${escape(this._t("idle"))}</span>`;
    }
    return `
      <div class="zone">
        <button type="button" class="linkish" ${this._moreInfo(key)}>
          <span class="secondary">${escape(label)}</span>
          <span class="value">${escape(this._format(key))}${target}</span>
        </button>
        ${chip}
      </div>`;
  }

  _tank() {
    const zones = ["tank_upper", "tank_middle", "tank_lower"].filter((key) => this._has(key));
    if (!zones.length) return "";
    return `
      <section>
        <h3>${escape(this._t("tank"))}</h3>
        <div class="tank">
          <div class="vessel" aria-hidden="true">
            ${zones.map((key) => `<div style="background: ${this._tempColor(key)}"></div>`).join("")}
          </div>
          <div class="zones">
            ${this._zone(this._t("upper"), "tank_upper", "tank_upper_target", "tank_upper_heating")}
            ${this._zone(this._t("middle"), "tank_middle")}
            ${this._zone(this._t("lower"), "tank_lower", "tank_lower_target", "tank_lower_heating")}
          </div>
        </div>
        ${this._stepper("tank_base", this._t("tank_base"), false)}
      </section>`;
  }

  _chip(key, onLabel, offLabel) {
    if (!this._has(key)) return "";
    const on = this._isOn(key);
    return `<span class="chip ${on ? "on" : ""}"><span class="dot"></span>${escape(on ? onLabel : offLabel)}</span>`;
  }

  _circuit(n) {
    const key = `circuit_${n}`;
    if (!this._has(key)) return "";
    const target = this._state(`${key}_target`)
      ? ` <span class="target">→ ${escape(this._format(`${key}_target`))}</span>`
      : "";
    const mixing = this._number(`${key}_mixing`);
    const mixingRow =
      mixing === undefined
        ? ""
        : `<div class="mixing">
            <span class="secondary">${escape(this._t("mixing"))}</span>
            <div class="bar" role="img" aria-label="${escape(this._t("mixing"))} ${mixing} %">
              <div style="width: ${Math.max(0, Math.min(100, mixing))}%"></div>
            </div>
            <span class="pct">${escape(this._format(`${key}_mixing`))}</span>
          </div>`;
    return `
      <section>
        <div class="circuit-head">
          <h3>${escape(this._t(key))}</h3>
          <button type="button" class="linkish value" ${this._moreInfo(key)}>${escape(this._format(key))}${target}</button>
        </div>
        <div class="chips">
          ${this._chip(`${key}_pump`, this._t("pump_running"), this._t("pump_stopped"))}
          ${this._chip(`${key}_demand`, this._t("demand"), this._t("no_demand"))}
          ${this._chip(`${key}_setback`, this._t("setback"), this._t("setback"))}
        </div>
        ${mixingRow}
        ${this._stepper(`${key}_shift`, this._t("shift"), true)}
      </section>`;
  }

  _tile(key, label, iconName, pumpKey, iconClass = "") {
    if (!this._has(key)) return "";
    const running = this._isOn(pumpKey);
    const pump = running ? ` · ${this._t("pump")}` : "";
    return `
      <button type="button" class="tile" ${this._moreInfo(key)}>
        <span class="${running ? iconClass : ""}">${icon(iconName, 22)}</span>
        <span class="tile-value">${escape(this._format(key))}</span>
        <span class="small">${escape(label + pump)}</span>
      </button>`;
  }

  _tiles() {
    const tiles = [
      this._tile("fireplace", this._t("fireplace"), "flame", "fireplace_pump", "active"),
      this._tile("solar", this._t("solar"), "sun", "solar_pump", "active"),
      this._tile("pool_filtration", this._t("pool"), "waves", "pool_pump"),
      this._tile("cooling", this._t("cooling"), "snowflake"),
    ].join("");
    return tiles.trim() ? `<div class="tiles">${tiles}</div>` : "";
  }

  _render() {
    if (!this._hass) return;
    const deviceId = this._deviceId();
    this._entities = deviceId ? this._entityMap(deviceId) : {};
    const body = Object.keys(this._entities).length
      ? this._header() + this._alarm() + this._tank() + this._circuit(1) + this._circuit(2) + this._tiles()
      : `<div class="empty">${escape(this._t("no_device"))}</div>`;
    const html = `<style>${STYLES}</style><ha-card>${body}</ha-card>`;
    if (html === this._html) return;

    // Keep keyboard focus on a -/+ button across re-renders.
    const focused = this.shadowRoot.activeElement;
    const focusKey = focused?.dataset?.step && `[data-step="${focused.dataset.step}"][data-delta="${focused.dataset.delta}"]`;
    this._html = html;
    this.shadowRoot.innerHTML = html;
    if (focusKey) this.shadowRoot.querySelector(focusKey)?.focus();
  }
}

class IQR23CardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass || !this._config) return;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = (schema) => {
        const lang = this._hass.locale?.language || this._hass.language || "en";
        const table = TRANSLATIONS[lang.split("-")[0]] || TRANSLATIONS.en;
        return table[schema.name === "device_id" ? "device" : schema.name];
      };
      this._form.addEventListener("value-changed", (ev) => {
        const config = { ...ev.detail.value };
        for (const key of Object.keys(config)) {
          if (config[key] === "" || config[key] === undefined) delete config[key];
        }
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
      });
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.schema = [
      { name: "device_id", selector: { device: { integration: DOMAIN } } },
      { name: "title", selector: { text: {} } },
      { name: "show_controls", default: true, selector: { boolean: {} } },
    ];
    this._form.data = { show_controls: true, ...this._config };
  }
}

customElements.get("iqr23-card") || customElements.define("iqr23-card", IQR23Card);
customElements.get("iqr23-card-editor") || customElements.define("iqr23-card-editor", IQR23CardEditor);

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "iqr23-card")) {
  const lang = (navigator.language || "en").split("-")[0];
  window.customCards.push({
    type: "iqr23-card",
    name: "iQ R23",
    description: (TRANSLATIONS[lang] || TRANSLATIONS.en).card_description,
    preview: true,
    documentationURL: "https://github.com/filipek92/iqr23",
  });
}
