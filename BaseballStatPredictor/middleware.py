from django.utils.deprecation import MiddlewareMixin
from BaseballStatPredictor.models import User

class UserEmailMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if hasattr(request, 'user') and isinstance(request.user, User):
            request.user_email = request.user.email
        else:
            request.user_email = None