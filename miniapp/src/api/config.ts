// API 配置管理
// 根据微信运行环境自动选择后端地址

// 基础配置 - 这些值会被环境变量覆盖
const DEFAULT_CONFIG = {
  // 本地开发地址
  development: 'http://127.0.0.1:8000',
  // 服务器地址（生产环境）
  production: 'http://150.158.2.190:8000',
  // 备用服务器地址（如果有）
  // backup: 'http://43.134.54.137:8000'
}

/**
 * 获取 API 基础地址
 * 优先级：
 * 1. 环境变量 TARO_APP_API_BASE_URL
 * 2. 根据微信环境判断
 * 3. 默认配置
 */
export const getApiBase = (): string => {
  // 1. 优先使用环境变量（由 Taro 构建时注入）
  const envUrl = process.env.TARO_APP_API_BASE_URL
  if (envUrl) {
    console.log('[API] 使用环境变量配置:', envUrl)
    return envUrl
  }

  // 2. 如果没有环境变量，返回空字符串（使用相对路径或后续配置）
  console.warn('[API] 未配置 API 基础地址')
  return ''
}

/**
 * 判断当前运行环境
 */
export const getEnvironment = (): 'development' | 'production' | 'unknown' => {
  // 微信小程序环境判断
  if (typeof wx !== 'undefined') {
    try {
      // 通过账号信息判断
      const accountInfo = wx.getAccountInfoSync()
      const env = accountInfo.miniProgram.envVersion
      
      // envVersion 可能值：
      // 'develop' - 开发版（开发者工具预览）
      // 'trial' - 体验版
      // 'release' - 正式版
      
      if (env === 'develop') {
        return 'development'
      } else if (env === 'trial' || env === 'release') {
        return 'production'
      }
    } catch (e) {
      console.warn('[API] 无法获取微信环境信息')
    }
  }
  
  // 根据 NODE_ENV 判断
  if (process.env.NODE_ENV === 'production') {
    return 'production'
  }
  
  return 'development'
}

/**
 * 手动切换 API 地址（调试用）
 */
export const switchApiBase = (type: 'local' | 'server'): string => {
  const urls = {
    local: DEFAULT_CONFIG.development,
    server: DEFAULT_CONFIG.production
  }
  
  const newUrl = urls[type]
  console.log(`[API] 手动切换到${type === 'local' ? '本地' : '服务器'}:`, newUrl)
  
  // 可以在这里添加持久化逻辑（如写入 storage）
  return newUrl
}

// 导出配置供其他模块使用
export default {
  getApiBase,
  getEnvironment,
  switchApiBase,
  DEFAULT_CONFIG
}
