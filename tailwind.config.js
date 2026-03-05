// tailwind.config.js
module.exports = {
  content: [
    './templates/**/*.html',
    './modulo_gestion_qr/templates/**/*.html',
    './static/src/**/*.js',
    './node_modules/flowbite/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        whatsapp: '#25D366',
        whatsappDark: '#128C7E',
      },
    },
  },
  plugins: [
    require('flowbite/plugin'),
  ],
}
