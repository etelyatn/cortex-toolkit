# Animation Domain Context

<!-- Skeletal animation asset inspection and capability-gated Phase B/B2/C authoring conventions for CortexAnimation -->

## What CortexAnimation Does

`CortexAnimation` exposes the `anim` MCP domain for Unreal skeletal animation assets.
It can inspect `UAnimSequence`, `UAnimMontage`, `USkeleton`, and `UAnimBlueprint`
metadata, and can author guarded sequence skeleton named notifies, editable float curves,
montage sections, skeleton sockets, object notifies, and notify states. Authoring families are available only when live
capabilities advertise every command in the family.

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
| `anim.add_curve` | Add one editable float curve to a sequence. |
| `anim.set_curve_keys` | Replace one float curve's finite, strictly increasing, unique keys (maximum 500). |
| `anim.remove_curve` | Remove one editable float curve selected by `curve_name`. |
| `anim.add_montage_section` | Add a unique montage section with `start_time` and optional `next_section`. |
| `anim.update_montage_section` | Update one montage section selected by `{ index, name, start_time }`. |
| `anim.remove_montage_section` | Remove one montage section selected by `{ index, name, start_time }`. |
| `anim.add_socket` | Add one socket to a skeleton after validating `bone_name`. |
| `anim.set_socket_transform` | Update a skeleton socket selected by `{ index, socket_name, bone_name }`. |
| `anim.remove_socket` | Remove one skeleton socket selected by `{ index, socket_name, bone_name }`. |
| `anim.add_notify` | Add one visible, placeable object notify to a sequence. |
| `anim.update_notify` | Move one object notify selected by `{ index, class_path, time }`. |
| `anim.remove_notify` | Remove one object notify selected by `{ index, class_path, time }`. |
| `anim.add_notify_state` | Add one visible, placeable notify state with start time and duration. |
| `anim.update_notify_state` | Move/resize one state selected by `{ index, class_path, time, duration }`. |
| `anim.remove_notify_state` | Remove one state selected by `{ index, class_path, time, duration }`. |

## Boundaries

Use this domain for skeletal animation assets only. Do not use it for UMG animation,
Sequencer, Control Rig authoring, Niagara, material animation, Blueprint Timeline
components, runtime playback control, retargeting, IK, pose search, motion matching,
blendspace inspection, or motion/keyframe generation.

Use a family only when live capabilities advertise every command in that family. Named
notifies, float curves, object notifies, and notify states apply to `UAnimSequence`; montage sections apply to
`UAnimMontage`; sockets mutate only `USkeleton::Sockets`. Do not call or invent later-stage
AnimBP authoring, blendspace, retargeting, runtime preview, Sequencer, or Control Rig commands.
There is no `anim.save_asset`; use a mutation's `save=true` option, or `core.save_asset`
where appropriate.

Named-notify update/remove selectors match only zero-duration skeleton named notifies.
Object-notify selectors use `{ index, class_path, time }`; state selectors additionally
include `duration`. Montage and socket update/remove selectors must use their full canonical selector objects.

## Response Discipline

Every successful inspection response includes `asset_path`, `asset_type`, `name`, and
`fingerprint`. Large arrays are returned as collection objects with `count`, `returned`,
`truncated`, and `items`.

Every successful mutation response includes `operation`, `selector`,
`changed`, `dirty_before`, `dirty_after`, `saved`, `saved_packages`, `before`, `after`,
and `current_fingerprint`. `save` defaults to `false`; use `dry_run=true` to preview
without mutation or dirtying the asset.
