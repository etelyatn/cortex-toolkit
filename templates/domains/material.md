# Material Domain Context

> Fill in the sections below. Delete the HTML comment examples as you go.
> Agents read this file before every task.

## Naming Conventions

<!-- Material naming rules for this project.
     WHY: The agent uses these to create correctly-named assets and avoid
          guessing prefixes (e.g., M_Rock vs. M_ENV_Rock vs. MAT_Rock).
     Example:
     - Master materials: M_{Category}_{Name}  (e.g., M_ENV_YourMaterial)
     - Material instances: MI_{Category}_{Name}  (e.g., MI_ENV_YourMaterial_Variant)
     - Material functions: MF_{Name}  (e.g., MF_YourFunction)
     - Textures: T_{Name}_{Suffix}  (e.g., T_YourMaterial_D for diffuse)
     - Category separators: underscore between prefix, category, and name
-->

## Instance Hierarchy

<!-- Which materials are masters and what instances inherit from them.
     WHY: The agent needs to know master materials before creating instances.
          Without this it may create orphan instances or use the wrong parent,
          breaking parameter inheritance and causing unexpected shader permutations.
     Example:
     - M_YourMaster_Opaque — master for all opaque environment surfaces
       - MI_YourMaster_Rock — rock variant
       - MI_YourMaster_Dirt — dirt variant
     - M_YourMaster_Foliage — master for all two-sided foliage
       - MI_YourMaster_Grass — grass variant
-->

## Parameter Collections (MPCs)

<!-- Global Material Parameter Collections used across materials.
     WHY: The agent needs to avoid duplicating MPCs and must know which
          collection to reference when wiring global parameters into a material.
     Example:
     - MPC_YourGlobal  (Content/Materials/MPCs/MPC_YourGlobal)
       - WindStrength (scalar) — drives foliage sway amplitude
       - TimeOfDay (scalar) — 0..1 fed from game code each tick
     - MPC_YourPostProcess  (Content/Materials/MPCs/MPC_YourPostProcess)
       - VignetteIntensity (scalar)
-->

## Texture Conventions

<!-- Folder layout, naming suffixes, and channel-packing rules.
     WHY: The agent needs to search in the right folders and interpret packed
          channels correctly when reading or writing material expressions.
     Example:
     - Textures live in Content/Textures/{Category}/
     - Suffix conventions:
       - _D  — diffuse / albedo (sRGB)
       - _N  — normal map (linear)
       - _ORM — occlusion (R), roughness (G), metallic (B) packed
       - _E  — emissive mask (linear)
     - Example: T_YourMaterial_ORM packs AO/Roughness/Metallic into one texture
-->

## Key Materials

<!-- Critical shared materials that many assets reference.
     WHY: The agent checks referencers before modifying a shared material to
          avoid unintended visual regressions across the project.
     Example:
     - M_YourMaster_Opaque  (Content/Materials/Masters/M_YourMaster_Opaque)
       Used by: all environment static meshes; modify only with art lead approval
     - M_YourDecal_Damage  (Content/Materials/Decals/M_YourDecal_Damage)
       Used by: damage decal system; parameter changes affect all decal actors
-->
