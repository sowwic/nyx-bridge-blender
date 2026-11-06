import bpy
import nyx_bridge_blender

from .preferences import connection_arguments, get_preferences


class NYX_OT_connect(bpy.types.Operator):
    """Connect this Blender to Nyx, and keep trying until Nyx is running."""

    bl_idname = "nyx.connect"
    bl_label = "Connect to Nyx"

    def execute(self, context):
        """Start the client with the settings of the preferences."""
        nyx_bridge_blender.start(**connection_arguments(get_preferences(context)))
        return {"FINISHED"}


class NYX_OT_disconnect(bpy.types.Operator):
    """Disconnect this Blender from Nyx."""

    bl_idname = "nyx.disconnect"
    bl_label = "Disconnect from Nyx"

    def execute(self, context):
        """Stop the client."""
        nyx_bridge_blender.stop()
        return {"FINISHED"}
