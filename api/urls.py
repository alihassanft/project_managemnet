from django.urls import path,include
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'project_memberships', ProjectMembershipViewSet)

urlpatterns = [
    path('login/',UserLoginAPIView.as_view(),name='login'),
    path('signup/',UserSignUpAPIView.as_view(),name='signup'),
    path('get_user/',GetUserAPIView.as_view()),
    path('', include(router.urls)),
]
