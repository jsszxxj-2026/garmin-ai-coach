export type DailyAnalysisResponse = {
  date: string
  raw_data_summary: string
  ai_advice: string
  summary?: {
    sleep?: number | null
    battery?: number | null
    stress?: number | null
  }
  charts?: {
    labels: string[]
    paces: number[]
    heart_rates: number[]
    cadences: number[]
  }
}

export type WechatLoginRequest = {
  code: string
}

export type WechatLoginResponse = {
  openid: string
  unionid?: string
}

export type WechatBindGarminRequest = {
  openid: string
  garmin_email: string
  garmin_password: string
  is_cn?: boolean
}

export type WechatBindGarminResponse = {
  bound: boolean
}

export type WechatUnbindGarminRequest = {
  openid: string
}

export type WechatUnbindGarminResponse = {
  unbound: boolean
}

export type WechatProfileResponse = {
  openid: string
  has_binding: boolean
  garmin_email?: string
  is_cn?: boolean
}

export type WechatChatRequest = {
  openid: string
  message: string
}

export type WechatChatResponse = {
  reply: string
}
