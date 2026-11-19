const assert = require('assert');
const refresh = require('../static/js/refresh-control.js');

(async () => {
    let running = 0, peak = 0, calls = 0, release;
    const block = new Promise(resolve => { release = resolve; });
    const work = async () => {
        calls++;
        running++;
        peak = Math.max(peak, running);
        if (calls === 1) await block;
        running--;
    };
    const first = refresh.singleFlight('analysis', work);
    const second = refresh.singleFlight('analysis', work);
    const third = refresh.singleFlight('analysis', work);
    assert.strictEqual(first, second);
    assert.strictEqual(second, third);
    assert.equal(calls, 1);
    release();
    await first;
    assert.equal(calls, 2); // many refresh requests coalesce into one rerun
    assert.equal(peak, 1);

    let scheduled = 0, pendingResolve, active = 0, max = 0;
    let startedResolve;
    const started = new Promise(resolve => { startedResolve = resolve; });
    const stop = refresh.schedule(async () => {
        scheduled++;
        max = Math.max(max, ++active);
        if (scheduled === 1) {
            startedResolve();
            await new Promise(resolve => { pendingResolve = resolve; });
        }
        active--;
    }, 10, 0);
    await started;
    await new Promise(resolve => setTimeout(resolve, 40));
    assert.equal(scheduled, 1); // no interval can start another while blocked
    pendingResolve();
    await new Promise(resolve => setTimeout(resolve, 35));
    stop();
    assert(scheduled >= 2);
    assert.equal(max, 1);
    console.log('Refresh single-flight and scheduling tests passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
