#!/bin/sh
# Run the script to download models
echo "Running download_model.py..."
python download_model.py
# Start the API server
echo "Starting the FastAPI server..."
python app.py