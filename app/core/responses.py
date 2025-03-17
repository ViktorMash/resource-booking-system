from typing import Optional, Any, Dict
from fastapi.responses import JSONResponse
from fastapi import status, HTTPException, Request
from datetime import datetime, date

from app.schemas import ResponseSchema, ResponseMetaSchema
from app.core import settings
from app.core.utils import get_status_suffix


class ApiResponse:
    """
    Unified API response class for the application.
    Provides a consistent structure for all API responses.
    """

    @staticmethod
    def _prepare_data(data: Any) -> Any:
        """
        Prepare SQLAlchemy models (ORM objects) for serialization to JSON
        """

        # handle None
        if data is None:
            return None

        # handle ORM objects
        if hasattr(data, '__table__'):

            # convert ORM object to dict
            result = {}
            for column in data.__table__.columns:
                value = getattr(data, column.name)

                # handle datetime values
                if isinstance(value, (datetime, date)):
                    result[column.name] = value.strftime(settings.DATETIME_TEMPLATE)
                else:
                    result[column.name] = value
            return result

        # handle dicts
        if isinstance(data, dict):
            return {k: ApiResponse._prepare_data(v) for k, v in data.items()}

        # handle lists
        elif isinstance(data, list):
            return [ApiResponse._prepare_data(item) for item in data]

        # return other types as is
        return data


    @staticmethod
    def _create_response(
            data: Optional[Any] = None,
            status_code: int = status.HTTP_200_OK,
            message: str = "",
            details: Optional[str] = None,
            headers: Optional[Dict[str, str]] = None
    ) -> JSONResponse:
        """
        Creating standardized response using pydantic schema
        """
        meta = ResponseMetaSchema(
            status=get_status_suffix(status_code),
            status_code=status_code,
            message=message,
            details=details
        )

        # Prepare data for JSON serialization
        prepared_data = ApiResponse._prepare_data(data) if data is not None else None

        response_obj = ResponseSchema(
            data=prepared_data,
            meta=meta
        )

        return JSONResponse(
            content=response_obj.model_dump(),
            headers=headers
        )

    @classmethod
    def success(
            cls,
            data: Optional[Any] = None,
            status_code=status.HTTP_200_OK,
            message: str = "Operation completed successfully",
            details: Optional[str] = None
    ) -> JSONResponse:
        """
        Success response
        """
        return cls._create_response(
            data=data,
            status_code=status_code,
            message=message,
            details=details
        )

    @classmethod
    def error(
            cls,
            status_code=status.HTTP_400_BAD_REQUEST,
            message: str = "Operation failed",
            details: Optional[str] = None,
            headers: Optional[Dict[str, str]] = None
    ) -> JSONResponse:
        """
        Error response
        """
        return cls._create_response(
            status_code=status_code,
            message=message,
            details=details,
            headers=headers
        )


class CustomException(HTTPException):
    """
    Custom exception class that will be converted to a standardized API response
    """

    def __init__(
            self,
            status_code: int,
            message: str,
            details: Optional[str] = None,
            headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(
            status_code=status_code,
            detail=details,
            headers=headers
        )
        self.message = message
        self.details = details


def exception_handler(request: Request, exc: CustomException) -> JSONResponse:
    """
    Exception handler for CustomException
    Returns a standardized API response
    """
    return ApiResponse.error(
        status_code=exc.status_code,
        message=exc.message,
        details=exc.details,
    )