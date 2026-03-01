import { useEffect, useRef, useState } from 'react'
import { View, Text, Input, Button, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'

import { chat, getChatHistory, getProfile } from '../../api/coach'
import type { ChatMessage, WechatProfileResponse } from '../../types'

import './index.scss'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [profile, setProfile] = useState<WechatProfileResponse | null>(null)
  const [scrollToMsg, setScrollToMsg] = useState('')
  const [pageHeight, setPageHeight] = useState(600)

  useEffect(() => {
    // windowHeight 已经是去掉导航栏后的可用高度
    const sysInfo = Taro.getSystemInfoSync()
    setPageHeight(sysInfo.windowHeight)

    fetchProfile()
    fetchHistory()
  }, [])

  useEffect(() => {
    // 每次 messages 变化，滚动到底部
    if (messages.length > 0) {
      const lastMsg = messages[messages.length - 1]
      // 先清空再设值，确保相同 id 也能触发滚动
      setScrollToMsg('')
      setTimeout(() => {
        setScrollToMsg(`msg-${lastMsg.id}`)
      }, 150)
    }
  }, [messages])

  const fetchProfile = async () => {
    try {
      const data = await getProfile()
      setProfile(data)
    } catch (err) {
      console.error('Failed to fetch profile:', err)
    }
  }

  const fetchHistory = async () => {
    try {
      const data = await getChatHistory(20)
      const historyMessages: Message[] = data.messages.map((msg: ChatMessage, idx: number) => ({
        id: `history-${msg.id || idx}`,
        role: msg.role,
        content: msg.content,
        timestamp: msg.created_at || new Date().toISOString(),
      }))
      setMessages(historyMessages)
    } catch (err) {
      console.error('Failed to fetch chat history:', err)
    }
  }

  const handleSend = async () => {
    if (!inputValue.trim() || loading) return

    const userMessage = inputValue.trim()
    setInputValue('')

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])

    const loadingMsg: Message = {
      id: 'loading',
      role: 'assistant',
      content: '...',
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, loadingMsg])

    setLoading(true)

    try {
      const response = await chat({ message: userMessage })

      setMessages(prev => {
        const filtered = prev.filter(msg => msg.id !== 'loading')
        const aiMsg: Message = {
          id: `ai-${Date.now()}`,
          role: 'assistant',
          content: response.reply,
          timestamp: new Date().toISOString(),
        }
        return [...filtered, aiMsg]
      })
    } catch (err) {
      setMessages(prev => {
        const filtered = prev.filter(msg => msg.id !== 'loading')
        const errorMsg: Message = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: '抱歉，发送失败，请稍后重试。',
          timestamp: new Date().toISOString(),
        }
        return [...filtered, errorMsg]
      })
    } finally {
      setLoading(false)
    }
  }

  const isBound = profile?.has_binding

  // 输入区域高度（padding + input + safe area ≈ 56px）
  const inputAreaHeight = 56
  const scrollHeight = pageHeight - inputAreaHeight

  return (
    <View className='chat-page'>
      {!isBound ? (
        <View className='chat-empty'>
          <Text className='chat-empty-text'>请先绑定 Garmin 账号，然后和教练聊天</Text>
          <Button className='primary-button' onClick={() => Taro.switchTab({ url: '/pages/home/index' })}>
            去绑定
          </Button>
        </View>
      ) : (
        <>
          <ScrollView
            className='chat-messages'
            scrollY
            scrollIntoView={scrollToMsg}
            scrollWithAnimation
            style={{ height: `${scrollHeight}px` }}
          >
            {messages.length === 0 ? (
              <View className='chat-welcome'>
                <Text className='chat-welcome-title'>🏃‍♂️ 冠军你好！</Text>
                <Text className='chat-welcome-text'>
                  我是你的 AI 跑步教练，有什么关于训练、睡眠、恢复的问题都可以问我！
                </Text>
              </View>
            ) : (
              messages.map(msg => (
                <View
                  key={msg.id}
                  id={`msg-${msg.id}`}
                  className={`chat-message ${msg.role === 'user' ? 'chat-message-user' : 'chat-message-assistant'}`}
                >
                  <View className='chat-message-content'>
                    <Text className='chat-message-text'>{msg.content}</Text>
                  </View>
                </View>
              ))
            )}
          </ScrollView>

          <View className='chat-input-area'>
            <Input
              className='chat-input'
              type='text'
              placeholder='问教练一个问题...'
              value={inputValue}
              onInput={(e) => setInputValue(e.detail.value)}
              onConfirm={handleSend}
              confirmType='send'
              disabled={loading}
            />
            <Button
              className='chat-send-button'
              onClick={handleSend}
              disabled={!inputValue.trim() || loading}
            >
              {loading ? '...' : '↑'}
            </Button>
          </View>
        </>
      )}
    </View>
  )
}

export default Chat
