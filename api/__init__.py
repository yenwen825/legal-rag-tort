from api.health import health_bp
from api.search import search_bp

def register_blueprints(app):
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(search_bp, url_prefix='/api')