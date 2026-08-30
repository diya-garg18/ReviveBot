"""Make the project root importable so tests can `import config` and
`from revivebot import ...` no matter where pytest is invoked from.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
