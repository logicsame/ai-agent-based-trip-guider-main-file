import os
from pathlib import Path
import logging


logging.basicConfig(level=logging.INFO, format='[%(asctime)s]: %(message)s:')

project_name = 'tripplanner'

list_of_files = [
    '.github/workflows/.gitkeep',
    f"src/{project_name}/__init__.py",
    f"src/{project_name}/utils/__init__.py",
    f"src/{project_name}/utils/common.py",
    f"src/{project_name}/spot_searching_system_p1",
   

    "test.py",
    "main.py",
    "Dockerfile",
    "requirements.txt",
    "setup.py",
    
     ]


for filepath in list_of_files:
    filpath = Path(filepath)
    filedir, filename = os.path.split(filepath)
    
    
    if filedir != "":
        os.makedirs(filedir, exist_ok=True)
        logging.info(f"Creatin directory:{filedir} for the {filename}")
        
    if (not os.path.exists(filepath)) or (os.path.getsize(filepath) == 0):
        with open(filepath, 'w') as f:
            pass
        logging.info(f'Creating empty file: {filepath}')
        
        
    else:
        logging.info(f'{filename} is already exist')
        