const assert = require('assert');
const time = require('../static/js/market-time.js');
const expected = '14 Jan 2026, 09:30 IST';
const cases = [
  '2026-01-14T04:00:00Z',
  '2026-01-14T09:30:00+05:30',
  '2026-01-14 09:30:00',
  '14-Jan-2026 09:30:00',
  Date.parse('2026-01-14T04:00:00Z') / 1000,
  String(Date.parse('2026-01-14T04:00:00Z') / 1000),
  Date.parse('2026-01-14T04:00:00Z')
];
for (const value of cases) assert.equal(time.formatChennaiTime(value), expected, String(value));
assert.equal(time.formatChennaiTime('not a time'), 'Time unavailable');
assert.equal(time.toEpochSeconds('not a time'), null);
assert.equal(time.formatChartTick(Date.parse('2026-01-14T04:00:00Z') / 1000, 3), '09:30');
console.log('Chennai market-time tests passed');
