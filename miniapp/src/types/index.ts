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

export type HomeSummaryResponse = {
  latest_run: {
    start_time: string
    distance_km: number
    intensity?: string | null
    avg_pace?: string | null
    duration_min?: number | null
  } | null
  week_stats: {
    distance_km: number
    avg_speed_kmh?: number | null
  } | null
  month_stats: {
    distance_km: number
    avg_speed_kmh?: number | null
  } | null
  ai_brief: {
    week?: string | null
    month?: string | null
  } | null
  updated_at?: string | null
}

export type PeriodAnalysisResponse = {
  period: string
  start_date: string
  end_date: string
  run_count: number
  total_distance_km: number
  avg_speed_kmh?: number | null
  sleep_days: number
  avg_sleep_hours?: number | null
  ai_analysis?: string | null
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
