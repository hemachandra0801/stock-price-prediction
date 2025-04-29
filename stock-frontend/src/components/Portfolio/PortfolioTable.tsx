import { useState } from 'react'
import { StockHolding } from '../../api'
import { FiArrowUp, FiArrowDown } from 'react-icons/fi'
import TransactionModal from '../TransactionModal'
import PredictionModal from '../PredictionModal'
import numeral from 'numeral'

interface Props {
  holdings: StockHolding[]
}

export default function PortfolioTable({ holdings }: Props) {
  const [selectedStock, setSelectedStock] = useState<StockHolding | null>(null)
  const [actionType, setActionType] = useState<'buy' | 'sell' | null>(null)
  const [showPrediction, setShowPrediction] = useState(false)

  const getProfitColor = (profit: number) => 
    profit > 0 ? 'text-green-600' : profit < 0 ? 'text-red-600' : 'text-gray-500'

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Shares</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Profit</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {holdings.map((holding) => (
            <tr key={holding.symbol}>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="font-medium text-gray-900">{holding.name}</div>
                <div className="text-sm text-gray-500">{holding.symbol}</div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">{holding.shares}</td>
              <td className="px-6 py-4 whitespace-nowrap">
                {numeral(holding.currentPrice).format('$0,0.00')}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {numeral(holding.shares * holding.currentPrice).format('$0,0.00')}
              </td>
              <td className={`px-6 py-4 whitespace-nowrap ${getProfitColor(holding.profitPercentage)}`}>
                <div className="flex items-center">
                    {holding.profitPercentage > 0 ? (
                        <FiArrowUp className="w-4 h-4" />
                    ) : (
                        <FiArrowDown className="w-4 h-4" />
                    )}
                  <span className="ml-1">{holding.profitPercentage.toFixed(2)}%</span>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap space-x-2">
                <button
                  onClick={() => {
                    setSelectedStock(holding)
                    setActionType('buy')
                  }}
                  className="px-3 py-1 bg-green-100 text-green-800 rounded-md hover:bg-green-200"
                >
                  Buy
                </button>
                <button
                  onClick={() => {
                    setSelectedStock(holding)
                    setActionType('sell')
                  }}
                  className="px-3 py-1 bg-red-100 text-red-800 rounded-md hover:bg-red-200"
                >
                  Sell
                </button>
                <button
                  onClick={() => {
                    setSelectedStock(holding)
                    setShowPrediction(true)
                  }}
                  className="px-3 py-1 bg-blue-100 text-blue-800 rounded-md hover:bg-blue-200"
                >
                  Predict
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {selectedStock && actionType && (
        <TransactionModal
          stock={selectedStock}
          actionType={actionType}
          onClose={() => {
            setSelectedStock(null)
            setActionType(null)
          }}
        />
      )}

      {selectedStock && showPrediction && (
        <PredictionModal
          stock={selectedStock}
          onClose={() => {
            setSelectedStock(null)
            setShowPrediction(false)
          }}
        />
      )}
    </div>
  )
}