from django.db import models
from django.contrib.auth.models import User

class Table1(models.Model):
    col1 = models.CharField(max_length=100)
    col2 = models.IntegerField()
    col3 = models.TextField()
    col4 = models.BooleanField(default=False)

    def __str__(self):
        return self.col1

class Table2(models.Model):
    col1 = models.CharField(max_length=100)
    col2 = models.IntegerField()
    col3 = models.TextField()
    col4 = models.BooleanField(default=False)

    def __str__(self):
        return self.col1

class TablePermission(models.Model):
    TABLE_CHOICES = (
        ('table1', 'Table 1'),
        ('table2', 'Table 2'),
        ('report', 'Report'),  
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    table = models.CharField(choices=TABLE_CHOICES, max_length=10)
    can_read = models.BooleanField(default=False)
    can_write = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'table')

    
    def __str__(self):
        return f"{self.user.username} - {self.table}"