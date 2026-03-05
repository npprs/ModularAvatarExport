"""
Data structures for Modular Avatar Export
"""

import bpy  # type: ignore
from bpy.types import PropertyGroup


class NOPPERS_ExportTemplate(PropertyGroup):
    """A saved export template. Stores name mappings as 'obj:target' pairs separated by semicolons."""

    data: bpy.props.StringProperty(default="")  # "ObjA:TargetA;ObjB:TargetB"


class NOPPERS_BoneCollectionItem(PropertyGroup):
    """A bone collection entry with an enabled toggle"""

    enabled: bpy.props.BoolProperty(name="Include", default=True)


# Module-level cache to prevent GC of dynamic enum items
_template_enum_cache = []


def _get_template_items(self, context):
    global _template_enum_cache
    _template_enum_cache = [
        ("NEW", "New", "Create a new template from current selection")
    ]
    if context and context.scene:
        for i, t in enumerate(context.scene.noppers_ma_export_templates):
            _template_enum_cache.append((str(i), t.name, ""))
    return _template_enum_cache


def _on_active_template_changed(self, context):
    """Apply the selected template: select its objects and populate noppers_ma_export_target_name fields."""
    if self.noppers_ma_export_active_template == "NEW":
        self.noppers_ma_export_template_name = ""
        return
    idx = int(self.noppers_ma_export_active_template)
    if idx >= len(self.noppers_ma_export_templates):
        return
    template = self.noppers_ma_export_templates[idx]
    if not template.data:
        return
    mappings = dict(
        pair.split(":", 1) for pair in template.data.split(";") if ":" in pair
    )

    last_armature = None
    for obj_name, target_name in mappings.items():
        obj = self.objects.get(obj_name)
        if obj:
            obj.hide_set(False)
            obj.hide_viewport = False
            obj.noppers_ma_export_target_name = target_name
            if obj.type == "ARMATURE":
                last_armature = obj

    if last_armature and context.view_layer:
        context.view_layer.objects.active = last_armature


def register():
    bpy.utils.register_class(NOPPERS_ExportTemplate)
    bpy.utils.register_class(NOPPERS_BoneCollectionItem)

    bpy.types.Object.noppers_ma_export_target_name = bpy.props.StringProperty(
        name="Export As",
        description="Name to use when exporting this object (leave empty to use current name)",
        default="",
    )

    bpy.types.Object.noppers_ma_bone_collection_items = bpy.props.CollectionProperty(
        type=NOPPERS_BoneCollectionItem
    )

    bpy.types.Scene.noppers_ma_export_templates = bpy.props.CollectionProperty(
        type=NOPPERS_ExportTemplate
    )

    bpy.types.Scene.noppers_ma_export_active_template = bpy.props.EnumProperty(
        name="Template",
        items=_get_template_items,
        update=_on_active_template_changed,
    )

    bpy.types.Scene.noppers_ma_export_template_name = bpy.props.StringProperty(
        name="Template Name", description="Name for the new template", default=""
    )

    bpy.types.Scene.noppers_ma_source_scene_name = bpy.props.StringProperty(
        name="MA Source Scene",
        description="Set when this scene is in staging — stores the name of the original scene",
        default="",
    )


def unregister():
    del bpy.types.Scene.noppers_ma_source_scene_name
    del bpy.types.Scene.noppers_ma_export_template_name
    del bpy.types.Scene.noppers_ma_export_active_template
    del bpy.types.Scene.noppers_ma_export_templates
    del bpy.types.Object.noppers_ma_bone_collection_items
    del bpy.types.Object.noppers_ma_export_target_name
    bpy.utils.unregister_class(NOPPERS_BoneCollectionItem)
    bpy.utils.unregister_class(NOPPERS_ExportTemplate)
