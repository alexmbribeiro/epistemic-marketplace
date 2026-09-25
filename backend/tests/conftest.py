"""Test configuration.

The suite deliberately touches no database and makes no model calls. Every
piece tested here is pure logic — the Elo arithmetic, the jury draw, name
resolution, output coercion, trajectory metrics, retry classification — which
is where the bugs in this project actually lived.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
