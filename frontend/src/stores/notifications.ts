import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getNotifications as apiGetNotifications, markAsRead as apiMarkAsRead, markAllAsRead as apiMarkAllAsRead } from '../api/notifications'

export interface Notification {
  id: number
  task_id: number
  event_name: string
  message: string
  change_type: string
  is_read: boolean
  created_at: string
}

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref<Notification[]>([])
  const loading = ref(false)

  const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

  async function fetchNotifications(unreadOnly = false) {
    loading.value = true
    try {
      const res = await apiGetNotifications({ unread_only: unreadOnly, limit: 100 })
      notifications.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function markRead(id: number) {
    await apiMarkAsRead(id)
    const n = notifications.value.find(n => n.id === id)
    if (n) n.is_read = true
  }

  async function markAllRead() {
    await apiMarkAllAsRead()
    notifications.value.forEach(n => n.is_read = true)
  }

  function addNotification(notification: Notification) {
    notifications.value.unshift(notification)
  }

  return { notifications, loading, unreadCount, fetchNotifications, markRead, markAllRead, addNotification }
})
