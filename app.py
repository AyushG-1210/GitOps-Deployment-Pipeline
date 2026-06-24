from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

# --- Configuration ---
CONFIG_FILE = 'config.json'

def load_config():
    """Loads the theme configuration from config.json"""
    config_path = os.path.join(app.root_path, CONFIG_FILE)
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback in case config.json is missing
        return {
            "theme_name": "Error",
            "main_text": "ERROR: config.json not found",
            "app_state": "theme-standby"
        }

# --- Routes ---

@app.route('/')
def index():
    """
    Renders the main page.
    The page will be loaded with the *initial* config.
    """
    config_data = load_config()
    return render_template('index.html', config=config_data)

@app.route('/api/theme')
def api_theme():
    """
    This is the API endpoint for JavaScript.
    It just returns the raw theme data as JSON.
    """
    config_data = load_config()
    return jsonify(config_data)

@app.route('/health')
def health():
    """Health check endpoint"""
    return "OK", 200

# --- Run the App ---
if __name__ == "__main__":
    # Run on port 5000, as specified in your Dockerfile
    app.run(host='0.0.0.0', port=5000)

