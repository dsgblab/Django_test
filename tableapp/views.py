from django.shortcuts import render, redirect, get_object_or_404
from .models import TablePermission, PvoRegistro
from .forms import PvoRegistroForm
from django.contrib.auth.decorators import login_required
from django.db import connections, connection
from django.http import HttpResponse
from django.utils import timezone
from django.utils.timezone import now
from datetime import datetime, date
from django.shortcuts import render, get_object_or_404
from .models import PvoRegistro
from django.contrib.auth.decorators import login_required
from simple_history.utils import update_change_reason
from two_factor.views import SetupView
from django.shortcuts import redirect
from django_otp.plugins.otp_totp.models import TOTPDevice
from decimal import Decimal
from .models import TablePermission, PvoRegistro, FPConfig, FPCatalogo
from decimal import Decimal




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
        'can_edit_full': check_perm(user, table, 'edit_full'),
        'can_edit_flp': check_perm(user, table, 'edit_flp'),
        'can_edit_fef': check_perm(user, table, 'edit_fef'),
        'can_view_history': check_perm(user, table, 'view_history'),  
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
        'can_edit_full':  check_perm(request.user, 'edit_dates', 'edit_full'),
        'can_edit_flp':   check_perm(request.user, 'edit_dates', 'edit_flp'),
        'can_edit_fif':   check_perm(request.user, 'edit_dates', 'edit_fif'),
        'can_edit_fef':   check_perm(request.user, 'edit_dates', 'edit_fef'),
        'can_view_history': check_perm(request.user, 'report', 'view_history'),
    }


    registros_finales = []

    # 1) Consulta principal (JOIN a FP con COLLATE para resolver conflicto)
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

                -- ===== columnas de configuración FP (entre Estado Pedido y Cantidad Pedida) =====
                FP.estado_fp        AS [ESTADO FP],
                FP.tiempo_fp_horas  AS [TIEMPO FP],
                FP.familia          AS [FAMILIA],
                FP.tipo             AS [TIPO],
                FP.batch            AS [BATCH],
                FP.planta           AS [PLANTA],
                FP.tamano_lote      AS [TAMANO_LOTE],
                FP.personal_fase    AS [PERSONAL_FASE],
                -- ===============================================================================

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
               AND in_pediddetal.pedtipocons   = in_pedidencab.peetipocons
               AND in_pediddetal.pedcompania   = in_pedidencab.peecompania
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
                ON in_pediddetal.pedcompania  = Op.Compania
               AND in_pediddetal.pedconsecutivo = Op.Pedido
               AND in_pediddetal.pedsecuencia  = Op.[Secuencia Pedido]
            LEFT OUTER JOIN (
                SELECT
                    MAX(in_movimientos.movfechmovi) AS [Fecha Despacho],
                    in_movimientos.movconsedocuorig + in_movimientos.movcompania + in_movimientos.movcodiitem AS ID
                FROM ssf_genericos.dbo.in_movimientos
                WHERE in_movimientos.movtipocons IN ('DVTAN', 'DVTAX')
                GROUP BY in_movimientos.movconsedocuorig + in_movimientos.movcompania + in_movimientos.movcodiitem
            ) F
                ON in_pedidencab.peeconsecutivo + in_pedidencab.peecompania + in_pediddetal.pedcodiitem = F.ID

            -- JOIN a la config de FP por código de producto (ajustado con COLLATE)
            LEFT OUTER JOIN django_test_db.dbo.tableapp_fpconfig AS FP WITH (NOLOCK)
                ON FP.codigo_producto COLLATE Modern_Spanish_CI_AS = in_pediddetal.pedcodiitem

            INNER JOIN ssf_genericos.dbo.in_items
                ON in_pediddetal.pedcodiitem  = in_items.itecodigo
               AND in_pediddetal.pedcompania  = in_items.itecompania
            INNER JOIN ssf_genericos.dbo.V_SIS_BI_clientesv2
                ON V_SIS_BI_clientesv2.[Nit Cliente] = in_pedidencab.peecliente
               AND V_SIS_BI_clientesv2.Compañia     = in_pedidencab.peecompania

            LEFT OUTER JOIN django_test_db.dbo.tableapp_pvoregistro
                ON CONCAT(in_pedidencab.peeconsecutivo, in_pedidencab.peecompania, in_pediddetal.pedsecuencia)
                   = tableapp_pvoregistro.pid COLLATE Latin1_General_CI_AS

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

    # 2) Fechas locales
    with connections['default'].cursor() as cursor2:
        cursor2.execute("""
            SELECT pid, fecha_full, fecha_flp, fecha_fif, fecha_fef, creado_por_id, fecha_creacion
            FROM tableapp_pvoregistro
        """)
        fechas = cursor2.fetchall()

    fechas_dict = {
        row[0]: {
            'FULL': row[1],
            'FLP':  row[2],
            'FIF':  row[3],
            'FEF':  row[4],
            'ACTUALIZADO_POR': row[5],
            'ACTUALIZADO_EN':  row[6],
        }
        for row in fechas
    }

    # 3) Fusión
    for row in rows:
        registro = dict(zip(columns, row))
        pid_base = str(registro['PID']).strip()

        fechas_extra = fechas_dict.get(pid_base, {})
        registro['Fecha FULL'] = fechas_extra.get('FULL') or registro.get('Fecha FULL')
        registro['Fecha FLP']  = fechas_extra.get('FLP')  or registro.get('Fecha FLP')
        registro['Fecha FIF']  = fechas_extra.get('FIF')  or registro.get('Fecha FIF')
        registro['Fecha FEF']  = fechas_extra.get('FEF')  or registro.get('Fecha FEF')
        registro['Actualizado por'] = fechas_extra.get('ACTUALIZADO_POR')
        registro['Última Fecha']    = fechas_extra.get('ACTUALIZADO_EN')

        registros_finales.append(registro)

    skip_cols = [
        'Fecha Entrega Planta',
        'Fecha Estimado Fin',
        'Fecha FULL',
        'Fecha FLP',
        'Fecha FIF',
        'Fecha FEF',
    ]
        # 4) Catálogo para combos
    catalogo = {
        'estados_fp': list(
            FPCatalogo.objects.filter(grupo='ESTADO FP')
            .values_list('valor', flat=True).order_by('valor')
        ),
        'familias': list(
            FPCatalogo.objects.filter(grupo='FAMILIA')
            .values_list('valor', flat=True).order_by('valor')
        ),
        'tipos': list(
            FPCatalogo.objects.filter(grupo='TIPO')
            .values_list('valor', flat=True).order_by('valor')
        ),
        'plantas': list(
            FPCatalogo.objects.filter(grupo='PLANTA')
            .values_list('valor', flat=True).order_by('valor')
        ),
    }


    return render(request, 'tableapp/query_report.html', {
        'registros': registros_finales,
        'columns': columns,
        'perms': permisos,
        'skip_cols': skip_cols,
        'catalogo': catalogo,
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
                    'Inicio Fab.',
                    fecha_fif,
                    creado_por_id,
                    fecha_creacion,
                    ''
                FROM tableapp_pvoregistro
                WHERE fecha_fif IS NOT NULL

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
        registro.actualizado_por = request.user
        registro.actualizado_en = timezone.now()
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
        registro.actualizado_por = request.user
        registro.actualizado_en = timezone.now()
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


@login_required
def actualizar_fecha(request, pid, campo):
    if request.method == 'PUT':
        try:
            body_unicode = request.body.decode('utf-8')
            data = dict(x.split('=') for x in body_unicode.split('&'))
            fecha_nueva = data.get('fecha', '')
            print(f"Actualizando {pid}: campo={campo}, fecha={fecha_nueva}")

            registro, created = PvoRegistro.objects.get_or_create(pid=pid)

            # Asigna el usuario para simple_history
            update_change_reason(registro, f"{campo} actualizado por {request.user.username}")
            registro._history_user = request.user  # Asegura que quede registrado

            if campo == 'FULL':
                registro.fecha_full = fecha_nueva or None
            elif campo == 'FLP':
                registro.fecha_flp = datetime.strptime(fecha_nueva, '%Y-%m-%d') if fecha_nueva else None
            elif campo == 'FIF': 
                registro.fecha_fif = datetime.strptime(fecha_nueva, '%Y-%m-%d') if fecha_nueva else None
            elif campo == 'FEF':
                registro.fecha_fef = datetime.strptime(fecha_nueva, '%Y-%m-%d') if fecha_nueva else None

            #  Actualiza siempre quien y cuándo
            registro.creado_por = request.user
            registro.fecha_creacion = now()

            registro.save()
            return HttpResponse(status=204)
        except Exception as e:
            print(f"Error actualizando {pid}: {e}")
            return HttpResponse(f"Error: {e}", status=400)
    return HttpResponse(status=405)


@login_required
def pvo_historial_modal(request, pid):
    if not check_perm(request.user, 'edit_dates', 'view_history'):
        return render(request, 'tableapp/no_permission.html')

    registro = get_object_or_404(PvoRegistro, pid=pid)
    historico = []

    campos_visibles = [
        field.name for field in registro.history.model._meta.fields
        if field.name not in (
            'id', 'history_id', 'history_date', 'history_user',
            'history_type', 'history_change_reason',
            'creado_por', 'fecha_creacion'
        )
    ]

    for h in registro.history.all().order_by('-history_date'):
        cambios_reales = []
        if h.prev_record:
            for field in campos_visibles:
                old = getattr(h.prev_record, field, None)
                new = getattr(h, field, None)
                if old != new:
                    cambios_reales.append({
                        'field': field,
                        'old': old,
                        'new': new
                    })
        
        if cambios_reales:
            historico.append({
                'history': h,
                'cambios': cambios_reales
            })

    return render(request, 'tableapp/pvo_historial_modal.html', {
        'registro': registro,
        'historico': historico,
    })

@login_required
def login_redirect_view(request):
    user = request.user
    if not TOTPDevice.objects.filter(user=user, confirmed=True).exists():
        return redirect('/account/two_factor/setup/')
    
    return redirect('dashboard')


class CustomSetupView(SetupView):
    def done(self, form_list, **kwargs):
        return redirect('dashboard') 



@login_required
def actualizar_fp(request, codigo_producto, campo):
    """
    PUT desde HTMX para actualizar FPConfig y reflejar en tableapp_pvoregistro.
    Reglas:
      - estado_fp            -> F_* = nombre de la fase (texto)
      - tiempo_fp_horas      -> T_* de la fase actual; si F_* está vacío o parece fecha, también setea F_*
      - personal_fase        -> P_* de la fase actual; si F_* está vacío o parece fecha, también setea F_*
      - batch/planta/tamano_lote/familia/tipo -> copia homónima en pvoregistro
    """
    if request.method != 'PUT':
        return HttpResponse(status=405)

    try:
        body = request.body.decode('utf-8')
        parts = [p for p in body.split('&') if '=' in p]
        data = dict(p.split('=', 1) for p in parts)

        valor = (data.get('valor') or '').strip()
        pid   = (data.get('pid') or '').strip()

        permitidos = {
            'estado_fp', 'tiempo_fp_horas', 'familia', 'tipo',
            'batch', 'planta', 'tamano_lote', 'personal_fase'
        }
        if campo not in permitidos:
            return HttpResponse('Campo no permitido', status=400)

        # --- normalización para FPConfig
        if valor == '':
            nuevo_valor = None
        elif campo == 'tiempo_fp_horas':
            try:
                nuevo_valor = Decimal(valor.replace(',', '.'))
            except Exception:
                return HttpResponse('Valor inválido para TIEMPO FP (horas)', status=400)
        elif campo == 'personal_fase':
            try:
                nuevo_valor = int(valor)
            except Exception:
                return HttpResponse('Valor inválido para PERSONAL_FASE', status=400)
        else:
            nuevo_valor = valor

        # Upsert en FPConfig
        fp, _ = FPConfig.objects.get_or_create(codigo_producto=codigo_producto)
        setattr(fp, campo, nuevo_valor)
        fp.save()

        # Si vino PID, aqui la idea es reflejarlo en  pvoregistro
        if pid:
            reg, _ = PvoRegistro.objects.get_or_create(pid=pid)

            # Mapa de fase -> columnas (F, T, P)
            fase_map = {
                'DISPENSACION': ('f_dispensacion', 't_dispensacion', 'p_dispensacion'),
                'PESAJE': ('f_pesaje', 't_pesaje', 'p_pesaje'),
                'FABRICACION': ('f_fabricacion', 't_fabricacion', 'p_fabricacion'),
                'ENFRIAMIENTO': ('f_enfriamiento', 't_enfriamiento', 'p_enfriamiento'),
                'ENVASADO': ('f_envasado', 't_envasado', 'p_envasado'),
                'ACONDICIONAMIENTO': ('f_acondicionamiento', 't_acondicionamiento', 'p_acondicionamiento'),
                'EMBALAJE': ('f_embalaje', 't_embalaje', 'p_embalaje'),
                'DESPACHO': ('f_despacho', 't_despacho', 'p_despacho'),
            }

            # Copias directas a pvoregistro
            if campo in {'batch', 'planta', 'tamano_lote', 'familia', 'tipo'}:
                setattr(reg, campo, nuevo_valor)

            # Helper
            def parece_fecha(v):
                if v is None:
                    return False
                s = str(v)
                return len(s) >= 10 and s[4] == '-' and s[7] == '-'

            # Cuando cambia la fase -> F_* = nombre de la fase
            if campo == 'estado_fp':
                fase = (valor or '').upper()
                cols = fase_map.get(fase)
                if cols:
                    col_f, _, _ = cols
                    setattr(reg, col_f, fase)

            # Tiempo / Personal -> T_* o P_* de la fase actual
            if campo in {'tiempo_fp_horas', 'personal_fase'}:
                fase_actual = (fp.estado_fp or '').upper()
                cols = fase_map.get(fase_actual)
                if not cols:
                    return HttpResponse('Define primero ESTADO FP para esta fila.', status=400)
                col_f, col_t, col_p = cols

                # Además: si F_* está vacío o era una fecha vieja, lo dejo fijo al nombre de la fase
                f_val = getattr(reg, col_f, None)
                if not f_val or parece_fecha(f_val):
                    setattr(reg, col_f, fase_actual)

                if campo == 'tiempo_fp_horas':
                    setattr(reg, col_t, nuevo_valor)
                else:
                    setattr(reg, col_p, nuevo_valor)

            reg.creado_por = request.user
            reg.fecha_creacion = now()
            reg.save()

        return HttpResponse(status=204)

    except Exception as e:
        print(f'Error actualizar_fp [{codigo_producto}::{campo}]: {e}')
        return HttpResponse(f'Error: {e}', status=400)
