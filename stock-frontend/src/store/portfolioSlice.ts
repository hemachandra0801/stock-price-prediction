// import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit'
// import { fetchPortfolio, StockHolding } from '../api'
// import api from '../api'

// interface TradeRequest {
//     symbol: string
//     action: 'buy' | 'sell'
//     shares: number
//     price: number
//   }

// interface PortfolioState {
//   holdings: StockHolding[]
//   totalValue: number
//   status: 'idle' | 'loading' | 'succeeded' | 'failed'
// }

// const initialState: PortfolioState = {
//   holdings: [],
//   totalValue: 0,
//   status: 'idle'
// }

// export const loadPortfolio = createAsyncThunk('portfolio/load', async () => {
//   return await fetchPortfolio()
// })

// export const executeTrade = createAsyncThunk(
//     'portfolio/executeTrade',
//     async (trade: TradeRequest, { rejectWithValue }) => {
//       try {
//         const response = await api.post('/api/trade', trade)
//         return response.data
//       } catch (error: any) {
//         return rejectWithValue(error.response?.data?.message || 'Trade failed')
//       }
//     }
//   )

//   const portfolioSlice = createSlice({
//     name: 'portfolio',
//     initialState,
//     reducers: {},
//     extraReducers: (builder) => {
//       builder
//         .addCase(executeTrade.pending, (state) => {
//           state.status = 'loading'
//         })
//         .addCase(executeTrade.fulfilled, (state, action: PayloadAction<StockHolding>) => {
//           const index = state.holdings.findIndex(h => h.symbol === action.payload.symbol)
          
//           if (index >= 0) {
//             // Update existing holding
//             state.holdings[index] = action.payload
//           } else {
//             // Add new holding
//             state.holdings.push(action.payload)
//           }
          
//           state.totalValue = state.holdings.reduce(
//             (sum, holding) => sum + (holding.shares * holding.currentPrice),
//             0
//           )
//           state.status = 'succeeded'
//         })
//         .addCase(executeTrade.rejected, (state) => {
//           state.status = 'failed'
//         })
//     }
//   })

// export default portfolioSlice.reducer








import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit';
import api from '../api';
import { logoutUser } from './authSlice';
import { store } from '.';

interface StockHolding {
  symbol: string;
  name: string;
  quantity: number;
  currentPrice: number;
  avgPrice: number;
  value: number;
  profitPercentage: number;
  prediction?: {
    open: number;
    high: number;
    low: number;
    close: number;
  };
  tradeShares?: number;
}

interface TradeRequest {
  symbol: string;
  action: 'buy' | 'sell';
  quantity: number;
  price: number;
}

interface PredictionResponse {
  symbol: string;
  predictions: {
    open: number;
    high: number;
    low: number;
    close: number;
  }
}

interface PortfolioState {
  holdings: StockHolding[];
  totalValue: number;
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const initialState: PortfolioState = {
  holdings: [],
  totalValue: 0,
  status: 'idle',
  error: null
};

export const loadPortfolio = createAsyncThunk(
  'portfolio/load',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/portfolio');
      return response.data;
    } catch (error: any) {
      // Handle 401 specifically
      if (error.response?.status === 401) {
        store.dispatch(logoutUser());
      }
      return rejectWithValue(
        error.response?.data?.detail || 
        'Failed to load portfolio. Please try again.'
      );
    }
  }
);

export const executeTrade = createAsyncThunk(
  'portfolio/executeTrade',
  async (trade: TradeRequest, { rejectWithValue }) => {
    try {
      const response = await api.post('/portfolio/transactions', trade)
      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Trade failed')
    }
  }
);

export const fetchPrediction = createAsyncThunk(
  'portfolio/fetchPrediction',
  async (symbol: string, { rejectWithValue }) => {
    try {
      const response = await api.get(`/portfolio/predictions/${symbol}`);
      return { symbol, ...response.data };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Prediction failed');
    }
  }
);

const portfolioSlice = createSlice({
  name: 'portfolio',
  initialState,
  reducers: {
    setTradeShares: (state, action: PayloadAction<{symbol: string; shares: number}>) => {
      const holding = state.holdings.find(h => h.symbol === action.payload.symbol);
      if (holding) {
        if (typeof holding.tradeShares === 'undefined') {
          holding.tradeShares = 0;
        }
        holding.tradeShares = action.payload.shares;
      }
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(loadPortfolio.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(loadPortfolio.fulfilled, (state, action: PayloadAction<StockHolding[]>) => {
        state.holdings = action.payload;
        state.totalValue = action.payload.reduce((sum, h) => sum + h.value, 0);
        state.status = 'succeeded';
      })
      .addCase(loadPortfolio.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message || 'Failed to load portfolio';
      })
      .addCase(executeTrade.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(executeTrade.fulfilled, (state, action: PayloadAction<StockHolding>) => {
        const index = state.holdings.findIndex(h => h.symbol === action.payload.symbol);
        if (index >= 0) {
          state.holdings[index] = action.payload;
        } else {
          state.holdings.push(action.payload);
        }
        state.totalValue = state.holdings.reduce((sum, h) => sum + h.value, 0);
        state.status = 'succeeded';
      })
      .addCase(executeTrade.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload as string;
      })
      .addCase(fetchPrediction.fulfilled, (state, action: PayloadAction<PredictionResponse>) => {
        const holding = state.holdings.find(h => h.symbol === action.payload.symbol);
        if (holding) {
          holding.prediction = action.payload.predictions
        }
      });
  }
});

export const { setTradeShares } = portfolioSlice.actions;
export default portfolioSlice.reducer;