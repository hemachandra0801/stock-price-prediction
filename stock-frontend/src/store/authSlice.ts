// authSlice.ts
import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import api from '../api';
import type { AppDispatch, RootState } from './index';

interface AuthState {
  user: null | { email: string; userId?: string, token: string };
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  status: 'idle',
  error: null
};

export const loginUser = createAsyncThunk(
  'auth/login',
  async (credentials: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const formData = new URLSearchParams();
      formData.append('username', credentials.email);
      formData.append('password', credentials.password);
      
      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRF-Token': await getCSRFToken()
        }
      });
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || error.message || 'Login failed');
    }
  }
);

export const registerUser = createAsyncThunk(
  'auth/register',
  async (credentials: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const formData = new URLSearchParams();
      formData.append('email', credentials.email);
      formData.append('password', credentials.password);
      
      const response = await api.post('/auth/register', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRF-Token': await getCSRFToken()
        }
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          // Join multiple errors
          return rejectWithValue(
            error.response.data.detail.map((e: any) => e.msg).join(', ')
          );
        }
        return rejectWithValue(error.response.data.detail);
      }
      return rejectWithValue(error.response?.data?.detail || error.message || 'Registration failed');
    }
  }
);

// CSRF Token Helper
const getCSRFToken = async () => {
  const response = await api.get('/auth/csrf-token');
  return response.data.csrf_token;
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logoutUser: (state) => {
      state.user = null;
      api.post('/auth/logout');
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(loginUser.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.user = { 
          email: action.payload.email,
          userId: action.payload.user_id,
          token: action.payload.access_token
        };
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload as string;
      })
      .addCase(registerUser.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.user = {
          email: action.payload.email,
          userId: action.payload.user_id,
          token: action.payload.access_token
        };
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.status = 'failed';
        if (typeof action.payload === 'string') {
          state.error = action.payload;
        } else {
          state.error = 'Invalid registration data';
        }
      });
  }
});

export const { logoutUser } = authSlice.actions;
export const selectCurrentUser = (state: RootState) => state.auth.user;
export default authSlice.reducer;