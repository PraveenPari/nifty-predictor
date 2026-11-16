// Standalone TOTP Test
// Since I can't easily require the browser js file, I'll paste the logic here to test.

const secret = '542WYM7GZSMT73TU625FXJAV2M';

const base32Decode = function (base32) {
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
    return Buffer.from(output);
};

// Simplified HMAC for Node
const crypto = require('crypto');

function generate(secret) {
    const key = base32Decode(secret);
    const epoch = Math.floor(Date.now() / 1000);
    const time = Math.floor(epoch / 30);
    const timeBuffer = Buffer.alloc(8);
    timeBuffer.writeUInt32BE(time, 4);

    const hmac = crypto.createHmac('sha1', key);
    hmac.update(timeBuffer);
    const signature = hmac.digest();

    const offset = signature[signature.length - 1] & 0xf;
    const code = ((signature[offset] & 0x7f) << 24) |
        ((signature[offset + 1] & 0xff) << 16) |
        ((signature[offset + 2] & 0xff) << 8) |
        (signature[offset + 3] & 0xff);

    console.log("Current TOTP: " + (code % 1000000).toString().padStart(6, '0'));
}

generate(secret);
