# nyx-bridge-blender

Connects Blender to a running [Nyx](https://github.com/sowwic/nyx), so stages can send
commands to Blender and get the results back. It is the Blender client of
[nyx-bridge](https://github.com/sowwic/nyx-bridge): Blender **connects out** to the bridge
server of Nyx, Nyx never launches or reaches into Blender on its own.

In Blender: open the 3D viewport sidebar (`N`), tab **Nyx**, press **Connect to Nyx**. Or
from Python:

```python
import nyx_bridge_blender

nyx_bridge_blender.start()        # connects, retrying until Nyx is up
```

```python
# in blender --background
import nyx_bridge_blender

nyx_bridge_blender.BlenderClient().serve_forever()
```

| If you want to... | Read |
| --- | --- |
| Install the extension and connect Blender to Nyx | [User Guide](user/index.md) |
| Work on nyx-bridge-blender, run its tests with `bpy` | [Developer Guide](dev/index.md) |
| Look up a class or function | API reference (see the navigation) |

Requires Blender 4.2 or newer. See also
[nyx-bridge-maya](https://github.com/sowwic/nyx-bridge-maya).
