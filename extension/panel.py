import bpy
import nyx_bridge_blender

REDRAW_INTERVAL = 1.0
"""Seconds between redraws of the panel, so it follows the connection."""

_redraw_wanted = False


class NYX_PT_bridge(bpy.types.Panel):
    """Connection to Nyx, in the sidebar of the 3D viewport."""

    bl_label = "Nyx Bridge"
    bl_idname = "NYX_PT_bridge"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Nyx"

    def draw(self, context):
        """Show the state of the connection and the button for the next step."""
        layout = self.layout
        client = nyx_bridge_blender.get_client()
        if nyx_bridge_blender.is_connected():
            layout.label(text=f"Connected to {client.server_name}", icon="LINKED")
            layout.label(text=f"As {client.name}")
        elif nyx_bridge_blender.is_running():
            layout.label(text="Waiting for Nyx...", icon="TIME")
        else:
            layout.label(text="Not connected", icon="UNLINKED")

        if nyx_bridge_blender.is_running():
            layout.operator("nyx.disconnect", icon="X")
        else:
            layout.operator("nyx.connect", icon="PLAY")


def _redraw() -> float | None:
    """Timer: redraw the areas showing the panel.

    Returns:
        float | None: seconds until the next call, None once the redraws are off.
    """
    if not _redraw_wanted:
        return None
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()
    return REDRAW_INTERVAL


def start_redraws() -> None:
    """Keep the panel up to date with the connection."""
    global _redraw_wanted
    _redraw_wanted = True
    if not bpy.app.timers.is_registered(_redraw):
        bpy.app.timers.register(_redraw, first_interval=REDRAW_INTERVAL, persistent=True)


def stop_redraws() -> None:
    """Stop redrawing the panel."""
    global _redraw_wanted
    _redraw_wanted = False
