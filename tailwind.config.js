/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./**/*.html",
    "./static/js/**/*.js",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2c3e50',    // Amity navy
        secondary: '#e74c3c',  // Amity red
        accent: '#3498db',     // Amity blue
      }
    },
  },
  plugins: [],
}
