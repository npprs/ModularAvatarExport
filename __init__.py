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
_register_classes, _unregister_classes = bpy.utils.register_classes_factory(classes)


def _sync_bone_collections(scene, _depsgraph):
    """Sync armature bone collection changes"""

    if scene.noppers_ma_source_scene_name != "":
        return  # staging scene — skip

    for obj in scene.objects:
        if obj.type != "ARMATURE":
            continue

        collections = obj.data.collections
        items = obj.noppers_ma_bone_collection_items
        if len(collections) == len(items) and all(
            c.name == i.name for c, i in zip(collections, items)
        ):
            continue

        existing = {item.name: item.enabled for item in items}
        items.clear()

        for bone in collections:
            item = items.add()
            item.name = bone.name
            item.enabled = existing.get(bone.name, True)


def register():
    data.register()
    _register_classes()
    bpy.app.handlers.depsgraph_update_post.append(_sync_bone_collections)


def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(_sync_bone_collections)
    _unregister_classes()
    data.unregister()
