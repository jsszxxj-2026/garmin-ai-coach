import { useParams } from 'react-router-dom'
import { useDailyAnalysis } from '../hooks/useDailyAnalysis'
import Loading from '../components/Loading'
import Error from '../components/Error'
import { MarkdownView } from '../components/MarkdownView'
import { ChartView } from '../components/ChartView'
import { format } from 'date-fns'
import { zhCN } from 'date-fns/locale'

export default function Analysis() {
  const { date } = useParams<{ date?: string }>()
  const { data, isLoading, error, refetch } = useDailyAnalysis(date)

  if (isLoading) {
    return <Loading />
  }

  if (error) {
    return <Error onRetry={() => refetch()} />
  }

  if (!data) {
    return <Error message="暂无数据" />
  }

  return (
    <div className="space-y-6">
      <div className="card-dark">
        <span className="sport-kicker">Performance Detail</span>
        <h1 className="mt-4 text-3xl font-black text-white">详细分析</h1>
        <p className="mt-1 text-sm text-slate-200">
          {format(new Date(data.date), 'yyyy年MM月dd日 EEEE', { locale: zhCN })}
        </p>
      </div>

      <div className="card">
        <h2 className="mb-4 text-xl font-bold text-slate-900">AI 教练建议</h2>
        <div className="border-t border-slate-200 pt-4">
          <MarkdownView content={data.ai_advice} />
        </div>
      </div>

      {data.charts && data.charts.labels.length > 0 && (
        <div className="card">
          <ChartView data={data.charts} />
        </div>
      )}

      {data.raw_data_summary && data.raw_data_summary !== '暂无数据' && (
        <div className="card">
          <h2 className="mb-4 text-xl font-bold text-slate-900">原始数据</h2>
          <div className="border-t border-slate-200 pt-4">
            <MarkdownView content={data.raw_data_summary} />
          </div>
        </div>
      )}
    </div>
  )
}
