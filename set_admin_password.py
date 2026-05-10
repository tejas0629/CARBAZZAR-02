#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carbazzar_final.settings')
django.setup()

from django.contrib.auth.models import User

try:
    user = User.objects.get(username='admin')
    user.set_password('admin123')
    user.save()
    print('✅ Admin credentials set:')
    print('   Username: admin')
    print('   Password: admin123')
    print(f'   is_staff: {user.is_staff}')
    print(f'   is_superuser: {user.is_superuser}')
except User.DoesNotExist:
    print('❌ Admin user not found')
except Exception as e:
    print(f'❌ Error: {e}')
