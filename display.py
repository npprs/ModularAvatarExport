"""
Display UI panels for Modular Avatar Export
"""

from bpy.types import Panel
from .data import parse_template_data


class NOPPERS_PT_ModularAvatarExport(Panel):
    """Main panel for Modular Avatar Export"""

    bl_label = "Modular Avatar Export"
    bl_idname = "NOPPERS_PT_modular_avatar_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NOPPERS Tools"  # Shared addon category

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Staging mode — show return button and nothing else
        if scene.noppers_ma_source_scene_name != "":
            self._draw_clean_room(layout, scene)
            return

        # Edit mode
        is_new = scene.noppers_ma_export_active_template == "NEW"

        self._draw_template_selector(layout, context, scene, is_new)
        layout.separator()

        if is_new:
            # New Template - Can SAVE
            self._draw_new_template(layout, context)
        else:
            # Saved Template - Can EXPORT, UPDATE, or DELETE
            self._draw_saved_template(layout, scene)

    def _draw_template_selector(self, layout, context, scene, is_new):
        """Template dropdown with save/remove buttons."""
        row = layout.row(align=True)
        row.prop(scene, "noppers_ma_export_active_template", text="")

        if is_new:
            # New Template - SAVE
            has_selection = any(
                obj.type in {"MESH", "ARMATURE"} for obj in context.selected_objects
            )
            save_sub_row = row.row(align=True)
            save_sub_row.enabled = has_selection
            save_sub_row.operator("noppers.save_template", text="", icon="ADD")
            layout.prop(
                scene,
                "noppers_ma_export_template_name",
                text="",
                placeholder="Template name...",
            )
        else:
            # Saved Template - UPDATE or DELETE
            row.operator("noppers.save_template", text="", icon="ADD")
            row.operator("noppers.remove_template", text="", icon="REMOVE")

    def _draw_clean_room(self, layout, scene):
        """Staging mode - Can return to source scene"""
        col = layout.column(align=True)
        col.label(
            text=f"Source:  {scene.noppers_ma_source_scene_name}", icon="SCENE_DATA"
        )
        layout.separator()
        row = layout.row()
        row.scale_y = 1.6
        row.operator(
            "noppers.return_to_scene",
            text=f"Return to  {scene.noppers_ma_source_scene_name}",
            icon="LOOP_BACK",
        )

    def _draw_mesh_list(self, layout, meshes):
        """Draw export name fields for a list of mesh objects."""
        target_counts = {}
        for obj in meshes:
            target_name = obj.noppers_ma_export_target_name.strip() or obj.name
            target_counts[target_name] = target_counts.get(target_name, 0) + 1

        for obj in meshes:
            box = layout.box()
            col = box.column(align=True)
            row = col.row()
            row.enabled = False
            row.label(text=obj.name)
            name_row = col.row(align=True)
            name_row.prop(
                obj,
                "noppers_ma_export_target_name",
                text="Export As",
                placeholder=obj.name,
            )
            target_name = obj.noppers_ma_export_target_name.strip() or obj.name
            if target_counts.get(target_name, 0) > 1:
                name_row.label(text="", icon="LINKED")

    def _draw_armature_bone_collection(self, layout, armatures, empty_label):
        """Draw export name and bone collections for the first armature, or an empty label."""
        if not armatures:
            layout.label(text=empty_label, icon="INFO")
            return
        obj = armatures[0]
        col = layout.column(align=True)
        row = col.row()
        row.enabled = False
        row.label(text=obj.name)
        col.prop(
            obj,
            "noppers_ma_export_target_name",
            text="Export As",
            placeholder=obj.name,
        )

        layout.separator()
        layout.label(text="Bone Collections:", icon="GROUP_BONE")
        if obj.noppers_ma_bone_collection_items:
            for item in obj.noppers_ma_bone_collection_items:
                layout.prop(item, "enabled", text=item.name)
        else:
            layout.label(text="No bone collections found", icon="INFO")

    def _draw_new_template(self, layout, context):
        """New template - Update UI based on scene selection"""
        selected_meshes = [
            obj for obj in context.selected_objects if obj.type == "MESH"
        ]
        selected_armatures = [
            obj for obj in context.selected_objects if obj.type == "ARMATURE"
        ]

        # Meshes
        layout.label(text="Meshes:", icon="MESH_DATA")
        if selected_meshes:
            self._draw_mesh_list(layout, selected_meshes)
        else:
            layout.label(text="Select one or more meshes", icon="INFO")

        # Armature
        layout.separator()
        layout.label(text="Armature:", icon="ARMATURE_DATA")
        self._draw_armature_bone_collection(
            layout, selected_armatures, "Select an armature"
        )

    def _draw_saved_template(self, layout, scene):
        """Template-data-driven UI — persistent regardless of selection."""
        idx = int(scene.noppers_ma_export_active_template)
        if idx >= len(scene.noppers_ma_export_templates):
            return
        template = scene.noppers_ma_export_templates[idx]
        mappings, _ = parse_template_data(template.data)

        meshes = [
            scene.objects[n]
            for n, _ in mappings.items()
            if scene.objects.get(n) and scene.objects[n].type == "MESH"
        ]
        armatures = [
            scene.objects[n]
            for n, _ in mappings.items()
            if scene.objects.get(n) and scene.objects[n].type == "ARMATURE"
        ]

        # Meshes
        layout.label(text="Meshes:", icon="MESH_DATA")
        self._draw_mesh_list(layout, meshes)

        # Armature
        layout.separator()
        layout.label(text="Armature:", icon="ARMATURE_DATA")
        self._draw_armature_bone_collection(
            layout, armatures, "No armature in template"
        )

        # Stage for export
        layout.separator()
        row = layout.row()
        row.scale_y = 1.4
        row.operator("noppers.prepare_export", text="Stage Export")
