import api from './index'

export interface RegisterData {
  username: string
  email: string
  password: string
}

export interface LoginData {
  username: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
}

export function register(data: RegisterData) {
  return api.post('/api/auth/register', data)
}

export function login(data: LoginData) {
  return api.post<AuthResponse>('/api/auth/login', data)
}

export function getMe() {
  return api.get('/api/auth/me')
}
