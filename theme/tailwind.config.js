module.exports = {
    content: [
      './templates/**/*.html',
      './theme/static/src/**/*.js',
      // مسیرهای دیگر به فایل‌های HTML/JS شما
    ],
    theme: {
      extend: {},
    },
    plugins: [
      require('daisyui')
    ],
  }