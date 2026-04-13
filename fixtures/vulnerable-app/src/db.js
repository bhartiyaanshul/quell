// SQL injection vulnerability — user input directly concatenated into query
const express = require('express');
const mysql = require('mysql');
const router = express.Router();

const db = mysql.createConnection({
  host: 'localhost',
  user: 'root',
  password: 'password123',
  database: 'myapp'
});

// BAD: SQL injection via string concatenation
router.get('/users', (req, res) => {
  const userId = req.query.id;
  const query = "SELECT * FROM users WHERE id = '" + userId + "'";
  db.query(query, (err, results) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(results);
  });
});

// BAD: SQL injection via template literal
router.post('/search', (req, res) => {
  const searchTerm = req.body.term;
  db.query(`SELECT * FROM products WHERE name LIKE '%${searchTerm}%'`, (err, results) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(results);
  });
});

module.exports = router;
