# Texture Resource UI QA — 2026-08-16

Открыта актуальная страница `/studio?textures=1#builder`. В Universal 3D Graph появился selector `builder3dTextureResource`, содержащий загруженный `scene_signal_launch_hero.png · supporting_image`.

Через UI выбран image resource и нажата кнопка «Применить к 3D node». Studio показала сообщение `Resource media_f8464c4d1de44f05aca12f2c7c3e0954 добавлен в graph. Теперь запустите 3D still preview.`, а JSON textarea был переформатирован и получил typed `resourceId`.

UI layout проверен по viewport: selector, apply action и preview actions находятся в отдельном вертикальном блоке без наложения controls. Server/API demo также подтвердил реальный still PNG и MP4 motion с пользовательской картинкой на plane.

После заполнения `TextureSignalGallery` и запуска `3D still preview` UI показал `3D still отрендерен (2 nodes).` В preview pane появился PNG `/preview/scenes/f9657b2bd51a.png`; screenshot подтверждает, что пользовательская картинка видна на 3D geometry вместе с orbit/grid scene. Это завершает UI end-to-end проверку: Resources → resourceId → graph mutation → API resolution → Remotion texture render.
