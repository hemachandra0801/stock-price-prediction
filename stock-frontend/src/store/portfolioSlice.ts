import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit'
import { fetchPortfolio, StockHolding } from '../api'
import api from '../api'

interface TradeRequest {
    symbol: string
    action: 'buy' | 'sell'
    shares: number
    price: number
  }

interface PortfolioState {
  holdings: StockHolding[]
  totalValue: number
  status: 'idle' | 'loading' | 'succeeded' | 'failed'
}

const initialState: PortfolioState = {
  holdings: [],
  totalValue: 0,
  status: 'idle'
}

export const loadPortfolio = createAsyncThunk('portfolio/load', async () => {
  return await fetchPortfolio()
})

export const executeTrade = createAsyncThunk(
    'portfolio/executeTrade',
    async (trade: TradeRequest, { rejectWithValue }) => {
      try {
        const response = await api.post('/api/trade', trade)
        return response.data
      } catch (error: any) {
        return rejectWithValue(error.response?.data?.message || 'Trade failed')
      }
    }
  )

  const portfolioSlice = createSlice({
    name: 'portfolio',
    initialState,
    reducers: {},
    extraReducers: (builder) => {
      builder
        .addCase(executeTrade.pending, (state) => {
          state.status = 'loading'
        })
        .addCase(executeTrade.fulfilled, (state, action: PayloadAction<StockHolding>) => {
          const index = state.holdings.findIndex(h => h.symbol === action.payload.symbol)
          
          if (index >= 0) {
            // Update existing holding
            state.holdings[index] = action.payload
          } else {
            // Add new holding
            state.holdings.push(action.payload)
          }
          
          state.totalValue = state.holdings.reduce(
            (sum, holding) => sum + (holding.shares * holding.currentPrice),
            0
          )
          state.status = 'succeeded'
        })
        .addCase(executeTrade.rejected, (state) => {
          state.status = 'failed'
        })
    }
  })

export default portfolioSlice.reducer