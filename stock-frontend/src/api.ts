import axios from 'axios'

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  withCredentials: true
})

api.interceptors.request.use(async (config) => {
    if (['post', 'put', 'patch', 'delete'].includes(config.method?.toLowerCase() ?? '')) {
      const { data } = await axios.get(
        `${process.env.REACT_APP_API_URL}/auth/csrf-token`,
        { withCredentials: true }
      )
      config.headers['X-CSRF-Token'] = data.csrfToken
    }
    return config
})

export interface StockHolding {
  symbol: string
  name: string
  shares: number
  currentPrice: number
  profitPercentage: number
}

export const fetchPortfolio = async (): Promise<StockHolding[]> => {
  const response = await api.get('/portfolio')
  return response.data
}

export const fetchPrediction = async (symbol: string): Promise<any> => {
  const response = await api.get(`/predict/${symbol}`)
  return response.data
}
  
export default api