"""Smoke check for Studio v2 procedural audio catalog."""
from msf.audio.music import MUSIC_REGISTRY
from msf.audio.sfx import SFX_REGISTRY
import msf.audio.sfx_extra  # noqa: F401 — registers the extra local SFX pack
from msf.studio.sound_design import all_recipes


if __name__ == "__main__":
    missing = []
    for recipe in all_recipes():
        if recipe.music_bed not in MUSIC_REGISTRY:
            missing.append(f"music:{recipe.scene_name}:{recipe.music_bed}")
        for cue in recipe.cues:
            if cue.sfx_id not in SFX_REGISTRY:
                missing.append(f"sfx:{recipe.scene_name}:{cue.sfx_id}")
    if missing:
        raise SystemExit("Missing audio IDs: " + ", ".join(missing))
    print(f"music_beds={len(MUSIC_REGISTRY)}")
    print(f"sfx={len(SFX_REGISTRY)}")
    print(f"recipes={len(tuple(all_recipes()))}")
