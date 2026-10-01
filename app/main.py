from fastapi import FastAPI

from app.core import health
from app.core.exception_handlers import (
    authentication_exception_handler,
    authorization_exception_handler,
    conflict_exception_handler,
    not_found_exception_handler,
    service_unavailable_exception_handler,
    unexpected_exception_handler,
    validation_exception_handler,
)
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    ConflictException,
    NotFoundException,
    ServiceUnavailableException,
    ValidationException,
)
from app.modules.auth import router as auth
from app.modules.users import router as users

app = FastAPI(title="FoodGo API", version="1.0.0")

app.add_exception_handler(AuthenticationException, authentication_exception_handler)  # type: ignore
app.add_exception_handler(AuthorizationException, authorization_exception_handler)  # type: ignore
app.add_exception_handler(NotFoundException, not_found_exception_handler)  # type: ignore
app.add_exception_handler(ConflictException, conflict_exception_handler)  # type: ignore
app.add_exception_handler(ValidationException, validation_exception_handler)  # type: ignore
app.add_exception_handler(
    ServiceUnavailableException, service_unavailable_exception_handler
)  # type: ignore
app.add_exception_handler(Exception, unexpected_exception_handler)


app.include_router(health.router)
app.include_router(users.router)
app.include_router(auth.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "FoodGo API"}
