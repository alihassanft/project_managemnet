from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from .serializers import *
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from .permissions import *
# 
from rest_framework.exceptions import ValidationError
from django.core.exceptions import PermissionDenied

# Create your views here.

#customer tokenobrainpiar view to get user information 
class UserLoginAPIView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        required_fields = ['email', 'password']
        missing_fields = [field for field in required_fields if field not in request.data]
        if missing_fields:
            errors = {field:["This field is required."] for field in missing_fields }
            return Response(errors,status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        token = serializer.validated_data.get('access')
        refresh = serializer.validated_data.get('refresh')
        data = {
            'access_token': token,
            'refresh_token': refresh,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name':user.first_name,
                'last_name':user.last_name,
                'contact_number':user.contact_num,
                'address':user.address,
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
            }}
        return Response({"data":data}, status=status.HTTP_200_OK)


class UserSignUpAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            response_data = {
                "user": serializer.data,
                "access_token": access_token,
                "refresh_token": refresh_token
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 
class GetUserAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        user = request.user
        user_data = User.objects.filter(id=user.id)
        serializer_data = UserSerializer(user_data,many=True)
        return Response({'data':serializer_data.data})
# 

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsProjectCreator]  # Only creator can modify project
 
    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(creator=user, deleted=False)
    
    def perform_create(self, serializer):
        project = serializer.save(creator=self.request.user)
        ProjectMembership.objects.create(
            project=project,
            member=self.request.user,
            can_create_task=True,
            can_edit_task=True,
            can_delete_task=True,
            can_add_member=True
        )
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted = True  # Soft delete by marking as deleted
        instance.save()
        return Response({'status': 'Project deleted'}, status=status.HTTP_204_NO_CONTENT)

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated | CanCreateTask | CanEditTask | CanDeleteTask]  # Member permissions
    
    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.filter(deleted=False)  # Exclude soft-deleted tasks

        project_id = self.request.query_params.get('project')
        user_projects = ProjectMembership.objects.filter(member=user).values_list('project_id', flat=True)
        print("user projects ",user_projects)
        if project_id:
            if int(project_id) in user_projects:
                return queryset.filter(project_id=project_id)
        else:
            # Return tasks for all projects the user is a member of
            return queryset.filter(project_id__in=user_projects)

    def perform_create(self, serializer):
        project_id = self.request.data.get('project')
        if not project_id:
            raise ValidationError("Project ID is required to create a task.")
        
        # Check if the user has permission to create tasks in the project
        try:
            project_membership = ProjectMembership.objects.get(project_id=project_id, member=self.request.user)
            if not project_membership.can_create_task:
                raise PermissionDenied("You do not have permission to create tasks for this project.")
        except ProjectMembership.DoesNotExist:
            raise PermissionDenied("You do not have permission to create tasks for this project.")

        serializer.save(creator=self.request.user, project_id=project_id)
    
    # update
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        project_id = instance.project_id

        # Check if the user has permission to edit the task
        if not CanEditTask().has_permission(request, self):
            raise PermissionDenied("You do not have permission to edit tasks for this project.")

        return super().update(request, *args, **kwargs)
    
    # delete
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if the user has permission to delete the task
        if not CanDeleteTask().has_permission(request, self):
            raise PermissionDenied("You do not have permission to delete tasks for this project.")

        # Soft delete
        instance.deleted = True
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)



class ProjectMembershipViewSet(viewsets.ModelViewSet):
    queryset = ProjectMembership.objects.all()
    serializer_class = ProjectMembershipSerializer
    permission_classes = [IsAuthenticated, CanAddMember]  # Only members who can add members

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        project_id = serializer.validated_data['project'].id
        member_ids = serializer.validated_data['members']

        # Get project and check permissions for the current user
        try:
            project = Project.objects.get(id=project_id,deleted=False)
            current_user_membership = ProjectMembership.objects.get(project=project, member=request.user)
            if not current_user_membership.can_add_member:
                return Response({'status': 'permission denied'}, status=status.HTTP_403_FORBIDDEN)
        except Project.DoesNotExist:
            return Response({'status': 'project not found'}, status=status.HTTP_404_NOT_FOUND)
        except ProjectMembership.DoesNotExist:
            return Response({'status': 'membership not found'}, status=status.HTTP_403_FORBIDDEN)

        # Create memberships for each member ID in the list
        for member_id in member_ids:
            try:
                member = User.objects.get(id=member_id.id)
                ProjectMembership.objects.create(
                    project=project,
                    member=member,
                    can_create_task=serializer.validated_data.get('can_create_task', False),
                    can_edit_task=serializer.validated_data.get('can_edit_task', False),
                    can_delete_task=serializer.validated_data.get('can_delete_task', False),
                    can_add_member=serializer.validated_data.get('can_add_member', False)
                )
            except User.DoesNotExist:
                return Response({'status': f'user with id {member_id} not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'status': 'members added'}, status=status.HTTP_201_CREATED)










