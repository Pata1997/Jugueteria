from flask import send_file
from flask_login import login_required
from app.models import NotaCredito
from app.utils.nota_credito_ticket import generar_nota_credito_ticket_pdf
from io import BytesIO
from flask import Blueprint

bp = Blueprint('notas_credito_pdf', __name__)

@bp.route('/ventas/notas-credito/pdf/<int:nota_id>')
@login_required
def descargar_nota_credito_pdf(nota_id):
    nota = NotaCredito.query.get_or_404(nota_id)
    
    # Generar PDF con el nuevo generador SET-compliant
    pdf_bytes = generar_nota_credito_ticket_pdf(nota)
    
    pdf_buffer = BytesIO(pdf_bytes) if isinstance(pdf_bytes, bytes) else pdf_bytes
    pdf_buffer.seek(0)
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'nota_credito_{nota.numero_nota}.pdf'
    )
