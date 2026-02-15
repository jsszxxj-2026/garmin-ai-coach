import { describe, expect, it, vi } from 'vitest'

vi.mock('@tarojs/components', () => {
  return {
    View: 'View',
    Text: 'Text',
    Button: 'Button',
  }
})

import Error from '../src/components/Error'
import Loading from '../src/components/Loading'
import MarkdownView from '../src/components/MarkdownView'
import StatCard from '../src/components/StatCard'

type TestNode = {
  type?: string
  props?: {
    ['data-testid']?: string
    children?: unknown
    onClick?: () => void
  }
}

const getTestId = (node: TestNode | undefined, id: string) => {
  if (!node) {
    return undefined
  }

  if (node.props?.['data-testid'] === id) {
    return node
  }

  const children = node.props?.children
  if (!children) {
    return undefined
  }

  if (Array.isArray(children)) {
    for (const child of children) {
      const match = getTestId(child as TestNode, id)
      if (match) {
        return match
      }
    }
    return undefined
  }

  return getTestId(children as TestNode, id)
}

const findByType = (node: TestNode | undefined, type: string) => {
  if (!node) {
    return undefined
  }

  if (node.type === type) {
    return node
  }

  const children = node.props?.children
  if (!children) {
    return undefined
  }

  if (Array.isArray(children)) {
    for (const child of children) {
      const match = findByType(child as TestNode, type)
      if (match) {
        return match
      }
    }
    return undefined
  }

  return findByType(children as TestNode, type)
}

const findAllByType = (node: TestNode | undefined, type: string) => {
  const matches: TestNode[] = []

  const walk = (target?: TestNode) => {
    if (!target) {
      return
    }

    if (target.type === type) {
      matches.push(target)
    }

    const children = target.props?.children
    if (!children) {
      return
    }

    if (Array.isArray(children)) {
      for (const child of children) {
        walk(child as TestNode)
      }
      return
    }

    walk(children as TestNode)
  }

  walk(node)
  return matches
}

const clickNode = (node?: TestNode) => {
  node?.props?.onClick?.()
}

const getNodeText = (node?: TestNode) => {
  const children = node?.props?.children
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

describe('base components', () => {
  it('renders Loading with text', () => {
    const node = Loading()

    const root = getTestId(node, 'loading')
    expect(root).toBeTruthy()
    expect(getNodeText(root)).toContain('加载中')
  })

  it('renders Error message and calls retry', () => {
    const onRetry = vi.fn()
    const node = Error({ message: '网络错误', onRetry })

    const root = getTestId(node, 'error')
    expect(root).toBeTruthy()
    expect(getNodeText(root)).toContain('网络错误')

    const button = findByType(root, 'Button')
    clickNode(button)
    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it('renders StatCard title, value, and unit', () => {
    const node = StatCard({ title: '距离', value: '10', unit: 'km' })

    const root = getTestId(node, 'stat-card')
    expect(root).toBeTruthy()
    expect(getNodeText(root)).toContain('距离')
    expect(getNodeText(root)).toContain('10')
    expect(getNodeText(root)).toContain('km')
  })

  it('renders MarkdownView paragraphs', () => {
    const node = MarkdownView({ content: '第一段\n第二段' })

    const root = getTestId(node, 'markdown')
    expect(root).toBeTruthy()

    const paragraphs = findAllByType(root, 'Text')
    const text = paragraphs.map((node) => getNodeText(node)).join('')
    expect(text).toContain('第一段')
    expect(text).toContain('第二段')
  })

  it('renders MarkdownView headings and list', () => {
    const node = MarkdownView({ content: '# 标题\n- 列表A\n- 列表B' })

    const root = getTestId(node, 'markdown')
    expect(root).toBeTruthy()

    const paragraphs = findAllByType(root, 'Text')
    const text = paragraphs.map((node) => getNodeText(node)).join('')
    expect(text).toContain('标题')
    expect(text).toContain('列表A')
    expect(text).toContain('列表B')
  })
})
