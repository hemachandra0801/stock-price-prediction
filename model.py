import json

with open('stock-price-prediction/config.json') as f:
    data = json.load(f)

stock_list = data['Stocks']
print(stock_list)  # Will show the list of stocks