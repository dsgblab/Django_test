from django.shortcuts import render, redirect, get_object_or_404
from .models import Table1, Table2, TablePermission
from .forms import Table1Form, Table2Form
from django.contrib.auth.decorators import login_required
from django.db import connections
from django.http import HttpResponse

def check_perm(user, table, perm):
    try:
        perms = TablePermission.objects.get(user=user, table=table)
        return getattr(perms, f"can_{perm}")
    except TablePermission.DoesNotExist:
        return False

def get_perm_dict(user, table):
    return {
        'can_write': check_perm(user, table, 'write'),
        'can_delete': check_perm(user, table, 'delete'),
        'can_read': check_perm(user, table, 'read'),
        'can_edit': check_perm(user, table, 'edit'),
    }

@login_required
def dashboard(request):
    perms = {
        'report': check_perm(request.user, 'report', 'read'),
        'can_read_table1': check_perm(request.user, 'table1', 'read'),
        'can_read_table2': check_perm(request.user, 'table2', 'read'),
    }

    return render(request, 'tableapp/dashboard.html', {
        'perms': perms
    })



@login_required
def table1_list(request):
    if not check_perm(request.user, 'table1', 'read'):
        return render(request, 'tableapp/no_permission.html')
    data = Table1.objects.all()
    perms = get_perm_dict(request.user, 'table1')
    return render(request, 'tableapp/table1_list.html', {'data': data, 'perms': perms})

@login_required
def table1_create(request):
    if not check_perm(request.user, 'table1', 'write'):
        return render(request, 'tableapp/no_permission.html')

    form = Table1Form(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        if request.htmx:
            return HttpResponse(status=204)  
        return redirect('table1_list')

    perms = get_perm_dict(request.user, 'table1')
    return render(request, 'tableapp/form.html', {'form': form, 'cancel_url': 'table1_list', 'perms': perms})

@login_required
def table1_delete(request, pk):
    if not check_perm(request.user, 'table1', 'delete'):
        return render(request, 'tableapp/no_permission.html')
    obj = get_object_or_404(Table1, pk=pk)
    obj.delete()
    return redirect('table1_list')

@login_required
def table1_edit(request, pk):
    if not check_perm(request.user, 'table1', 'edit'):
        return render(request, 'tableapp/no_permission.html')

    obj = get_object_or_404(Table1, pk=pk)
    form = Table1Form(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        if request.htmx:
            return HttpResponse(status=204)
        return redirect('table1_list')

    perms = get_perm_dict(request.user, 'table1')
    return render(request, 'tableapp/form.html', {
        'form': form,
        'cancel_url': 'table1_list',
        'perms': perms,
        'object': obj  # ✅ Solo aquí
    })



@login_required
def table2_list(request):
    if not check_perm(request.user, 'table2', 'read'):
        return render(request, 'tableapp/no_permission.html')
    data = Table2.objects.all()
    perms = get_perm_dict(request.user, 'table2')
    return render(request, 'tableapp/table2_list.html', {'data': data, 'perms': perms})

@login_required
def table2_create(request):
    if not check_perm(request.user, 'table2', 'write'):
        return render(request, 'tableapp/no_permission.html')

    form = Table2Form(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        if request.htmx:
            return HttpResponse(status=204)
        return redirect('table2_list')

    perms = get_perm_dict(request.user, 'table2')
    return render(request, 'tableapp/form.html', {'form': form, 'cancel_url': 'table2_list', 'perms': perms})

@login_required
def table2_delete(request, pk):
    if not check_perm(request.user, 'table2', 'delete'):
        return render(request, 'tableapp/no_permission.html')
    obj = get_object_or_404(Table2, pk=pk)
    obj.delete()
    return redirect('table2_list')

@login_required
def table2_edit(request, pk):
    if not check_perm(request.user, 'table2', 'edit'):
        return render(request, 'tableapp/no_permission.html')

    obj = get_object_or_404(Table2, pk=pk)
    form = Table2Form(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        if request.htmx:
            return HttpResponse(status=204)
        return redirect('table2_list')

    perms = get_perm_dict(request.user, 'table2')
    return render(request, 'tableapp/form.html', {
        'form': form,
        'cancel_url': 'table2_list',
        'perms': perms,
        'object': obj  # ✅ Solo aquí también
    })



@login_required
def query_result_view(request):
    if not check_perm(request.user, 'report', 'read'):
        return render(request, 'tableapp/no_permission.html')
    with connections['ssf_genericos'].cursor() as cursor:
        cursor.execute("""
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
