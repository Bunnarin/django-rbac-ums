from django.db import models
from django.conf import settings

class TimestampMixin(models.Model):
    """
    Abstract base class that provides automatic timestamp tracking.
    
    Adds two timestamp fields to any model that inherits from it:
    - created_at: Automatically set when the object is first created
    - updated_at: Automatically updated every time the object is saved
    
    Attributes:
        created_at: DateTimeField that automatically records creation time
        updated_at: DateTimeField that automatically records last update time
    
    Meta:
        abstract: True - This is an abstract base class
        ordering: ['-created_at'] - Default ordering by creation time (newest first)
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Updated At")

    class Meta:
        abstract = True
        ordering = ['-created_at']

class AuthorMixin(models.Model):
    """
    Abstract base class that provides authorship tracking.
    
    Adds an author field that links to the User model, allowing tracking of
    who created each record. The author field can be null if the record
    was created before the author field was added.
    
    Attributes:
        author: ForeignKey to AUTH_USER_MODEL that tracks who created the record
    
    Meta:
        abstract: True - This is an abstract base class
    
    Notes:
        - Uses dynamic related_name to avoid naming conflicts
        - Provides a help_text for better documentation in admin interface
    """
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Created By",
        related_name='%(class)s_created',
        help_text="The user who created this record."
    )

    class Meta:
        abstract = True

class UserRLSMixin(models.Model):
    """
    Abstract base class for implementing Row-Level Security (RLS).
    
    Provides a base implementation for models that need to restrict access
    based on user relationships. Models inheriting this mixin must implement
    their own get_user_rls_filter method to define how records should be
    filtered for each user.
    
    Meta:
        abstract: True - This is an abstract base class
    
    Requirements:
        - Must be used with RLSManager
        - Must implement get_user_rls_filter method in inheriting models
    """
    class Meta:
        abstract = True

    def get_user_rls_filter(self, user):
        """
        Get the filter condition for row-level security.
        
        This method should be overridden by inheriting models to provide
        specific filtering logic based on user relationships.
        
        Args:
            user: The user for whom to generate the filter
            
        Raises:
            NotImplementedError: If the method is not overridden in the inheriting class
        """
        raise NotImplementedError(
            f"Model {self.__class__.__name__} inheriting UserRLSMixin "
            "must implement get_user_rls_filter method."
        )