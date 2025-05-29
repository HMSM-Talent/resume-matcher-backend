from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import EmailValidator, RegexValidator
from .models import CustomUser, CandidateProfile, CompanyProfile

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'role', 'is_active', 'date_joined', 'first_name', 'last_name')
        read_only_fields = ('id', 'date_joined')

class CandidateProfileSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )

    class Meta:
        model = CandidateProfile
        fields = ('phone_number',)

class CompanyProfileSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )
    company_name = serializers.CharField(required=True)

    class Meta:
        model = CompanyProfile
        fields = ('phone_number', 'company_name')

class BaseRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(validators=[EmailValidator()])

    class Meta:
        model = User
        fields = ('email', 'password', 'password2')

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

class CandidateRegistrationSerializer(BaseRegistrationSerializer):
    first_name = serializers.CharField(required=True, max_length=30)
    last_name = serializers.CharField(required=True, max_length=30)
    profile = CandidateProfileSerializer(required=False)

    class Meta(BaseRegistrationSerializer.Meta):
        fields = BaseRegistrationSerializer.Meta.fields + ('first_name', 'last_name', 'profile')

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password')
        validated_data.pop('password2')
        user = User.objects.create_user(
            **validated_data,
            password=password,
            role=User.Role.CANDIDATE
        )
        CandidateProfile.objects.create(user=user, **profile_data)
        return user

class CompanyRegistrationSerializer(BaseRegistrationSerializer):
    profile = CompanyProfileSerializer(required=True)

    class Meta(BaseRegistrationSerializer.Meta):
        fields = BaseRegistrationSerializer.Meta.fields + ('profile',)

    def validate_profile(self, value):
        if not value.get('company_name'):
            raise serializers.ValidationError("Company name is required.")
        return value

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password')
        validated_data.pop('password2')
        user = User.objects.create_user(
            **validated_data,
            password=password,
            role=User.Role.COMPANY
        )
        CompanyProfile.objects.create(user=user, **profile_data)
        return user