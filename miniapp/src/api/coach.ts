import { apiClient } from './client'
import type {
  DailyAnalysisResponse,
  WechatBindGarminRequest,
  WechatBindGarminResponse,
  WechatChatRequest,
  WechatChatResponse,
  WechatLoginRequest,
  WechatLoginResponse,
  WechatProfileResponse,
} from '../types'

export const getDailyAnalysis = async () => {
  return apiClient.get<DailyAnalysisResponse>('/api/coach/daily-analysis')
}

export const getDailyAnalysisByDate = async (date: string) => {
  return apiClient.get<DailyAnalysisResponse>('/api/coach/daily-analysis', {
    target_date: date,
  })
}

export const loginWechat = async (payload: WechatLoginRequest) => {
  return apiClient.post<WechatLoginResponse>('/api/wechat/login', payload)
}

export const bindGarmin = async (payload: WechatBindGarminRequest) => {
  return apiClient.post<WechatBindGarminResponse>('/api/wechat/bind-garmin', payload)
}

export const getProfile = async () => {
  return apiClient.get<WechatProfileResponse>('/api/wechat/profile')
}

export const chat = async (payload: WechatChatRequest) => {
  return apiClient.post<WechatChatResponse>('/api/wechat/chat', payload)
}
