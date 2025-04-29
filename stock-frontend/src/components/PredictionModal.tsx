import { useEffect, useState } from 'react'
import { StockHolding } from '../api'
import { Line } from 'react-chartjs-2'
import { Chart, registerables } from 'chart.js'
import { fetchPrediction } from '../api'

Chart.register(...registerables)

interface Prediction {
  date: string
  open: number
  high: number
  low: number
  close: number
}

interface Props {
  stock: StockHolding
  onClose: () => void
}

export default function PredictionModal({ stock, onClose }: Props) {
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadPrediction = async () => {
      try {
        const data = await fetchPrediction(stock.symbol)
        setPredictions(data)
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
        ) : (
          <div className="space-y-4">
            <Line
              data={{
                labels: predictions.map(p => p.date),
                datasets: [{
                  label: 'Predicted Close Price',
                  data: predictions.map(p => p.close),
                  borderColor: '#4F46E5',
                  tension: 0.1
                }]
              }}
            />
            
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 rounded">
                <h3 className="font-medium mb-2">Next Day Prediction</h3>
                <div className="space-y-1">
                  <div>Open: ${predictions[0]?.open.toFixed(2)}</div>
                  <div>High: ${predictions[0]?.high.toFixed(2)}</div>
                  <div>Low: ${predictions[0]?.low.toFixed(2)}</div>
                  <div>Close: ${predictions[0]?.close.toFixed(2)}</div>
                </div>
              </div>
            </div>
          </div>
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