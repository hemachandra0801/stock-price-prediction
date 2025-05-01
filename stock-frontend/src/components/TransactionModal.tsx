import { useState } from 'react'
import { StockHolding } from '../api'
import { useAppDispatch } from '../store/index'
import { executeTrade } from '../store/portfolioSlice'

interface Props {
  stock: StockHolding
  actionType: 'buy' | 'sell'
  onClose: () => void
}

export default function TransactionModal({ stock, actionType, onClose }: Props) {
  const [shares, setShares] = useState('')
  const dispatch = useAppDispatch()

  const handleSubmit = async () => {
    const sharesNumber = parseInt(shares)
    if (sharesNumber > 0) {
      await dispatch(executeTrade({
        symbol: stock.symbol,
        action: actionType,
        quantity: sharesNumber,
        price: stock.currentPrice
      }))
      onClose()
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white p-6 rounded-lg max-w-sm w-full">
        <h2 className="text-xl font-bold mb-4">
          {actionType === 'buy' ? 'Buy' : 'Sell'} {stock.name}
        </h2>
        <input
          type="number"
          value={shares}
          onChange={(e) => setShares(e.target.value)}
          placeholder="Number of shares"
          className="w-full mb-4 p-2 border rounded"
        />
        <div className="flex justify-end space-x-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className={`px-4 py-2 text-white rounded ${
              actionType === 'buy' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
            }`}
          >
            Confirm {actionType}
          </button>
        </div>
      </div>
    </div>
  )
}