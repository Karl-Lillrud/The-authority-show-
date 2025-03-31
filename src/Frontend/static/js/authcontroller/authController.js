const crypto = require('crypto');
const mailer = require('../../../backend/utils/mailer'); // Adjusted path for mail utility

// Generate and send a verification code
exports.sendVerificationCode = async (req, res) => {
    const { email } = req.body;

    // Generate a 6-digit numeric code
    const verificationCode = Math.floor(100000 + Math.random() * 900000).toString();

    // Store the code temporarily (e.g., in-memory or database)
    await storeVerificationCode(email, verificationCode);

    // Send the code via email
    await mailer.sendMail({
        to: email,
        subject: 'Your Verification Code',
        text: `Your verification code is: ${verificationCode}`
    });

    res.status(200).send({ message: 'Verification code sent to your email.' });
};

// Validate the verification code during login
exports.loginWithVerificationCode = async (req, res) => {
    const { email, code } = req.body;

    // Validate the code
    const isValid = await validateVerificationCode(email, code);
    if (!isValid) {
        return res.status(400).send({ message: 'Invalid verification code.' });
    }

    // Proceed with login (e.g., generate a token)
    const token = generateAuthToken(email);
    res.status(200).send({ token });
};

// Helper functions
async function storeVerificationCode(email, code) {
    // Store the code in a database or in-memory store with an expiration time
    // ...implementation...
}

async function validateVerificationCode(email, code) {
    // Check if the code matches the stored code and is not expired
    // ...implementation...
}

function generateAuthToken(email) {
    // Generate a JWT or similar token for authenticated sessions
    // ...implementation...
}
