from flask import Blueprint, render_template, request
from services.library_service import get_patron_status_report

patron = Blueprint('patron', __name__)

@patron.route('/patron/status')
def status():
    patron_id = request.args.get('patron_id')
    if patron_id:
        status = get_patron_status_report(patron_id)
        return render_template('patron.html', patron_id=patron_id, status=status)
    return render_template('patron.html')