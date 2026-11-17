// Angel One SmartAPI Configuration
//
// SECURITY: NEVER hardcode real credentials in this file — it ships to browsers.
// Provide values at runtime via `window.API_CONFIG_OVERRIDE`, e.g. injected by
// your server into the page before this script, or a local untracked file:
//   window.API_CONFIG_OVERRIDE = {
//     API_KEY: '...', SECRET_KEY: '...', CLIENT_CODE: '...',
//     PASSWORD: '...', TOTP_SECRET: '...', AUTO_LOGIN: true
//   };
const API_CONFIG = {
    API_KEY: '',
    SECRET_KEY: '',
    CLIENT_CODE: '',
    PASSWORD: '',
    TOTP_SECRET: '',
    AUTO_LOGIN: false // set true only when credentials are injected at runtime
};

if (typeof window !== 'undefined' && window.API_CONFIG_OVERRIDE) {
    Object.assign(API_CONFIG, window.API_CONFIG_OVERRIDE);
}

if (typeof window !== 'undefined') {
    window.API_CONFIG = API_CONFIG;
}
if (typeof module !== 'undefined') {
    module.exports = API_CONFIG;
}
