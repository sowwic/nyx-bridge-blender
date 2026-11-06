import bpy


class NYX_AP_preferences(bpy.types.AddonPreferences):
    """Where Nyx is, and whether to connect when the extension is enabled."""

    bl_idname = __package__

    address: bpy.props.StringProperty(
        name="Address",
        description="host:port of Nyx. Empty finds a Nyx running on this computer",
    )
    token: bpy.props.StringProperty(
        name="Token",
        description="Token of the Nyx server. Empty uses the one Nyx wrote or the "
        "environment",
        subtype="PASSWORD",
    )
    client_name: bpy.props.StringProperty(
        name="Name",
        description="Name Nyx shows for this Blender. Empty uses the process id",
    )
    auto_connect: bpy.props.BoolProperty(
        name="Connect on start",
        description="Connect to Nyx when Blender starts or the extension is enabled",
        default=False,
    )

    def draw(self, context):
        """Draw the settings."""
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, "auto_connect")
        layout.prop(self, "address")
        layout.prop(self, "token")
        layout.prop(self, "client_name")


def get_preferences(context=None):
    """Get the preferences of the extension.

    Args:
        context (bpy.types.Context | None): context, the current one if omitted.

    Returns:
        NYX_AP_preferences | None: preferences, None while the extension is not
            enabled as an add-on (e.g. in tests).
    """
    context = context or bpy.context
    addon = context.preferences.addons.get(__package__)
    return addon.preferences if addon is not None else None


def connection_arguments(preferences=None) -> dict:
    """Get the arguments of `nyx_bridge_blender.start` the preferences describe.

    Args:
        preferences (NYX_AP_preferences | None): preferences, none give the defaults.

    Returns:
        dict: `address`, `token` and `name`, None for what is empty.
    """
    if preferences is None:
        return {"address": None, "token": None, "name": None}
    return {
        "address": preferences.address.strip() or None,
        "token": preferences.token or None,
        "name": preferences.client_name.strip() or None,
    }
