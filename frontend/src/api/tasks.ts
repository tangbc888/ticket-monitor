import api from './index'

export interface TaskData {
  event_name: string
  event_url: string
  platform: string
  target_session?: string
  check_interval?: number
  is_active?: boolean
}

export function getTasks() {
  return api.get('/api/tasks')
}

export function createTask(data: TaskData) {
  return api.post('/api/tasks', data)
}

export function updateTask(id: number, data: Partial<TaskData>) {
  return api.put(`/api/tasks/${id}`, data)
}

export function deleteTask(id: number) {
  return api.delete(`/api/tasks/${id}`)
}

export function getTaskStatus(id: number) {
  return api.get(`/api/tasks/${id}/status`)
}
