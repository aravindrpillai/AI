from django.db import models
from django.utils import timezone

class RollingCodes(models.Model):

    email = models.EmailField(null=False, unique=True)
    app = models.CharField(max_length=10, null=False)
    code = models.CharField(max_length=10, null=False)
    gen_time = models.DateTimeField(null=True, default=timezone.now())
    valid_for = models.IntegerField(null=False, default=20)

    class Meta:
        db_table = 'util_rolling_codes'
        constraints = [
            models.UniqueConstraint(fields=["email", "app"], name="util_unique_tog_1")
        ]
        indexes = [
            models.Index(fields=["email", "app"], name="util_index_1")
        ]

