// PortfolioPage.tsx
import { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../store/index';
import { loadPortfolio, executeTrade, fetchPrediction, setTradeShares } from '../store/portfolioSlice';

const PortfolioPage = () => {
  const dispatch = useAppDispatch();
  const { holdings, totalValue, status, error } = useAppSelector(state => state.portfolio);
  const [tradeAmounts, setTradeAmounts] = useState<{ [symbol: string]: number }>({});

  useEffect(() => {
    dispatch(loadPortfolio());
  }, [dispatch]);

  const handleTrade = (symbol: string, action: 'buy' | 'sell') => {
    const quantity = tradeAmounts[symbol] || 0;
    if (quantity > 0) {
      const holding = holdings.find(h => h.symbol === symbol);
      if (holding) {
        dispatch(executeTrade({
          symbol,
          action,
          quantity,
          price: holding.currentPrice
        }));
      }
    }
  };

  return (
    <div className="p-4">
      <div className="mb-8">
        <h2 className="text-2xl font-bold">
          Total Portfolio Value: ${totalValue.toLocaleString(undefined, { maximumFractionDigits: 2 })}
        </h2>
      </div>

      {error && <div className="text-red-500 mb-4">{error}</div>}

      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-gray-100">
            <th className="p-3 text-left">Symbol</th>
            <th className="p-3 text-left">Shares</th>
            <th className="p-3 text-left">Value</th>
            <th className="p-3 text-left">Profit %</th>
            <th className="p-3 text-left">Trade</th>
            <th className="p-3 text-left">Predict</th>
          </tr>
        </thead>
        <tbody>
          {holdings.map(holding => (
            <tr key={holding.symbol} className="border-b">
              <td className="p-3">
                <div className="font-medium">{holding.symbol}</div>
                <div className="text-sm text-gray-600">{holding.name}</div>
              </td>
              <td className="p-3">{holding.quantity.toLocaleString()}</td>
              <td className="p-3">${holding.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
              <td className={`p-3 ${holding.profitPercentage >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {holding.profitPercentage.toFixed(2)}%
              </td>
              <td className="p-3">
                <div className="flex gap-2">
                  <input
                    type="number"
                    min="1"
                    value={holding.tradeShares || ''}
                    onChange={(e) => {
                      const shares = Math.max(1, parseInt(e.target.value) || 0);
                      dispatch(setTradeShares({
                        symbol: holding.symbol,
                        shares
                      }));
                    }}
                    className="w-20 px-2 py-1 border rounded"
                  />
                  <button
                    onClick={() => handleTrade(holding.symbol, 'buy')}
                    className="px-3 py-1 bg-green-100 text-green-800 rounded hover:bg-green-200"
                  >
                    Buy
                  </button>
                  <button
                    onClick={() => handleTrade(holding.symbol, 'sell')}
                    className="px-3 py-1 bg-red-100 text-red-800 rounded hover:bg-red-200"
                  >
                    Sell
                  </button>
                </div>
              </td>
              <td className="p-3">
                <button
                  onClick={() => dispatch(fetchPrediction(holding.symbol))}
                  className="px-3 py-1 bg-blue-100 text-blue-800 rounded hover:bg-blue-200"
                >
                  Predict
                </button>
                {holding.prediction && (
                  <div className="mt-2 text-sm grid grid-cols-2 gap-1">
                    <div>O: {holding.prediction.open.toFixed(2)}</div>
                    <div>H: {holding.prediction.high.toFixed(2)}</div>
                    <div>L: {holding.prediction.low.toFixed(2)}</div>
                    <div>C: {holding.prediction.close.toFixed(2)}</div>
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {status === 'loading' && <div className="mt-4 text-gray-600">Loading...</div>}
    </div>
  );
};

export default PortfolioPage;