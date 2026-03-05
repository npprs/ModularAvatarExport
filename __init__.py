"""
Modular Avatar Export - Automate modular avatar export
"""

import bpy  # type: ignore
from . import operators, display, data

classes = (
    operators.NOPPERS_OT_SaveTemplate,
    operators.NOPPERS_OT_RemoveTemplate,
    operators.NOPPERS_OT_PrepareExport,
    operators.NOPPERS_OT_ReturnToScene,
    display.NOPPERS_PT_ModularAvatarExport,
    # TODO: Add a way to detect zombie bone(s) without collections
)


def _sync_bone_collections(scene, depsgraph):
    """Sync armature bone collection changes"""

    if scene.noppers_ma_source_scene_name != "":
        return  # Skip if not in source scene

    for obj in scene.objects:
        if obj.type != "ARMATURE":
            continue

        cols = obj.data.collections
        items = obj.noppers_ma_bone_collection_items
        if len(cols) == len(items) and all(
            c.name == i.name for c, i in zip(cols, items)
        ):
            continue

        existing = {item.name: item.enabled for item in items}
        items.clear()

        for col in cols:
            item = items.add()
            item.name = col.name
            item.enabled = existing.get(col.name, True)


def register():
    data.register()

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.app.handlers.depsgraph_update_post.append(_sync_bone_collections)


def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(_sync_bone_collections)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    data.unregister()


if __name__ == "__main__":
    register()
