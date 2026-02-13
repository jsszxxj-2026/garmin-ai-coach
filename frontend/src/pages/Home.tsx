import { useDailyAnalysis } from '../hooks/useDailyAnalysis'
import Loading from '../components/Loading'
import Error from '../components/Error'
import { MarkdownView } from '../components/MarkdownView'
import { format } from 'date-fns'
import { zhCN } from 'date-fns/locale'

export default function Home() {
  const { data, isLoading, error, refetch } = useDailyAnalysis()

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
        <span className="sport-kicker">Daily Brief</span>
        <div className="mt-4 flex items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black text-white">每日分析</h1>
            <p className="mt-1 text-sm text-slate-200">
              {format(new Date(data.date), 'yyyy年MM月dd日 EEEE', { locale: zhCN })}
            </p>
          </div>
          <div className="rounded-2xl border border-white/20 bg-white/10 px-4 py-3 text-right">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-300">状态</p>
            <p className="text-lg font-bold text-white">Ready to Run</p>
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="mb-4 text-xl font-bold text-slate-900">AI 教练建议</h2>
        <div className="border-t border-slate-200 pt-4">
          <MarkdownView content={data.ai_advice} />
        </div>
      </div>

      {data.raw_data_summary && data.raw_data_summary !== '暂无数据' && (
        <div className="card">
          <h2 className="mb-4 text-xl font-bold text-slate-900">数据摘要</h2>
          <div className="border-t border-slate-200 pt-4">
            <MarkdownView content={data.raw_data_summary} />
          </div>
        </div>
      )}
    </div>
  )
}
