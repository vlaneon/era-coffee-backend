import sys
import io
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
import django
django.setup()

from django.core.management import call_command

output_file = 'db_backup.json'
original_stdout = sys.stdout

with io.open(output_file, 'w', encoding='utf-8') as f:
    sys.stdout = f
    call_command('dumpdata', indent=2, natural_foreign=True, natural_primary=True)

sys.stdout = original_stdout
print("Дамп успешно создан в файле:", output_file)