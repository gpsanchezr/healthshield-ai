from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class UsuarioManager(BaseUserManager):
    def create_user(self, username, email, password=None, rol='analista', **extra_fields):
        if not username:
            raise ValueError('El username es requerido')
        if not email:
            raise ValueError('El email es requerido')

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, rol=rol, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('rol', 'administrador')
        extra_fields.setdefault('is_active', True)
        return self.create_user(username=username, email=email, password=password, **extra_fields)


class UsuarioClinico(AbstractBaseUser, PermissionsMixin):
    """Usuario del sistema con roles clínicos."""

    ROL_ADMIN = 'administrador'
    ROL_MEDICO = 'medico'
    ROL_ANALISTA = 'analista'

    ROL_CHOICES = [
        (ROL_ADMIN, 'Administrador'),
        (ROL_MEDICO, 'Médico'),
        (ROL_ANALISTA, 'Analista'),
    ]

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default=ROL_ANALISTA)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    objects = UsuarioManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return f'{self.username} ({self.rol})'

    @property
    def is_staff(self):
        return self.rol == self.ROL_ADMIN

