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

export const stockAPI = {
  search(keyword) {
    return api.get('/stock/search', { params: { keyword } })
  },
  getInfo(code) {
    return api.get(`/stock/${code}`)
  },
  getValuation(code, modelCode) {
    return api.get(`/stock/${code}/valuation`, { params: { model_code: modelCode } })
  },
  getHistory(code, startDate, endDate) {
    return api.get(`/stock/${code}/history`, { params: { start_date: startDate, end_date: endDate } })
  }
}

export const watchlistAPI = {
  getList() {
    return api.get('/watchlist')
  },
  add(item) {
    return api.post('/watchlist', item)
  },
  remove(code) {
    return api.delete(`/watchlist/${code}`)
  },
  batchCalculate() {
    return api.post('/watchlist/batch')
  }
}

export const schedulerAPI = {
  getConfig() {
    return api.get('/scheduler/config')
  },
  updateConfig(config) {
    return api.put('/scheduler/config', config)
  },
  run() {
    return api.post('/scheduler/run')
  }
}

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

export default api
