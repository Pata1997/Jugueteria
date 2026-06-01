import sys

with open('app/routes/compras.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
i = 0
while i < len(lines):
    line = lines[i]
    if line.strip() == "return jsonify({":
        # Check if the next line is "        )"
        if i + 1 < len(lines) and lines[i+1].strip() == ")":
            # This is the corrupted block!
            out.append("    return jsonify({\n")
            out.append("        'id': compra.id,\n")
            out.append("        'numero_compra': compra.numero_compra,\n")
            out.append("        'proveedor': compra.proveedor.razon_social if compra.proveedor else 'N/A',\n")
            out.append("        'tipo': compra.tipo,\n")
            out.append("        'total': float(compra.total or 0),\n")
            out.append("        'subtotal': float(compra.subtotal or 0),\n")
            out.append("        'iva': float(compra.iva or 0),\n")
            out.append("        'estado': compra.estado\n")
            out.append("    })\n\n\n")
            out.append("# ===== NOTAS DE CRÉDITO Y DÉBITO =====\n")
            out.append("from app.models.nota_credito_compra import NotaCreditoCompra, NotaCreditoCompraDetalle\n")
            out.append("from app.models.nota_debito_compra import NotaDebitoCompra, NotaDebitoCompraDetalle\n\n")
            out.append("@bp.route('/notas')\n")
            out.append("@login_required\n")
            out.append("def listar_nc_nd_compras():\n")
            out.append("    page = request.args.get('page', 1, type=int)\n")
            out.append("    tab = request.args.get('tab', 'credito')\n")
            out.append("    \n")
            out.append("    if tab == 'credito':\n")
            out.append("        notas = NotaCreditoCompra.query.order_by(NotaCreditoCompra.fecha_emision.desc()).paginate(\n")
            out.append("            page=page, per_page=20, error_out=False\n")
            out.append("        )\n")
            out.append("    else:\n")
            out.append("        notas = NotaDebitoCompra.query.order_by(NotaDebitoCompra.fecha_emision.desc()).paginate(\n")
            out.append("            page=page, per_page=20, error_out=False\n")
            out.append("        )\n")
            out.append("        \n")
            out.append("    return render_template('compras/listar_nc_nd.html', notas=notas, tab=tab)\n")
            
            # Skip until we hit the @bp.route('/<int:compra_id>/nota-credito' ...
            while i < len(lines) and not lines[i].startswith("@bp.route('/<int:compra_id>/nota-credito"):
                i += 1
            if i < len(lines):
                out.append(lines[i])
        else:
            out.append(line)
    else:
        out.append(line)
    i += 1

with open('app/routes/compras.py', 'w', encoding='utf-8') as f:
    f.writelines(out)

print("Done")
