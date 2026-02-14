import { afterEach, describe, expect, it, vi } from 'vitest'
import { act, create } from 'react-test-renderer'
import type { ReactTestRendererJSON } from 'react-test-renderer'

vi.mock('@tarojs/components', () => {
  return {
    View: 'View',
    Text: 'Text',
    Button: 'Button',
    Input: 'Input',
    Switch: 'Switch',
  }
})

vi.mock('@tarojs/taro', () => {
  return {
    default: {
      showToast: vi.fn(),
      navigateTo: vi.fn(),
    },
  }
})

vi.mock('../src/api/coach', () => {
  return {
    getDailyAnalysis: vi.fn(),
    getProfile: vi.fn(),
    bindGarmin: vi.fn(),
    unbindGarmin: vi.fn(),
  }
})

import Home from '../src/pages/home'
import {
  bindGarmin,
  getDailyAnalysis,
  getProfile,
  unbindGarmin,
} from '../src/api/coach'

type TestNode = ReactTestRendererJSON

const getTestId = (
  node: TestNode | TestNode[] | null | undefined,
  id: string
) => {
  if (!node) {
    return undefined
  }

  if (Array.isArray(node)) {
    for (const child of node) {
      const match = getTestId(child, id)
      if (match) {
        return match
      }
    }
    return undefined
  }

  const testId = node.props?.['data-testid']
  if (testId === id) {
    return node
  }

  const children = node.children
  if (!children) {
    return undefined
  }

  return getTestId(children as TestNode | TestNode[], id)
}

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
  const children = node?.children
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

const getDailyAnalysisMock = getDailyAnalysis as unknown as ReturnType<typeof vi.fn>
const getProfileMock = getProfile as unknown as ReturnType<typeof vi.fn>
const bindGarminMock = bindGarmin as unknown as ReturnType<typeof vi.fn>
const unbindGarminMock = unbindGarmin as unknown as ReturnType<typeof vi.fn>

describe('home page', () => {
  afterEach(() => {
    getDailyAnalysisMock.mockReset()
    getProfileMock.mockReset()
    bindGarminMock.mockReset()
    unbindGarminMock.mockReset()
  })

  it('renders loading state', async () => {
    const pending = new Promise(() => {})
    getDailyAnalysisMock.mockReturnValue(pending)
    getProfileMock.mockReturnValue(pending)

    const renderer = create(<Home />)
    await act(async () => {
      await flushPromises()
    })
    await act(async () => {
      await flushPromises()
    })

    const root = renderer.toJSON()

    expect(getTestId(root as TestNode | TestNode[], 'loading')).toBeTruthy()
  })

  it('renders error state when request fails', async () => {
    getDailyAnalysisMock.mockResolvedValue({
      date: '2024-01-01',
      raw_data_summary: 'ok',
      ai_advice: 'ok',
    })
    getProfileMock.mockRejectedValue(new Error('fail'))

    const renderer = create(<Home />)
    await act(async () => {
      await flushPromises()
    })
    await act(async () => {
      await flushPromises()
    })

    const root = renderer.toJSON()
    const error = getTestId(root as TestNode | TestNode[], 'error')
    expect(error).toBeTruthy()

    const loadingNodes = getTestId(root as TestNode | TestNode[], 'loading')
    expect(loadingNodes).toBeFalsy()
  })

  it('renders summary stats when available', async () => {
    getDailyAnalysisMock.mockResolvedValue({
      date: '2024-01-01',
      raw_data_summary: 'ok',
      ai_advice: 'ok',
      summary: {
        sleep: 7,
        battery: 82,
        stress: 33,
      },
    })
    getProfileMock.mockResolvedValue({
      openid: 'openid-1',
      garmin_bound: true,
    })

    const renderer = create(<Home />)
    await act(async () => {
      await flushPromises()
    })
    await act(async () => {
      await flushPromises()
    })

    const root = renderer.toJSON()
    const cards = getAllByTestId(root as TestNode | TestNode[], 'stat-card')
    expect(cards).toHaveLength(3)

    const loadingNodes = getTestId(root as TestNode | TestNode[], 'loading')
    expect(loadingNodes).toBeFalsy()
  })

  it('renders bind form and submits entered values', async () => {
    getDailyAnalysisMock.mockResolvedValue({
      date: '2024-01-01',
      raw_data_summary: 'ok',
      ai_advice: 'ok',
    })
    getProfileMock.mockResolvedValue({
      openid: 'openid-1',
      has_binding: false,
    })
    bindGarminMock.mockResolvedValue({ bound: true })

    const renderer = create(<Home />)
    await act(async () => {
      await flushPromises()
    })
    await act(async () => {
      await flushPromises()
    })

    const emailInput = renderer.root.findByProps({
      'data-testid': 'garmin-email-input',
    })
    const passwordInput = renderer.root.findByProps({
      'data-testid': 'garmin-password-input',
    })
    const isCnSwitch = renderer.root.findByProps({
      'data-testid': 'garmin-is-cn-switch',
    })
    const bindButton = renderer.root.findByProps({
      'data-testid': 'bind-submit',
    })

    await act(async () => {
      emailInput.props.onInput({ detail: { value: 'user@example.com' } })
      passwordInput.props.onInput({ detail: { value: 'secret' } })
      isCnSwitch.props.onChange({ detail: { value: true } })
    })

    await act(async () => {
      bindButton.props.onClick()
      await flushPromises()
    })

    expect(bindGarminMock).toHaveBeenCalledWith({
      openid: 'local-openid',
      garmin_email: 'user@example.com',
      garmin_password: 'secret',
      is_cn: true,
    })
  })

  it('shows rebind action when bound and refreshes to show form', async () => {
    getDailyAnalysisMock.mockResolvedValue({
      date: '2024-01-01',
      raw_data_summary: 'ok',
      ai_advice: 'ok',
    })
    getProfileMock
      .mockResolvedValueOnce({
        openid: 'openid-1',
        has_binding: true,
      })
      .mockResolvedValueOnce({
        openid: 'openid-1',
        has_binding: false,
      })
    unbindGarminMock.mockResolvedValue({ unbound: true })

    const renderer = create(<Home />)
    await act(async () => {
      await flushPromises()
    })
    await act(async () => {
      await flushPromises()
    })

    const rebindButton = renderer.root.findByProps({
      'data-testid': 'unbind-rebind',
    })

    await act(async () => {
      rebindButton.props.onClick()
      await flushPromises()
    })

    expect(unbindGarminMock).toHaveBeenCalledWith({ openid: 'local-openid' })
    const emailInput = renderer.root.findByProps({
      'data-testid': 'garmin-email-input',
    })
    expect(emailInput).toBeTruthy()
  })
})
