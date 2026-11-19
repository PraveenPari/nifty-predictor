/* Keep slow refreshes from piling up while allowing a single queued rerun. */
(function (root) {
    'use strict';
    const flights = new Map();
    function singleFlight(key, task) {
        const existing = flights.get(key);
        if (existing) {
            existing.queued = true;
            return existing.promise;
        }
        const state = {queued: false, promise: null};
        flights.set(key, state);
        state.promise = (async () => {
            try {
                do {
                    state.queued = false;
                    await task();
                } while (state.queued);
            } finally {
                flights.delete(key);
            }
        })();
        return state.promise;
    }
    function schedule(task, delay, firstDelay = delay) {
        let stopped = false;
        let timer;
        async function run() {
            if (stopped) return;
            try { await task(); } catch (e) { console.warn('Refresh failed', e); }
            if (!stopped) timer = setTimeout(run, delay);
        }
        timer = setTimeout(run, firstDelay);
        return () => { stopped = true; clearTimeout(timer); };
    }
    root.RefreshControl = {singleFlight, schedule};
    if (typeof module !== 'undefined' && module.exports) module.exports = root.RefreshControl;
})(typeof window !== 'undefined' ? window : globalThis);
