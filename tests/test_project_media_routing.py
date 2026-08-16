from msf.graph.video_graph import _apply_project_media


def test_project_media_routes_by_typed_role_without_storage_path() -> None:
    state = {
        "project_media": [
            {
                "asset_id": "media_" + "a" * 32,
                "role": "screen_recording",
                "kind": "video",
                "caption": "Показываем настройку в приложении",
                "src": "studio-resources/run_" + "b" * 32 + "/recording.webm",
            },
            {
                "asset_id": "media_" + "c" * 32,
                "role": "hero_image",
                "kind": "image",
                "caption": "Официальный скриншот продукта",
                "src": "studio-resources/run_" + "b" * 32 + "/hero.png",
            },
        ]
    }
    scenes = [{"text": "Цепляющий hook"}, {"text": "Показываем шаг"}, {"text": "Проверяем результат"}]

    routed = _apply_project_media(scenes, state)

    assert routed[0]["text"] == "Цепляющий hook"  # hook remains text-first
    assert routed[1]["preset"] == "ScreenGuide"
    assert routed[1]["src"].startswith("studio-resources/run_")
    assert routed[2]["preset"] == "ImageSpotlight"
    assert routed[2]["images"] == [routed[2]["src"]]
    assert [row["role"] for row in state["media_assignments"]] == ["screen_recording", "hero_image"]
    assert all("output" not in row["src"] for row in routed[1:])


def test_project_media_leaves_nonvisual_assets_out_of_renderer_scene_inputs() -> None:
    state = {
        "project_media": [{
            "asset_id": "media_" + "d" * 32,
            "role": "reference_audio",
            "kind": "audio",
            "caption": "Голосовой референс",
            "src": "studio-resources/run_" + "e" * 32 + "/voice.wav",
        }]
    }
    scenes = [{"text": "Нарратив"}]
    assert _apply_project_media(scenes, state) == scenes
    assert state["media_assignments"] == []
