from rest_framework import permissions
from .models import *

class IsProjectCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.creator == request.user

class CanCreateTask(permissions.BasePermission):
    def has_permission(self, request, view):
        project_id = view.kwargs.get('project') or request.data.get('project')
        if not project_id:
            return False
        try:
            permission = ProjectMembership.objects.get(member=request.user, project_id=project_id)
            return permission.can_create_task
        except ProjectMembership.DoesNotExist:
            print("in expect")
            return False

class CanEditTask(permissions.BasePermission):
    def has_permission(self, request, view):
        project_id = view.kwargs.get('project') or request.data.get('project')
        if not project_id:
            return False

        try:
            permission = ProjectMembership.objects.get(member=request.user, project_id=project_id)
            return permission.can_edit_task
        except ProjectMembership.DoesNotExist:
            return False

class CanDeleteTask(permissions.BasePermission):
    def has_permission(self, request, view):
        project_id = view.kwargs.get('project') or request.data.get('project')
        if not project_id:
            return False

        try:
            permission = ProjectMembership.objects.get(member=request.user, project_id=project_id)
            return permission.can_delete_task
        except ProjectMembership.DoesNotExist:
            return False

class CanAddMember(permissions.BasePermission):
    def has_permission(self, request, view):
        print("can add member")
        project_id = request.data.get('project')  # Get the project ID from the request data
        print("project_id",project_id)
        if not project_id:
            print("false")
            return False
        
        try:
            membership = ProjectMembership.objects.get(project_id=project_id, member=request.user)
            print("membership",membership)
            return membership.can_add_member
        except ProjectMembership.DoesNotExist:
            return False
