from django.core.management.base import BaseCommand
from events.models import Category

class Command(BaseCommand):
    help = 'Seeds the database with default categories'

    def handle(self, *args, **kwargs):
        categories = [
            ("Hackathon", "bi-code-slash"),
            ("Seminar", "bi-mic"),
            ("Workshop", "bi-tools"),
            ("Conference", "bi-megaphone"),
            ("Meetup", "bi-people"),
            ("Webinar", "bi-display"),
            ("Networking", "bi-diagram-3")
        ]
        
        count = 0
        for name, icon in categories:
            obj, created = Category.objects.get_or_create(name=name, defaults={"icon": icon})
            if created:
                count += 1
                
        self.stdout.write(self.style.SUCCESS(f'Successfully added {count} new categories!'))
