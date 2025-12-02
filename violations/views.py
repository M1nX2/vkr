import os
import logging
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from datetime import datetime, timedelta
import requests
from .models import Violation

logger = logging.getLogger(__name__)

# Основной и резервный URL бэкенда
API_URL = getattr(settings, 'PYTHON_API_URL', 'http://neurodog-backend:8000')
API_URL_FALLBACK = getattr(settings, 'PYTHON_API_URL_FALLBACK', None)


def get_available_api_url():
    """Получение доступного URL бэкенда (основной или резервный)"""
    # Пробуем основной URL
    try:
        response = requests.get(f'{API_URL}/health', timeout=5)
        if response.status_code == 200:
            logger.info(f'Основной бэкенд доступен: {API_URL}')
            return API_URL
    except Exception as e:
        logger.warning(f'Основной бэкенд недоступен ({API_URL}): {e}')
    
    # Пробуем резервный URL, если указан
    if API_URL_FALLBACK:
        try:
            response = requests.get(f'{API_URL_FALLBACK}/health', timeout=5)
            if response.status_code == 200:
                logger.info(f'Резервный бэкенд доступен: {API_URL_FALLBACK}')
                return API_URL_FALLBACK
        except Exception as e:
            logger.warning(f'Резервный бэкенд недоступен ({API_URL_FALLBACK}): {e}')
    
    logger.error('Ни один из бэкендов не доступен')
    return None


def check_api_health():
    """Проверка доступности Python API"""
    return get_available_api_url() is not None


class MainView(View):
    """Главная страница"""
    def get(self, request):
        # Проверяем доступность бэкенда
        backend_available = check_api_health()
        return render(request, 'main.html', {
            'backend_available': backend_available
        })


class VideoUploadView(View):
    """Загрузка и обработка видео"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def options(self, request):
        """Обработка OPTIONS запросов для CORS"""
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken'
        return response
    
    def post(self, request):
        logger.info(f'POST запрос на /api/video/upload/ получен')
        logger.info(f'Request method: {request.method}')
        logger.info(f'Request FILES: {list(request.FILES.keys())}')
        
        # Проверяем доступность API и получаем доступный URL
        api_url = get_available_api_url()
        if not api_url:
            return JsonResponse({
                'success': False,
                'message': f'Python API недоступен. Проверено: {API_URL}' + (f', {API_URL_FALLBACK}' if API_URL_FALLBACK else '')
            }, status=503)
        
        # Проверяем наличие файла
        if 'videoFile' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'Файл не найден'
            }, status=400)
        
        file = request.FILES['videoFile']
        
        # Проверяем размер файла (500MB)
        max_size = 500 * 1024 * 1024
        if file.size > max_size:
            return JsonResponse({
                'success': False,
                'message': f'Размер файла ({round(file.size / 1024 / 1024, 2)}MB) превышает максимально допустимый (500MB)'
            }, status=413)
        
        # Проверяем тип файла
        allowed_types = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo']
        if file.content_type not in allowed_types:
            return JsonResponse({
                'success': False,
                'message': 'Неподдерживаемый тип файла'
            }, status=400)
        
        try:
            logger.info(f'Начало обработки видео: {file.name}')
            
            # Отправляем файл в Python API (используем доступный URL)
            with file.open('rb') as f:
                files = {'file': (file.name, f, file.content_type)}
                response = requests.post(
                    f'{api_url}/api/v1/process-video',
                    files=files,
                    timeout=600
                )
            
            logger.info(f'Ответ от Python API: {response.status_code}')
            
            if response.status_code == 200:
                data = response.json()
                
                # Сохраняем нарушения в базу данных
                if 'violations' in data and isinstance(data['violations'], list) and len(data['violations']) > 0:
                    try:
                        for violation_data in data['violations']:
                            Violation.objects.create(
                                time=violation_data.get('time', '00:00:00'),
                                type=violation_data.get('type', 'Неубранные экскременты'),
                                description=violation_data.get('description', ''),
                                source=violation_data.get('source', ''),
                                date=violation_data.get('date', datetime.now().date()),
                                video_id=data.get('video_id'),
                                video_url=violation_data.get('video_url'),
                                breed=violation_data.get('breed'),
                                muzzle=violation_data.get('muzzle'),
                            )
                        logger.info(f'Сохранено нарушений в БД: {len(data["violations"])}')
                    except Exception as e:
                        logger.error(f'Ошибка сохранения нарушений в БД: {e}')
                else:
                    logger.info('Нарушений не обнаружено, пропускаем сохранение в БД')
                
                return JsonResponse({
                    'success': True,
                    'data': data
                })
            else:
                logger.error(f'Ошибка Python API: {response.text}')
                return JsonResponse({
                    'success': False,
                    'message': f'Ошибка обработки видео: {response.text}',
                    'status': response.status_code
                }, status=response.status_code)
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f'Ошибка подключения к Python API: {e}')
            return JsonResponse({
                'success': False,
                'message': f'Не удалось подключиться к Python API. Проверьте, что сервис запущен и доступен по адресу: {API_URL}'
            }, status=503)
        except Exception as e:
            logger.error(f'Ошибка обработки видео: {e}')
            return JsonResponse({
                'success': False,
                'message': f'Ошибка: {str(e)}'
            }, status=500)


class ViolationsListView(View):
    """Получение списка нарушений"""
    
    def get(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        try:
            # Пытаемся получить из Python API
            params = {}
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            
            response = requests.get(f'{API_URL}/api/v1/violations', params=params, timeout=10)
            
            if response.status_code == 200:
                return JsonResponse({
                    'success': True,
                    'violations': response.json()
                })
        except Exception:
            pass
        
        # Fallback на базу данных
        query = Violation.objects.all()
        
        if start_date:
            query = query.filter(date__gte=start_date)
        if end_date:
            query = query.filter(date__lte=end_date)
        
        violations = query.order_by('date', 'time')
        
        violations_data = [{
            'time': v.time,
            'type': v.type,
            'description': v.description,
            'source': v.source,
            'date': v.date.strftime('%Y-%m-%d'),
            'video_url': v.video_url,
            'breed': v.breed,
            'muzzle': v.muzzle,
        } for v in violations]
        
        return JsonResponse({
            'success': True,
            'violations': violations_data
        })


class VideoViolationsView(View):
    """Получение нарушений для конкретного видео"""
    
    def get(self, request, video_id):
        try:
            response = requests.get(f'{API_URL}/api/v1/violations/{video_id}', timeout=10)
            
            if response.status_code == 200:
                return JsonResponse({
                    'success': True,
                    'data': response.json()
                })
        except Exception:
            pass
        
        # Fallback на базу данных
        violations = Violation.objects.filter(video_id=video_id)
        
        violations_data = [{
            'time': v.time,
            'type': v.type,
            'description': v.description,
            'source': v.source,
            'date': v.date.strftime('%Y-%m-%d'),
            'video_url': v.video_url,
            'breed': v.breed,
            'muzzle': v.muzzle,
        } for v in violations]
        
        return JsonResponse({
            'success': True,
            'data': {
                'video_id': video_id,
                'violations': violations_data,
                'processing_time': None
            }
        })


class VideoProgressView(View):
    """Получение прогресса обработки видео"""
    
    def get(self, request, video_id):
        try:
            response = requests.get(f'{API_URL}/api/v1/progress/{video_id}', timeout=10)
            
            if response.status_code == 200:
                return JsonResponse(response.json())
        except Exception:
            pass
        
        # Если прогресс не найден, возможно обработка завершена
        return JsonResponse({
            'percent': 100,
            'status': 'Завершено',
            'completed': True
        })


class VideoView(View):
    """Получение обработанного видео"""
    
    def get(self, request, video_id):
        try:
            response = requests.get(f'{API_URL}/api/v1/video/{video_id}', timeout=30, stream=True)
            
            if response.status_code == 200:
                http_response = HttpResponse(response.content, content_type='video/mp4')
                return http_response
        except Exception as e:
            logger.error(f'Ошибка получения видео: {e}')
        
        return JsonResponse({
            'success': False,
            'message': 'Видео не найдено'
        }, status=404)


class ReportView(View):
    """Страница отчетов"""
    
    def get(self, request):
        # Получаем даты из сессии или по умолчанию
        start_date = request.session.get('report_start_date', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date = request.session.get('report_end_date', timezone.now().strftime('%Y-%m-%d'))
        
        # Получаем нарушения из базы данных
        violations = Violation.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date', 'time')
        
        violations_data = [{
            'time': v.time,
            'type': v.type,
            'description': v.description,
            'breed': v.breed or 'Не указана',
            'muzzle': 'Да' if v.muzzle else ('Нет' if v.muzzle is False else 'Не указано'),
            'video_url': v.video_url,
            'source': v.source,
            'date': v.date.strftime('%Y-%m-%d')
        } for v in violations]
        
        return render(request, 'report.html', {
            'violations': violations_data,
            'start_date': start_date,
            'end_date': end_date,
            'report_title': f'Отчет о нарушениях за период с {start_date} по {end_date}'
        })
    
    def post(self, request):
        from django.contrib import messages
        from django.shortcuts import redirect
        
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        if not start_date or not end_date:
            messages.error(request, 'Необходимо указать обе даты')
            return redirect('report')
        
        if datetime.strptime(end_date, '%Y-%m-%d') < datetime.strptime(start_date, '%Y-%m-%d'):
            messages.error(request, 'Дата окончания не может быть раньше даты начала')
            return redirect('report')
        
        # Сохраняем в сессию
        request.session['report_start_date'] = start_date
        request.session['report_end_date'] = end_date
        
        return redirect('report')


class ExportExcelView(View):
    """Экспорт отчета в Excel"""
    
    def get(self, request):
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment
        from django.http import HttpResponse
        
        start_date = request.session.get('report_start_date', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date = request.session.get('report_end_date', timezone.now().strftime('%Y-%m-%d'))
        
        # Получаем нарушения
        violations = Violation.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date', 'time')
        
        # Создаем Excel файл
        wb = Workbook()
        ws = wb.active
        ws.title = 'Нарушения'
        
        # Заголовки
        headers = ['Дата', 'Таймкод', 'Тип нарушения', 'Описание', 'Порода', 'Намордник', 'Источник видео', 'Ссылка на видео']
        ws.append(headers)
        
        # Стили для заголовков
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # Данные
        for v in violations:
            ws.append([
                v.date.strftime('%Y-%m-%d'),
                v.time,
                v.type,
                v.description,
                v.breed or 'Не указана',
                'Да' if v.muzzle else ('Нет' if v.muzzle is False else 'Не указано'),
                v.source,
                v.video_url or 'Не указана'
            ])
        
        # Автоподбор ширины колонок
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Создаем ответ
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f'violations_report_{start_date}_to_{end_date}.xlsx'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        wb.save(response)
        return response

