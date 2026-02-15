import { useEffect, useMemo, useState } from 'react'
import { View, Text, Button, Input, Switch } from '@tarojs/components'
import Taro from '@tarojs/taro'

import Error from '../../components/Error'
import Loading from '../../components/Loading'
import StatCard from '../../components/StatCard'
import { bindGarmin, getDailyAnalysis, getHomeSummary, getProfile, unbindGarmin } from '../../api/coach'
import type { DailyAnalysisResponse, HomeSummaryResponse, WechatProfileResponse } from '../../types'

import './index.scss'

function Home() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<DailyAnalysisResponse | null>(null)
  const [homeSummary, setHomeSummary] = useState<HomeSummaryResponse | null>(null)
  const [profile, setProfile] = useState<WechatProfileResponse | null>(null)
  const [openid] = useState('local-openid')
  const [garminEmail, setGarminEmail] = useState('')
  const [garminPassword, setGarminPassword] = useState('')
  const [isCn, setIsCn] = useState(false)

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
      const [profileResponse, analysisResponse, homeSummaryResponse] = await Promise.all([
        getProfile(openid),
        getDailyAnalysis(),
        getHomeSummary(openid),
      ])
      setProfile(profileResponse)
      setAnalysis(analysisResponse)
      setHomeSummary(homeSummaryResponse)
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
    try {
      await bindGarmin({
        openid,
        garmin_email: garminEmail,
        garmin_password: garminPassword,
        is_cn: isCn,
      })
      Taro.showToast({ title: '已提交绑定', icon: 'success' })
      fetchData()
    } catch (err) {
      Taro.showToast({ title: '绑定失败', icon: 'none' })
    }
  }

  const handleUnbind = async () => {
    try {
      await unbindGarmin({ openid })
      Taro.showToast({ title: '已解绑', icon: 'success' })
      fetchData()
    } catch (err) {
      Taro.showToast({ title: '解绑失败', icon: 'none' })
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
  const latestRun = homeSummary?.latest_run
  const weekStats = homeSummary?.week_stats
  const monthStats = homeSummary?.month_stats
  const aiBrief = homeSummary?.ai_brief

  return (
    <View className='page home'>
      <View className='hero'>
        <Text className='title'>训练助手</Text>
        <Text className='subtitle'>今日概览与智能建议</Text>
      </View>

      {isBound ? (
        <View className='bind-card'>
          <Text className='bind-title'>Garmin 已绑定</Text>
          <Text className='bind-desc'>如需更换账号，请先解绑再重新绑定</Text>
          <Button
            className='primary-button'
            onClick={handleUnbind}
            data-testid='unbind-rebind'
          >
            解绑/重新绑定
          </Button>
        </View>
      ) : (
        <View className='bind-card'>
          <Text className='bind-title'>绑定 Garmin 账号</Text>
          <Text className='bind-desc'>绑定后可同步睡眠、体能电量与压力数据</Text>
          <View className='bind-form'>
            <Input
              className='bind-input'
              type='text'
              placeholder='Garmin 邮箱'
              value={garminEmail}
              onInput={(event) => setGarminEmail(event.detail.value)}
              data-testid='garmin-email-input'
            />
            <Input
              className='bind-input'
              type='text'
              password
              placeholder='Garmin 密码'
              value={garminPassword}
              onInput={(event) => setGarminPassword(event.detail.value)}
              data-testid='garmin-password-input'
            />
            <View className='bind-switch'>
              <Text>中国区账号</Text>
              <Switch
                checked={isCn}
                onChange={(event) => setIsCn(event.detail.value)}
                data-testid='garmin-is-cn-switch'
              />
            </View>
          </View>
          <Button
            className='primary-button'
            onClick={handleBind}
            data-testid='bind-submit'
          >
            立即绑定
          </Button>
        </View>
      )}

      {latestRun ? (
        <View className='summary'>
          <Text className='section-title'>最近一次跑步</Text>
          <View className='summary-grid'>
            <StatCard
              title='距离'
              value={String(latestRun.distance_km)}
              unit='km'
            />
            <StatCard
              title='配速'
              value={latestRun.avg_pace || '-'}
            />
            <StatCard
              title='强度'
              value={latestRun.intensity || '-'}
            />
          </View>
        </View>
      ) : null}

      {weekStats || monthStats ? (
        <View className='summary'>
          <Text className='section-title'>周/月统计</Text>
          <View className='summary-grid'>
            {weekStats ? (
              <StatCard
                title='本周跑量'
                value={String(weekStats.distance_km)}
                unit='km'
              />
            ) : null}
            {weekStats ? (
              <StatCard
                title='本周均速'
                value={weekStats.avg_speed_kmh ? String(weekStats.avg_speed_kmh) : '-'}
                unit='km/h'
              />
            ) : null}
            {monthStats ? (
              <StatCard
                title='本月跑量'
                value={String(monthStats.distance_km)}
                unit='km'
              />
            ) : null}
            {monthStats ? (
              <StatCard
                title='本月均速'
                value={monthStats.avg_speed_kmh ? String(monthStats.avg_speed_kmh) : '-'}
                unit='km/h'
              />
            ) : null}
          </View>
        </View>
      ) : null}

      {aiBrief?.week || aiBrief?.month ? (
        <View className='summary'>
          <Text className='section-title'>教练简评</Text>
          <View className='summary-grid'>
            {aiBrief?.week ? (
              <StatCard title='本周' value={aiBrief.week} />
            ) : null}
            {aiBrief?.month ? (
              <StatCard title='本月' value={aiBrief.month} />
            ) : null}
          </View>
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
