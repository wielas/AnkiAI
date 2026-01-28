/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                jungle: {
                    DEFAULT: '#003310',
                    light: '#004d18',
                    dark: '#001a08',
                },
                lime: {
                    DEFAULT: '#c7ef4e',
                    light: '#d4f371',
                    dark: '#b0d632',
                },
            },
            fontFamily: {
                serif: ['Lora', 'serif'],
                sans: ['Inter', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
