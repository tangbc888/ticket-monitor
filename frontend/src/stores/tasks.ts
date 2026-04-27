import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getTasks as apiGetTasks, createTask as apiCreateTask, updateTask as apiUpdateTask, deleteTask as apiDeleteTask } from '../api/tasks'
import type { TaskData } from '../api/tasks'

export interface Task {
  id: number
  event_name: string
  event_url: string
  platform: string
  target_session: string
  check_interval: number
  is_active: boolean
  last_checked_at: string | null
  created_at: string
}

export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref<Task[]>([])
  const loading = ref(false)

  async function fetchTasks() {
    loading.value = true
    try {
      const res = await apiGetTasks()
      tasks.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function addTask(data: TaskData) {
    const res = await apiCreateTask(data)
    tasks.value.unshift(res.data)
    return res.data
  }

  async function editTask(id: number, data: Partial<TaskData>) {
    const res = await apiUpdateTask(id, data)
    const idx = tasks.value.findIndex(t => t.id === id)
    if (idx !== -1) tasks.value[idx] = res.data
    return res.data
  }

  async function removeTask(id: number) {
    await apiDeleteTask(id)
    tasks.value = tasks.value.filter(t => t.id !== id)
  }

  const activeTasks = () => tasks.value.filter(t => t.is_active)

  return { tasks, loading, fetchTasks, addTask, editTask, removeTask, activeTasks }
})
