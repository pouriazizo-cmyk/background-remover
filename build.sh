#!/bin/bash
# Build script for background remover
#!/bin/bash

echo "🔧 Installing dependencies..."
pip install -r requirements.txt

echo "📁 Creating necessary directories..."
mkdir -p static/uploads

echo "✅ Setup completed!"
chmod +x start.sh

echo "🚀 Auto-ping system will be active in production"