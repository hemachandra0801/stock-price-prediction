import { useDispatch, useSelector } from 'react-redux'
import { AppDispatch, RootState } from '../store/index'
import { loginUser, registerUser, logoutUser } from '../store/authSlice'
import { useNavigate } from 'react-router-dom'

export const useAuth = () => {
  const dispatch = useDispatch<AppDispatch>()
  const navigate = useNavigate()
  const { user, status, error } = useSelector((state: RootState) => state.auth)

  const handleLogin = async (email: string, password: string) => {
    try {
      await dispatch(loginUser({ email, password })).unwrap()
      navigate('/')
    } catch (error) {
      throw error
    }
  }

  const handleSignup = async (email: string, password: string) => {
    try {
      await dispatch(registerUser({ email, password })).unwrap()
      navigate('/')
    } catch (error) {
      throw error
    }
  }

  const handleLogout = () => {
    dispatch(logoutUser())
    navigate('/login')
  }

  return {
    user,
    isAuthenticated: !!user,
    isLoading: status === 'loading',
    error,
    login: handleLogin,
    signup: handleSignup,
    logout: handleLogout
  }
}