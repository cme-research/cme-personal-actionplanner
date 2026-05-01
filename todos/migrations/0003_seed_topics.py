from django.db import migrations

DEFAULT_TOPICS = ["House", "Business", "Personal", "Gardening"]


def seed_topics(apps, schema_editor):
    Topic = apps.get_model("todos", "Topic")
    for name in DEFAULT_TOPICS:
        Topic.objects.get_or_create(name=name)


def remove_topics(apps, schema_editor):
    Topic = apps.get_model("todos", "Topic")
    Topic.objects.filter(name__in=DEFAULT_TOPICS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("todos", "0002_todoitem_estimation"),
    ]

    operations = [
        migrations.RunPython(seed_topics, remove_topics),
    ]
