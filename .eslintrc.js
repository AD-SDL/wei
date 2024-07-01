/* eslint-env node */
require('@rushstack/eslint-patch/modern-module-resolution')

module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:vue/vue3-essential',
    '@typescript-eslint/recommended',
    '@vue/eslint-config-prettier',
    '@vue/eslint-config-typescript'
  ]
}
