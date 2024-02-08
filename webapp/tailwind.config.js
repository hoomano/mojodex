const screens = {
  xs: "0px", // phone
  sm: "576px", // phone rotated
  md: "768px", // tablet
  lg: "992px", // tablet rotated / small desktop
  xl: "1200px", // big desktop
  xxl: "1400px",
  "3xl": "1800px",
};

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./modules/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      screens: screens,
      width: screens,
      colors: {
        primary: {
          main: "#3763E7",
          dark: "#1D52BF",
          light: "#86ADFF",
        },
        gray: {
          light: "#F3F4F6", // Grey 1
          lighter: "#879BB7", // Grey 2
          medium: "#E2E6ED",
          dark: "#4C5563",
          darker: "#1F2937", // Grey 4
        },
        white: "#fff",
        black: "#000",
        error: {
          primary: "#DC3545",
          secondary: "#F5EAC6",
        },
        warning: {
          primary: "#FFC107",
          secondary: "rgba(255, 193, 7, 0.2)",
        },
        success: {
          primary: "#28A745",
          secondary: "#CAE5D3",
        },
        error: {
          DEFAULT: "RED",
        },
        background: {
          textbox: "rgba(0, 0, 0, 0.02)",
        },
      },
      fontSize: {
        h1: "40px",
        h2: "32px",
        h3: "28px",
        h4: "24px",
        h5: "20px",
        h6: "16px",
        subtitle1: [
          "12px",
          {
            fontWeight: "400",
            lineHeight: "16px",
          },
        ],
        subtitle2: [
          "12px",
          {
            fontWeight: "600",
            lineHeight: "16px",
          },
        ],
        subtitle3: [
          "14px",
          {
            fontWeight: "400",
            lineHeight: "20px",
          },
        ],
        subtitle4: [
          "14px",
          {
            fontWeight: "600",
            lineHeight: "20px",
          },
        ],
        subtitle5: [
          "16px",
          {
            fontWeight: "400",
            lineHeight: "20px",
          },
        ],
        subtitle6: [
          "16px",
          {
            fontWeight: "600",
            lineHeight: "20px",
          },
        ],
        subtitle7: [
          "18px",
          {
            fontWeight: "400",
            lineHeight: "24px",
          },
        ],
        subtitle8: [
          "18px",
          {
            fontWeight: "600",
            lineHeight: "24px",
          },
        ],
      },
      boxShadow: {
        small: "0px 1px 4px rgba(0, 0, 0, 0.1)",
        regular: "0px 4px 10px rgba(0, 0, 0, 0.12)",
        larger: "0px 8px 35px rgba(0, 0, 0, 0.16)",
      },
      animation: {
        "fade-in": "fade-in 0.5s linear forwards",
        marquee: "marquee var(--marquee-duration) linear infinite",
        "spin-slow": "spin 4s linear infinite",
        "spin-slower": "spin 6s linear infinite",
        "spin-reverse": "spin-reverse 1s linear infinite",
        "spin-reverse-slow": "spin-reverse 4s linear infinite",
        "spin-reverse-slower": "spin-reverse 6s linear infinite",
      },
      borderRadius: {
        "4xl": "2rem",
        "5xl": "2.5rem",
      },
      keyframes: {
        "fade-in": {
          from: {
            opacity: "0",
          },
          to: {
            opacity: "1",
          },
        },
        marquee: {
          "100%": {
            transform: "translateY(-50%)",
          },
        },
        "spin-reverse": {
          to: {
            transform: "rotate(-360deg)",
          },
        },
      },
      maxWidth: {
        "2xl": "40rem",
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/aspect-ratio"),
    require("@tailwindcss/typography"),
  ],
};
