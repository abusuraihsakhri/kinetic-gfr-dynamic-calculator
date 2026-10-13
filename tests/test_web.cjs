const test = require('node:test');
const assert = require('node:assert/strict');
const { calculate } = require('../web/kinetic.js');
const fs = require('node:fs');
const path = require('node:path');

const example = {
  steady_state_creatinine: 1, baseline_gfr: 90,
  creatinine_1: 1.8, creatinine_2: 2.4, hours: 24,
  max_creatinine_rise_per_day: 1.5, unit: 'mg/dL'
};

test('Chen numerical reference and correction', () => {
  const r = calculate(example);
  assert.equal(r.kegfr, 25.71);
  assert.equal(r.kinetic_factor, 0.6);
});
test('constant and declining creatinine', () => {
  assert.equal(calculate({...example, creatinine_1: 1, creatinine_2: 1}).kegfr, 90);
  assert.equal(calculate({...example, creatinine_1: 2.4, creatinine_2: 1.8}).kegfr, 60);
});
test('micromoles produce same clearance', () => {
  const converted = {...example, unit: 'umol/L',
    steady_state_creatinine: 88.4, creatinine_1: 1.8*88.4, creatinine_2: 2.4*88.4 };
  assert.equal(calculate(converted).kegfr, calculate(example).kegfr);
});
test('reject invalid values and negative model estimates', () => {
  for (const change of [
    {hours:0}, {hours:'not a number'}, {creatinine_1:Infinity},
    {creatinine_2:''}, {baseline_gfr:-9},
    {max_creatinine_rise_per_day:0}, {creatinine_2:5},
    {unit:'invalid'}
  ]) assert.throws(() => calculate({...example,...change}));
});
test('static page uses local source and has no mock clinical reports', () => {
  const html = fs.readFileSync(path.join(__dirname,'../web/index.html'),'utf8');
  assert.match(html, /<script src="\.\/kinetic\.js"><\/script>/);
  assert.match(html, /KineticGFR\.calculate\(values\)/);
  assert.doesNotMatch(html, /DOSSIER-SIM|Air-Gapped Active|fetch\('\/api\/audit'/);
});
