import type { UserConfigExport } from '@tarojs/cli'
import { defineConfig } from '@tarojs/cli'

import dev from './dev'
import prod from './prod'

export default defineConfig(async () => {
  const config: UserConfigExport = {
    projectName: 'miniapp',
    date: '2026-02-13',
    designWidth: 750,
    deviceRatio: {
      640: 2.34 / 2,
      750: 1,
      828: 1.81 / 2,
    },
    sourceRoot: 'src',
    outputRoot: 'dist',
    plugins: ['@tarojs/plugin-platform-weapp'],
    framework: 'react',
    compiler: 'webpack5',
    mini: {},
    h5: {},
  }

  const isDev = process.env.NODE_ENV === 'development'

  if (isDev) {
    return {
      ...config,
      ...dev,
    }
  }

  return {
    ...config,
    ...prod,
  }
})
