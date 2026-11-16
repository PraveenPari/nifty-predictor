// Angel One SmartAPI Integration Module
// Documentation: https://smartapi.angelone.in/

const AngelOneAPI = {
    // Configuration - User needs to fill these
    config: {
        apiKey: '', // Your SmartAPI Key
        clientCode: '', // Your Angel One Client ID
        password: '', // Your trading password
        totp: '', // TOTP secret or current TOTP
        isConfigured: false
    },

    // API Endpoints
    endpoints: {
        base: 'https://apiconnect.angelone.in',
        login: '/rest/auth/angelbroking/user/v1/loginByPassword',
        generateSession: '/rest/auth/angelbroking/user/v1/generateSession',
        profile: '/rest/secure/angelbroking/user/v1/getProfile',
        ltp: '/rest/secure/angelbroking/order/v1/getLtpData',
        marketData: '/rest/secure/angelbroking/market/v1/quote',
        candleData: '/rest/secure/angelbroking/historical/v1/getCandleData',
        optionChain: '/rest/secure/angelbroking/marketData/v1/optionGreek'
    },

    // Proxies to try in order
    proxies: [
        '', // Direct
        'https://corsproxy.io/?',
        'http://localhost:3001/angel-api', // Local Proxy (Fail-safe)
        'https://api.allorigins.win/raw?url=',
        'https://api.codetabs.com/v1/proxy?quest='
    ],

    // Smart Fetch with Failover
    smartFetch: async function (endpoint, options) {
        let lastError;

        for (const proxy of this.proxies) {
            try {
                // Construct URL: If proxy is empty, use direct. Else prepend proxy.
                const targetUrl = this.endpoints.base + endpoint;
                const finalUrl = proxy ? proxy + encodeURIComponent(targetUrl) : targetUrl;

                console.log(`Trying connection via: ${proxy ? 'Proxy' : 'Direct'}...`);

                const response = await fetch(finalUrl, options);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();
                return data; // Success!

            } catch (e) {
                console.warn(`Failed via ${proxy || 'Direct'}:`, e.message);
                lastError = e;
                // Continue to next proxy
            }
        }
        throw lastError; // All failed
    },

    // Symbol tokens for Nifty and Bank Nifty
    tokens: {
        nifty: '99926000',      // NIFTY 50 Index
        banknifty: '99926009',  // BANK NIFTY Index
        niftyFut: '35001',      // NIFTY Current Month Future
        bankniftyFut: '35002'   // BANKNIFTY Current Month Future
    },

    // Exchange codes
    exchanges: {
        NSE: 'NSE',
        NFO: 'NFO',
        BSE: 'BSE',
        MCX: 'MCX'
    },

    // Session data
    session: {
        jwtToken: null,
        refreshToken: null,
        feedToken: null,
        isLoggedIn: false
    },

    // Initialize with credentials
    initialize: function (apiKey, clientCode, password, totp) {
        this.config.apiKey = apiKey;
        this.config.clientCode = clientCode;
        this.config.password = password;
        this.config.totp = totp;
        this.config.isConfigured = true;
        console.log('Angel One API configured');
    },

    // Login and get session
    login: async function () {
        if (!this.config.isConfigured) {
            throw new Error('API not configured. Please call initialize() first.');
        }

        const payload = {
            clientcode: this.config.clientCode,
            password: this.config.password,
            totp: this.config.totp
        };

        try {
            const data = await this.smartFetch(this.endpoints.login, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-UserType': 'USER',
                    'X-SourceID': 'WEB',
                    'X-ClientLocalIP': '192.168.1.1',
                    'X-ClientPublicIP': '10.10.10.10',
                    'X-MACAddress': 'MAC_ADDRESS',
                    'X-PrivateKey': this.config.apiKey
                },
                body: JSON.stringify(payload)
            });

            if (data.status && data.data) {
                this.session.jwtToken = data.data.jwtToken;
                this.session.refreshToken = data.data.refreshToken;
                this.session.feedToken = data.data.feedToken;
                this.session.isLoggedIn = true;
                console.log('Angel One Login successful');
                return data;
            } else {
                throw new Error(data.message || 'Login failed');
            }
        } catch (error) {
            console.error('Angel One Login Final Failure:', error);
            throw error;
        }
    },

    // Get headers for authenticated requests
    getAuthHeaders: function () {
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-UserType': 'USER',
            'X-SourceID': 'WEB',
            'X-ClientLocalIP': '192.168.1.1',
            'X-ClientPublicIP': '10.10.10.10',
            'X-MACAddress': 'MAC_ADDRESS',
            'X-PrivateKey': this.config.apiKey,
            'Authorization': 'Bearer ' + this.session.jwtToken
        };
    },

    // Get LTP (Last Traded Price)
    getLTP: async function (exchange, symbolToken) {
        if (!this.session.isLoggedIn) {
            throw new Error('Not logged in');
        }

        const payload = {
            exchange: exchange,
            symboltoken: symbolToken,
            tradingsymbol: ''
        };

        try {
            const data = await this.smartFetch(this.endpoints.ltp, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify(payload)
            });

            return data.data;
        } catch (error) {
            console.error('Get LTP Error:', error);
            throw error;
        }
    },

    // Get Market Quote (full data)
    getMarketQuote: async function (exchange, symbolToken) {
        if (!this.session.isLoggedIn) {
            throw new Error('Not logged in');
        }

        const payload = {
            mode: 'FULL',
            exchangeTokens: {
                [exchange]: [symbolToken]
            }
        };

        try {
            const data = await this.smartFetch(this.endpoints.marketData, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify(payload)
            });

            return data.data;
        } catch (error) {
            console.error('Get Market Quote Error:', error);
            throw error;
        }
    },

    // Get Historical/Candle Data
    getCandleData: async function (exchange, symbolToken, interval, fromDate, toDate) {
        if (!this.session.isLoggedIn) {
            throw new Error('Not logged in');
        }

        const payload = {
            exchange: exchange,
            symboltoken: symbolToken,
            interval: interval,
            fromdate: fromDate, // Format: YYYY-MM-DD HH:mm
            todate: toDate       // Format: YYYY-MM-DD HH:mm
        };

        try {
            const data = await this.smartFetch(this.endpoints.candleData, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify(payload)
            });

            return data.data;
        } catch (error) {
            console.error('Get Candle Data Error:', error);
            throw error;
        }
    },

    // Get Option Greeks (for option chain like data)
    getOptionGreeks: async function (name, expiryDate) {
        if (!this.session.isLoggedIn) {
            throw new Error('Not logged in');
        }

        const payload = {
            name: name, // NIFTY or BANKNIFTY
            expirydate: expiryDate // Format: DDMMMYYYY (e.g., 02JAN2025)
        };

        try {
            const data = await this.smartFetch(this.endpoints.optionChain, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify(payload)
            });

            return data.data;
        } catch (error) {
            console.error('Get Option Greeks Error:', error);
            throw error;
        }
    },

    // Helper: Get current Nifty data
    getNiftyData: async function () {
        return await this.getMarketQuote('NSE', this.tokens.nifty);
    },

    // Helper: Get current Bank Nifty data
    getBankNiftyData: async function () {
        return await this.getMarketQuote('NSE', this.tokens.banknifty);
    },

    // Helper: Get Nifty historical candles
    getNiftyCandleData: async function (interval = 'FIVE_MINUTE') {
        let now = new Date();
        // AUTO-CORRECT: If system time is 2026 (User env), force it to 2025 for API compatibility
        if (now.getFullYear() === 2026) {
            now.setFullYear(2025);
        }

        const fromDate = new Date(now);
        fromDate.setHours(9, 15, 0);

        const toDateStr = now.toISOString().slice(0, 16).replace('T', ' ');
        const fromDateStr = fromDate.toISOString().slice(0, 16).replace('T', ' ');

        return await this.getCandleData('NSE', this.tokens.nifty, interval, fromDateStr, toDateStr);
    },

    // Helper: Get Bank Nifty historical candles
    getBankNiftyCandleData: async function (interval = 'FIVE_MINUTE') {
        let now = new Date();
        // AUTO-CORRECT: If system time is 2026, force it to 2025
        if (now.getFullYear() === 2026) {
            now.setFullYear(2025);
        }

        const fromDate = new Date(now);
        fromDate.setHours(9, 15, 0);

        const toDateStr = now.toISOString().slice(0, 16).replace('T', ' ');
        const fromDateStr = fromDate.toISOString().slice(0, 16).replace('T', ' ');

        return await this.getCandleData('NSE', this.tokens.banknifty, interval, fromDateStr, toDateStr);
    },

    // Get next weekly expiry date
    getNextExpiry: function () {
        const now = new Date();
        const day = now.getDay();
        const daysUntilThursday = (4 - day + 7) % 7;
        const nextThursday = new Date(now);
        nextThursday.setDate(now.getDate() + (daysUntilThursday === 0 ? 7 : daysUntilThursday));

        const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
        const dd = String(nextThursday.getDate()).padStart(2, '0');
        const mmm = months[nextThursday.getMonth()];
        const yyyy = nextThursday.getFullYear();

        return `${dd}${mmm}${yyyy}`;
    },

    // Calculate ATM strike
    getATMStrike: function (spotPrice, strikeInterval = 50) {
        return Math.round(spotPrice / strikeInterval) * strikeInterval;
    },

    // Generate option symbol
    generateOptionSymbol: function (index, expiry, strike, optionType) {
        // Format: NIFTY02JAN2524200CE
        return `${index}${expiry}${strike}${optionType}`;
    }
};

// Helper function to check if API credentials are configured
function isAngelOneConfigured() {
    return AngelOneAPI.config.isConfigured;
}

// Helper function to configure Angel One API
function configureAngelOne(apiKey, clientCode, password, totp) {
    AngelOneAPI.initialize(apiKey, clientCode, password, totp);
}

// Export
window.AngelOneAPI = AngelOneAPI;
window.isAngelOneConfigured = isAngelOneConfigured;
window.configureAngelOne = configureAngelOne;
