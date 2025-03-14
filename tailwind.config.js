module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./app/**/*.{js,ts,jsx,tsx}",  // Include your app folder as well
  ],
  theme: {
    extend: {
      colors: {
        'border': '#d1d5db',  // Define the color for border-border
        'background': '#f8f9fa',  // Define the background color for bg-background
        'foreground': '#1f2937',  // Define the foreground color for text-foreground
      },
    },
  },
  plugins: [],
}
