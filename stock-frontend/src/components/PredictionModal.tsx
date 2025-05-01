import { useEffect, useState } from 'react'
import { StockHolding } from '../api'
import { Line } from 'react-chartjs-2'
import { Chart, registerables } from 'chart.js'
import { fetchPrediction } from '../api'

Chart.register(...registerables)

interface Prediction {
  open: number
  high: number
  low: number
  close: number
  symbol: string
}

interface Props {
  stock: StockHolding
  onClose: () => void
}

export default function PredictionModal({ stock, onClose }: Props) {
  const [prediction, setPrediction] = useState<Prediction | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadPrediction = async () => {
      try {
        const data = await fetchPrediction(stock.symbol)
        setPrediction(data) // Directly set the prediction object
      } catch (error) {
        console.error('Failed to fetch prediction')
      } finally {
        setLoading(false)
      }
    }
    loadPrediction()
  }, [stock.symbol])

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white p-6 rounded-lg max-w-2xl w-full">
        <h2 className="text-xl font-bold mb-4">{stock.name} Price Prediction</h2>

        {loading ? (
          <div className="text-center py-4">Loading predictions...</div>
        ) : prediction ? (
          <div className="space-y-4">
            {/* Chart component */}
            <Line
              data={{
                labels: ['Prediction'], // Static label since it's one prediction
                datasets: [{
                  label: 'Predicted Close Price',
                  data: [prediction.close], // Access prediction directly
                  borderColor: '#4F46E5',
                  tension: 0.1
                }]
              }}
            />

            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 rounded">
                <h3 className="font-medium mb-2">Next Day Prediction</h3>
                <div className="space-y-1">
                  <div>Open: ${prediction.open.toFixed(2)}</div>
                  <div>High: ${prediction.high.toFixed(2)}</div>
                  <div>Low: ${prediction.low.toFixed(2)}</div>
                  <div>Close: ${prediction.close.toFixed(2)}</div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-4 text-red-600">Failed to load prediction data.</div>
        )}

        <button
          onClick={onClose}
          className="mt-4 px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded float-right"
        >
          Close
        </button>
      </div>
    </div>
  )
}
