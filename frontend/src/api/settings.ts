import api from './index'

export interface SettingsData {
  email?: string
  email_notify_enabled?: boolean
  websocket_notify_enabled?: boolean
}

export function getSettings() {
  return api.get('/api/settings')
}

export function updateSettings(data: SettingsData) {
  return api.put('/api/settings', data)
}
