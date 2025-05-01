// components/Auth/Login.tsx
import { useForm } from 'react-hook-form'
import { useAuth } from '../../hooks/useAuth'
import { Link } from 'react-router-dom'
import { FiLock, FiMail } from 'react-icons/fi'

interface LoginForm {
  email: string
  password: string
}

export default function Login() {
  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>()
  const { login, isLoading, error: authError } = useAuth()

  const onSubmit = async (data: LoginForm) => {
    try {
      await login(data.email, data.password)
    } catch (error) {
      console.error('Login failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50">
      <div className="w-full max-w-md px-8 py-12 bg-white rounded-3xl shadow-xl transition-all duration-300 hover:shadow-2xl">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-800 mb-4 animate-fade-in-down">
            Welcome Back
          </h1>
          <p className="text-gray-500">Sign in to manage your stock portfolio</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
          <div className="space-y-6">
            <div className="relative">
              <FiMail className="absolute top-1/2 left-4 transform -translate-y-1/2 text-gray-400" />
              <input
                {...register('email', {
                  required: 'Email is required',
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Invalid email address'
                  }
                })}
                type="email"
                placeholder="Email address"
                className="w-full pl-12 pr-4 py-3 rounded-lg border border-gray-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
                disabled={isLoading}
              />
              {errors.email && (
                <p className="text-red-500 text-sm mt-1 ml-1">{errors.email.message}</p>
              )}
            </div>

            <div className="relative">
              <FiLock className="absolute top-1/2 left-4 transform -translate-y-1/2 text-gray-400" />
              <input
                {...register('password', {
                  required: 'Password is required',
                  minLength: {
                    value: 8,
                    message: 'Password must be at least 8 characters'
                  }
                })}
                type="password"
                placeholder="Password"
                className="w-full pl-12 pr-4 py-3 rounded-lg border border-gray-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
                disabled={isLoading}
              />
              {errors.password && (
                <p className="text-red-500 text-sm mt-1 ml-1">{errors.password.message}</p>
              )}
            </div>
          </div>

          {authError && (
            <div className="text-center py-3 px-4 bg-red-50 text-red-600 rounded-lg animate-shake">
              {authError}
            </div>
          )}

          <button
            type="submit"
            className="w-full py-3 px-6 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-semibold rounded-lg transition-all transform hover:scale-[1.02]"
            disabled={isLoading}
          >
            {isLoading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                </svg>
                Signing in...
              </span>
            ) : (
              'Sign In'
            )}
          </button>

          <div className="text-center text-sm mt-6">
            <span className="text-gray-600">Don't have an account? </span>
            <Link
              to="/signup"
              className="font-semibold text-purple-600 hover:text-purple-700 transition-colors"
            >
              Create account
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}