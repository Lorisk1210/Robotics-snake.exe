import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from frontend.app_frontend import app

if __name__ == '__main__':
    print("="*60)
    print("Starting Snakes & Ladders Frontend Server")
    print("="*60)
    print("\nOpen your browser and go to:")
    print("  http://localhost:5001")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=False)

