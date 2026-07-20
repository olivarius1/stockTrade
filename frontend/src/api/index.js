/**
 * API 请求模块。
 *
 * 使用 axios 实例统一管理请求，自动附加 JWT token 和 401 跳转登录。
 * baseURL 为 /api，开发环境通过 Vite proxy 转发到后端 8001 端口。
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(response => {
  return response.data
}, error => {
  if (error.response && error.response.status === 401) {
    localStorage.removeItem('token')
    window.location.href = '/login'
  }
  return Promise.reject(error)
})

export const authAPI = {
  login(data) {
    return api.post('/auth/login', data)
  },
  verify() {
    return api.get('/auth/verify')
  }
}

/**
 * 股票数据 API。
 * 获取股票基本信息和搜索，估值相关调用见 valuationAPI。
 */
export const stockAPI = {
  search(keyword) {
    return api.get('/stock/search', { params: { keyword } })
  },
  getInfo(code) {
    return api.get(`/stock/${code}`)
  },
  getSectors() {
    return api.get('/stock/sectors')
  },
  getSectorStocks(industry) {
    return api.get(`/stock/sectors/${industry}`)
  }
}

/**
 * 估值 API。
 * 为什么独立模块：估值是核心功能，独立 API 模块使调用方更清晰。
 */
export const valuationAPI = {
  getReport(code, modelCode) {
    return api.get(`/valuation/report/${code}`, { params: { model_code: modelCode } })
  },
  getHistory(code, startDate, endDate) {
    return api.get(`/valuation/history/${code}`, { params: { start_date: startDate, end_date: endDate } })
  },
  getMarketUndervalued(params) {
    return api.get('/valuation/market/undervalued', { params })
  },
  incremental(code) {
    return api.post(`/valuation/incremental/${code}`)
  }
}

/** 自选股管理 API */
export const watchlistAPI = {
  getList() {
    return api.get('/watchlist')
  },
  getSummary(groupId) {
    return api.get('/watchlist/summary', { params: { group_id: groupId } })
  },
  add(item) {
    return api.post('/watchlist', item)
  },
  remove(code) {
    return api.delete(`/watchlist/${code}`)
  },
  batchCalculate() {
    return api.post('/watchlist/batch')
  },
  moveToGroup(code, groupId) {
    return api.put(`/watchlist/${code}/group`, null, { params: { group_id: groupId } })
  }
}

/** 定时任务管理 API */
export const schedulerAPI = {
  getConfig() {
    return api.get('/scheduler/config')
  },
  updateConfig(config) {
    return api.put('/scheduler/config', config)
  },
  run() {
    return api.post('/scheduler/run')
  },
  triggerKlineFetch() {
    return api.post('/scheduler/kline-fetch')
  },
  getKlineFetchProgress() {
    return api.get('/scheduler/kline-fetch/progress')
  },
  getKlineFetchHistory() {
    return api.get('/scheduler/kline-fetch/history')
  }
}

/** 估值模型和因子管理 API */
export const modelsAPI = {
  getModels() {
    return api.get('/models')
  },
  getModel(code) {
    return api.get(`/models/${code}`)
  },
  getFactors() {
    return api.get('/models/factors')
  },
  getFactor(code) {
    return api.get(`/models/factors/${code}`)
  }
}

/** 分组管理 API */
export const groupAPI = {
  getList() {
    return api.get('/groups')
  },
  create(data) {
    return api.post('/groups', data)
  },
  rename(id, data) {
    return api.put(`/groups/${id}`, data)
  },
  remove(id) {
    return api.delete(`/groups/${id}`)
  }
}

export default api
