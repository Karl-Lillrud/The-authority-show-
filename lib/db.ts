import { MongoClient } from 'mongodb';

// MongoDB Configuration
const MONGODB_URI = process.env.MONGODB_URI || "mongodb://localhost:27017";
const DATABASE_NAME = "Podmanager";


// Initialize MongoDB Client
const client = new MongoClient(MONGODB_URI, {
  // No need for `useNewUrlParser` and `useUnifiedTopology`
});

async function connectToDatabase() {
  try {
    await client.connect();
    console.log('MongoDB connected successfully');
    const database = client.db(DATABASE_NAME);
    return database;
  } catch (error) {
    console.error('MongoDB connection error:', error);
    throw error;
  }
}

export default connectToDatabase;
