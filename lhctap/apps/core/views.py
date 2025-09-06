from django.http import JsonResponse
from django.db import connection
from django.utils import timezone


def health_check(request):
    """Endpoint de health check para monitoramento"""
    try:
        # Verificar conexão com banco
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'database': 'connected',
            'version': '1.0.0'
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'error': str(e)
        }, status=503)
