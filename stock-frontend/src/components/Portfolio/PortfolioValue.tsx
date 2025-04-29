import { useSelector } from 'react-redux'
import { RootState } from '../../store/index'
import numeral from 'numeral'

export default function PortfolioValue() {
  const { totalValue } = useSelector((state: RootState) => state.portfolio)
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm mb-8">
      <h2 className="text-2xl font-bold text-gray-900">
        Portfolio Value: {numeral(totalValue).format('$0,0.00')}
      </h2>
    </div>
  )
}