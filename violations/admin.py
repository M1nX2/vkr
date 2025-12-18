from django.contrib import admin
from django.db.utils import OperationalError, DatabaseError
import logging

logger = logging.getLogger(__name__)

# Пытаемся импортировать модель и зарегистрировать её в admin
# Если БД недоступна, просто пропускаем регистрацию
try:
    from .models import Violation
    
    @admin.register(Violation)
    class ViolationAdmin(admin.ModelAdmin):
        list_display = ['date', 'time', 'type', 'breed', 'muzzle']
        list_filter = ['date', 'type', 'muzzle']
        search_fields = ['type', 'description', 'breed']
        date_hierarchy = 'date'
except (OperationalError, DatabaseError) as e:
    logger.warning(f'БД недоступна, пропускаем регистрацию модели Violation в admin: {e}')
except Exception as e:
    logger.warning(f'Ошибка при регистрации модели Violation в admin: {e}')

