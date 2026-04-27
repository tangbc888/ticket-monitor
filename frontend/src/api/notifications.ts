import api from './index'

export interface NotificationParams {
  skip?: number
  limit?: number
  unread_only?: boolean
}

export function getNotifications(params?: NotificationParams) {
  return api.get('/api/notifications', { params })
}

export function markAsRead(id: number) {
  return api.put(`/api/notifications/${id}/read`)
}

export function markAllAsRead() {
  return api.put('/api/notifications/read-all')
}
