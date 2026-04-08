from django.core.management.base import BaseCommand

from todos.models import Topic

DEFAULT_TOPICS = ["House", "Business", "Personal", "Gardening"]


class Command(BaseCommand):
    help = "Create default topics if they don't exist"

    def handle(self, *args, **options):
        for name in DEFAULT_TOPICS:
            topic, created = Topic.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created topic "{name}"'))
            else:
                self.stdout.write(f'Topic "{name}" already exists')
