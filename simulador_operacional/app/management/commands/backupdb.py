from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
import shutil
from datetime import datetime

class Command(BaseCommand):
    help = 'Gera um backup do banco de dados SQLite.'

    def handle(self, *args, **options):
        db_path = settings.DATABASES['default']['NAME']
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_file = backup_dir / f'db_{timestamp}.sqlite3'
        shutil.copy(db_path, backup_file)
        self.stdout.write(self.style.SUCCESS(f'Backup criado em {backup_file}'))
