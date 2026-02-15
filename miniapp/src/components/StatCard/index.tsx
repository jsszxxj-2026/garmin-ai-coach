import { View, Text } from '@tarojs/components'

import '../index.scss'

type StatCardProps = {
  title: string
  value: string
  unit?: string
}

function StatCard({ title, value, unit }: StatCardProps) {
  return (
    <View className='stat-card' data-testid='stat-card'>
      <Text className='stat-title'>{title}</Text>
      <View className='stat-body'>
        <Text className='stat-value'>{value}</Text>
        {unit ? <Text className='stat-unit'>{unit}</Text> : null}
      </View>
    </View>
  )
}

export default StatCard
