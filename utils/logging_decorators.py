import logging
from functools import wraps

logger_user = logging.getLogger("user")
logger_job_posting = logging.getLogger("job_posting")
logger_resume = logging.getLogger("resume")
logger_search = logging.getLogger("search")
logger_utils = logging.getLogger("utils")


def log_user_call(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        logger_user.info(f"요청: {request.method} {request.path}")
        try:
            response = view_func(request, *args, **kwargs)
            logger_user.info(f"응답: {response.status_code} {request.path}")
            return response
        except Exception as e:
            logger_user.exception(f"에러 발생: {e}")
            raise

    return wrapper


def log_job_posting_call(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        logger_job_posting.info(f"요청: {request.method} {request.path}")
        try:
            response = view_func(request, *args, **kwargs)
            logger_job_posting.info(f"응답: {response.status_code} {request.path}")
            return response
        except Exception as e:
            logger_job_posting.exception(f"에러 발생: {e}")
            raise

    return wrapper


def log_resume_call(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        logger_resume.info(f"요청: {request.method} {request.path}")
        try:
            response = view_func(request, *args, **kwargs)
            logger_resume.info(f"응답: {response.status_code} {request.path}")
            return response
        except Exception as e:
            logger_resume.exception(f"에러 발생: {e}")
            raise

    return wrapper


def log_search_call(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        logger_search.info(f"요청: {request.method} {request.path}")
        try:
            response = view_func(request, *args, **kwargs)
            logger_search.info(f"응답: {response.status_code} {request.path}")
            return response
        except Exception as e:
            logger_search.exception(f"에러 발생: {e}")
            raise

    return wrapper


def log_utils_call(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        logger_utils.info(f"요청: {request.method} {request.path}")
        try:
            response = view_func(request, *args, **kwargs)
            logger_utils.info(f"응답: {response.status_code} {request.path}")
            return response
        except Exception as e:
            logger_utils.exception(f"에러 발생: {e}")
            raise

    return wrapper
