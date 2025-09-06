import logging
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger('lhctap.audit')


class AuditMiddleware:
    """Middleware para auditoria de requisições"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = timezone.now()
        
        response = self.get_response(request)
        
        # Log apenas requisições importantes
        if self.should_audit(request):
            duration = (timezone.now() - start_time).total_seconds()
            
            logger.info(
                f"Request: {request.method} {request.path} | "
                f"User: {getattr(request.user, 'username', 'anonymous')} | "
                f"IP: {self.get_client_ip(request)} | "
                f"Status: {response.status_code} | "
                f"Duration: {duration:.3f}s"
            )
        
        return response
    
    def should_audit(self, request):
        """Determina se a requisição deve ser auditada"""
        audit_paths = ['/api/', '/dashboard/', '/admin/']
        return any(request.path.startswith(path) for path in audit_paths)
    
    def get_client_ip(self, request):
        """Extrai IP do cliente considerando proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')