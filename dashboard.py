import os
import sys
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv

# Load env variables before importing database
load_dotenv()

# Add project root to path so we can import backend_service
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend_service.core.services.crm_log_service import CRMLogService
from backend_service.core.database import Base, engine

# Ensure tables are created
Base.metadata.create_all(bind=engine)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
if hasattr(app, 'json'):
    app.json.ensure_ascii = False
log_service = CRMLogService()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/logs')
def get_logs():
    # Fetch latest 100 logs
    logs = log_service.get_logs(limit=100)
    return jsonify(logs)

@app.route('/api/traces')
def get_traces():
    import json
    log_file = os.path.join(os.getcwd(), "logs", "traces.jsonl")
    if not os.path.exists(log_file):
        return jsonify({"traces": []})
        
    traces = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    traces.append(json.loads(line))
                except:
                    pass
                    
    # Return newest first
    return jsonify({"traces": traces[::-1]})

if __name__ == '__main__':
    print("="*50)
    print("Starting CRM Log Dashboard on http://localhost:5000")
    print("="*50)
    app.run(debug=True, port=5000)
