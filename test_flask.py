#!/usr/bin/env python3
import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Test Flask App is Working!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"Starting test Flask app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
