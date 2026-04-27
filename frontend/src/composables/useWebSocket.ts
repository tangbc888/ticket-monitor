import { ref, onUnmounted } from 'vue'
import { ElNotification } from 'element-plus'
import { useNotificationsStore } from '../stores/notifications'

export function useWebSocket() {
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  function connect() {
    const token = localStorage.getItem('token')
    if (!token) return

    const wsUrl = `ws://localhost:8000/ws/notifications?token=${token}`
    ws.value = new WebSocket(wsUrl)

    ws.value.onopen = () => {
      connected.value = true
    }

    ws.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const store = useNotificationsStore()
        store.addNotification(data)

        ElNotification({
          title: '票务变动通知',
          message: data.message || `${data.event_name} 有新的票务变动`,
          type: 'warning',
          duration: 5000
        })
      } catch (e) {
        console.error('WebSocket消息解析失败:', e)
      }
    }

    ws.value.onclose = () => {
      connected.value = false
      // 5秒后自动重连
      reconnectTimer = setTimeout(connect, 5000)
    }

    ws.value.onerror = () => {
      ws.value?.close()
    }
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    ws.value?.close()
    ws.value = null
    connected.value = false
  }

  onUnmounted(() => {
    disconnect()
  })

  return { connected, connect, disconnect }
}
