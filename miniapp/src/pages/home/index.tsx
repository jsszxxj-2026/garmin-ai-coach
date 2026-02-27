import { useEffect, useState } from 'react'
import { View, Text, Button, Input, Switch } from '@tarojs/components'
import Taro from '@tarojs/taro'

import Error from '../../components/Error'
import Loading from '../../components/Loading'
import StatCard from '../../components/StatCard'
import { bindGarmin, getHomeSummary, getPeriodAnalysis, getProfile, unbindGarmin } from '../../api/coach'
import type { HomeSummaryResponse, PeriodAnalysisResponse, WechatProfileResponse } from '../../types'

import './index.scss'

function Home() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [homeSummary, setHomeSummary] = useState<HomeSummaryResponse | null>(null)
  const [profile, setProfile] = useState<WechatProfileResponse | null>(null)
  const [openid] = useState('local-openid')
  const [garminEmail, setGarminEmail] = useState('')
  const [garminPassword, setGarminPassword] = useState('')
  const [isCn, setIsCn] = useState(false)
  const [showPeriodModal, setShowPeriodModal] = useState(false)
  const [periodAnalysis, setPeriodAnalysis] = useState<PeriodAnalysisResponse | null>(null)
  const [periodLoading, setPeriodLoading] = useState(false)
  const [activePeriod, setActivePeriod] = useState<'week' | 'month'>('week')

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [profileResponse, homeSummaryResponse] = await Promise.all([
        getProfile(openid),
        getHomeSummary(openid),
      ])
      setProfile(profileResponse)
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

  const handleLatestRunClick = () => {
    if (homeSummary?.latest_run?.start_time) {
      const date = homeSummary.latest_run.start_time.split('T')[0]
      Taro.navigateTo({ url: `/pages/analysis/index?target_date=${date}` })
    }
  }

  const handlePeriodStatsClick = async (period: 'week' | 'month') => {
    setActivePeriod(period)
    setPeriodAnalysis(null)
    setShowPeriodModal(true)
    setPeriodLoading(true)
    try {
      const data = await getPeriodAnalysis(openid, period)
      setPeriodAnalysis(data)
    } catch (err) {
      Taro.showToast({ title: '获取分析失败', icon: 'none' })
    } finally {
      setPeriodLoading(false)
    }
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
          <View className='run-card' onClick={handleLatestRunClick}>
            <View className='run-card-header'>
              <Text className='run-card-date'>
                {latestRun.start_time ? latestRun.start_time.replace('T', ' ').slice(0, 16) : '-'}
              </Text>
              <Text className='run-card-intensity'>{latestRun.intensity || '-'}</Text>
            </View>
            <View className='run-card-stats'>
              <View className='run-card-stat'>
                <Text className='run-card-value'>{String(latestRun.distance_km)}</Text>
                <Text className='run-card-unit'>km</Text>
              </View>
              <View className='run-card-stat'>
                <Text className='run-card-value'>{latestRun.avg_pace || '-'}</Text>
                <Text className='run-card-unit'>配速</Text>
              </View>
              <View className='run-card-stat'>
                <Text className='run-card-value'>{latestRun.duration_min || '-'}</Text>
                <Text className='run-card-unit'>分钟</Text>
              </View>
            </View>
          </View>
        </View>
      ) : null}

      {weekStats || monthStats ? (
        <View className='summary'>
          <Text className='section-title'>周/月统计（点击查看分析）</Text>
          <View className='summary-grid'>
            {weekStats ? (
              <StatCard
                title='本周跑量'
                value={String(weekStats.distance_km)}
                unit='km'
                onClick={() => handlePeriodStatsClick('week')}
              />
            ) : null}
            {weekStats ? (
              <StatCard
                title='本周均速'
                value={weekStats.avg_speed_kmh ? String(weekStats.avg_speed_kmh) : '-'}
                unit='km/h'
                onClick={() => handlePeriodStatsClick('week')}
              />
            ) : null}
            {monthStats ? (
              <StatCard
                title='本月跑量'
                value={String(monthStats.distance_km)}
                unit='km'
                onClick={() => handlePeriodStatsClick('month')}
              />
            ) : null}
            {monthStats ? (
              <StatCard
                title='本月均速'
                value={monthStats.avg_speed_kmh ? String(monthStats.avg_speed_kmh) : '-'}
                unit='km/h'
                onClick={() => handlePeriodStatsClick('month')}
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

      <View className='actions'>
        <Button className='ghost-button' onClick={handleAnalysis}>
          查看详细分析
        </Button>
        <Button className='ghost-button' onClick={handleChat}>
          进入聊天
        </Button>
      </View>

      {showPeriodModal && (
        <View className='modal-mask' onClick={() => setShowPeriodModal(false)}>
          <View className='modal-content' onClick={(e) => e.stopPropagation()}>
            <Text className='modal-title'>
              {activePeriod === 'week' ? '本周' : '本月'}分析
            </Text>
            {periodLoading ? (
              <Loading />
            ) : periodAnalysis ? (
              <View className='modal-body'>
                <View className='modal-stats'>
                  <Text className='modal-label'>跑步次数：{periodAnalysis.run_count} 次</Text>
                  <Text className='modal-label'>总跑量：{periodAnalysis.total_distance_km} km</Text>
                  <Text className='modal-label'>平均速度：{periodAnalysis.avg_speed_kmh || '-'} km/h</Text>
                  <Text className='modal-label'>睡眠天数：{periodAnalysis.sleep_days} 天</Text>
                  <Text className='modal-label'>平均睡眠：{periodAnalysis.avg_sleep_hours || '-'} 小时</Text>
                </View>
                {periodAnalysis.ai_analysis && (
                  <View className='modal-ai'>
                    <Text className='modal-ai-title'>AI 分析：</Text>
                    <Text className='modal-ai-content'>{periodAnalysis.ai_analysis}</Text>
                  </View>
                )}
              </View>
            ) : (
              <Text>加载失败</Text>
            )}
            <Button className='modal-close' onClick={() => setShowPeriodModal(false)}>
              关闭
            </Button>
          </View>
        </View>
      )}
    </View>
  )
}

export default Home
