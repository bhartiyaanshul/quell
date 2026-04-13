// Plain-text password storage + weak JWT + hardcoded secrets
const express = require('express');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');
const router = express.Router();

// BAD: Hardcoded JWT secret, and it's too short
const JWT_SECRET = 'mysecret';

// BAD: Password stored as MD5 hash (weak crypto)
router.post('/register', async (req, res) => {
  const { email, password } = req.body;
  const hashedPassword = crypto.createHash('md5').update(password).digest('hex');

  await db.collection('users').insertOne({
    email,
    password: hashedPassword,
    createdAt: new Date()
  });

  res.json({ message: 'User created' });
});

// BAD: Plain-text password comparison
router.post('/login', async (req, res) => {
  const { email, password } = req.body;
  const user = await db.collection('users').findOne({ email });

  // Storing and comparing passwords without any hashing
  if (user && user.password === password) {
    const token = jwt.sign({ userId: user._id }, JWT_SECRET, { expiresIn: '30d' });
    res.json({ token });
  } else {
    res.status(401).json({ error: 'Invalid credentials' });
  }
});

// BAD: eval() with user input
router.post('/calculate', (req, res) => {
  const { expression } = req.body;
  const result = eval(expression);
  res.json({ result });
});

// BAD: Function constructor with user input
router.post('/transform', (req, res) => {
  const { code } = req.body;
  const fn = new Function('data', code);
  const result = fn(req.body.data);
  res.json({ result });
});

module.exports = router;
