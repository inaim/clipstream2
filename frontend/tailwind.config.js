/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'cyber-purple': '#7B2CBF',
        'sunset-orange': '#FF6B35',
        'neon-yellow': '#FFD60A',
        'mint-green': '#06FFA5',
        'sky-blue': '#5BC0EB',
        'electric-violet': '#9D4EDD',
      },
      backgroundImage: {
        'gradient-genz': 'linear-gradient(135deg, #7B2CBF 0%, #9D4EDD 100%)',
        'gradient-cyber': 'linear-gradient(135deg, #7B2CBF 0%, #5BC0EB 100%)',
        'gradient-sunset': 'linear-gradient(135deg, #FF6B35 0%, #FFD60A 100%)',
        'gradient-fresh': 'linear-gradient(135deg, #06FFA5 0%, #5BC0EB 100%)',
        'gradient-vibrant': 'linear-gradient(135deg, #9D4EDD 0%, #FFD60A 100%)',
      },
    },
  },
  plugins: [],
};
