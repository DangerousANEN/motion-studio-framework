# Catalog contract

Use `SceneManifest` as the runtime contract. Treat these fields as authoritative:

| Field | Agent action |
|---|---|
| `name` / `asset_id` / `version` | Pin the intended stable asset; never invent a name. |
| `status` / `capability_tier` | Filter visibility before selecting an asset. |
| `fields` | Populate only declared renderer props. |
| `data_driven` / `required_data_hints` | Require real structured data before selection. |
| `intent_tags` / `category` | Rank candidates for the creative brief. |
| `compatible_effect_families` | Limit effect selection to known families. |
| `recommended_audio_roles` | Select a semantic sound-design recipe, not a random file. |

Call `search_library` first, then `get_scene_manifest` for selected candidates. Do not embed static lists in prompts. Unknown fields, unknown effects and unknown style kits are hard validation errors because the renderer may otherwise fall back silently.
