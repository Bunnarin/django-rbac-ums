from django.db import models
from django.db.models import Q
from django.conf import settings # Use settings.AUTH_USER_MODEL for user ForeignKey

class TimestampMixin(models.Model):
    """
    Abstract base class that provides created_at and updated_at fields.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Updated At")

    class Meta:
        abstract = True # This tells Django not to create a table for this model itself
        ordering = ['-created_at'] # A common default ordering

class AuthorMixin(models.Model):
    """
    Abstract base class that provides an author field linked to the User model.
    """
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True, # Allow blank author, especially if it's set on save
        verbose_name="Created By",
        related_name='%(class)s_created', # Dynamic related_name to avoid clashes
        help_text="The user who created this record."
    )

    class Meta:
        abstract = True

class UserRLSMixin(models.Model):
    """
    Mixin for models that need to define how they relate to a specific user
    for default RLS, e.g., via an 'author' or 'owner' field.
    """
    class Meta:
        abstract = True

    def get_user_rls_filter(self, user):
        """
        Returns a Q object to filter objects to those specific to the user.
        Models inheriting this mixin should override this method to define
        you need to override this sht to author, professor, student...
        sht must be used with the RLSManager
        """
        # example override
        # return Q(author=user)
        raise NotImplementedError(
            f"Model {self.__class__.__name__} inheriting UserSpecificRLSMixin "
            "must implement get_user_rls_filter method."
        )