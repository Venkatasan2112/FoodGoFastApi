class AppException(Exception):
    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class AuthenticationException(AppException):
    pass


class AuthorizationException(AppException):
    pass


class NotFoundException(AppException):
    pass


class ConflictException(AppException):
    pass


class ValidationException(AppException):
    pass


class ServiceUnavailableException(AppException):
    pass
