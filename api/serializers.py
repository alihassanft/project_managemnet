from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import *
from django.utils.text import slugify



#custom login serializer from TokenObtainPairSerializer
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        return token

# User Signup
class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        # fields = '__all__'
        fields = ["first_name","last_name","username","email","contact_num","address",'password']


    def create(self, validated_data):
        # Generate a username based on the user's email
        email = validated_data.get('email')
        username = slugify(email.split('@')[0])
        # first_name = validated_data.get('first_name')
        # last_name = validated_data.get('last_name')

        user = User.objects.create(
            username=username,  # Assign the generated username
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            contact_num=validated_data.get('contact_num', ''),
            address=validated_data.get('address', '')

        )
        user.set_password(validated_data['password'])
        user.save()

        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # fields = '__all__'
        fields = ["first_name","last_name","username","email","contact_num","address"]


# 
class ProjectMembershipSerializer(serializers.ModelSerializer):
    members = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=User.objects.all()), write_only=True)

    class Meta:
        model = ProjectMembership
        # fields = '__all__'
        fields = ['project', 'members', 'can_create_task', 'can_edit_task', 'can_delete_task', 'can_add_member']

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        # fields = '__all__'
        read_only_fields = ['creator']  # Make creator read-only
        exclude = ['deleted']

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        # fields = '__all__'
        read_only_fields = ['creator']  # Make creator read-only
        exclude = ['deleted']

