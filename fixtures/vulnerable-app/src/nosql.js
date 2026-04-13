// NoSQL injection vulnerabilities
const express = require('express');
const router = express.Router();

// BAD: NoSQL injection — user input passed directly to MongoDB query
router.post('/login', async (req, res) => {
  const { username, password } = req.body;
  const user = await db.collection('users').findOne({
    username: username,
    password: password,
  });
  // An attacker can send { "username": { "$gt": "" }, "password": { "$gt": "" } }
  if (user) {
    res.json({ token: generateToken(user) });
  } else {
    res.status(401).json({ error: 'Invalid credentials' });
  }
});

// BAD: User-controlled query operators
router.get('/search', async (req, res) => {
  const filter = JSON.parse(req.query.filter);
  const results = await db.collection('products').find(filter).toArray();
  res.json(results);
});

module.exports = router;
