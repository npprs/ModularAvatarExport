"""Tests for data.py — pure functions only, no Blender required.

Run from the workspace root:
    python -m pytest ModularAvatarExport/tests/
"""

import importlib.util
import json
import os
import sys
import unittest
from unittest.mock import MagicMock

# Mock bpy before importing — data.py imports bpy at module level
sys.modules["bpy"] = MagicMock()
sys.modules["bpy.types"] = MagicMock()

# Load data.py directly, bypassing __init__.py (which imports operators/display)
_spec = importlib.util.spec_from_file_location(
    "data", os.path.join(os.path.dirname(__file__), "..", "data.py")
)
_data = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_data)

parse_template_data = _data.parse_template_data
encode_template_data = _data.encode_template_data


# --- Fixtures ---
# MMD naming standards

STANDARD_MESHES = {"Body_HighPoly": "BodyAll", "Head_HighPoly": "Body"}
STANDARD_ARMATURE = {"Armature_WIP": "Armature"}
STANDARD_BONE_COLLECTIONS = {"Base": True}


# --- encode_template_data ---


class TestEncodeTemplateData(unittest.TestCase):

    def _decode(self, meshes, armature, bone_collections):
        return json.loads(encode_template_data(meshes, armature, bone_collections))

    def test_should_encode_meshes_as_source_target_pairs(self):
        result = self._decode(STANDARD_MESHES, {}, {})
        self.assertEqual(
            result["meshes"][0], {"source": "Body_HighPoly", "target": "BodyAll"}
        )

    def test_should_nest_bone_collections_under_armature(self):
        result = self._decode(
            STANDARD_MESHES, STANDARD_ARMATURE, STANDARD_BONE_COLLECTIONS
        )
        arm = result["armature"]
        self.assertEqual(arm["source"], "Armature_WIP")
        self.assertEqual(arm["target"], "Armature")
        self.assertIn({"name": "Base", "enabled": True}, arm["bone_collections"])

    def test_should_omit_armature_key_when_none_given(self):
        result = self._decode(STANDARD_MESHES, {}, {})
        self.assertFalse(result.get("armature"))

    def test_should_preserve_disabled_collection_state(self):
        result = self._decode({}, STANDARD_ARMATURE, {"Base": True, "OutfitA": False})
        cols = result["armature"]["bone_collections"]
        self.assertIn({"name": "Base", "enabled": True}, cols)
        self.assertIn({"name": "OutfitA", "enabled": False}, cols)


# --- parse_template_data ---


class TestParseTemplateData(unittest.TestCase):
    def test_should_return_empty_when_data_is_uninitialized(self):
        self.assertEqual(parse_template_data(""), ({}, {}))

    def test_should_return_empty_when_json_is_invalid(self):
        self.assertEqual(parse_template_data("not valid json"), ({}, {}))


# --- Round-trip (encode → parse) ---


class TestRoundTrip(unittest.TestCase):
    def _round_trip(self, meshes, armature, bone_collections):
        encoded = encode_template_data(meshes, armature, bone_collections)
        all_objects, col_states = parse_template_data(encoded)
        return all_objects, col_states

    def test_should_preserve_all_mappings_on_round_trip(self):
        all_objects, col_states = self._round_trip(
            STANDARD_MESHES, STANDARD_ARMATURE, STANDARD_BONE_COLLECTIONS
        )
        self.assertEqual(all_objects, {**STANDARD_MESHES, **STANDARD_ARMATURE})
        self.assertEqual(col_states, STANDARD_BONE_COLLECTIONS)

    def test_should_return_empty_col_states_when_no_armature(self):
        all_objects, col_states = self._round_trip(STANDARD_MESHES, {}, {})
        self.assertEqual(all_objects, STANDARD_MESHES)
        self.assertEqual(col_states, {})


if __name__ == "__main__":
    unittest.main()
