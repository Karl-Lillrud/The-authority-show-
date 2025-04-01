import express from "express";
import { signin, sendVerificationCode, loginWithVerificationCode } from "./authService.js"; // Example service file

const router = express.Router();

// Sign in route
router.post("/signin", async (req, res) => {
  try {
    const { email, password } = req.body;
    const redirectUrl = await signin(email, password);
    res.json({ redirect_url: redirectUrl });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Send verification code route
router.post("/send-verification-code", async (req, res) => {
  try {
    const { email } = req.body;
    await sendVerificationCode(email);
    res.status(200).send("Verification code sent.");
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Login with verification code route
router.post("/login-with-code", async (req, res) => {
  try {
    const { email, code } = req.body;
    const redirectUrl = await loginWithVerificationCode(email, code);
    res.json({ redirect_url: redirectUrl });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

export default router;
