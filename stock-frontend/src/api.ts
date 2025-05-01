import axios from 'axios'
import { store } from './store';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  withCredentials: true
})

api.interceptors.response.use(
  response => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Handle token expiration
    }
    return Promise.reject(error);
  }
);

api.interceptors.request.use(async (config) => {
    const token = store.getState().auth.user?.token;
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    if (['post', 'put', 'patch', 'delete'].includes(config.method?.toLowerCase() || '')) {
      try {
        const { data } = await api.get("/auth/csrf-token");
        config.headers["X-CSRF-Token"] = data.csrf_token;
      } catch (error) {
        console.error("CSRF token fetch failed:", error);
      }
    }
    return config
}, (error) => {
  return Promise.reject(error);
});

export interface StockHolding {
  symbol: string
  name: string
  quantity: number
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