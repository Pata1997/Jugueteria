// Autocomplete para Nº Factura / Nº Servicio en Reclamos

document.addEventListener('DOMContentLoaded', function() {
    // Autocomplete Reclamos
    var input = document.getElementById('documento_numero');
    var clienteSelect = document.getElementById('cliente_id');
    var documentoId = document.getElementById('documento_id');
    var documentoTipo = document.getElementById('documento_tipo');
    var dropdown;

    if (input) {
        input.addEventListener('input', function() {
            var term = input.value.trim();
            if (term.length < 2) {
                closeDropdown();
                return;
            }
            fetch('/servicios/reclamos/buscar_documento?term=' + encodeURIComponent(term))
                .then(response => response.json())
                .then(data => {
                    showDropdown(data);
                });
        });
    }

    function showDropdown(results) {
        closeDropdown();
        dropdown = document.createElement('div');
        dropdown.className = 'autocomplete-dropdown list-group position-absolute w-100';
        if (!results.length) {
            var noResult = document.createElement('div');
            noResult.className = 'list-group-item text-muted';
            noResult.textContent = 'Sin coincidencias';
            dropdown.appendChild(noResult);
        } else {
            results.forEach(function(item) {
                var option = document.createElement('button');
                option.type = 'button';
                option.className = 'list-group-item list-group-item-action';
                option.textContent = item.numero + ' (' + item.tipo + ') - ' + item.cliente_nombre;
                option.onclick = function() {
                    input.value = item.numero;
                    documentoId.value = item.id;
                    documentoTipo.value = item.tipo;
                    if (clienteSelect) {
                        clienteSelect.value = item.cliente_id;
                    }
                    closeDropdown();
                };
                dropdown.appendChild(option);
            });
        }
        input.parentNode.appendChild(dropdown);
    }

    function closeDropdown() {
        if (dropdown) {
            dropdown.parentNode.removeChild(dropdown);
            dropdown = null;
        }
    }

    document.addEventListener('click', function(e) {
        if (dropdown && !dropdown.contains(e.target) && e.target !== input) {
            closeDropdown();
        }
    });

    // Filtros dinámicos Reclamos
    var estadoSelect = document.getElementById('filtro_estado');
    var prioridadSelect = document.getElementById('filtro_prioridad');
    var tabla = document.querySelector('table');

    function filtrarTabla() {
        var estado = estadoSelect.value;
        var prioridad = prioridadSelect.value;
        var filas = tabla.querySelectorAll('tbody tr');
        filas.forEach(function(tr) {
            var tdEstado = tr.querySelector('td:nth-child(6)');
            var tdPrioridad = tr.querySelector('td:nth-child(7)');
            var mostrar = true;
            if (estado && tdEstado.textContent.trim().toLowerCase() !== estado.replace('_', ' ').toLowerCase()) {
                mostrar = false;
            }
            if (prioridad && tdPrioridad.textContent.trim().toLowerCase() !== prioridad.toLowerCase()) {
                mostrar = false;
            }
            tr.style.display = mostrar ? '' : 'none';
        });
    }

    if (estadoSelect && prioridadSelect && tabla) {
        estadoSelect.addEventListener('change', filtrarTabla);
        prioridadSelect.addEventListener('change', filtrarTabla);
    }
});
