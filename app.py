from flask import Flask, render_template
from api import register_blueprints
import os
from dotenv import load_dotenv
from services.judgment_service import get_judgment_by_id

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

register_blueprints(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/judgment/<int:id>')
def judgment(id: int):
    return render_template('judgment.html', judgment=get_judgment_by_id(id))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
