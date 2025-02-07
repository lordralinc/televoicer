from tortoise import fields, models

__all__ = ("VoiceTemplate",)


class VoiceTemplate(models.Model):
    id = fields.UUIDField(primary_key=True)
    user_id = fields.BigIntField()
    name = fields.CharField(max_length=64)
    file_id = fields.TextField()

    class Meta(models.Model.Meta):
        unique_together = ("user_id", "name")
