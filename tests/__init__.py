"""Tests mirror src/d4xmm. Run from the repo root: python -m unittest discover -s tests -t ."""
import os
import sys

# the package lives under src/, which is not on the path when unittest starts from the root
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
