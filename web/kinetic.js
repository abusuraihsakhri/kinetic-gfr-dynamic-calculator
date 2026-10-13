/* Chen (2013) kinetic GFR. No dependencies or network requests. */
(function (root) {
  'use strict';
  function calculate(values) {
    const unit = values.unit || 'mg/dL';
    if (!['mg/dL', 'umol/L'].includes(unit)) {
      throw new Error('Select mg/dL or µmol/L.');
    }
    const fields = ['steady_state_creatinine', 'baseline_gfr', 'creatinine_1', 'creatinine_2', 'hours'];
    const numeric = {};
    for (const name of fields) {
      const raw = values[name];
      if (raw === '' || raw === null || raw === undefined) throw new Error(name + ' is required.');
      numeric[name] = Number(raw);
      if (!Number.isFinite(numeric[name]) || numeric[name] <= 0) {
        throw new Error(name + ' must be a finite positive number.');
      }
    }
    const rawMax = values.max_creatinine_rise_per_day ?? 1.5;
    if (rawMax === '' || rawMax === null) throw new Error('Specify a maximum creatinine rise.');
    const maxRise = Number(rawMax);
    if (!Number.isFinite(maxRise) || maxRise <= 0) {
      throw new Error('Maximum creatinine rise must be a finite positive number.');
    }
    const factor = unit === 'umol/L' ? 1 / 88.4 : 1;
    const steady = numeric.steady_state_creatinine * factor;
    const first = numeric.creatinine_1 * factor;
    const last = numeric.creatinine_2 * factor;
    const mean = (first + last) / 2;
    const delta = last - first;
    const kineticFactor = 1 - 24 * delta / (numeric.hours * maxRise);
    if (kineticFactor < -1e-12) {
      throw new Error('Rise exceeds the chosen anuric maximum. The model gives a negative clearance; review assumptions.');
    }
    const kegfr = steady * numeric.baseline_gfr / mean * Math.max(kineticFactor, 0);
    if (!Number.isFinite(kegfr)) throw new Error('Result is outside supported numeric range.');
    return {
      kegfr: Math.round(kegfr * 100) / 100,
      mean_creatinine: Math.round(mean / factor * 10000) / 10000,
      creatinine_change: Math.round(delta / factor * 10000) / 10000,
      kinetic_factor: Math.round(Math.max(kineticFactor, 0) * 1000000) / 1000000,
      clearance_unit: 'same as baseline clearance',
      creatinine_unit: unit
    };
  }
  root.KineticGFR = { calculate };
  if (typeof module !== 'undefined' && module.exports) module.exports = { calculate };
})(typeof window !== 'undefined' ? window : globalThis);
