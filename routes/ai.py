from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import os

from services.ai_service import (
    generate_notes,
    summarize_note,
    explain_text,
    generate_questions,
    chat_assistant
)

# Retrieve the limiter instance from the app
ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

def get_limiter():
    from app import limiter
    return limiter

def require_api_key(f):
    """Decorator to instantly fail if API limit/key isn't configured."""
    import functools
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not os.environ.get("GEMINI_API_KEY"):
            return jsonify({'error': 'AI features are currently unavailable. Missing API Key.'}), 503
        return f(*args, **kwargs)
    return decorated_function


@ai_bp.route('/generate', methods=['POST'])
@login_required
@require_api_key
def api_generate():
    """Rate-limited generation of note structures based on a topic."""
    limiter = get_limiter()
    limiter.limit("5 per minute")(lambda: None)()
    
    data = request.get_json()
    if not data or 'topic' not in data:
        return jsonify({'error': 'Topic is required'}), 400
        
    topic = data.get('topic')
    markdown_content = generate_notes(topic)
    return jsonify({'result': markdown_content})


@ai_bp.route('/summarize', methods=['POST'])
@login_required
@require_api_key
def api_summarize():
    limiter = get_limiter()
    limiter.limit("5 per minute")(lambda: None)()
    
    data = request.get_json()
    content = data.get('content')
    if not content:
        return jsonify({'error': 'Content is required'}), 400
        
    summary = summarize_note(content)
    return jsonify({'result': summary})


@ai_bp.route('/explain', methods=['POST'])
@login_required
@require_api_key
def api_explain():
    limiter = get_limiter()
    limiter.limit("10 per minute")(lambda: None)()
    
    data = request.get_json()
    text = data.get('text')
    is_code = data.get('is_code', False)
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
        
    explanation = explain_text(text, is_code=is_code)
    return jsonify({'result': explanation})


@ai_bp.route('/questions', methods=['POST'])
@login_required
@require_api_key
def api_questions():
    limiter = get_limiter()
    limiter.limit("3 per minute")(lambda: None)()
    
    data = request.get_json()
    content = data.get('content')
    
    if not content:
        return jsonify({'error': 'Content is required'}), 400
        
    questions = generate_questions(content)
    return jsonify({'result': questions})


@ai_bp.route('/chat', methods=['POST'])
@login_required
@require_api_key
def api_chat():
    limiter = get_limiter()
    limiter.limit("10 per minute")(lambda: None)()
    
    data = request.get_json()
    query = data.get('query')
    context = data.get('context')
    
    if not query or not context:
        return jsonify({'error': 'Query and context are required'}), 400
        
    response = chat_assistant(query, context)
    return jsonify({'result': response})
