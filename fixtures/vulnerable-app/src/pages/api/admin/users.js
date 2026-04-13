// Admin route with no authentication
export default async function handler(req, res) {
  // BAD: No auth check — anyone can access admin endpoints
  if (req.method === 'GET') {
    const users = await db.collection('users').find({}).toArray();
    return res.json(users);
  }

  if (req.method === 'DELETE') {
    const { userId } = req.body;
    await db.collection('users').deleteOne({ _id: userId });
    return res.json({ message: 'User deleted' });
  }

  res.status(405).json({ error: 'Method not allowed' });
}
