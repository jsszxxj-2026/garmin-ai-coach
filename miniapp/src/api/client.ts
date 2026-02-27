import Taro from '@tarojs/taro'

export const getApiBase = () => process.env.TARO_APP_API_BASE_URL || ''

const normalizeUrl = (base: string, path: string) => {
  if (!base) {
    return path
  }
  const trimmedBase = base.replace(/\/+$/, '')
  const trimmedPath = path.replace(/^\/+/, '')
  return `${trimmedBase}/${trimmedPath}`
}

export const apiClient = {
  get: async <T,>(path: string, params?: Record<string, unknown>): Promise<T> => {
    const response = await Taro.request<T>({
      url: normalizeUrl(getApiBase(), path),
      method: 'GET',
      data: params,
      timeout: 15000,
    })
    return response.data as T
  },
  post: async <T,>(path: string, data?: Record<string, unknown>): Promise<T> => {
    const response = await Taro.request<T>({
      url: normalizeUrl(getApiBase(), path),
      method: 'POST',
      data,
      timeout: 15000,
    })
    return response.data as T
  },
}
