'use client';

import { useEffect, useRef } from 'react';
import { useReducedMotion } from 'framer-motion';
import type Hls from 'hls.js';

const source = 'https://stream.mux.com/8wrHPCX2dC3msyYU9ObwqNdm00u3ViXvOSHUMRYSEe5Q.m3u8';

export function SignInVideoBackground() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    const video = videoRef.current;
    if (!video || reducedMotion) return;
    let disposed = false;
    let player: Hls | undefined;
    video.muted = true;
    const play = () => { if (!disposed) void video.play().catch(() => {}); };
    video.addEventListener('canplay', play);

    void import('hls.js').then(({ default: HlsPlayer }) => {
      if (disposed) return;
      if (HlsPlayer.isSupported()) {
        player = new HlsPlayer({ capLevelToPlayerSize: true });
        player.loadSource(source);
        player.attachMedia(video);
        player.on(HlsPlayer.Events.ERROR, (_, data) => {
          if (data.fatal) { player?.destroy(); player = undefined; }
        });
      } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = source;
      }
    }).catch(() => {});

    return () => {
      disposed = true;
      video.removeEventListener('canplay', play);
      player?.destroy();
      video.pause();
      video.removeAttribute('src');
      video.load();
    };
  }, [reducedMotion]);

  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0 z-0 bg-black">
      <video ref={videoRef} autoPlay={!reducedMotion} loop muted playsInline tabIndex={-1}
        className="absolute inset-0 h-full w-full object-cover" />
      <div className="absolute inset-0 bg-black/25" />
      <div className="absolute left-0 right-0 top-0 h-[200px]"
        style={{ background: 'linear-gradient(to bottom, black, transparent)' }} />
      <div className="absolute bottom-0 left-0 right-0 h-[200px]"
        style={{ background: 'linear-gradient(to top, black, transparent)' }} />
    </div>
  );
}
