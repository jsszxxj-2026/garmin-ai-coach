import { View, Text } from '@tarojs/components'

import '../index.scss'

type MarkdownViewProps = {
  content: string
}

function MarkdownView({ content }: MarkdownViewProps) {
  const paragraphs = content
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0)

  return (
    <View className='markdown' data-testid='markdown'>
      {paragraphs.map((line, index) => (
        <Text className='markdown-paragraph' key={`${index}-${line}`}>
          {line}
        </Text>
      ))}
    </View>
  )
}

export default MarkdownView
