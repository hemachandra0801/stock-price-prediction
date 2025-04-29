import { useEffect } from 'react'
import { useAppDispatch, useAppSelector } from '../store/index'
import { loadPortfolio } from '../store/portfolioSlice'
import PortfolioValue from './Portfolio/PortfolioValue'
import PortfolioTable from './Portfolio/PortfolioTable'
import { useAuth } from '../hooks/useAuth'

const HomePage = () => {
  const dispatch = useAppDispatch()
  const { holdings, status } = useAppSelector((state) => state.portfolio)
  const { logout } = useAuth()

  useEffect(() => {
    dispatch(loadPortfolio())
  }, [dispatch])

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold">Stock Portfolio</h1>
        <button
          onClick={logout}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Logout
        </button>
      </div>
      
      <PortfolioValue />
      
      {status === 'loading' ? (
        <div className="text-center py-8">Loading portfolio...</div>
      ) : (
        <PortfolioTable holdings={holdings} />
      )}
    </div>
  )
}

export default HomePage