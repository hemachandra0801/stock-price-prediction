#!/bin/bash

# Navigate to project directory
cd /home/hiran/Desktop/mlops/project/stock-price-prediction

# Activate virtual environment (if using one)
source venv/bin/activate  # Adjust path as needed

# Run scripts with error handling
echo "$(date): Starting data pipeline" >> cron.log

python createdata.py && \
python loadhistoricaldata.py >> cron.log 2>&1

if [ $? -eq 0 ]; then
    echo "$(date): Success" >> cron.log
else
    echo "$(date): Failed - check errors above" >> cron.log
    # Optional: Send alert
    # mail -s "Data Pipeline Failed" your@email.com < cron.log
fi