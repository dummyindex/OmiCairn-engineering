export default {
  plugins: [
    '@umijs/plugins/dist/initial-state',
    '@umijs/plugins/dist/model',
    '@umijs/plugins/dist/request',
    '@umijs/plugins/dist/antd',
  ],
  antd: {},
  initialState: {},
  model: {},
  request: {
    dataField: '',
  },
  define: {
    'process.env.UMI_APP_API_URL_PREFIX': process.env.UMI_APP_API_URL_PREFIX || '',
    'process.env.UMI_APP_SERVICE_CLOUD': process.env.UMI_APP_SERVICE_CLOUD || '',
    'process.env.UMI_APP_STATIC_RESOURCE_BASE_URL': process.env.UMI_APP_STATIC_RESOURCE_BASE_URL || '',
    'process.env.UMI_APP_DEMO_FUNCTION_BLOCK_URL': process.env.UMI_APP_DEMO_FUNCTION_BLOCK_URL || '',
    'process.env.UMI_APP_SERVER_TIMEZONE': process.env.UMI_APP_SERVER_TIMEZONE || '',
  },
  links: [
    {
      rel: 'icon',
      type: 'image/svg+xml',
      href: '/static/favicon.svg',
    },
  ],
  // hash: true,
  routes: [
    { path: '/', redirect: '/login/byPassword' },
    {
      path: '/index',
      redirect: '/login/byPassword',
    },
    {
      path: '/index.html',
      redirect: '/login/byPassword',
    },
    {
      path: '/login',
      component: '@/pages/login/index',
      routes: [
        {
          path: '/login/byPassword',
          component: '@/pages/login/byPassword',
        },
        {
          path: '/login/byUserName',
          component: '@/pages/login/byUserName',
        },
      ],
    },
    {
      path: '/management',
      component: '@/pages/management/index',
      routes: [
        {
          path: '/management/homeMain',
          component: '@/pages/management/homeMain',
        },
        {
          path: '/management/data',
          component: '@/pages/management/dataSource',
        },
        {
          path: '/management/snapshot',
          component: '@/pages/management/visualizionGallery',
        },
        {
          path: '/management/sharedData',
          component: '@/pages/management/sharedList',
        },
        {
          path: '/management/gptPage',
          component: '@/pages/management/gptPage',
        },
        {
          path: '/management/allApps',
          component: '@/pages/management/allApps',
        },
        {
          path: '/management/myLibraries',
          component: '@/pages/management/myLibraries',
        },
      ],
    },
    {
      path: '/controlCenter/userCenter',
      component: '@/pages/controlCenter/userCenter',
      routes: [
        {
          path: '/controlCenter/userCenter/nameSetting',
          component: '@/pages/controlCenter/userCenter/nameSetting',
        },
        {
          path: '/controlCenter/userCenter/apiKey',
          component: '@/pages/controlCenter/userCenter/apiKey',
        },
      ],
    },
    {
      path: '/controlCenter/messageCenter',
      component: '@/pages/controlCenter/messageCenter',
      routes: [
        {
          path: '/controlCenter/messageCenter/serviceBulletin',
          component: '@/pages/controlCenter/messageCenter/serviceBulletin',
        },
        {
          path: '/controlCenter/messageCenter/collaborationNotification',
          component: '@/pages/controlCenter/messageCenter/collaborationNotification',
        },
        {
          path: '/controlCenter/messageCenter/analysisProgressNotification',
          component: '@/pages/controlCenter/messageCenter/analysisProgressNotification',
        },
      ],
    },
    {
      path: '/analysisPanel',
      component: '@/pages/analysisPanel/index',
      routes: [
        {
          path: '/analysisPanel/flowPanel',
          component: '@/pages/analysisPanel/flowPanel',
        },
        {
          path: '/analysisPanel/workflowReportPanel',
          component: '@/pages/analysisPanel/workflowReportPanel',
        },
      ],
    },
    {
      path: '/functionBlock',
      component: '@/pages/functionBlock/index',
    },
  ],
  npmClient: 'pnpm',
  jsMinifier: 'terser',
  chainWebpack: function (config, { webpack }) {
    // Configure JS output to be served as application/javascript
    config.module.rule('js').test(/\.js$/).use('babel-loader').loader('babel-loader').end();

    config.output
      .filename('[name].[hash:8].js') // Output filename pattern
      .chunkFilename('[name].[hash:8].async.js'); // Async chunk filename pattern
  },
};
