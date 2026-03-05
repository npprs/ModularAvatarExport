# Modular Export

Automate VRChat avatar modular export workflow with clean renaming and bone collection filtering.

## Goal

Simplify exporting different avatar modules (body, head, outfit, props) from a single mega-armature project.

## Problem

VRChat avatar development uses modular rigs maintained with tools like VRCFury and Modular Avatar. Blender makes exporting individual parts painful:

1. **Naming Conflicts**: Duplicating `Armature_WIP` creates `Armature.001`, `.002`, etc. (Blender enforces unique names)
2. **Manual Renaming**: Must rename object AND data names, one at a time
3. **Bone Cleanup**: Manually delete unused bone collections before export
4. **Repetitive**: Do this for every module (body, head, outfit1, outfit2, etc.)
5. **Error-Prone**: Easy to miss a rename or export the wrong thing

## Solution

**"Clean Room" Export Process:**

Create a temporary, empty scene where Blender can't create naming conflicts. Then:
1. Duplicate selected objects to clean scene
2. Rename perfectly (no `.001` interference)
3. Delete unwanted bone collections
4. Export FBX
5. Clean up automatically

## How It Works

1. **Define Rename Map** (one-time setup)
   - `Armature_WIP` → `Armature`
   - `Body_HighPoly` → `Body`
   - `Willa_Head_HighPoly` → `Willa_Head`

2. **Create Export Profiles** (one-time setup)
   - Profile: "Body + Head"
   - Keep bone collections: Base Body, Head
   - Objects to export: Armature, Body, Head
   - Optional: Force join specific meshes (e.g., Body + Head → Body for VRCFT/MMD)

3. **Export** (one-click)
   - Select profile: "Body + Head"
   - Click "Export"
   - Addon:
     - Creates temp scene
     - Joins configured meshes (if specified)
     - Duplicates + renames
     - Removes unwanted bones
     - Exports FBX
     - Deletes temp scene
   - Done

## Workflow Benefits

- **Original file untouched** - No risk of accidentally renaming your main rig
- **Perfect naming** - Always exports as `Armature`, `Body`, etc.
- **One-click** - Set up once, then just select profile and export
- **Repeatable** - Same result every time for outfit1, outfit2, props, etc.

## Technical Details

- Uses temporary scene + duplicates (avoids naming conflicts)
- Bone collection filtering by name
- Optional: Per-profile mesh joining (e.g., for VRCFT/MMD compatibility where head+body must be single "Body" mesh)
- Auto-renames object + data names
- Custom export profiles stored in blend file
