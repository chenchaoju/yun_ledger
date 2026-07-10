import { defineStore } from 'pinia'
import http from '../utils/http'
import { disableAutoLoginForSession } from '../utils/authPreferences'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('access_token') || '',
    user: JSON.parse(localStorage.getItem('current_user') || 'null')
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token)
  },
  actions: {
    setSession(data) {
      this.token = data.access_token
      this.user = data.user
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('current_user', JSON.stringify(data.user))
    },
    async login(payload) {
      const { data } = await http.post('/auth/login', payload)
      this.setSession(data)
    },
    async register(payload) {
      const { data } = await http.post('/auth/register', payload)
      this.setSession(data)
    },
    async fetchMe() {
      const { data } = await http.get('/auth/me')
      this.user = data
      localStorage.setItem('current_user', JSON.stringify(data))
    },
    async updateProfile(payload) {
      const { data } = await http.put('/auth/me', payload)
      this.user = data
      localStorage.setItem('current_user', JSON.stringify(data))
    },
    logout() {
      disableAutoLoginForSession()
      this.token = ''
      this.user = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('current_user')
    }
  }
})
