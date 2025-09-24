#!/bin/bash
# Start script for background remover
#!/bin/bash

# فعال کردن پینگ خودکار در محیط production
export ENVIRONMENT=production

# شروع برنامه
echo "🚀 Starting Background Remover App with Auto-Ping..."
gunicorn --bind 0.0.0.0:8000 --preload app:app