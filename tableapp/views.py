from django.shortcuts import render, redirect, get_object_or_404
from .models import TablePermission, PvoRegistro
from .forms import PvoRegistroForm
from django.contrib.auth.decorators import login_required
from django.db import connections, connection
from django.http import HttpResponse
from django.utils import timezone
from django.utils.timezone import now
from datetime import datetime, date


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
    }

    return render(request, 'tableapp/dashboard.html', {
        'perms': perms
    })



@login_required
def query_report_view(request):
    if not check_perm(request.user, 'report', 'read'):
        return render(request, 'tableapp/no_permission.html')
    
    permisos = {
        'can_edit_dates': check_perm(request.user, 'edit_dates', 'edit'),
        'can_edit_full': check_perm(request.user, 'edit_dates', 'edit_full'),
        'can_edit_flp': check_perm(request.user, 'edit_dates', 'edit_flp'),
        'can_edit_fef': check_perm(request.user, 'edit_dates', 'edit_fef'),
    }
    registros_finales = []

    # 1. Consulta principal (SSF_GENERICOS)
    with connections['ssf_genericos'].cursor() as cursor:
        cursor.execute("""
            SELECT
                CONCAT(in_pedidencab.peeconsecutivo, in_pedidencab.peecompania, in_pediddetal.pedsecuencia) AS PID,
                in_pedidencab.peeconsecutivo AS Pedido,
                in_pedidencab.peeordecompclie AS [OC Cliente],
                in_pedidencab.peecliente AS [Nit Cliente],
                V_SIS_BI_clientesv2.[Razon Social],
                in_pediddetal.pedcodiitem AS [Codigo Producto],
                in_items.itedesclarg AS [Producto Largo],
                in_pedidencab.peefechelab AS [Fecha Pedido],
                in_pediddetal.pedfechrequ AS [Fecha Requerida],
                F.[Fecha Despacho],
                CASE
                    WHEN in_pediddetal.eobnombre IN ('Cerrado', 'Completo') THEN 0
                    ELSE DATEDIFF(DAY, GETDATE(), Op.[Fecha Estimado Fin])
                END AS [Dias de Retraso],
                CASE
                    WHEN in_pediddetal.eobnombre = 'Cerrado' THEN 'Cerrado'
                    WHEN in_pediddetal.eobnombre = 'Completo' THEN 'Despacho Completo'
                    WHEN Op.[Estado Nombre] IN ('En Planeacion', 'En firme', 'Suspendido') THEN 'Compras & ABT'
                    WHEN Op.[Estado Nombre] IN ('Por ejecutar', 'En ejecucion') THEN 'En Produccion'
                    ELSE 'X'
                END AS [Estado Pedido],
                in_pediddetal.pedcantpediump AS [Cantidad Pedida],
                in_pediddetal.pedcantpediump * in_pediddetal.pedprecunit AS [Valor Pedido],
                in_pediddetal.pedcantdespump AS [Cantidad Despachada],
                in_pediddetal.pedcantdespump * in_pediddetal.pedprecunit AS [Valor Despacho],
                in_pediddetal.pedcantpediump - in_pediddetal.pedcantdespump AS [Cantidad Pendiente],
                (in_pediddetal.pedcantpediump - in_pediddetal.pedcantdespump) * in_pediddetal.pedprecunit AS [Valor Pendiente],
                Op.Op AS OP
            FROM ssf_genericos.dbo.in_pedidencab WITH (NOLOCK)
            INNER JOIN ssf_genericos.dbo.in_pediddetal WITH (NOLOCK)
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
                FROM ssf_genericos.dbo.pd_ordenproceso
                WHERE pd_ordenproceso.eobcodigo IN ('PE', 'EP', 'EF', 'EE', 'SU')
                    AND pd_ordenproceso.orpcompania = '01'
                    AND CAST(pd_ordenproceso.orpcantrecibida AS NVARCHAR(15)) + pd_ordenproceso.eobnombre NOT IN ('0.00Cerrado', '0.00Finalizada')
                GROUP BY
                    pd_ordenproceso.orpcompania,
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
            LEFT OUTER JOIN (
                SELECT
                    MAX(in_movimientos.movfechmovi) AS [Fecha Despacho],
                    in_movimientos.movconsedocuorig + in_movimientos.movcompania + in_movimientos.movcodiitem AS ID
                FROM ssf_genericos.dbo.in_movimientos
                WHERE in_movimientos.movtipocons IN ('DVTAN', 'DVTAX')
                GROUP BY in_movimientos.movconsedocuorig + in_movimientos.movcompania + in_movimientos.movcodiitem
            ) F
                ON in_pedidencab.peeconsecutivo + in_pedidencab.peecompania + in_pediddetal.pedcodiitem = F.ID
            INNER JOIN ssf_genericos.dbo.in_items
                ON in_pediddetal.pedcodiitem = in_items.itecodigo
                AND in_pediddetal.pedcompania = in_items.itecompania
            INNER JOIN ssf_genericos.dbo.V_SIS_BI_clientesv2
                ON V_SIS_BI_clientesv2.[Nit Cliente] = in_pedidencab.peecliente
                AND V_SIS_BI_clientesv2.Compañia = in_pedidencab.peecompania
            LEFT OUTER JOIN django_test_db.dbo.tableapp_pvoregistro
                ON CONCAT(in_pedidencab.peeconsecutivo, in_pedidencab.peecompania, in_pediddetal.pedsecuencia) = tableapp_pvoregistro.pid COLLATE Latin1_General_CI_AS
            WHERE
                YEAR(in_pedidencab.peefechelab) >= YEAR(GETDATE()) - 1
                AND in_pedidencab.peecompania = '01'
                AND in_pediddetal.eobnombre NOT IN ('Cerrado', 'Completo')
                AND in_pedidencab.peetipocons <> 'PECOP'
                AND in_pediddetal.pedcodiitem NOT LIKE '%SER%'
                AND (
                    in_pediddetal.pedrazoncierre IS NULL
                    OR in_pediddetal.pedrazoncierre IN ('07-PEDIDO COMPLETO', '08-PRODUCTO AVERIADO', '03- FACTURADO', '')
                )
            ORDER BY [Fecha Requerida]
        """)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]

    # 2. Consulta de fechas locales
    with connections['default'].cursor() as cursor2:
        cursor2.execute("""
            SELECT pid, fecha_full, fecha_flp, fecha_fef
            FROM tableapp_pvoregistro
        """)
        fechas = cursor2.fetchall()
        fechas_dict = {
            row[0]: {'FULL': row[1], 'FLP': row[2], 'FEF': row[3]}
            for row in fechas
        }

    # 3. Fusión 
    for row in rows:
        registro = dict(zip(columns, row))
        pid_base = str(registro['PID']).strip()

        fechas_extra = fechas_dict.get(pid_base, {})
        # Si existe fecha en PvoRegistro, pues la usamos.
        registro['Fecha FULL'] = fechas_extra.get('FULL') or registro.get('Fecha FULL')
        registro['Fecha FLP'] = fechas_extra.get('FLP') or registro.get('Fecha FLP')
        registro['Fecha FEF'] = fechas_extra.get('FEF') or registro.get('Fecha FEF')
 

        registros_finales.append(registro)

    return render(request, 'tableapp/query_report.html', {
        'registros': registros_finales,
        'columns': columns,
        'perms': permisos,
    })



@login_required
def historial_pvo_view(request):
    if not check_perm(request.user, 'report', 'read'):
        return render(request, 'tableapp/no_permission.html')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM (
                SELECT
                    pid AS guid,
                    'Compras' AS [Área],
                    fecha_full AS [Fecha],
                    creado_por_id AS actualizado_por,
                    fecha_creacion AS actualizado_en,
                    '' AS comentario
                FROM tableapp_pvoregistro
                WHERE fecha_full IS NOT NULL

                UNION ALL

                SELECT
                    pid,
                    'Liberación',
                    fecha_flp,
                    creado_por_id,
                    fecha_creacion,
                    ''
                FROM tableapp_pvoregistro
                WHERE fecha_flp IS NOT NULL

                UNION ALL

                SELECT
                    pid,
                    'Producción',
                    fecha_fef,
                    creado_por_id,
                    fecha_creacion,
                    ''
                FROM tableapp_pvoregistro
                WHERE fecha_fef IS NOT NULL
            ) AS historial
            ORDER BY guid, actualizado_en DESC
        """)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]

    return render(request, 'tableapp/query_results.html', {
        'columns': columns,
        'rows': rows
    })

@login_required
def pvo_list(request):
    if not check_perm(request.user, 'report', 'read'):
        return render(request, 'tableapp/no_permission.html')
    
    registros = PvoRegistro.objects.all()
    perms = get_perm_dict(request.user, 'report')  
    return render(request, 'tableapp/pvo_list.html', {
        'registros': registros,
        'perms': perms
    })


@login_required
def pvo_create(request):
    if not check_perm(request.user, 'report', 'write'):
        return render(request, 'tableapp/no_permission.html')

    form = PvoRegistroForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        registro = form.save(commit=False)
        registro.creado_por = request.user
        registro.fecha_creacion = timezone.now()
        registro.save()
        if request.htmx:
            return HttpResponse(status=204)
        return redirect('pvo_list')

    perms = get_perm_dict(request.user, 'report')
    return render(request, 'tableapp/form.html', {
        'form': form,
        'cancel_url': 'pvo_list',
        'perms': perms
    })


@login_required
def pvo_edit(request, pk):
    if not check_perm(request.user, 'report', 'edit'):
        return render(request, 'tableapp/no_permission.html')

    registro = get_object_or_404(PvoRegistro, pk=pk)
    form = PvoRegistroForm(request.POST or None, instance=registro)

    if request.method == 'POST' and form.is_valid():
        registro = form.save(commit=False)
        registro.creado_por = request.user 
        registro.save()
        if request.htmx:
            return HttpResponse(status=204)
        return redirect('pvo_list')

    perms = get_perm_dict(request.user, 'report')
    return render(request, 'tableapp/form.html', {
        'form': form,
        'cancel_url': 'pvo_list',
        'perms': perms,
        'object': registro
    })



def actualizar_fecha(request, pid, campo):
    

    if request.method == 'PUT':
        try:
            body_unicode = request.body.decode('utf-8')
            data = dict(x.split('=') for x in body_unicode.split('&'))
            fecha_nueva = data.get('fecha', '')
            print(f"Actualizando {pid}: campo={campo}, fecha={fecha_nueva}")

            registro, created = PvoRegistro.objects.get_or_create(pid=pid)

            if campo == 'FULL':
                registro.fecha_full = fecha_nueva or None
            elif campo == 'FLP':
                registro.fecha_flp = datetime.strptime(fecha_nueva, '%Y-%m-%d') if fecha_nueva else None
            elif campo == 'FEF':
                registro.fecha_fef = datetime.strptime(fecha_nueva, '%Y-%m-%d') if fecha_nueva else None

            registro.creado_por = request.user
            registro.save()
            return HttpResponse(status=204)
        except Exception as e:
            return HttpResponse(f"Error: {e}", status=400)
    return HttpResponse(status=405)
