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
    return render(request, 'tableapp/form.html', {'form': form})

@login_required
def table1_delete(request, pk):
    if not check_perm(request.user, 'table1', 'delete'):
        return render(request, 'tableapp/no_permission.html')
    obj = get_object_or_404(Table1, pk=pk)
    obj.delete()
    return redirect('table1_list')

# Similar views for table2...
