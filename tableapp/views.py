from django.shortcuts import render, redirect, get_object_or_404
from .models import Table1, Table2, TablePermission
from .forms import Table1Form, Table2Form
from django.contrib.auth.decorators import login_required

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