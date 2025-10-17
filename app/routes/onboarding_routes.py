# onboarding_routes.py
from flask import Blueprint, render_template
from flask_login import login_required

onboarding_bp = Blueprint('onboarding', __name__)

@onboarding_bp.route('/onboarding')
@login_required
def show_onboarding():
    return render_template('onboarding.html')
