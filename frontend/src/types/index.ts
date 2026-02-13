export interface DailyAnalysisResponse {
  date: string
  raw_data_summary: string
  ai_advice: string
  charts?: ChartData
}

export interface ChartData {
  labels: string[]
  paces: number[]
  heart_rates: number[]
  cadences: number[]
}

export interface ChartDataPoint {
  label: string
  pace: number
  heartRate: number
  cadence: number
}
