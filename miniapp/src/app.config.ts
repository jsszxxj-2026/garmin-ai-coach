export default defineAppConfig({
  pages: ['pages/home/index', 'pages/history/index', 'pages/analysis/index', 'pages/chat/index'],
  tabBar: {
    list: [
      {
        pagePath: 'pages/home/index',
        text: '首页',
      },
      {
        pagePath: 'pages/history/index',
        text: '历史',
      },
    ],
  },
  window: {
    navigationBarTitleText: 'PaceMind',
  },
})
