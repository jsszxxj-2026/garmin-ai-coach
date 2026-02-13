import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { create } from 'react-test-renderer'
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
      navigateTo: vi.fn(),
    },
  }
})

import Taro from '@tarojs/taro'
import History from '../src/pages/history'

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

const clickNode = (node?: TestNode) => {
  node?.props?.onClick?.()
}

const navigateToMock = Taro.navigateTo as unknown as ReturnType<typeof vi.fn>

describe('history page', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2024, 1, 10, 12, 0, 0))
  })

  afterEach(() => {
    vi.useRealTimers()
    navigateToMock.mockReset()
  })

  it('renders last 7 dates', () => {
    const renderer = create(<History />)
    const root = renderer.toJSON()

    const dateNodes = getAllByTestId(root as TestNode | TestNode[], 'history-item')
    expect(dateNodes).toHaveLength(7)

    const text = dateNodes.map((node) => node.props?.['data-date'])
    expect(text).toEqual([
      '2024-02-10',
      '2024-02-09',
      '2024-02-08',
      '2024-02-07',
      '2024-02-06',
      '2024-02-05',
      '2024-02-04',
    ])
  })

  it('navigates to analysis with target_date', () => {
    const renderer = create(<History />)
    const root = renderer.toJSON()

    const items = getAllByTestId(root as TestNode | TestNode[], 'history-item')
    clickNode(items[0])

    expect(navigateToMock).toHaveBeenCalledWith({
      url: '/pages/analysis/index?target_date=2024-02-10',
    })
  })
})
