const Dotenv = require("dotenv-webpack");

module.exports = {
  // ...existing configuration...
  plugins: [
    new Dotenv({
      path: "./.env", // Path to your .env file
      safe: true // Load '.env.example' to verify the '.env' variables are all set. Can also be a string to a different file.
    })
    // ...other plugins...
  ]
};
