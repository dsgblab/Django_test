from django.shortcuts import render, redirect, get_object_or_404
from .models import Table1, Table2, TablePermission
from .forms import Table1Form, Table2Form
from django.contrib.auth.decorators import login_required
from django.db import connections

def check_perm(user, table, perm):
    try:
        perms = TablePermission.objects.get(user=user, table=table)
        return getattr(perms, f"can_{perm}")
    except TablePermission.DoesNotExist:
        return False

@login_required
def dashboard(request):
    return render(request, 'tableapp/dashboard.html')

@login_required
def table1_list(request):
    if not check_perm(request.user, 'table1', 'read'):
        return render(request, 'tableapp/no_permission.html')
    data = Table1.objects.all()
    return render(request, 'tableapp/table1_list.html', {'data': data})

@login_required
def table1_create(request):
    if not check_perm(request.user, 'table1', 'write'):
        return render(request, 'tableapp/no_permission.html')
    if request.method == 'POST':
        form = Table1Form(request.POST)
        if form.is_valid():
            form.save()
            return redirect('table1_list')
    else:
        form = Table1Form()
    return render(request, 'tableapp/form.html', {'form': form, 'cancel_url': 'table1_list'})  # Para que el boton cancel redirija a la tabla correcta en este caso table 1


@login_required
def table1_delete(request, pk):
    if not check_perm(request.user, 'table1', 'delete'):
        return render(request, 'tableapp/no_permission.html')
    obj = get_object_or_404(Table1, pk=pk)
    obj.delete()
    return redirect('table1_list')

# Similar views for table2...
@login_required
def table2_list(request):
    if not check_perm(request.user, 'table2', 'read'):
        return render(request, 'tableapp/no_permission.html')
    data = Table2.objects.all()
    return render(request, 'tableapp/table2_list.html', {'data': data})

@login_required
def table2_create(request):
    if not check_perm(request.user, 'table2', 'write'):
        return render(request, 'tableapp/no_permission.html')
    if request.method == 'POST':
        form = Table2Form(request.POST)
        if form.is_valid():
            form.save()
            return redirect('table2_list')
    else:
        form = Table2Form()
    return render(request, 'tableapp/form.html', {'form': form, 'cancel_url': 'table2_list'})  # y pues lo mismo para table2


@login_required
def table2_delete(request, pk):
    if not check_perm(request.user, 'table2', 'delete'):
        return render(request, 'tableapp/no_permission.html')
    obj = get_object_or_404(Table2, pk=pk)
    obj.delete()
    return redirect('table2_list')


@login_required
def query_result_view(request):
    with connections['ssf_genericos'].cursor() as cursor:
        cursor.execute("""
            -- AQUÍ pega la query completa que compartiste, sin cortar
            SELECT
              in_pedidencab.peeconsecutivo AS Pedido,
              in_pediddetal.pedsecuencia AS [Secuencia Pedido],
              in_pedidencab.peecompania AS Compania,
              in_pedidencab.peeordecompclie AS [OC Cliente],
              in_pedidencab.peecliente AS [Nit Cliente],
              in_pediddetal.pedcodiitem AS [Codigo Item],
              in_pedidencab.peefechelab AS [Fecha Pedido],
              in_pediddetal.pedfechrequ AS [Fecha Requerido],
              in_pediddetal.pedprecunit AS [Precio Unitario],
              in_pediddetal.pedcantpediump AS [Cantidad Pedida],
              in_pediddetal.pedcantpediump * in_pediddetal.pedprecunit AS [Valor Pedido],
              in_pediddetal.pedcantdespump AS [Cantidad Despachada],
              in_pediddetal.pedcantdespump * in_pediddetal.pedprecunit AS [Valor Despachado],
              in_pediddetal.pedcantpediump - in_pediddetal.pedcantdespump AS [Cantidad Pendiente],
              (in_pediddetal.pedcantpediump - in_pediddetal.pedcantdespump) * in_pediddetal.pedprecunit AS [Valor Pendiente],
              Op.Op AS Op,
              in_pediddetal.eobnombre AS [Estado Pedido],
              Op.[Estado Nombre] AS [Estado Op],
              in_pediddetal.pedrazoncierre AS [Razon Cierre],
              in_pedidencab.peeconsecutivo + in_pedidencab.peecompania + in_pediddetal.pedcodiitem AS ID,
              CONCAT(in_pedidencab.peeconsecutivo, '-', in_pediddetal.pedsecuencia, '-', Op.Op) AS GUID,
              Op.[Fecha Entrega Planta],
              Op.[Fecha Estimado Fin],
              CASE
                WHEN in_pediddetal.eobnombre IN ('Cerrado', 'Completo') THEN 0
                ELSE DATEDIFF(DAY, GETDATE(), Op.[Fecha Estimado Fin])
              END AS [Dias de Retraso]
            FROM dbo.in_pedidencab WITH (NOLOCK)
            INNER JOIN dbo.in_pediddetal WITH (NOLOCK)
              ON in_pediddetal.pedconsecutivo = in_pedidencab.peeconsecutivo
                AND in_pediddetal.pedtipocons = in_pedidencab.peetipocons
                AND in_pediddetal.pedcompania = in_pedidencab.peecompania
            LEFT OUTER JOIN (
                SELECT
                    pd_ordenproceso.orpcompania AS Compania,
                    MAX(pd_ordenproceso.orpconsecutivo) AS Op,
                    pd_ordenproceso.orpconspedi AS Pedido,
                    pd_ordenproceso.orpsecupedi AS [Secuencia Pedido],
                    pd_ordenproceso.eobcodigo AS Estado,
                    pd_ordenproceso.eobnombre AS [Estado Nombre],
                    pd_ordenproceso.orpfechaentrega AS [Fecha Entrega Planta],
                    pd_ordenproceso.orpfechestifin AS [Fecha Estimado Fin],
                    SUM(pd_ordenproceso.orpcantrecibida) AS [Cantidad Recibida]
                FROM dbo.pd_ordenproceso
                WHERE pd_ordenproceso.eobcodigo IN ('PE', 'EP', 'EF', 'EE', 'SU')
                  AND pd_ordenproceso.orpcompania = '01'
                GROUP BY pd_ordenproceso.orpcompania,
                         pd_ordenproceso.orpconspedi,
                         pd_ordenproceso.orpsecupedi,
                         pd_ordenproceso.eobcodigo,
                         pd_ordenproceso.eobnombre,
                         pd_ordenproceso.orpfechaentrega,
                         pd_ordenproceso.orpfechestifin,
                         pd_ordenproceso.orpcantrecibida
            ) Op
              ON in_pediddetal.pedcompania = Op.Compania
              AND in_pediddetal.pedconsecutivo = Op.Pedido
              AND in_pediddetal.pedsecuencia = Op.[Secuencia Pedido]
            WHERE YEAR(in_pedidencab.peefechelab) >= YEAR(GETDATE()) - 2
              AND in_pedidencab.peetipocons <> 'PECOP'
              AND in_pediddetal.pedcodiitem NOT LIKE '%SER%'
        """)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    return render(request, 'tableapp/query_results.html', {
        'columns': columns,
        'rows': rows
    })


