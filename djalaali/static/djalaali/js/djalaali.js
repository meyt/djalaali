// djalaali/static/djalaali/js/djalaali.js
// Calendar popup widget. Requires djalaali-core.js to be loaded first.
(function () {
  'use strict';

  const {
    MIN_YEAR, MAX_YEAR, isValidView, monthLength, toJalaali, d2g, j2d,
  } = window.DjalaaliCore;

  const DEFAULT_MONTH_NAMES = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'];
  const DEFAULT_WEEKDAY_SHORT_NAMES = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج']; // Saturday to Friday
  const DEFAULT_TODAY_LABEL = 'امروز';
  const TIME_UNITS = ['hour', 'minute', 'second'];
  const FRIDAY_COLUMN_INDEX = 6; // last column in the week grid (Sat=0 ... Fri=6)

  /* ------------------------------------------------------------------ *
   * Small formatting helpers
   * ------------------------------------------------------------------ */

  function pad2(n) { return String(n).padStart(2, '0'); }
  const DEFAULT_DATE_FORMAT = '%Y/%m/%d';
  function formatJalaaliDate(jy, jm, jd, fmt) {
    return (fmt || DEFAULT_DATE_FORMAT)
      .replace(/%([Ymd%])/g, (_, c) => ({ Y: jy, m: pad2(jm), d: pad2(jd), '%': '%' }[c]));
  }
  function formatIsoDate(gy, gm, gd) { return `${gy}-${pad2(gm)}-${pad2(gd)}`; }
  // Parses a value written in a strptime-like format limited to %Y, %m, %d.
  function parseJalaaliDate(value, fmt) {
    if (!value) return null;
    const order = [];
    const pattern = (fmt || DEFAULT_DATE_FORMAT).split(/(%[Ymd%])/).map((part) => {
      if (part === '%Y') { order.push('jy'); return '(\\d{4})'; }
      if (part === '%m') { order.push('jm'); return '(\\d{1,2})'; }
      if (part === '%d') { order.push('jd'); return '(\\d{1,2})'; }
      if (part === '%%') return '%';
      return part.replace(/[.*+?^${}()|[\]\\\/-]/g, '\\$&');
    }).join('');
    const match = new RegExp(`^${pattern}$`).exec(value.trim());
    if (!match) return null;
    const result = {};
    order.forEach((key, i) => { result[key] = Number(match[i + 1]); });
    return 'jy' in result && 'jm' in result && 'jd' in result ? result : null;
  }
  function inputFormat(input) { return (input && input.dataset.dateFormat) || DEFAULT_DATE_FORMAT; }

  /* ------------------------------------------------------------------ *
   * Calendar widget (singleton popup, one per page, reused per input)
   * ------------------------------------------------------------------ */

  const state = {
    activeInput: null,   // the .djalaali-datepicker text input currently bound
    timeInput: null,     // the sibling .vTimeField input, if any
    calendarEl: null,    // cached widget root element
    els: null,           // cached child elements of the widget
    view: { jy: null, jm: null }, // currently displayed Jalaali year/month
    monthNames: DEFAULT_MONTH_NAMES,
    weekdayNames: DEFAULT_WEEKDAY_SHORT_NAMES,
    todayLabel: DEFAULT_TODAY_LABEL,
  };

  function parseNameList(raw, fallback) {
    if (!raw) return fallback;
    try {
      const parts = JSON.parse(raw);
      const valid = Array.isArray(parts) && parts.length === fallback.length &&
        parts.every((p) => typeof p === 'string');
      return valid ? parts : fallback;
    } catch (e) {
      return fallback;
    }
  }

  function buildCalendarMarkup() {
    const cal = document.createElement('div');
    cal.className = 'djalaali-calendar';
    cal.setAttribute('role', 'dialog');
    cal.innerHTML = `
            <div class="djalaali-header">
                <div class="djalaali-nav-group">
                    <button type="button" class="djalaali-prev-month" aria-label="Previous month">&laquo;</button>
                    <span class="djalaali-title-month"></span>
                    <button type="button" class="djalaali-next-month" aria-label="Next month">&raquo;</button>
                </div>
                <div class="djalaali-nav-group">
                    <input type="number" class="djalaali-year-input" min="${MIN_YEAR}" max="${MAX_YEAR}">
                </div>
            </div>
            <div class="djalaali-weekdays"></div>
            <div class="djalaali-grid"></div>
            <div class="djalaali-time-section" hidden>
                ${TIME_UNITS.map((unit, i) => `${i ? '<span class="djalaali-time-separator">:</span>' : ''}
                <div class="djalaali-time-col">
                    <input type="number" class="djalaali-time-input djalaali-${unit}" min="0" max="${unit === 'hour' ? 23 : 59}">
                    <small class="djalaali-time-label djalaali-${unit}-label"></small>
                </div>`).join('')}
            </div>
            <div class="djalaali-footer">
                <button type="button" class="djalaali-today-btn"></button>
            </div>
        `;
    document.body.appendChild(cal);

    const q = (sel) => cal.querySelector(sel);
    state.els = {
      title: q('.djalaali-title-month'),
      year: q('.djalaali-year-input'),
      weekdays: q('.djalaali-weekdays'),
      grid: q('.djalaali-grid'),
      timeSection: q('.djalaali-time-section'),
      todayBtn: q('.djalaali-today-btn'),
      time: {},
    };
    TIME_UNITS.forEach((unit) => {
      state.els.time[unit] = { input: q(`.djalaali-${unit}`), label: q(`.djalaali-${unit}-label`) };
    });

    cal.querySelector('.djalaali-prev-month').addEventListener('click', () => navigateMonth(-1));
    cal.querySelector('.djalaali-next-month').addEventListener('click', () => navigateMonth(1));
    state.els.todayBtn.addEventListener('click', jumpToToday);

    state.els.grid.addEventListener('click', (e) => {
      const cell = e.target.closest('.djalaali-day');
      if (!cell || !state.activeInput) return;
      state.activeInput.value = formatJalaaliDate(state.view.jy, state.view.jm, Number(cell.dataset.day), inputFormat(state.activeInput));
      state.activeInput.dispatchEvent(new Event('change', { bubbles: true }));
      closeCalendar();
    });

    function setYear(newYear) {
      if (!isValidView(newYear, state.view.jm)) return;
      state.view.jy = newYear;
      renderCalendar();
    }

    state.els.year.addEventListener('change', (e) => setYear(parseInt(e.target.value, 10)));

    // Wheel over the month header (arrows + title): up = next month, down = previous.
    state.els.title.parentElement.addEventListener('wheel', (e) => {
      e.preventDefault();
      if (e.deltaY) navigateMonth(e.deltaY < 0 ? 1 : -1);
    }, { passive: false });

    // Wheel up = next year, wheel down = previous year (clamped to the valid range).
    state.els.year.addEventListener('wheel', (e) => {
      e.preventDefault();
      if (e.deltaY) setYear(state.view.jy + (e.deltaY < 0 ? 1 : -1));
    }, { passive: false });

    TIME_UNITS.forEach((unit) => {
      const { input } = state.els.time[unit];
      input.addEventListener('change', syncTimeInputFromWidget);
      input.addEventListener('wheel', onTimeWheel, { passive: false });
    });

    return cal;
  }

  function getOrCreateCalendar() {
    if (!state.calendarEl || !document.body.contains(state.calendarEl)) {
      state.calendarEl = buildCalendarMarkup();
    }
    return state.calendarEl;
  }

  // Wheel up increases, wheel down decreases; wraps around (23 -> 0, 0 -> 23).
  function onTimeWheel(e) {
    e.preventDefault();
    if (!e.deltaY) return;
    const input = e.currentTarget;
    const min = Number(input.min);
    const max = Number(input.max);
    const range = max - min + 1;
    const step = e.deltaY < 0 ? 1 : -1;
    const current = parseInt(input.value, 10) || 0;
    input.value = ((current - min + step) % range + range) % range + min;
    syncTimeInputFromWidget();
  }

  function syncTimeInputFromWidget() {
    if (!state.timeInput) return;
    state.timeInput.value = TIME_UNITS
      .map((unit) => (state.els.time[unit].input.value || '0').padStart(2, '0'))
      .join(':');
  }

  /* ---- rendering ---- */

  function todayJalaali() {
    const now = new Date();
    const [jy, jm, jd] = toJalaali(now.getFullYear(), now.getMonth() + 1, now.getDate());
    return { jy, jm, jd };
  }

  function isSameDate(a, b) {
    return !!a && !!b && a.jy === b.jy && a.jm === b.jm && a.jd === b.jd;
  }

  function renderCalendar() {
    if (!state.calendarEl) return;
    const { jy, jm } = state.view;
    const { title, year, grid } = state.els;

    title.textContent = state.monthNames[jm - 1];
    year.value = jy;

    const firstJdn = j2d(jy, jm, 1);
    const [gy, gm, gd] = d2g(firstJdn);
    const startOffset = (new Date(gy, gm - 1, gd).getDay() + 1) % 7; // shift so Saturday = column 0

    const today = todayJalaali();
    const selected = state.activeInput ? parseJalaaliDate(state.activeInput.value, inputFormat(state.activeInput)) : null;

    const fragment = document.createDocumentFragment();
    for (let i = 0; i < startOffset; i++) {
      const empty = document.createElement('div');
      empty.className = 'djalaali-empty';
      fragment.appendChild(empty);
    }
    const daysInMonth = monthLength(jy, jm);
    for (let d = 1; d <= daysInMonth; d++) {
      fragment.appendChild(buildDayCell(d, firstJdn + d - 1, (startOffset + d - 1) % 7, {
        isToday: isSameDate({ jy, jm, jd: d }, today),
        isSelected: isSameDate({ jy, jm, jd: d }, selected),
      }));
    }
    grid.replaceChildren(fragment);
  }

  function buildDayCell(d, jdn, colIndex, { isToday, isSelected }) {
    const dayCell = document.createElement('button');
    dayCell.type = 'button';
    dayCell.className = 'djalaali-day';
    dayCell.dataset.day = d;
    dayCell.classList.toggle('djalaali-holiday', colIndex === FRIDAY_COLUMN_INDEX);
    dayCell.classList.toggle('djalaali-today', isToday);
    dayCell.classList.toggle('djalaali-selected', isSelected);
    if (isToday) dayCell.setAttribute('aria-current', 'date');
    dayCell.setAttribute('aria-pressed', String(isSelected));

    const [gy, gm, gd] = d2g(jdn);
    dayCell.title = formatIsoDate(gy, gm, gd);
    dayCell.setAttribute('aria-label', `${d} ${state.monthNames[state.view.jm - 1]} ${state.view.jy}`);
    dayCell.textContent = d;
    return dayCell;
  }

  /* ---- navigation ---- */

  function navigateMonth(delta) {
    let { jy, jm } = state.view;
    jm += delta;
    if (jm > 12) { jm = 1; jy += 1; }
    if (jm < 1) { jm = 12; jy -= 1; }
    if (!isValidView(jy, jm)) return;
    state.view = { jy, jm };
    renderCalendar();
  }

  function jumpToToday() {
    const { jy, jm } = todayJalaali();
    state.view = { jy, jm };
    renderCalendar();
  }

  /* ---- open/close + time-field linkage ---- */

  function findSiblingTimeField(dateInput) {
    // Stop below <body> so we never bind a time field from an unrelated widget.
    let container = dateInput.parentElement;
    while (container && container.tagName !== 'BODY') {
      const field = container.querySelector('.vTimeField');
      if (field) return field;
      container = container.parentElement;
    }
    return null;
  }

  function setupTimeSection(input) {
    const hasTime = input.dataset.djalaaliHasTime === 'true';
    state.els.timeSection.hidden = !hasTime;

    state.timeInput = null;
    if (!hasTime) return;

    TIME_UNITS.forEach((unit) => {
      state.els.time[unit].label.textContent =
        input.dataset[`${unit}Label`] || unit.charAt(0).toUpperCase() + unit.slice(1);
    });

    state.timeInput = findSiblingTimeField(input);

    const parts = state.timeInput && state.timeInput.value ? state.timeInput.value.split(':') : [];
    TIME_UNITS.forEach((unit, i) => {
      state.els.time[unit].input.value = parseInt(parts[i], 10) || 0;
    });
  }

  function setupLabels(input) {
    state.monthNames = parseNameList(input.dataset.monthNames, DEFAULT_MONTH_NAMES);
    state.weekdayNames = parseNameList(input.dataset.weekdayNames, DEFAULT_WEEKDAY_SHORT_NAMES);
    state.todayLabel = input.dataset.todayLabel || DEFAULT_TODAY_LABEL;

    state.els.weekdays.replaceChildren(...state.weekdayNames.map((name) => {
      const el = document.createElement('div');
      el.textContent = name;
      return el;
    }));
    state.els.todayBtn.textContent = state.todayLabel;
  }

  function openCalendar(input) {
    state.activeInput = input;
    const cal = getOrCreateCalendar();

    setupLabels(input);
    setupTimeSection(input);

    const parsed = parseJalaaliDate(input.value, inputFormat(input));
    const { jy, jm } = parsed && isValidView(parsed.jy, parsed.jm) ? parsed : todayJalaali();

    state.view = { jy, jm };
    renderCalendar();

    cal.style.display = 'block';
    positionCalendar();
  }

  // Keep the popup fully inside the viewport: below the input when it fits,
  // otherwise above, otherwise on the roomier side with a scrollable max-height.
  function positionCalendar() {
    const cal = state.calendarEl;
    if (!cal || !state.activeInput) return;
    const rect = state.activeInput.getBoundingClientRect();
    const vw = document.documentElement.clientWidth;
    const vh = document.documentElement.clientHeight;

    cal.style.maxHeight = '';
    const { offsetWidth: w, offsetHeight: fullHeight } = cal;

    const spaceBelow = vh - rect.bottom;
    const spaceAbove = rect.top;
    const placeBelow = fullHeight <= spaceBelow || (fullHeight > spaceAbove && spaceBelow >= spaceAbove);
    const available = placeBelow ? spaceBelow : spaceAbove;

    if (fullHeight > available) cal.style.maxHeight = `${Math.max(available, 0)}px`;
    const h = Math.min(fullHeight, available);

    const top = placeBelow ? rect.bottom : rect.top - h;
    const left = Math.max(0, Math.min(rect.left, vw - w));
    cal.style.top = `${top + window.scrollY}px`;
    cal.style.left = `${left + window.scrollX}px`;
  }

  function closeCalendar() {
    if (state.calendarEl) state.calendarEl.style.display = 'none';
    state.activeInput = null;
    state.timeInput = null;
  }

  /* ------------------------------------------------------------------ *
   * Global event wiring
   * ------------------------------------------------------------------ */

  document.addEventListener('DOMContentLoaded', function () {
    document.body.addEventListener('focusin', function (e) {
      if (e.target.classList.contains('djalaali-datepicker')) {
        openCalendar(e.target);
      }
    });

    document.addEventListener('focusin', function (e) {
      if (state.activeInput && !e.target.closest('.djalaali-calendar') && !e.target.classList.contains('djalaali-datepicker')) {
        closeCalendar();
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && state.activeInput) {
        const input = state.activeInput;
        closeCalendar();
        input.focus({ preventScroll: true });
      }
    });

    window.addEventListener('resize', positionCalendar);
    window.addEventListener('scroll', positionCalendar, true); // capture: also nested scroll containers

    document.addEventListener('click', function (e) {
      if (state.activeInput && !e.target.closest('.djalaali-calendar') && !e.target.classList.contains('djalaali-datepicker')) {
        closeCalendar();
      }
    });
  });
})();
