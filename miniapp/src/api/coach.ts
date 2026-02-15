import { apiClient } from './client'
import type {
  DailyAnalysisResponse,
  HomeSummaryResponse,
  WechatBindGarminRequest,
  WechatBindGarminResponse,
  WechatChatRequest,
  WechatChatResponse,
  WechatLoginRequest,
  WechatLoginResponse,
  WechatProfileResponse,
  WechatUnbindGarminRequest,
  WechatUnbindGarminResponse,
} from '../types'

export const getDailyAnalysis = async () => {
  return apiClient.get<DailyAnalysisResponse>('/api/coach/daily-analysis')
}

export const getDailyAnalysisByDate = async (date: string) => {
  return apiClient.get<DailyAnalysisResponse>('/api/coach/daily-analysis', {
    target_date: date,
  })
}

export const getHomeSummary = async (openid: string) => {
  return apiClient.get<HomeSummaryResponse>('/api/coach/home-summary', { openid })
}

export const loginWechat = async (payload: WechatLoginRequest) => {
  return apiClient.post<WechatLoginResponse>('/api/wechat/login', payload)
}

export const bindGarmin = async (payload: WechatBindGarminRequest) => {
  return apiClient.post<WechatBindGarminResponse>('/api/wechat/bind-garmin', payload)
}

export const unbindGarmin = async (payload: WechatUnbindGarminRequest) => {
  return apiClient.post<WechatUnbindGarminResponse>('/api/wechat/unbind-garmin', payload)
}

export const getProfile = async (openid: string) => {
  return apiClient.get<WechatProfileResponse>('/api/wechat/profile', { openid })
}

export const chat = async (payload: WechatChatRequest) => {
  return apiClient.post<WechatChatResponse>('/api/wechat/chat', payload)
}
