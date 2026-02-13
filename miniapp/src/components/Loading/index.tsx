import { View, Text } from '@tarojs/components'

import '../index.scss'

function Loading() {
  return (
    <View className='loading' data-testid='loading'>
      <Text className='loading-text'>加载中</Text>
    </View>
  )
}

export default Loading
