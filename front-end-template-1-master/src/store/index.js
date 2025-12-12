// store/index.js
import Vue from 'vue'
import Vuex from 'vuex'
import { getToken, getUser, setToken, setUser, clearAuth } from '@/utils/auth'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    token: getToken() || '',
    user: getUser() || null
  },
  mutations: {
    SET_TOKEN(state, token) {
      state.token = token
      setToken(token) // 同时存到localStorage
    },
    SET_USER(state, user) {
      state.user = user
      setUser(user) // 同时存到localStorage
    },
    CLEAR_AUTH(state) {
      state.token = ''
      state.user = null
      clearAuth()
    }
  },
  getters: {
    isAuthenticated: state => !!state.token,
    currentUser: state => state.user,
    currentUserId: state => state.user?.user_id || state.user?.userId
  },
  actions: {
    login({ commit }, { token, user }) {
      commit('SET_TOKEN', token)
      commit('SET_USER', user)
    },
    logout({ commit }) {
      commit('CLEAR_AUTH')
    }
  },
  modules: {}
})