import Taro from '@tarojs/taro'
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'

import { getDailyAnalysis } from '../src/api/coach'

vi.mock('@tarojs/taro', () => {
  return {
    default: {
      request: vi.fn(),
    },
  }
})

const requestMock = Taro.request as unknown as ReturnType<typeof vi.fn>

describe('api client', () => {
  beforeEach(() => {
    requestMock.mockResolvedValue({ data: { ok: true } })
  })

  afterEach(() => {
    requestMock.mockReset()
    delete process.env.TARO_APP_API_BASE_URL
  })

  it('uses base url without double slashes', async () => {
    process.env.TARO_APP_API_BASE_URL = 'https://example.com/'

    await getDailyAnalysis()

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        url: 'https://example.com/api/coach/daily-analysis',
        method: 'GET',
      })
    )
  })

  it('calls Taro.request with default base url', async () => {
    await getDailyAnalysis()

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        url: '/api/coach/daily-analysis',
        method: 'GET',
      })
    )
  })
})
