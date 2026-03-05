"""
Display panels for Modular Avatar Export
"""

import bpy  # type: ignore
from bpy.types import Panel


class NOPPERS_PT_ModularAvatarExport(Panel):
    """Main panel for Modular Avatar Export"""

    bl_label = "Modular Avatar Export"
    bl_idname = "NOPPERS_PT_modular_avatar_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NOPPERS Tools"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Staging mode — show return button and nothing else
        if scene.source_scene_name:
            self._draw_clean_room(layout, scene)
            return

        is_new = scene.export_active_template == "NEW"

        # ── Template Selector ─────────────────────────────────
        row = layout.row(align=True)
        row.prop(scene, "export_active_template", text="")
        if is_new:
            has_selection = any(
                obj.type in {"MESH", "ARMATURE"} for obj in context.selected_objects
            )
            save_sub = row.row(align=True)
            save_sub.enabled = has_selection
            save_sub.operator("noppers.save_template", text="", icon="ADD")
            layout.prop(
                scene, "export_template_name", text="", placeholder="Template name..."
            )
        else:
            row.operator("noppers.save_template", text="", icon="ADD")
            row.operator("noppers.remove_template", text="", icon="REMOVE")

        layout.separator()

        if is_new:
            self._draw_new_template(layout, context)
        else:
            self._draw_saved_template(layout, context, scene)

    def _draw_clean_room(self, layout, scene):
        """Shown when the current Blender scene is in staging."""
        col = layout.column(align=True)
        col.label(text=f"Source:  {scene.source_scene_name}", icon="SCENE_DATA")
        layout.separator()
        row = layout.row()
        row.scale_y = 1.6
        row.operator(
            "noppers.return_to_scene",
            text=f"Return to  {scene.source_scene_name}",
            icon="LOOP_BACK",
        )

    def _draw_new_template(self, layout, context):
        """Selection-driven UI for building a new template."""
        selected_meshes = [
            obj for obj in context.selected_objects if obj.type == "MESH"
        ]
        selected_armatures = [
            obj for obj in context.selected_objects if obj.type == "ARMATURE"
        ]

        # Meshes
        layout.label(text="Meshes:", icon="MESH_DATA")
        if selected_meshes:
            target_counts = {}
            for obj in selected_meshes:
                t = obj.export_target_name.strip() or obj.name
                target_counts[t] = target_counts.get(t, 0) + 1

            for obj in selected_meshes:
                box = layout.box()
                col = box.column(align=True)
                row = col.row()
                row.enabled = False
                row.label(text=obj.name)
                t = obj.export_target_name.strip() or obj.name
                name_row = col.row(align=True)
                name_row.prop(
                    obj, "export_target_name", text="Export As", placeholder=obj.name
                )
                if target_counts.get(t, 0) > 1:
                    name_row.label(text="", icon="LINKED")
        else:
            layout.label(text="Select one or more meshes", icon="INFO")

        # Armature
        layout.separator()
        layout.label(text="Armature:", icon="ARMATURE_DATA")
        if selected_armatures:
            obj = selected_armatures[0]
            col = layout.column(align=True)
            row = col.row()
            row.enabled = False
            row.label(text=obj.name)
            col.prop(obj, "export_target_name", text="Export As", placeholder=obj.name)

            layout.separator()
            layout.label(text="Bone Collections:", icon="GROUP_BONE")
            if obj.bone_collection_items:
                for item in obj.bone_collection_items:
                    layout.prop(item, "enabled", text=item.name)
            else:
                layout.label(text="No bone collections found", icon="INFO")
        else:
            layout.label(text="Select an armature", icon="INFO")

    def _draw_saved_template(self, layout, context, scene):
        """Template-data-driven UI — persistent regardless of selection."""
        idx = int(scene.export_active_template)
        if idx >= len(scene.export_templates):
            return
        template = scene.export_templates[idx]
        mappings = [
            pair.split(":", 1) for pair in template.data.split(";") if ":" in pair
        ]

        meshes = [
            (n, t)
            for n, t in mappings
            if scene.objects.get(n) is None or scene.objects[n].type == "MESH"
        ]
        armatures = [
            (n, t)
            for n, t in mappings
            if scene.objects.get(n) and scene.objects[n].type == "ARMATURE"
        ]

        # Meshes
        layout.label(text="Meshes:", icon="MESH_DATA")
        target_counts = {}
        for obj_name, _ in meshes:
            obj = scene.objects.get(obj_name)
            if obj:
                t = obj.export_target_name.strip() or obj.name
                target_counts[t] = target_counts.get(t, 0) + 1

        for obj_name, _ in meshes:
            obj = scene.objects.get(obj_name)
            box = layout.box()
            col = box.column(align=True)
            # Name row with status icon
            name_row = col.row(align=True)
            if obj is None:
                name_row.label(text="", icon="ERROR")
                name_row.label(text=obj_name + "  (missing)")
            else:
                if obj.hide_get() or obj.hide_viewport:
                    name_row.label(text="", icon="HIDE_ON")
                name_row.label(text=obj_name)
            # Export name field (editable if object exists)
            if obj:
                t = obj.export_target_name.strip() or obj.name
                name_row2 = col.row(align=True)
                name_row2.prop(
                    obj, "export_target_name", text="Export As", placeholder=obj.name
                )
                if target_counts.get(t, 0) > 1:
                    name_row2.label(text="", icon="LINKED")

        # Armature
        layout.separator()
        layout.label(text="Armature:", icon="ARMATURE_DATA")
        if armatures:
            obj_name, _ = armatures[0]
            obj = scene.objects.get(obj_name)
            if obj is None:
                row = layout.row()
                row.label(text="", icon="ERROR")
                row.label(text=obj_name + "  (missing)")
            else:
                col = layout.column(align=True)
                status_row = col.row()
                if obj.hide_get() or obj.hide_viewport:
                    status_row.label(text="", icon="HIDE_ON")
                status_row.label(text=obj_name)
                col.prop(
                    obj, "export_target_name", text="Export As", placeholder=obj.name
                )

                layout.separator()
                layout.label(text="Bone Collections:", icon="GROUP_BONE")
                if obj.bone_collection_items:
                    for item in obj.bone_collection_items:
                        layout.prop(item, "enabled", text=item.name)
                else:
                    layout.label(text="No bone collections found", icon="INFO")
        else:
            layout.label(text="No armature in template", icon="INFO")

        # Staging mode — show return button and nothing else
        layout.separator()
        row = layout.row()
        row.scale_y = 1.4
        row.operator("noppers.prepare_export", text="Stage Export")
