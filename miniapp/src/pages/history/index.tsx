import { View, Text } from '@tarojs/components'
import Taro from '@tarojs/taro'

const padNumber = (value: number) => String(value).padStart(2, '0')

const formatDate = (date: Date) => {
  const year = date.getFullYear()
  const month = padNumber(date.getMonth() + 1)
  const day = padNumber(date.getDate())
  return `${year}-${month}-${day}`
}

const buildRecentDates = (count = 7) => {
  const today = new Date()
  const dates = [] as string[]

  for (let index = 0; index < count; index += 1) {
    const next = new Date(today)
    next.setDate(today.getDate() - index)
    dates.push(formatDate(next))
  }

  return dates
}

import './index.scss'

function History() {
  const dates = buildRecentDates(7)

  const handleTap = (date: string) => {
    Taro.navigateTo({ url: `/pages/analysis/index?target_date=${date}` })
  }

  return (
    <View className='page'>
      <Text className='title'>历史</Text>
      <Text className='subtitle'>查看你的训练记录</Text>
      <View className='list'>
        {dates.map((date) => (
          <View
            key={date}
            className='list-item'
            data-testid='history-item'
            data-date={date}
            onClick={() => handleTap(date)}
          >
            <Text className='date' data-testid='history-date'>
              {date}
            </Text>
            <Text className='arrow'>查看</Text>
          </View>
        ))}
      </View>
    </View>
  )
}

export default History
