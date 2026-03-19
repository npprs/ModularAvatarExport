"""
Data parsing for Modular Avatar Export
"""

import json

import bpy  # type: ignore
from bpy.types import PropertyGroup


class NOPPERS_ExportTemplate(PropertyGroup):
    """Modular avatar export template. Stores data as JSON with 'meshes' and 'armature' keys."""

    data: bpy.props.StringProperty(default="")


class NOPPERS_BoneCollectionItem(PropertyGroup):
    """Bone collection entry with an enabled toggle"""

    enabled: bpy.props.BoolProperty(name="Include", default=True)


def parse_template_data(data: str) -> tuple[dict[str, str], dict[str, bool]]:
    """Parse template data string into (object→target mappings, collection name→enabled state).

    Merges 'meshes' and 'armature' into a single dict for callers that iterate all objects.
    Returns empty dicts if data is empty or not valid JSON (e.g. templates from an older format).
    """
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        return {}, {}
    meshes = {m["source"]: m["target"] for m in parsed.get("meshes", [])}
    arm_data = parsed.get("armature")
    if arm_data:
        armature = {arm_data["source"]: arm_data["target"]}
        col_states = {
            c["name"]: c["enabled"] for c in arm_data.get("bone_collections", [])
        }
    else:
        armature = {}
        col_states = {}
    return {**meshes, **armature}, col_states


def encode_template_data(
    meshes: dict[str, str], armature: dict[str, str], bone_collections: dict[str, bool]
) -> str:
    """Encode mesh mappings, armature mapping, and bone collections into a template data string.

    meshes:
        {source_name: target_name, ...}
        Example: {"Body_WIP": "BodyAll", "Head_WIP": "Body"}

    armature:
        {source_name: target_name} — single entry, or empty dict if no armature.
        Example: {"Armature_WIP": "Armature"}

    bone_collections:
        {collection_name: is_enabled, ...} — ignored when armature is empty.
        Example: {"Base": True, "OutfitA": False}

    template (output):
        {
          "meshes": [{"source": str, "target": str}, ...],
          "armature": {"source": str, "target": str, "bone_collections": [{"name": str, "enabled": bool}, ...]} | null
        }

    """
    mesh_list = [
        {"source": source, "target": target} for source, target in meshes.items()
    ]
    armature_data = None
    if armature:
        source, target = next(iter(armature.items()))
        armature_data = {
            "source": source,
            "target": target,
            "bone_collections": [
                {"name": name, "enabled": enabled}
                for name, enabled in bone_collections.items()
            ],
        }
    return json.dumps({"meshes": mesh_list, "armature": armature_data})


@bpy.app.handlers.persistent
def sync_bone_collections(scene, _depsgraph):
    """Depsgraph handler — keeps noppers_ma_bone_collection_items in sync with armature collections.

    Scans all armatures rather than filtering by depsgraph updates: Blender does not reliably
    report bone collection additions/deletions as armature data updates.
    """
    if scene.noppers_ma_source_scene_name != "":
        return

    for obj in scene.objects:
        if obj.type != "ARMATURE":
            continue
        collections = obj.data.collections
        tracked_collection_items = obj.noppers_ma_bone_collection_items

        # Skip if collections are unchanged
        collection_names = [col.name for col in collections]
        tracked_names = [tracked.name for tracked in tracked_collection_items]

        if collection_names == tracked_names:
            continue

        # Preserve existing enabled states by name before clearing
        existing = {
            tracked.name: tracked.enabled for tracked in tracked_collection_items
        }

        # Rebuild tracked list from current collections
        tracked_collection_items.clear()

        for col in collections:
            entry = tracked_collection_items.add()
            entry.name = col.name
            entry.enabled = existing.get(col.name, True)


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
    """Apply the selected template: unhide its objects and restore noppers_ma_export_target_name fields."""
    if self.noppers_ma_export_active_template == "NEW":
        self.noppers_ma_export_template_name = ""
        return
    idx = int(self.noppers_ma_export_active_template)
    if idx >= len(self.noppers_ma_export_templates):
        return
    template = self.noppers_ma_export_templates[idx]
    mappings, col_states = parse_template_data(template.data)

    if not mappings and template.data:
        # Data is non-empty but invalid — template is corrupted, remove it
        self.noppers_ma_export_templates.remove(idx)
        self.noppers_ma_export_active_template = "NEW"
        return

    last_armature = None
    for obj_name, target_name in mappings.items():
        obj = self.objects.get(obj_name)
        if obj:
            # TODO: unhiding here overwrites the user's viewport state — consider
            # moving this to the Stage operator, applied to the duplicate instead.
            obj.hide_set(False)
            obj.hide_viewport = False
            obj.noppers_ma_export_target_name = target_name
            if obj.type == "ARMATURE":
                last_armature = obj

    if last_armature and context.view_layer:
        context.view_layer.objects.active = last_armature

    # Restore enabled bone collections saved in the template
    if last_armature:
        for item in last_armature.noppers_ma_bone_collection_items:
            item.enabled = col_states.get(item.name, True)


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
