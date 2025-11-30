from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.conf import settings


@require_GET
def api_status(request):
    """Simple API status endpoint"""
    return JsonResponse({
        'status': 'connected',
        'message': 'PollR API is running successfully!',
        'version': '1.0.0',
        'endpoints': {
            'graphql': '/graphql/',
            'api_docs': '/api/docs/',
            'admin': '/admin/',
            'rest_api': '/api/v1/'
        },
        'features': {
            'graphql': True,
            'rest_api': True,
            'background_tasks': True,
            'redis_cloud': True
        }
    })


@require_GET
def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'debug': settings.DEBUG,
        'database': 'connected' if hasattr(settings, 'DATABASES') else 'disconnected'
    })
