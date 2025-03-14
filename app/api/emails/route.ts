
import { NextApiRequest, NextApiResponse } from 'next';

const emails = [
  { id: 1, subject: "Welcome to the newsletter", body: "Hello, welcome!" },
  { id: 2, subject: "New article", body: "Check out our latest post!" }
];

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    res.status(200).json(emails);
  } else {
    res.status(405).json({ message: 'Method Not Allowed' });
  }
}
