from fastapi import HTTPException
from pydantic import BaseModel


class NotFoundException(HTTPException):
    def __init__(self, archive_type: BaseModel, id: str):
        super().__init__(
            status_code = 404, 
            detail = {
                'message': f'{archive_type.__name__} of id \'{id}\' not Found',
                'status': 404
            }
        )


class NotAuthenticatedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code = 401, 
            detail = {
                'message': 'User is not authenticated. Please, use the correct credentials.',
                'status': 401
            }
        )


class NotAuhorizedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code = 403, 
            detail = {
                'message': 'User is not authorized to perform this action.',
                'status': 403
            }
        )

class InternalServerErrorException(HTTPException):
    def __init__(self, detail: str = "An internal server error occurred.", error: Exception = None):
        super().__init__(
            status_code = 500,
            detail = {
                'message': detail,
                'status': 500,
                'error': str(error) if error else 'N/A'
            }
        )

def handle_exception(e: Exception) -> HTTPException:
    if isinstance(e, HTTPException):
        return e
    else:
        return InternalServerErrorException(error=e)