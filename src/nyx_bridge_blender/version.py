import importlib.metadata

try:
    __version__ = importlib.metadata.version("nyx-bridge-blender")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"
