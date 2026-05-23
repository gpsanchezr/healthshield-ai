"""
Management command to create a superuser if it doesn't exist.
Usage: python manage.py createsuperuser_if_not_exists --user admin --email admin@example.com --password secret
"""
from django.core.management.base import BaseCommand
from apps.authentication.models import UsuarioClinico


class Command(BaseCommand):
    help = 'Creates a superuser if no users exist in the database'

    def add_arguments(self, parser):
        parser.add_argument('--user', '--username', dest='username', default='admin')
        parser.add_argument('--email', dest='email', default='admin@healthshield.ai')
        parser.add_argument('--password', dest='password', default='admin123')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        if UsuarioClinico.objects.filter(username=username).exists():
            self.stdout.write(f'User "{username}" already exists — skipping.')
            return

        UsuarioClinico.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully.'))