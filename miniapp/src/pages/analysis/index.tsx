import { useEffect, useMemo, useState } from 'react'
import { View, Text } from '@tarojs/components'
import Taro from '@tarojs/taro'

import Error from '../../components/Error'
import Loading from '../../components/Loading'
import MarkdownView from '../../components/MarkdownView'
import StatCard from '../../components/StatCard'
import { getDailyAnalysis, getDailyAnalysisByDate } from '../../api/coach'
import type { DailyAnalysisResponse } from '../../types'

import './index.scss'

const getTargetDate = () => {
  const instance = Taro.getCurrentInstance()
  const targetDate = instance?.router?.params?.target_date
  return typeof targetDate === 'string' ? targetDate : undefined
}

function Analysis() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<DailyAnalysisResponse | null>(null)

  const summaryItems = useMemo(() => {
    const summary = analysis?.summary
    if (!summary) {
      return []
    }
    const items = [] as Array<{ title: string; value: string; unit?: string }>

    if (summary.sleep !== undefined && summary.sleep !== null) {
      items.push({ title: '睡眠', value: String(summary.sleep), unit: '小时' })
    }
    if (summary.battery !== undefined && summary.battery !== null) {
      items.push({ title: '体能电量', value: String(summary.battery), unit: '%' })
    }
    if (summary.stress !== undefined && summary.stress !== null) {
      items.push({ title: '压力', value: String(summary.stress) })
    }
    return items
  }, [analysis])

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const targetDate = getTargetDate()
      const response = targetDate
        ? await getDailyAnalysisByDate(targetDate)
        : await getDailyAnalysis()
      setAnalysis(response)
    } catch (err) {
      setError('获取数据失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  if (loading) {
    return <Loading />
  }

  if (error) {
    return <Error message={error} onRetry={fetchData} />
  }

  return (
    <View className='page analysis'>
      <View className='hero'>
        <Text className='title'>分析</Text>
        <Text className='subtitle'>今日训练概览</Text>
      </View>

      {summaryItems.length ? (
        <View className='summary'>
          <Text className='section-title'>关键指标</Text>
          <View className='summary-grid'>
            {summaryItems.map((item) => (
              <StatCard
                key={item.title}
                title={item.title}
                value={item.value}
                unit={item.unit}
              />
            ))}
          </View>
        </View>
      ) : null}

      <View className='section'>
        <Text className='section-title'>原始数据摘要</Text>
        <MarkdownView content={analysis?.raw_data_summary ?? '暂无数据'} />
      </View>

      <View className='section'>
        <Text className='section-title'>AI 建议</Text>
        <MarkdownView content={analysis?.ai_advice ?? '暂无数据'} />
      </View>
    </View>
  )
}

export default Analysis
