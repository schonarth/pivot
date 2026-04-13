from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed market configs and assets into the database"

    def handle(self, *args, **options):
        from markets.services import seed_market_configs
        from markets.seed_data import run_seed

        self.stdout.write("Seeding market configs...")
        seed_market_configs()
        self.stdout.write(self.style.SUCCESS("Market configs seeded."))

        self.stdout.write("Seeding assets...")
        run_seed()
        self.stdout.write(self.style.SUCCESS("Assets seeded."))