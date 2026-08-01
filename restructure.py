import os
import shutil
import glob
import re

root = '.'

dirs_to_create = ['frontend', 'frontend/templates', 'frontend/static', 'scripts', 'tests', 'docs', 'logs']
for d in dirs_to_create:
    os.makedirs(d, exist_ok=True)

# 1. Move frontend
if os.path.exists('backend/templates'):
    for item in os.listdir('backend/templates'):
        shutil.move(os.path.join('backend/templates', item), 'frontend/templates/')
    os.rmdir('backend/templates')

if os.path.exists('backend/static'):
    for item in os.listdir('backend/static'):
        shutil.move(os.path.join('backend/static', item), 'frontend/static/')
    os.rmdir('backend/static')

# 2. Rename backend to backend
if os.path.exists('backend'):
    if os.path.exists('backend'):
        # If backend already exists, move contents
        for item in os.listdir('backend'):
            shutil.move(os.path.join('backend', item), 'backend/')
        os.rmdir('backend')
    else:
        os.rename('backend', 'backend')

# 3. Move root files
for f in os.listdir('.'):
    if not os.path.isfile(f):
        continue
    if f.endswith('.md'):
        shutil.move(f, 'docs/')
    elif f.endswith('.log') or (f.endswith('.txt') and f != 'requirements.txt'):
        shutil.move(f, 'logs/')
    elif f.startswith('test_') and f.endswith('.py'):
        shutil.move(f, 'tests/')
    elif f.endswith('.py') and f not in ['start_anpr_system.bat', 'start_atlas_service.bat', 'requirements.txt', 'restructure.py']:
        shutil.move(f, 'scripts/')

print('Moved files.')

# 4. Find and replace 'from backend' and 'import backend' with 'backend'
def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        
        new_content = re.sub(r'\bsrc\b', 'backend', content)
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(new_content)
            print(f'Updated imports in {filepath}')
    except Exception as e:
        print(f'Error reading {filepath}: {e}')

for root_dir, dirs, files in os.walk('.'):
    if '.venv' in root_dir or '.git' in root_dir or 'frontend' in root_dir or 'logs' in root_dir or 'docs' in root_dir:
        continue
    for name in files:
        if name.endswith('.py') or name.endswith('.bat'):
            replace_in_file(os.path.join(root_dir, name))

# 5. Fix web_app.py paths
web_app_path = 'backend/api/web_app.py'
if os.path.exists(web_app_path):
    with open(web_app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update template_dir and static_dir specifically
    content = content.replace("os.path.abspath(os.path.join(current_dir, '../../backend/templates'))", "os.path.abspath(os.path.join(current_dir, '../../../frontend/templates'))")
    content = content.replace("os.path.abspath(os.path.join(current_dir, '../../backend/static'))", "os.path.abspath(os.path.join(current_dir, '../../../frontend/static'))")
    
    with open(web_app_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated web_app.py paths.')

# 6. Delete empty files
for root_dir, dirs, files in os.walk('.'):
    if '.venv' in root_dir or '.git' in root_dir:
        continue
    for name in files:
        filepath = os.path.join(root_dir, name)
        if os.path.getsize(filepath) == 0:
            os.remove(filepath)
            print(f'Deleted empty file: {filepath}')

print('Done restructuring.')
