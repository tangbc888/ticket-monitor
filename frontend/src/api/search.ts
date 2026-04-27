import api from './index'

export interface SearchParams {
  keyword: string
  platform?: string
}

export function searchEvents(data: SearchParams) {
  return api.post('/api/search', data, { timeout: 30000 })
}

// 获取演出详情（场次列表）
export function getEventDetail(eventId: string, platform: string) {
  return api.get('/api/events/detail', {
    params: { event_id: eventId, platform },
    timeout: 30000
  })
}
