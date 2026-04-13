// CORS misconfiguration + open redirect
const express = require('express');
const app = express();

// BAD: CORS wildcard with credentials
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  next();
});

// BAD: Insecure cookie settings
app.post('/login', (req, res) => {
  const token = generateToken(req.body);
  res.cookie('session', token, {
    httpOnly: false,
    secure: false,
  });
  res.json({ success: true });
});

// BAD: Open redirect — redirects to any user-supplied URL
app.get('/redirect', (req, res) => {
  const { url } = req.query;
  res.redirect(url);
});

// BAD: Another open redirect pattern
app.get('/goto', (req, res) => {
  const destination = req.query.dest;
  return res.redirect(302, destination);
});

app.listen(3000);
