import { useEffect, useMemo, useState } from 'react'
import { View, Text, Button } from '@tarojs/components'
import Taro from '@tarojs/taro'

import Error from '../../components/Error'
import Loading from '../../components/Loading'
import StatCard from '../../components/StatCard'
import { bindGarmin, getDailyAnalysis, getProfile } from '../../api/coach'
import type { DailyAnalysisResponse, WechatProfileResponse } from '../../types'

import './index.scss'

function Home() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<DailyAnalysisResponse | null>(null)
  const [profile, setProfile] = useState<WechatProfileResponse | null>(null)
  const [openid] = useState('local-openid')

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
      const [profileResponse, analysisResponse] = await Promise.all([
        getProfile(openid),
        getDailyAnalysis(),
      ])
      setProfile(profileResponse)
      setAnalysis(analysisResponse)
    } catch (err) {
      setError('获取数据失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleBind = async () => {
    if (!profile) {
      return
    }
    try {
      await bindGarmin({
        openid: profile.openid,
        garmin_email: 'placeholder@example.com',
        garmin_password: 'placeholder',
        is_cn: false,
      })
      Taro.showToast({ title: '已提交绑定', icon: 'success' })
      fetchData()
    } catch (err) {
      Taro.showToast({ title: '绑定失败', icon: 'none' })
    }
  }

  const handleAnalysis = () => {
    Taro.navigateTo({ url: '/pages/analysis/index' })
  }

  const handleChat = () => {
    Taro.showToast({ title: '聊天功能建设中', icon: 'none' })
  }

  if (loading) {
    return <Loading />
  }

  if (error) {
    return <Error message={error} onRetry={fetchData} />
  }

  const isBound = profile?.has_binding

  return (
    <View className='page home'>
      <View className='hero'>
        <Text className='title'>训练助手</Text>
        <Text className='subtitle'>今日概览与智能建议</Text>
      </View>

      {!isBound ? (
        <View className='bind-card'>
          <Text className='bind-title'>尚未绑定 Garmin 账号</Text>
          <Text className='bind-desc'>绑定后可同步睡眠、体能电量与压力数据</Text>
          <Button className='primary-button' onClick={handleBind}>
            立即绑定
          </Button>
        </View>
      ) : null}

      {summaryItems.length ? (
        <View className='summary'>
          <Text className='section-title'>今日指标</Text>
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

      <View className='actions'>
        <Button className='ghost-button' onClick={handleAnalysis}>
          查看详细分析
        </Button>
        <Button className='ghost-button' onClick={handleChat}>
          进入聊天
        </Button>
      </View>
    </View>
  )
}

export default Home
