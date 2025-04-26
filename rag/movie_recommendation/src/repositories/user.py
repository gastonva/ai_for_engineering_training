from src.models import User
from src.repositories.base import ModelRepository


class UserRepository(ModelRepository):
    model = User
