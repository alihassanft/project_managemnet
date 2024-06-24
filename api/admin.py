from django.contrib import admin
from .models import *
# Register your models here.


# User
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id','username','email','is_superuser','is_staff']
    search_fields = ('username', 'email', 'first_name', 'last_name')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['id','name','description','creator','get_members','deleted']
@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ['id','project','member','can_create_task','can_edit_task','can_delete_task','can_add_member']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['id','title','description','status','due_date','creator','deleted']



