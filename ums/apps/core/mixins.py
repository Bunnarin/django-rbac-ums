from django.db import models
from django.conf import settings

class TimestampMixin(models.Model):
    """
    Abstract base class that provides automatic timestamp tracking.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Updated At")

    class Meta:
        abstract = True
        ordering = ['-created_at']

class AuthorMixin(models.Model):
    """
    Abstract base class that provides authorship tracking.
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
