import { View, Text } from '@tarojs/components'

import '../index.scss'

type StatCardProps = {
  title: string
  value: string
  unit?: string
  onClick?: () => void
}

function StatCard({ title, value, unit, onClick }: StatCardProps) {
  return (
    <View className='stat-card' data-testid='stat-card' onClick={onClick}>
      <Text className='stat-title'>{title}</Text>
      <View className='stat-body'>
        <Text className='stat-value'>{value}</Text>
        {unit ? <Text className='stat-unit'>{unit}</Text> : null}
      </View>
    </View>
  )
}

export default StatCard
