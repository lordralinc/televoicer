import enum
import random
import string
import uuid

from tortoise import fields, models

__all__ = (
    "User",
    "VoiceTemplate",
    "VoiceTemplatePack",
)

rnd = random.SystemRandom()


class User(models.Model):
    voice_templates: fields.BackwardFKRelation["VoiceTemplate"]
    voice_template_packs: fields.BackwardFKRelation["VoiceTemplatePack"]

    id = fields.BigIntField(primary_key=True)
    username = fields.CharField(max_length=256)
    is_admin = fields.BooleanField(default=False)
    banned = fields.BooleanField(default=False)

    class Meta(models.Model.Meta):
        table = "users"
        indexes = (("username",),)


class VoiceTemplate(models.Model):
    user_id: int
    origin_template_id: uuid.UUID

    packs: fields.ManyToManyRelation["VoiceTemplatePack"]

    id = fields.UUIDField(primary_key=True)
    user: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
        "models.User", related_name="voice_templates"
    )
    name = fields.CharField(max_length=64)
    origin_template: fields.ForeignKeyNullableRelation["VoiceTemplate"] = fields.ForeignKeyField(
        "models.VoiceTemplate",
        null=True,
        on_delete=fields.SET_NULL,
    )
    file_id = fields.TextField()

    class Meta(models.Model.Meta):
        table = "voice_templates"
        ordering = ("name",)
        unique_together = ("user_id", "name")
        indexes = (("name",),)


class VoiceTemplatePack(models.Model):
    author_id: int

    class Privacy(enum.IntEnum):
        PRIVATE = enum.auto()
        PUBLIC = enum.auto()

    id = fields.UUIDField(primary_key=True)
    name = fields.CharField(max_length=64)
    privacy = fields.IntEnumField(Privacy, default=Privacy.PUBLIC)
    last_update = fields.DatetimeField(auto_now=True)
    shortcode = fields.CharField(max_length=6, unique=True)
    usage_count = fields.BigIntField(default=0)
    author: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
        "models.User", related_name="voice_template_packs"
    )
    templates: fields.ManyToManyRelation["VoiceTemplate"] = fields.ManyToManyField(
        "models.VoiceTemplate", related_name="packs"
    )

    @classmethod
    def generate_shortcode(cls) -> str:
        return "".join(rnd.choices(string.ascii_letters + string.digits, k=6))

    class Meta(models.Model.Meta):
        table = "voice_template_packs"
        ordering = ("name",)
        unique_together = ("author", "name")
        indexes = (
            ("author",),
            ("shortcode",),
            ("privacy",),
        )
