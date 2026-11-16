// Lightweight TOTP Generator (RFC 6238)
const TOTP = {
    base32Decode: function (base32) {
        const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
        let bits = '';
        let output = [];
        const cleanBase32 = base32.replace(/\s/g, '');

        for (let i = 0; i < cleanBase32.length; i++) {
            const val = alphabet.indexOf(cleanBase32.charAt(i).toUpperCase());
            if (val >= 0) {
                bits += val.toString(2).padStart(5, '0');
            }
        }

        for (let i = 0; i + 8 <= bits.length; i += 8) {
            output.push(parseInt(bits.substr(i, 8), 2));
        }
        return new Uint8Array(output);
    },

    generate: async function (secret) {
        try {
            const key = this.base32Decode(secret);
            const epoch = Math.floor(Date.now() / 1000);
            const time = Math.floor(epoch / 30);

            const timeBuffer = new ArrayBuffer(8);
            const timeView = new DataView(timeBuffer);
            timeView.setUint32(4, time);

            const cryptoKey = await window.crypto.subtle.importKey(
                "raw", key, { name: "HMAC", hash: "SHA-1" }, false, ["sign"]
            );

            const signature = await window.crypto.subtle.sign("HMAC", cryptoKey, timeBuffer);
            const hmac = new Uint8Array(signature);

            const offset = hmac[hmac.length - 1] & 0xf;
            const code = ((hmac[offset] & 0x7f) << 24) |
                ((hmac[offset + 1] & 0xff) << 16) |
                ((hmac[offset + 2] & 0xff) << 8) |
                (hmac[offset + 3] & 0xff);

            return (code % 1000000).toString().padStart(6, '0');
        } catch (e) {
            console.error('TOTP Generation Error:', e);
            return null;
        }
    }
};

window.TOTP = TOTP;
