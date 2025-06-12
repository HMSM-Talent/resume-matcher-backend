from rest_framework_simplejwt.authentication import JWTAuthentication
import logging

logger = logging.getLogger(__name__)

class LoggingJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        try:
            auth_header = request.headers.get('Authorization', '')
            logger.info(f"JWT Auth attempt - Header: {auth_header[:20]}...")
            
            result = super().authenticate(request)
            
            if result:
                user, token = result
                logger.info(f"JWT Auth successful - User: {user.email}, Token type: {token.token_type}")
            else:
                logger.warning("JWT Auth failed - No valid token found")
            
            return result
        except Exception as e:
            logger.error(f"JWT Auth error: {str(e)}", exc_info=True)
            raise 