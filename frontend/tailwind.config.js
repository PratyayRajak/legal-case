/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        judiciary: {
          50: "#f0f4f8",
          100: "#d9e2ec",
          500: "#243b53",
          800: "#102a43",
          900: "#0b1b2b",
        },
        gold: {
          500: "#b45309",
          600: "#92400e",
        },
      },
    },
  },
  plugins: [],
};
