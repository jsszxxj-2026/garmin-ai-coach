import { View, Text, Button } from '@tarojs/components'

import '../index.scss'

type ErrorProps = {
  message: string
  onRetry: () => void
}

function Error({ message, onRetry }: ErrorProps) {
  return (
    <View className='error' data-testid='error'>
      <Text className='error-text'>{message}</Text>
      <Button className='error-button' onClick={onRetry}>
        重试
      </Button>
    </View>
  )
}

export default Error
