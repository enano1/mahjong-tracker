#!/bin/bash

echo "Starting Mahjong Tracker..."
echo "Installing dependencies..."
pip3 install -r requirements.txt

echo "Starting server..."
python3 app.py 