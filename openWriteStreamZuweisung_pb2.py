"""Compatibility shim for generated proto imports.

Allows absolute imports like `import openWriteStreamZuweisung_pb2` to resolve
when running the project from the repository root.
"""

from generated.openWriteStreamZuweisung_pb2 import *  # noqa: F401,F403
