import sys
from pathlib import Path

# Adiciona o root do projeto ao sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
