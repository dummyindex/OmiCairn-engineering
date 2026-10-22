const { configUmiAlias, createConfig } = require('umi/test');

module.exports = async () => {
  const config = await configUmiAlias({
    ...createConfig({
      target: 'browser',
      jsTransformer: 'esbuild',
      jsTransformerOpts: { jsx: 'automatic' },
    }),
  });

  return config;
};
