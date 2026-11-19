/* Market timestamps: explicit offsets and Unix epochs are instants; naive
   Breeze candle strings are interpreted as exchange-local Asia/Kolkata time. */
(function (root) {
    'use strict';
    const months = {Jan:'01', Feb:'02', Mar:'03', Apr:'04', May:'05', Jun:'06',
                    Jul:'07', Aug:'08', Sep:'09', Oct:'10', Nov:'11', Dec:'12'};
    function toEpochSeconds(value) {
        if (value === null || value === undefined || value === '') return null;
        if (typeof value === 'number' || (typeof value === 'string' && /^\d{9,13}$/.test(value.trim()))) {
            const number = Number(value);
            return Number.isFinite(number) ? Math.floor(number >= 1e11 ? number / 1000 : number) : null;
        }
        if (typeof value !== 'string') return null;
        let clean = value.trim();
        const broker = /^(\d{1,2})-([A-Za-z]{3})-(\d{4})\s+(\d{2}:\d{2}:\d{2})$/.exec(clean);
        if (broker && months[broker[2]]) {
            clean = `${broker[3]}-${months[broker[2]]}-${broker[1].padStart(2, '0')}T${broker[4]}`;
        } else {
            clean = clean.replace(' ', 'T');
        }
        if (/^\d{4}-\d{2}-\d{2}$/.test(clean)) clean += 'T00:00:00';
        if (!/(?:Z|[+-]\d{2}:?\d{2})$/i.test(clean)) clean += '+05:30';
        const ms = Date.parse(clean);
        return Number.isFinite(ms) ? Math.floor(ms / 1000) : null;
    }
    function formatChennaiTime(value) {
        const seconds = toEpochSeconds(value);
        if (seconds === null) return 'Time unavailable';
        return new Intl.DateTimeFormat('en-GB', {
            timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric',
            hour: '2-digit', minute: '2-digit', hourCycle: 'h23'
        }).format(new Date(seconds * 1000)) + ' IST';
    }
    function formatChartTick(value, tickType) {
        if (typeof value !== 'number') return null; // let the chart format business-day objects
        const options = tickType === 0 ? {year: 'numeric'} :
                        tickType === 1 ? {month: 'short'} :
                        tickType === 2 ? {day: '2-digit', month: 'short'} :
                        {hour: '2-digit', minute: '2-digit', hourCycle: 'h23'};
        return new Intl.DateTimeFormat('en-GB', {timeZone: 'Asia/Kolkata', ...options}).format(new Date(value * 1000));
    }
    root.MarketTime = {toEpochSeconds, formatChennaiTime, formatChartTick};
    if (typeof module !== 'undefined' && module.exports) module.exports = root.MarketTime;
})(typeof window !== 'undefined' ? window : globalThis);
