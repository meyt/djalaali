// djalaali/static/djalaali/js/djalaali-core.js
// Pure Jalaali <-> Gregorian conversion helpers; no DOM access.
(function () {
  'use strict';

  /* Jalaali <-> Gregorian conversion (algorithm unchanged from original) */

  const BREAKS = [-61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210, 1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178];

  function div(a, b) { return Math.trunc(a / b); }
  function mod(a, b) { return a - Math.trunc(a / b) * b; }

  const jalCalCache = new Map();
  function jalCal(jy) {
    let cached = jalCalCache.get(jy);
    if (!cached) {
      cached = computeJalCal(jy);
      jalCalCache.set(jy, cached);
    }
    return cached;
  }

  function computeJalCal(jy) {
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

  window.DjalaaliCore = {
    MIN_YEAR, MAX_YEAR, isValidView, monthLength,
    toJalaali, toGregorian, j2d, d2g,
  };
})();
