# Animation Domain Context

<!-- Skeletal animation asset inspection and named-notify authoring conventions for CortexAnimation -->

## What CortexAnimation Does

`CortexAnimation` exposes the `anim` MCP domain for Unreal skeletal animation assets.
It can inspect `UAnimSequence`, `UAnimMontage`, `USkeleton`, and `UAnimBlueprint`
metadata, and can author a narrow Phase B slice: sequence skeleton named notifies.

## Commands

| Command | Purpose |
|---------|---------|
| `anim.list_assets` | List AnimSequence, AnimMontage, Skeleton, and AnimBlueprint assets by type, path, query, and limit. |
| `anim.get_sequence_info` | Inspect sequence timing, skeleton, notifies, curves, sync markers, root motion, and fingerprint. |
| `anim.get_montage_info` | Inspect montage length, sections, slots, segments, notifies, branching points, skeleton, and fingerprint. |
| `anim.get_skeleton_info` | Inspect bones, parent indexes, sockets, virtual bones, preview mesh, and fingerprint. |
| `anim.get_animbp_info` | Inspect AnimBP target skeleton, classes, state machines, states, transitions, node GUIDs, and graph GUIDs. |
| `anim.add_named_notify` | Add one sequence skeleton named notify with `expected_fingerprint`, `dry_run`, and optional `save`. |
| `anim.update_named_notify` | Update exactly one sequence skeleton named notify selected by `{ index, name, time }`. |
| `anim.remove_named_notify` | Remove exactly one sequence skeleton named notify selected by `{ index, name, time }`; missing targets are errors. |

## Boundaries

Use this domain for skeletal animation assets only. Do not use it for UMG animation,
Sequencer, Control Rig authoring, Niagara, material animation, Blueprint Timeline
components, runtime playback control, retargeting, IK, pose search, motion matching,
blendspace inspection, or motion/keyframe generation.

Only `add_named_notify`, `update_named_notify`, and `remove_named_notify` are available
for authoring in this slice. Do not call or invent object notify, notify state, curve,
montage section, socket, AnimBP authoring, blendspace, retargeting, runtime preview, or
animation `save_asset` commands.

Update/remove selectors match only zero-duration skeleton named notifies. Object
notifies and notify states are rejected before mutation.

## Response Discipline

Every successful inspection response includes `asset_path`, `asset_type`, `name`, and
`fingerprint`. Large arrays are returned as collection objects with `count`, `returned`,
`truncated`, and `items`.

Every successful named-notify mutation response includes `operation`, `selector`,
`changed`, `dirty_before`, `dirty_after`, `saved`, `saved_packages`, `before`, `after`,
and `current_fingerprint`. `save` defaults to `false`; use `dry_run=true` to preview
without mutation or dirtying the asset.
