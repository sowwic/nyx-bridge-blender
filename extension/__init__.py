"""Nyx Bridge: connects Blender to a running Nyx."""

import bpy
import nyx_bridge_blender

from . import operators, panel, preferences

CLASSES = (
    preferences.NYX_AP_preferences,
    operators.NYX_OT_connect,
    operators.NYX_OT_disconnect,
    panel.NYX_PT_bridge,
)

AUTO_CONNECT_DELAY = 1.0
"""Seconds to wait before connecting on start, the preferences are not there yet."""


def _auto_connect() -> None:
    """Timer: connect if the preferences say so."""
    settings = preferences.get_preferences()
    if settings is not None and settings.auto_connect:
        nyx_bridge_blender.start(**preferences.connection_arguments(settings))


def register():
    """Add the operators, the panel and the preferences."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    panel.start_redraws()
    bpy.app.timers.register(_auto_connect, first_interval=AUTO_CONNECT_DELAY)


def unregister():
    """Disconnect from Nyx and remove what was added."""
    if bpy.app.timers.is_registered(_auto_connect):
        bpy.app.timers.unregister(_auto_connect)
    panel.stop_redraws()
    nyx_bridge_blender.stop()
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
