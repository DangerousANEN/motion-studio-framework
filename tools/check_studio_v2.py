"""Small repeatable smoke check for the Studio v2 application layer."""
from copy import deepcopy

from msf.panel.demo_props import DEMO_PROPS, TEXT_ONLY
from msf.spec import FPS, HEIGHT, WIDTH, validate_spec
from msf.studio.catalog import all_scenes
from msf.studio.storyboard import StoryboardValidator


EXPECTED_SCENE_COUNT = 117


if __name__ == "__main__":
    scenes = all_scenes()
    names = {scene.name for scene in scenes}
    if len(scenes) != EXPECTED_SCENE_COUNT:
        raise RuntimeError(f"expected {EXPECTED_SCENE_COUNT} scenes, found {len(scenes)}")

    for scene in scenes:
        props = deepcopy(DEMO_PROPS.get(scene.name, TEXT_ONLY))
        payload = {
            "id": f"demo-{scene.name}",
            "durationInFrames": 720,
            "preset": scene.name,
            **props,
        }
        validate_spec({"fps": FPS, "width": WIDTH, "height": HEIGHT, "scenes": [payload]})

    print(f"scenes={len(scenes)} demo_fixtures={len(scenes)}")
    print(f"validator={StoryboardValidator.__name__}")
