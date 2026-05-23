from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import UsuarioClinico
from .permissions import EsAdministrador
from .serializers import LoginSerializer, RegisterSerializer


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class RefreshView(TokenRefreshView):
    pass


class RegisterView(generics.GenericAPIView):
    permission_classes = [EsAdministrador]
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        UsuarioClinico.objects.create_user(
            username=serializer.validated_data['username'],
            email=serializer.validated_data['email'],
            rol=serializer.validated_data['rol'],
            password=serializer.validated_data['password'],
        )
        return Response({'status': 'created'}, status=status.HTTP_201_CREATED)

