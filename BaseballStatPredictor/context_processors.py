from BaseballStatPredictor.models import User


def user_email(request):
    if hasattr(request, 'user') and isinstance(request.user, User):
        return {'user_email': request.user.email}
    return {'user_email': None}