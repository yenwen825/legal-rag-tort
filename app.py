"""
Legal RAG Tort - Flask Application
侵害配偶權判決 AI 檢索系統
"""

from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')


@app.route('/')
def index():
    """首頁"""
    return render_template('index.html')


@app.route('/api/search', methods=['POST'])
def search():
    """
    搜尋相似判決 API
    
    Request Body:
        {
            "query": "案情描述文字"
        }
    
    Response:
        {
            "results": [...],
            "stats": {...}
        }
    """
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': '請輸入查詢內容'}), 400
        
        # TODO: 實作向量搜尋邏輯
        return jsonify({
            'results': [],
            'stats': {
                'total': 0,
                'median_compensation': 0,
                'avg_compensation': 0,
                'min_compensation': 0,
                'max_compensation': 0
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/judgment/<judgment_id>')
def get_judgment(judgment_id):
    """
    取得判決詳細內容
    
    Args:
        judgment_id: 判決 ID
    
    Response:
        {
            "id": "...",
            "title": "...",
            "content": "...",
            "compensation": 0,
            "related_cases": []
        }
    """
    try:
        # TODO: 從資料庫查詢判決詳細內容
        return jsonify({
            'error': 'Not implemented yet'
        }), 501
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
