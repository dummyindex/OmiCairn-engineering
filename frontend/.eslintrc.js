module.exports = {
  extends: [require.resolve('@umijs/fabric/dist/eslint')],
  plugins: ['react'],

  // Custom global variables
  globals: {
    REACT_APP_ENV: true,
    REACT_APP_API_URL: true,
  },
  // Custom rules based on personal preference
  rules: {
    'no-console': 'off',
    'react-hooks/exhaustive-deps': 'off', // react-hooks dependency check
    'no-empty': 'off', // allow empty catch{} blocks
    '@typescript-eslint/no-shadow': ['off'], // disallow variable names in the current scope that shadow parent-scope variables
  },
};
