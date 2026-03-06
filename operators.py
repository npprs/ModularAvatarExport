"""
Operators for Modular Avatar Export
"""

import bpy  # type: ignore
from bpy.types import Operator


class NOPPERS_OT_SaveTemplate(Operator):
    """Save current selection and target names as a reusable template"""

    bl_idname = "noppers.save_template"
    bl_label = "Save Template"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        is_new = scene.noppers_ma_export_active_template == "NEW"

        if is_new:
            # New template: use name field + current selection
            name = scene.noppers_ma_export_template_name.strip()
            if not name:
                self.report({"WARNING"}, "Enter a template name first")
                return {"CANCELLED"}
            selected = [
                obj
                for obj in context.selected_objects
                if obj.type in {"MESH", "ARMATURE"}
            ]
            if not selected:
                self.report({"WARNING"}, "No meshes or armature selected")
                return {"CANCELLED"}
            pairs = [
                f"{obj.name}:{obj.noppers_ma_export_target_name or obj.name}"
                for obj in selected
            ]
        else:
            # Existing template: re-encode from stored object names using current field values
            idx = int(scene.noppers_ma_export_active_template)
            template = scene.noppers_ma_export_templates[idx]
            name = template.name
            stored = [
                pair.split(":", 1)[0]
                for pair in template.data.split(";")
                if ":" in pair
            ]
            pairs = []
            for obj_name in stored:
                obj = scene.objects.get(obj_name)
                if obj:
                    pairs.append(
                        f"{obj.name}:{obj.noppers_ma_export_target_name or obj.name}"
                    )

        # Append enabled bone collections from the armature as '|ColA,ColB'
        armature_obj = None
        if is_new:
            armature_obj = next(
                (obj for obj in selected if obj.type == "ARMATURE"), None
            )
        else:
            for obj_name in stored:
                obj = scene.objects.get(obj_name)
                if obj and obj.type == "ARMATURE":
                    armature_obj = obj
                    break

        data = ";".join(pairs)
        if armature_obj:
            enabled_cols = [
                item.name
                for item in armature_obj.noppers_ma_bone_collection_items
                if item.enabled
            ]
            if enabled_cols:
                data += "|" + ",".join(enabled_cols)

        # Overwrite if name already exists, otherwise add new
        template = next(
            (t for t in scene.noppers_ma_export_templates if t.name == name), None
        )
        if template is None:
            template = scene.noppers_ma_export_templates.add()
            template.name = name
        template.data = data

        # Switch dropdown to the saved template
        for i, t in enumerate(scene.noppers_ma_export_templates):
            if t.name == name:
                scene.noppers_ma_export_active_template = str(i)
                break

        self.report({"INFO"}, f"Saved template '{name}'")
        return {"FINISHED"}


class NOPPERS_OT_RemoveTemplate(Operator):
    """Remove the selected template"""

    bl_idname = "noppers.remove_template"
    bl_label = "Remove Template"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        templates = scene.noppers_ma_export_templates

        if not templates:
            return {"CANCELLED"}

        name = templates[int(scene.noppers_ma_export_active_template)].name
        templates.remove(int(scene.noppers_ma_export_active_template))
        scene.noppers_ma_export_active_template = "NEW"

        self.report({"INFO"}, f"Removed template '{name}'")
        return {"FINISHED"}


class NOPPERS_OT_PrepareExport(Operator):
    """Stage the active template for export in a clean scene"""

    bl_idname = "noppers.prepare_export"
    bl_label = "Stage Export"
    bl_options = {"REGISTER"}

    def execute(self, context):
        from collections import defaultdict

        scene = context.scene
        idx = int(scene.noppers_ma_export_active_template)
        template = scene.noppers_ma_export_templates[idx]
        mappings = [
            pair.split(":", 1) for pair in template.data.split(";") if ":" in pair
        ]
        if not mappings:
            self.report({"WARNING"}, "Template has no objects")
            return {"CANCELLED"}

        # Reuse existing staging scene if already built for this template
        room_name = f"Export: {template.name}"
        existing = bpy.data.scenes.get(room_name)
        if existing:
            context.window.scene = existing
            return {"FINISHED"}

        temp_scene = bpy.data.scenes.new(room_name)
        temp_scene.noppers_ma_source_scene_name = scene.name
        view_layer = temp_scene.view_layers[0]

        try:
            copies = []
            for obj_name, target_name in mappings:
                src = scene.objects.get(obj_name)
                if src is None:
                    self.report({"WARNING"}, f"'{obj_name}' not found, skipping")
                    continue
                copy = src.copy()
                copy.data = src.data.copy()
                temp_scene.collection.objects.link(copy)
                copies.append((copy, target_name, src))

            if not copies:
                self.report({"WARNING"}, "No objects found to build staging scene")
                bpy.data.scenes.remove(temp_scene)
                return {"CANCELLED"}

            # Join meshes sharing the same target name
            mesh_groups = defaultdict(list)
            for copy, target_name, src in copies:
                if src.type == "MESH":
                    mesh_groups[target_name].append(copy)

            for target_name, group in mesh_groups.items():
                if len(group) > 1:
                    with context.temp_override(
                        scene=temp_scene,
                        view_layer=view_layer,
                        selected_objects=group,
                        selected_editable_objects=group,
                        active_object=group[0],
                    ):
                        bpy.ops.object.join()
                group[0].rename(target_name, mode="ALWAYS")
                group[0].data.rename(target_name, mode="ALWAYS")

            # Rename armatures, collect enabled sets for bone deletion
            armature_enabled = {}
            for copy, target_name, src in copies:
                if src.type == "ARMATURE":
                    copy.rename(target_name, mode="ALWAYS")
                    copy.data.rename(target_name, mode="ALWAYS")
                    armature_enabled[copy] = {
                        item.name
                        for item in src.noppers_ma_bone_collection_items
                        if item.enabled
                    }

        except Exception as e:
            self.report({"ERROR"}, f"Failed to build staging scene: {e}")
            bpy.data.scenes.remove(temp_scene)
            return {"CANCELLED"}

        # Switch to staging scene before bone deletion — mode_set requires valid window/area context
        context.window.scene = temp_scene

        for copy, enabled in armature_enabled.items():
            context.view_layer.objects.active = copy
            bpy.ops.object.mode_set(mode="EDIT")
            arm = copy.data

            # Delete bones not in any enabled collection.
            to_delete = [
                bone
                for bone in arm.edit_bones
                if not any(col.name in enabled for col in bone.collections)
            ]
            for bone in to_delete:
                arm.edit_bones.remove(bone)

            bpy.ops.object.mode_set(mode="OBJECT")

        return {"FINISHED"}


class NOPPERS_OT_ReturnToScene(Operator):
    """Return to the original scene and destroy this staging scene"""

    bl_idname = "noppers.return_to_scene"
    bl_label = "Return to Scene"
    bl_options = {"REGISTER"}

    def execute(self, context):
        staging_scene = context.scene
        source_name = staging_scene.noppers_ma_source_scene_name
        source_scene = bpy.data.scenes.get(source_name)
        if source_scene is None:
            self.report({"WARNING"}, f"Original scene '{source_name}' not found")
            return {"CANCELLED"}

        # Switch every window showing the staging scene back to the source
        for window in context.window_manager.windows:
            if window.scene == staging_scene:
                window.scene = source_scene

        # Explicitly remove copied objects and their data to avoid orphan blocks
        ids_to_remove = []
        for obj in staging_scene.collection.objects:
            if obj.data:
                ids_to_remove.append(obj.data)
            ids_to_remove.append(obj)
        bpy.data.batch_remove(ids=ids_to_remove)

        bpy.data.scenes.remove(staging_scene, do_unlink=True)
        return {"FINISHED"}
