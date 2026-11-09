// djalaali/static/djalaali/js/djalaali.js
(function () {
  'use strict';

  /* ------------------------------------------------------------------ *
   * Jalaali <-> Gregorian conversion (algorithm unchanged from original)
   * ------------------------------------------------------------------ */

  const BREAKS = [-61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210, 1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178];
  const DEFAULT_MONTH_NAMES = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'];
  const DEFAULT_WEEKDAY_SHORT_NAMES = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج']; // Saturday to Friday
  const DEFAULT_TODAY_LABEL = 'امروز';
  const FRIDAY_COLUMN_INDEX = 6; // last column in the week grid (Sat=0 ... Fri=6)

  function div(a, b) { return Math.trunc(a / b); }
  function mod(a, b) { return a - Math.trunc(a / b) * b; }

  function jalCal(jy) {
    const bl = BREAKS.length;
    const gy = jy + 621;
    let leapJ = -14;
    let jp = BREAKS[0];
    let jm, jump = 0, n, i;

    if (jy < jp || jy >= BREAKS[bl - 1]) {
      throw new Error('Invalid Jalaali year ' + jy);
    }

    for (i = 1; i < bl; i += 1) {
      jm = BREAKS[i];
      jump = jm - jp;
      if (jy < jm) break;
      leapJ = leapJ + div(jump, 33) * 8 + div(mod(jump, 33), 4);
      jp = jm;
    }

    n = jy - jp;
    leapJ = leapJ + div(n, 33) * 8 + div(mod(n, 33) + 3, 4);
    if (mod(jump, 33) === 4 && jump - n === 4) leapJ += 1;

    const leapG = div(gy, 4) - div((div(gy, 100) + 1) * 3, 4) - 150;
    const march = 20 + leapJ - leapG;

    if (jump - n < 6) n = n - jump + div(jump + 4, 33) * 33;

    let leap = mod(mod(n + 1, 33) - 1, 4);
    if (leap === -1) leap = 4;

    return { leap, gy, march };
  }

  function g2d(gy, gm, gd) {
    let d = div((gy + div(gm - 8, 6) + 100100) * 1461, 4) + div(153 * mod(gm + 9, 12) + 2, 5) + gd - 34840408;
    d = d - div(div(gy + 100100 + div(gm - 8, 6), 100) * 3, 4) + 752;
    return d;
  }

  function d2g(jdn) {
    let j = 4 * jdn + 139361631;
    j = j + div(div(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908;
    const i = div(mod(j, 1461), 4) * 5 + 308;
    const gd = div(mod(i, 153), 5) + 1;
    const gm = mod(div(i, 153), 12) + 1;
    const gy = div(j, 1461) - 100100 + div(8 - gm, 6);
    return [gy, gm, gd];
  }

  function j2d(jy, jm, jd) {
    const r = jalCal(jy);
    return g2d(r.gy, 3, r.march) + (jm - 1) * 31 - div(jm, 7) * (jm - 7) + jd - 1;
  }

  function d2j(jdn) {
    const gy0 = d2g(jdn)[0];
    let jy = gy0 - 621;
    const r = jalCal(jy);
    const jdn1f = g2d(r.gy, 3, r.march);
    let k = jdn - jdn1f;

    if (k >= 0) {
      if (k <= 185) {
        const jm = 1 + div(k, 31);
        const jd = mod(k, 31) + 1;
        return [jy, jm, jd];
      }
      k -= 186;
    } else {
      jy -= 1;
      k += 179;
      if (r.leap === 1) k += 1;
    }

    const jm = 7 + div(k, 30);
    const jd = mod(k, 30) + 1;
    return [jy, jm, jd];
  }

  function toJalaali(gy, gm, gd) { return d2j(g2d(gy, gm, gd)); }
  function toGregorian(jy, jm, jd) { return d2g(j2d(jy, jm, jd)); }

  const MIN_YEAR = -61;
  const MAX_YEAR = BREAKS[BREAKS.length - 1] - 1;
  function isValidView(jy, jm) {
    return Number.isInteger(jy) && Number.isInteger(jm) &&
      jy >= MIN_YEAR && jy <= MAX_YEAR && jm >= 1 && jm <= 12;
  }

  function monthLength(jy, jm) {
    if (jm <= 6) return 31;
    if (jm <= 11) return 30;
    return jalCal(jy).leap === 0 ? 30 : 29;
  }

  /* ------------------------------------------------------------------ *
   * Small formatting helpers
   * ------------------------------------------------------------------ */

  function pad2(n) { return String(n).padStart(2, '0'); }
  function formatJalaaliDate(jy, jm, jd) { return `${jy}/${pad2(jm)}/${pad2(jd)}`; }
  function formatIsoDate(gy, gm, gd) { return `${gy}-${pad2(gm)}-${pad2(gd)}`; }
  function parseJalaaliDate(value) {
    if (!value) return null;
    const parts = value.split('/').map(Number);
    if (parts.length !== 3 || parts.some(isNaN)) return null;
    return { jy: parts[0], jm: parts[1], jd: parts[2] };
  }

  /* ------------------------------------------------------------------ *
   * Calendar widget (singleton popup, one per page, reused per input)
   * ------------------------------------------------------------------ */

  const state = {
    activeInput: null,   // the .djalaali-datepicker text input currently bound
    timeInput: null,     // the sibling .vTimeField input, if any
    calendarEl: null,    // cached widget root element
    view: { jy: null, jm: null }, // currently displayed Jalaali year/month
    monthNames: DEFAULT_MONTH_NAMES,
    weekdayNames: DEFAULT_WEEKDAY_SHORT_NAMES,
    todayLabel: DEFAULT_TODAY_LABEL,
  };

  function parseNameList(raw, fallback) {
    if (!raw) return fallback;
    const parts = raw.split(',').map((s) => s.trim()).filter(Boolean);
    return parts.length === fallback.length ? parts : fallback;
  }

  function buildCalendarMarkup() {
    const cal = document.createElement('div');
    cal.className = 'djalaali-calendar';
    cal.innerHTML = `
            <div class="djalaali-header">
                <div class="djalaali-nav-group">
                    <button type="button" class="djalaali-prev-month">&laquo;</button>
                    <span class="djalaali-title-month"></span>
                    <button type="button" class="djalaali-next-month">&raquo;</button>
                </div>
                <div class="djalaali-nav-group">
                    <input type="number" class="djalaali-year-input" min="1300" max="1500">
                </div>
            </div>
            <div class="djalaali-weekdays"></div>
            <div class="djalaali-grid"></div>
            <div class="djalaali-time-section" style="display: none;">
                <div class="djalaali-time-col">
                    <input type="number" class="djalaali-time-input djalaali-hour" min="0" max="23">
                    <small class="djalaali-time-label djalaali-hour-label"></small>
                </div>
                <span class="djalaali-time-separator">:</span>
                <div class="djalaali-time-col">
                    <input type="number" class="djalaali-time-input djalaali-minute" min="0" max="59">
                    <small class="djalaali-time-label djalaali-minute-label"></small>
                </div>
                <span class="djalaali-time-separator">:</span>
                <div class="djalaali-time-col">
                    <input type="number" class="djalaali-time-input djalaali-second" min="0" max="59">
                    <small class="djalaali-time-label djalaali-second-label"></small>
                </div>
            </div>
            <div class="djalaali-footer">
                <button type="button" class="djalaali-today-btn"></button>
            </div>
        `;
    document.body.appendChild(cal);

    cal.querySelector('.djalaali-prev-month').addEventListener('click', () => navigateMonth(-1));
    cal.querySelector('.djalaali-next-month').addEventListener('click', () => navigateMonth(1));
    cal.querySelector('.djalaali-today-btn').addEventListener('click', jumpToToday);

    cal.querySelector('.djalaali-year-input').addEventListener('change', (e) => {
      const newYear = parseInt(e.target.value, 10);
      if (isValidView(newYear, state.view.jm)) {
        state.view.jy = newYear;
        renderCalendar();
      }
    });

    cal.querySelectorAll('.djalaali-time-input').forEach((input) => {
      input.addEventListener('change', syncTimeInputFromWidget);
    });

    return cal;
  }

  function getOrCreateCalendar() {
    if (!state.calendarEl || !document.body.contains(state.calendarEl)) {
      state.calendarEl = buildCalendarMarkup();
    }
    return state.calendarEl;
  }

  function syncTimeInputFromWidget() {
    if (!state.timeInput) return;
    const cal = state.calendarEl;
    const h = (cal.querySelector('.djalaali-hour').value || '0').padStart(2, '0');
    const m = (cal.querySelector('.djalaali-minute').value || '0').padStart(2, '0');
    const s = (cal.querySelector('.djalaali-second').value || '0').padStart(2, '0');
    state.timeInput.value = `${h}:${m}:${s}`;
  }

  /* ---- rendering ---- */

  function renderCalendar() {
    const cal = state.calendarEl;
    if (!cal) return;
    const { jy, jm } = state.view;

    cal.querySelector('.djalaali-title-month').textContent = state.monthNames[jm - 1];
    cal.querySelector('.djalaali-year-input').value = jy;

    const grid = cal.querySelector('.djalaali-grid');
    grid.innerHTML = '';

    const daysInMonth = monthLength(jy, jm);
    const [gy, gm, gd] = toGregorian(jy, jm, 1);
    const firstOfMonth = new Date(gy, gm - 1, gd);
    const startOffset = (firstOfMonth.getDay() + 1) % 7; // shift so Saturday = column 0

    for (let i = 0; i < startOffset; i++) {
      const empty = document.createElement('div');
      empty.className = 'djalaali-empty';
      grid.appendChild(empty);
    }

    const todayGregorian = new Date();
    const [todayJy, todayJm, todayJd] = toJalaali(
      todayGregorian.getFullYear(),
      todayGregorian.getMonth() + 1,
      todayGregorian.getDate()
    );

    const selected = state.activeInput ? parseJalaaliDate(state.activeInput.value) : null;

    for (let d = 1; d <= daysInMonth; d++) {
      grid.appendChild(buildDayCell(d, jy, jm, startOffset, { todayJy, todayJm, todayJd }, selected));
    }
  }

  function buildDayCell(d, jy, jm, startOffset, today, selected) {
    const dayCell = document.createElement('div');
    dayCell.className = 'djalaali-day';

    const colIndex = (startOffset + d - 1) % 7;
    if (colIndex === FRIDAY_COLUMN_INDEX) {
      dayCell.classList.add('djalaali-holiday');
    }

    if (jy === today.todayJy && jm === today.todayJm && d === today.todayJd) {
      dayCell.classList.add('djalaali-today');
    }

    if (selected && jy === selected.jy && jm === selected.jm && d === selected.jd) {
      dayCell.classList.add('djalaali-selected');
    }

    const [ggy, ggm, ggd] = toGregorian(jy, jm, d);
    dayCell.title = formatIsoDate(ggy, ggm, ggd);
    dayCell.textContent = d;

    dayCell.addEventListener('click', () => {
      state.activeInput.value = formatJalaaliDate(jy, jm, d);
      state.activeInput.dispatchEvent(new Event('change'));
      closeCalendar();
    });

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
    const today = new Date();
    const [jy, jm] = toJalaali(today.getFullYear(), today.getMonth() + 1, today.getDate());
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

  function setupTimeSection(cal, input) {
    const hasTime = input.dataset.djalaaliHasTime === 'true';
    const timeSection = cal.querySelector('.djalaali-time-section');
    timeSection.style.display = hasTime ? 'flex' : 'none';

    state.timeInput = null;
    if (!hasTime) return;

    cal.querySelector('.djalaali-hour-label').textContent = input.dataset.hourLabel || 'Hour';
    cal.querySelector('.djalaali-minute-label').textContent = input.dataset.minuteLabel || 'Minute';
    cal.querySelector('.djalaali-second-label').textContent = input.dataset.secondLabel || 'Second';

    state.timeInput = findSiblingTimeField(input);

    let h = '00', m = '00', s = '00';
    if (state.timeInput && state.timeInput.value) {
      const parts = state.timeInput.value.split(':');
      h = parts[0] || '00';
      m = parts[1] || '00';
      s = parts[2] || '00';
    }
    cal.querySelector('.djalaali-hour').value = parseInt(h, 10) || 0;
    cal.querySelector('.djalaali-minute').value = parseInt(m, 10) || 0;
    cal.querySelector('.djalaali-second').value = parseInt(s, 10) || 0;
  }

  function setupLabels(cal, input) {
    state.monthNames = parseNameList(input.dataset.monthNames, DEFAULT_MONTH_NAMES);
    state.weekdayNames = parseNameList(input.dataset.weekdayNames, DEFAULT_WEEKDAY_SHORT_NAMES);
    state.todayLabel = input.dataset.todayLabel || DEFAULT_TODAY_LABEL;

    const weekdaysEl = cal.querySelector('.djalaali-weekdays');
    weekdaysEl.innerHTML = state.weekdayNames.map((w) => `<div>${w}</div>`).join('');

    cal.querySelector('.djalaali-today-btn').textContent = state.todayLabel;
  }

  function openCalendar(input) {
    state.activeInput = input;
    const cal = getOrCreateCalendar();

    setupLabels(cal, input);
    setupTimeSection(cal, input);

    const parsed = parseJalaaliDate(input.value);
    let jy, jm;
    if (parsed && isValidView(parsed.jy, parsed.jm)) {
      jy = parsed.jy; jm = parsed.jm;
    } else {
      const today = new Date();
      [jy, jm] = toJalaali(today.getFullYear(), today.getMonth() + 1, today.getDate());
    }

    state.view = { jy, jm };
    renderCalendar();

    const rect = input.getBoundingClientRect();
    cal.style.top = `${rect.bottom + window.scrollY}px`;
    cal.style.left = `${rect.left + window.scrollX}px`;
    cal.style.display = 'block';
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

    document.addEventListener('click', function (e) {
      if (state.activeInput && !e.target.closest('.djalaali-calendar') && !e.target.classList.contains('djalaali-datepicker')) {
        closeCalendar();
      }
    });
  });
})();
