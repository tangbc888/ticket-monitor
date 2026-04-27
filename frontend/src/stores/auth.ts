import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as apiLogin, register as apiRegister, getMe } from '../api/auth'
import type { LoginData, RegisterData } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref<any>(null)
  const loading = ref(false)

  async function login(data: LoginData) {
    loading.value = true
    try {
      const res = await apiLogin(data)
      token.value = res.data.access_token
      localStorage.setItem('token', token.value)
      await fetchUser()
    } finally {
      loading.value = false
    }
  }

  async function register(data: RegisterData) {
    loading.value = true
    try {
      await apiRegister(data)
    } finally {
      loading.value = false
    }
  }

  async function fetchUser() {
    try {
      const res = await getMe()
      user.value = res.data
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    window.location.href = '/login'
  }

  async function init() {
    if (token.value) {
      await fetchUser()
    }
  }

  return { token, user, loading, login, register, fetchUser, logout, init }
})
