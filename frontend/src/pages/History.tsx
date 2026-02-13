import { useState } from 'react'
import { useDailyAnalysis } from '../hooks/useDailyAnalysis'
import { format, subDays } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { Link } from 'react-router-dom'
import Loading from '../components/Loading'

export default function History() {
  const [selectedDate, setSelectedDate] = useState<string>(
    format(new Date(), 'yyyy-MM-dd')
  )
  
  const { data, isLoading } = useDailyAnalysis(selectedDate)

  // 生成最近7天的日期列表
  const recentDates = Array.from({ length: 7 }, (_, i) => {
    const date = subDays(new Date(), i)
    return {
      date: format(date, 'yyyy-MM-dd'),
      display: format(date, 'MM月dd日', { locale: zhCN }),
      isToday: i === 0,
    }
  })

  return (
    <div className="space-y-6">
      <div className="card-dark">
        <span className="sport-kicker">Archive</span>
        <h1 className="mt-4 text-3xl font-black text-white">历史记录</h1>
        <p className="mt-1 text-sm text-slate-200">按日期回看训练建议和恢复状态变化</p>
      </div>

      <div className="card">
        <h2 className="mb-4 text-lg font-bold text-slate-900">选择日期</h2>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7">
          {recentDates.map((item) => (
            <button
              key={item.date}
              onClick={() => setSelectedDate(item.date)}
              className={`rounded-xl px-3 py-2 text-sm font-semibold transition-all ${
                selectedDate === item.date
                  ? 'bg-orange-600 text-white shadow-md shadow-orange-500/30'
                  : item.isToday
                  ? 'bg-orange-100 text-orange-700 hover:bg-orange-200'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              <div className="text-xs">{item.isToday ? '今天' : ''}</div>
              <div>{item.display}</div>
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <Loading />
      ) : data ? (
        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-slate-900">
                {format(new Date(data.date), 'yyyy年MM月dd日 EEEE', { locale: zhCN })}
              </h2>
              <Link
                to={`/analysis/${data.date}`}
                className="btn-primary text-sm"
              >
                查看详情
              </Link>
            </div>
            <div className="border-t border-slate-200 pt-4">
              <div className="prose max-w-none">
                <div className="line-clamp-3 text-slate-700">
                  {data.ai_advice.substring(0, 200)}...
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-slate-500">该日期暂无数据</p>
        </div>
      )}
    </div>
  )
}
