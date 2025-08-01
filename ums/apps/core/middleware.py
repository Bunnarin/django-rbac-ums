import logging
from django.shortcuts import redirect
from django.contrib import messages

logger = logging.getLogger(__name__)

class GlobalExceptionHandlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        # Log the error
        logger.error(f"Error processing request: {str(exception)}", exc_info=True)
        
        # Show user-friendly message
        messages.error(
            request, 
            str(exception),
            extra_tags="alert-danger"
        )
        
        # Redirect to home or error page
        return redirect('home')