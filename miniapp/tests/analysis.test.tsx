import { afterEach, describe, expect, it, vi } from 'vitest'
import { act, create } from 'react-test-renderer'
import type { ReactTestRendererJSON } from 'react-test-renderer'

vi.mock('@tarojs/components', () => {
  return {
    View: 'View',
    Text: 'Text',
    Button: 'Button',
  }
})

vi.mock('@tarojs/taro', () => {
  return {
    default: {
      getCurrentInstance: vi.fn(),
    },
  }
})

vi.mock('../src/components/MarkdownView', () => {
  return {
    default: ({ content }: { content: string }) => {
      return (
        <View data-testid='markdown-text' data-content={content}>
          {content}
        </View>
      )
    },
  }
})

vi.mock('../src/api/coach', () => {
  return {
    getDailyAnalysis: vi.fn(),
    getDailyAnalysisByDate: vi.fn(),
  }
})

import Taro from '@tarojs/taro'
import { View } from '@tarojs/components'
import Analysis from '../src/pages/analysis'
import { getDailyAnalysis, getDailyAnalysisByDate } from '../src/api/coach'

type TestNode = ReactTestRendererJSON

const getAllByTestId = (
  node: TestNode | TestNode[] | null | undefined,
  id: string
) => {
  const matches: TestNode[] = []

  const walk = (target?: TestNode | TestNode[] | null) => {
    if (!target) {
      return
    }

    if (Array.isArray(target)) {
      for (const child of target) {
        walk(child)
      }
      return
    }

    if (target.props?.['data-testid'] === id) {
      matches.push(target)
    }

    const children = target.children
    if (!children) {
      return
    }

    walk(children as TestNode | TestNode[])
  }

  walk(node)
  return matches
}

const getNodeText = (node?: TestNode) => {
  const content = node?.props?.['data-content']
  if (typeof content === 'string' || typeof content === 'number') {
    return String(content)
  }

  const children = node?.children ?? node?.props?.children
  if (children === undefined || children === null) {
    return ''
  }

  if (typeof children === 'string' || typeof children === 'number') {
    return String(children)
  }

  if (Array.isArray(children)) {
    return children.map((child) => getNodeText(child as TestNode)).join('')
  }

  return getNodeText(children as TestNode)
}

const flushPromises = async () => {
  await new Promise((resolve) => setTimeout(resolve, 0))
}

const getCurrentInstanceMock = Taro.getCurrentInstance as unknown as ReturnType<
  typeof vi.fn
>
const getDailyAnalysisMock = getDailyAnalysis as unknown as ReturnType<
  typeof vi.fn
>
const getDailyAnalysisByDateMock = getDailyAnalysisByDate as unknown as ReturnType<
  typeof vi.fn
>

describe('analysis page', () => {
  afterEach(() => {
    getCurrentInstanceMock.mockReset()
    getDailyAnalysisMock.mockReset()
    getDailyAnalysisByDateMock.mockReset()
  })

  it('fetches analysis by date when target_date exists', async () => {
    getCurrentInstanceMock.mockReturnValue({
      router: {
        params: {
          target_date: '2024-02-10',
        },
      },
    })
    getDailyAnalysisByDateMock.mockResolvedValue({
      date: '2024-02-10',
      raw_data_summary: '原始数据摘要',
      ai_advice: '训练建议',
      summary: {
        sleep: 8,
        battery: 90,
        stress: 20,
      },
    })

    const renderer = create(<Analysis />)
    await act(async () => {
      await flushPromises()
    })
    await act(async () => {
      await flushPromises()
    })

    expect(getDailyAnalysisByDateMock).toHaveBeenCalledWith('2024-02-10')
    expect(getDailyAnalysisMock).not.toHaveBeenCalled()

    const root = renderer.toJSON()
    const cards = getAllByTestId(root as TestNode | TestNode[], 'stat-card')
    expect(cards).toHaveLength(3)

    const markdownText = getAllByTestId(
      root as TestNode | TestNode[],
      'markdown-text'
    )
    expect(markdownText).toHaveLength(2)
    const texts = markdownText.map((node) => getNodeText(node))
    expect(texts).toContain('原始数据摘要')
    expect(texts).toContain('训练建议')
  })

  it('fetches default analysis when target_date missing', async () => {
    getCurrentInstanceMock.mockReturnValue({
      router: {
        params: {},
      },
    })
    getDailyAnalysisMock.mockResolvedValue({
      date: '2024-02-11',
      raw_data_summary: '今日摘要',
      ai_advice: '今日建议',
    })

    const renderer = create(<Analysis />)
    await act(async () => {
      await flushPromises()
    })
    await act(async () => {
      await flushPromises()
    })

    expect(getDailyAnalysisMock).toHaveBeenCalledTimes(1)
    expect(getDailyAnalysisByDateMock).not.toHaveBeenCalled()

    const root = renderer.toJSON()
    const markdownText = getAllByTestId(
      root as TestNode | TestNode[],
      'markdown-text'
    )
    expect(markdownText).toHaveLength(2)
  })
})
