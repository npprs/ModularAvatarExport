# Modular Avatar Export

Blender addon for VRChat avatar modular export. Define per-module templates (which objects to export, export names, which bone collections to include), then stage and export with one click.

Solves Blender's naming conflict problem by duplicating objects into a temporary clean-room scene for renaming and export.

## Requirements

- Blender 4.5.7

## Usage

### Setup

- Have a working mesh and armature fully rigged and ready
- Define bone collections on the armature for each modular part (e.g. base, outfit A)

### Save a template

- Select meshes and the armature in the viewport
- Provide export names for the selected meshes
- Toggle which bone collections to include
- Name the template and click **+** to save

### Export

- Select a saved template and click **Stage Export**
- Export FBX from the staging scene, then click **Return**

## Development

### Building

```bash
blender --command extension build
blender --command extension validate
```

Run from the addon directory (requires `blender_manifest.toml`).

### Testing

Pure data functions can be tested without Blender:

```bash
cd ModularAvatarExport
python -m pytest tests/
python -m unittest discover tests/
```

## Manual Testing

### Core flow

- Select meshes + armature, name and save a template → appears in dropdown
- Stage a template → opens `Export: <name>` scene with objects renamed
- Two meshes with the same export name → joined into one on stage
- Disable a bone collection, stage → those bones absent from armature
- Click **Return** → back to original scene, staging scene gone
- Save `.blend`, reload → template still present and stages correctly

### Error paths

- **+** with two armatures selected → no template
- **+** with no name → no template


