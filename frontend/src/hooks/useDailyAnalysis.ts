import { useQuery } from '@tanstack/react-query'
import { coachApi } from '../api/coach'

export function useDailyAnalysis(date?: string) {
  return useQuery({
    queryKey: ['daily-analysis', date],
    queryFn: () => coachApi.getDailyAnalysis(date),
    staleTime: 5 * 60 * 1000, // 5 分钟缓存
  })
}
