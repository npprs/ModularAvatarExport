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


def register():
    data.register()
    _register_classes()
    bpy.app.handlers.depsgraph_update_post.append(data.sync_bone_collections)


def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(data.sync_bone_collections)
    _unregister_classes()
    data.unregister()
