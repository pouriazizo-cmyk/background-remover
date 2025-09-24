#!/bin/bash
# Start script for background remover
#!/bin/bash
gunicorn --bind 0.0.0.0:$PORT --preload app:app