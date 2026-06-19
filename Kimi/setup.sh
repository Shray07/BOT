#!/bin/bash
# Schengen Visa Monitor - Setup Script
# Run this first to install everything

echo "🔧 Setting up Schengen Visa Monitor..."

# Check Python version
python3 --version || python --version

# Install dependencies
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright Chromium..."
playwright install chromium

# Create data directory
mkdir -p data

echo "✅ Setup complete!"
echo ""
echo "⚠️  IMPORTANT: Before running, you MUST edit visa_monitor.py and set:"
echo "   - EMAIL_SENDER (your Gmail address)"
echo "   - EMAIL_PASSWORD (Gmail App Password, NOT your regular password)"
echo ""
echo "📖 How to get Gmail App Password:"
echo "   1. Go to https://myaccount.google.com/apppasswords"
echo "   2. Sign in with your Google Account"
echo "   3. Select 'Mail' and 'Other (Custom name)'"
echo "   4. Name it 'Visa Monitor'"
echo "   5. Copy the 16-character password"
echo ""
echo "🚀 To start monitoring:"
echo "   python3 visa_monitor.py"
