import { apiClient } from './client'
import type {
  ChatHistoryResponse,
  DailyAnalysisResponse,
  HomeSummaryResponse,
  PeriodAnalysisResponse,
  WechatBindGarminRequest,
  WechatBindGarminResponse,
  WechatChatRequest,
  WechatChatResponse,
  WechatProfileResponse,
  WechatUnbindGarminResponse,
} from '../types'

export const getDailyAnalysis = async () => {
  return apiClient.get<DailyAnalysisResponse>('/api/coach/daily-analysis')
}

export const getDailyAnalysisByDate = async (date: string) => {
  return apiClient.get<DailyAnalysisResponse>('/api/coach/daily-analysis', { target_date: date })
}

export const getHomeSummary = async () => {
  return apiClient.get<HomeSummaryResponse>('/api/coach/home-summary')
}

export const getPeriodAnalysis = async (period: string) => {
  return apiClient.get<PeriodAnalysisResponse>('/api/coach/period-analysis', { period })
}

export const bindGarmin = async (payload: WechatBindGarminRequest) => {
  return apiClient.post<WechatBindGarminResponse>('/api/wechat/bind-garmin', payload)
}

export const unbindGarmin = async () => {
  return apiClient.post<WechatUnbindGarminResponse>('/api/wechat/unbind-garmin')
}

export const getProfile = async () => {
  return apiClient.get<WechatProfileResponse>('/api/wechat/profile')
}

export const chat = async (payload: WechatChatRequest) => {
  return apiClient.post<WechatChatResponse>('/api/wechat/chat', payload)
}

export const getChatHistory = async (limit: number = 20) => {
  return apiClient.get<ChatHistoryResponse>('/api/wechat/chat/history', { limit })
}
