"""
Flask application package initialization.
"""
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Flask: The configured Flask application instance.
    """
    # 加载.env文件
    load_dotenv()
    app = Flask(__name__)
    CORS(app)
    
    # Import and register blueprints
    from api.api import api_bp
    app.register_blueprint(api_bp)
    
    return app