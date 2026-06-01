import sys

with open('app/routes/compras.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# We want to keep everything up to line 1103, and then append the proper cancelar_compra.
# Line 1103 is empty, line 1102 is "    return render_template('compras/crear_nota_debito.html', compra=compra)\n"

out = lines[:1103]

# Now append the correct cancelar_compra
correct_cancelar = """
@bp.route('/<int:id>/cancelar', methods=['POST'])
@login_required
def cancelar_compra(id):
    \"\"\"Cancela una compra que está en estado registrada (sin pagos)\"\"\"
    compra = Compra.query.get_or_404(id)
    
    if compra.estado != 'registrada':
        flash('Solo se pueden cancelar compras registradas que no han sido pagadas. Para compras con pagos utilice Notas de Crédito.', 'danger')
        return redirect(url_for('compras.ver', id=compra.id))
        
    try:
        compra.estado = 'cancelada'
        db.session.commit()
        registrar_bitacora('cancelar_compra', f'Compra {compra.numero_compra} cancelada')
        flash('Compra cancelada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cancelar la compra: {str(e)}', 'danger')
        
    return redirect(url_for('compras.pendientes_pago'))
"""

out.append(correct_cancelar)

with open('app/routes/compras.py', 'w', encoding='utf-8') as f:
    f.writelines(out)

print("Cleanup complete.")
