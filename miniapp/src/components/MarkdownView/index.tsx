import { View, Text } from '@tarojs/components'

import '../index.scss'

type MarkdownViewProps = {
  content: string
}

type InlineSegment = {
  type: 'text' | 'bold' | 'code'
  text: string
}

type Block = {
  type: 'h1' | 'h2' | 'h3' | 'paragraph' | 'quote' | 'list'
  text?: string
  items?: string[]
}

const splitBold = (text: string): InlineSegment[] => {
  const parts = text.split('**')
  return parts
    .map((part, index): InlineSegment => ({
      type: index % 2 === 1 ? 'bold' : 'text',
      text: part,
    }))
    .filter((part) => part.text.length > 0)
}

const parseInline = (text: string): InlineSegment[] => {
  const codeParts = text.split('`')
  const segments: InlineSegment[] = []

  codeParts.forEach((part, index) => {
    if (part.length === 0) {
      return
    }
    if (index % 2 === 1) {
      segments.push({ type: 'code', text: part })
      return
    }
    segments.push(...splitBold(part))
  })

  return segments
}

const renderInline = (text?: string) => {
  if (!text) {
    return null
  }
  return parseInline(text).map((segment, index) => {
    if (segment.type === 'text') {
      return <Text key={`${segment.type}-${index}`}>{segment.text}</Text>
    }
    if (segment.type === 'bold') {
      return (
        <Text className='markdown-bold' key={`${segment.type}-${index}`}>
          {segment.text}
        </Text>
      )
    }
    return (
      <Text className='markdown-code' key={`${segment.type}-${index}`}>
        {segment.text}
      </Text>
    )
  })
}

const parseBlocks = (content: string): Block[] => {
  const lines = content
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0)

  const blocks: Block[] = []
  let listBuffer: string[] = []

  const flushList = () => {
    if (listBuffer.length) {
      blocks.push({ type: 'list', items: listBuffer })
      listBuffer = []
    }
  }

  lines.forEach((line) => {
    if (line.startsWith('### ')) {
      flushList()
      blocks.push({ type: 'h3', text: line.slice(4) })
      return
    }
    if (line.startsWith('## ')) {
      flushList()
      blocks.push({ type: 'h2', text: line.slice(3) })
      return
    }
    if (line.startsWith('# ')) {
      flushList()
      blocks.push({ type: 'h1', text: line.slice(2) })
      return
    }
    if (line.startsWith('- ') || line.startsWith('* ')) {
      listBuffer.push(line.slice(2))
      return
    }
    if (line.startsWith('> ')) {
      flushList()
      blocks.push({ type: 'quote', text: line.slice(2) })
      return
    }
    flushList()
    blocks.push({ type: 'paragraph', text: line })
  })

  flushList()
  return blocks
}

function MarkdownView({ content }: MarkdownViewProps) {
  const blocks = parseBlocks(content)

  return (
    <View className='markdown' data-testid='markdown'>
      {blocks.map((block, index) => {
        if (block.type === 'list') {
          return (
            <View className='markdown-list' key={`list-${index}`}>
              {block.items?.map((item, itemIndex) => (
                <View className='markdown-list-item' key={`item-${itemIndex}-${item}`}>
                  <Text className='markdown-list-bullet'>•</Text>
                  <Text className='markdown-list-text'>{renderInline(item)}</Text>
                </View>
              ))}
            </View>
          )
        }

        if (block.type === 'quote') {
          return (
            <View className='markdown-quote' key={`quote-${index}`}>
              <Text className='markdown-quote-text'>{renderInline(block.text)}</Text>
            </View>
          )
        }

        const classNameMap: Record<string, string> = {
          h1: 'markdown-h1',
          h2: 'markdown-h2',
          h3: 'markdown-h3',
          paragraph: 'markdown-paragraph',
        }

        return (
          <Text className={classNameMap[block.type]} key={`block-${index}`}>
            {renderInline(block.text)}
          </Text>
        )
      })}
    </View>
  )
}

export default MarkdownView
