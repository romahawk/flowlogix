from flask import Blueprint

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/stats')
def stats():
    pass

