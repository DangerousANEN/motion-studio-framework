import React from 'react';
import { Audio, Sequence, Series, staticFile } from 'remotion';
import { VideoSpec } from '../VideoSpec.schema';
import { SceneDispatcher } from './SceneDispatcher';

export const MainComposition: React.FC<VideoSpec> = ({ scenes, audioUrl }) => {
  return (
    <div style={{ flex: 1, backgroundColor: '#0E0F11', display: 'flex' }}>
      {audioUrl && (
        <Audio src={audioUrl.startsWith('http') ? audioUrl : staticFile(audioUrl)} />
      )}
      <Series>
        {scenes.map((scene) => (
          <Series.Sequence
            key={scene.id}
            durationInFrames={scene.durationInFrames}
          >
            {scene.audioUrl && (
              <Audio
                src={
                  scene.audioUrl.startsWith('http')
                    ? scene.audioUrl
                    : staticFile(scene.audioUrl)
                }
              />
            )}
            <SceneDispatcher {...scene} />
          </Series.Sequence>
        ))}
      </Series>
    </div>
  );
};
