import Taro from '@tarojs/taro'

import type { WechatLoginResponse } from '../types'

const TOKEN_KEY = 'wechat_access_token'
const OPENID_KEY = 'wechat_openid'
const API_BASE = process.env.TARO_APP_API_BASE_URL || ''

let loginPromise: Promise<void> | null = null

const normalizeUrl = (base: string, path: string) => {
  if (!base) {
    return path
  }
  const trimmedBase = base.replace(/\/+$/, '')
  const trimmedPath = path.replace(/^\/+/, '')
  return `${trimmedBase}/${trimmedPath}`
}

export const getAccessToken = () => {
  if (typeof Taro.getStorageSync !== 'function') {
    return ''
  }
  const token = Taro.getStorageSync(TOKEN_KEY)
  return typeof token === 'string' ? token : ''
}

export const clearWechatSession = () => {
  if (typeof Taro.removeStorageSync === 'function') {
    Taro.removeStorageSync(TOKEN_KEY)
    Taro.removeStorageSync(OPENID_KEY)
  }
}

export const ensureWechatSession = async (): Promise<void> => {
  if (getAccessToken()) {
    return
  }

  if (loginPromise) {
    return loginPromise
  }

  loginPromise = (async () => {
    if (typeof Taro.login !== 'function') {
      return
    }
    const loginResult = await Taro.login()
    if (!loginResult.code) {
      throw new Error('微信登录失败: 未获取 code')
    }

    const response = await Taro.request<WechatLoginResponse>({
      url: normalizeUrl(API_BASE, '/api/wechat/login'),
      method: 'POST',
      data: { code: loginResult.code },
      timeout: 15000,
    })

    if (response.statusCode >= 400 || !response.data?.access_token) {
      const detail = (response.data as { detail?: string } | undefined)?.detail
      throw new Error(detail || '微信登录失败')
    }

    if (typeof Taro.setStorageSync === 'function') {
      Taro.setStorageSync(TOKEN_KEY, response.data.access_token)
      if (response.data.openid) {
        Taro.setStorageSync(OPENID_KEY, response.data.openid)
      }
    }
  })()

  try {
    await loginPromise
  } finally {
    loginPromise = null
  }
}
