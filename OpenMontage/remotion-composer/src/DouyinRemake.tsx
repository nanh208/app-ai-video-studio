import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Video,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { CaptionOverlay, WordCaption } from "./components/CaptionOverlay";
import { resolveAsset } from "./lib/resolveAsset";

export interface PunchText {
  id?: string;
  in_seconds: number;
  out_seconds: number;
  line1: string; // e.g. "VALI RỖNG SANG"
  line2?: string; // e.g. "3 VALI ĐẦY VỀ"
  color1?: string; // default "#FFFFFF"
  color2?: string; // default "#FFE600"
}

export interface StatPunch {
  id?: string;
  in_seconds: number;
  out_seconds: number;
  stat: string; // e.g. "22,9 TRIỆU"
  label?: string; // e.g. "LƯỢT XEM TIKTOK"
  statColor?: string; // default "#FFFFFF"
  labelColor?: string; // default "#FFE600"
}

export interface YellowBanner {
  id?: string;
  in_seconds: number;
  out_seconds: number;
  text: string; // e.g. "CƠN SỐT MUA SẮM QUỐC TẾ"
}

export interface VideoClipItem {
  id?: string;
  src: string;
  in_seconds: number;
  out_seconds: number;
  startAt?: number;
  layout?:
    | "fullscreen"
    | "letterbox_blur"
    | "news_mockup"
    | "split_top"
    | "split_bottom"
    | "pip";
  mediaType?: "video" | "image" | "news_mockup";
  source?: string; // e.g. "Nguồn: Tân Hoa Xã"
  newsDomain?: string; // e.g. "news.cn"
  newsHeadline?: string; // e.g. "Cơn sốt mua sắm China Haul bùng nổ..."
}

export interface DouyinRemakeProps {
  [key: string]: unknown;
  videoSrc?: string; // Background footage (single)
  videoClips?: VideoClipItem[]; // Multiple background clips (Multi-Reference B-Roll)
  muteOriginalVideo?: boolean;
  voiceSrc?: string; // Vietnamese Voiceover audio
  voiceVolume?: number;
  bgmSrc?: string; // Optional background music
  bgmVolume?: number;
  sourceText?: string; // Fallback source credit (e.g. "Nguồn: Douyin")
  punchTexts?: PunchText[];
  yellowBanners?: YellowBanner[];
  statPunches?: StatPunch[];
  captions?: WordCaption[];
}

// ---------------------------------------------------------------------------
// Big Punch Kinetic Typography (Chữ lớn đập vào mắt 2 tầng kiểu Douyin/TikTok)
// ---------------------------------------------------------------------------
const PunchTextItem: React.FC<{ item: PunchText; durationFrames: number }> = ({
  item,
  durationFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Snappy spring pop entrance
  const scale = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 140, mass: 0.8 },
    from: 0.78,
    to: 1.0,
  });

  // Fade out in last 5 frames
  const opacity = interpolate(
    frame,
    [durationFrames - 5, durationFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute",
        top: "46%",
        left: "4%",
        right: "4%",
        transform: `translateY(-50%) scale(${scale})`,
        opacity,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        zIndex: 45,
        pointerEvents: "none",
      }}
    >
      {/* Line 1: Big White Text with thick black stroke */}
      {item.line1 && (
        <div
          style={{
            fontFamily: "'Montserrat', Impact, 'Arial Black', sans-serif",
            fontSize: 82,
            fontWeight: 900,
            textTransform: "uppercase",
            letterSpacing: "0.02em",
            color: item.color1 || "#FFFFFF",
            WebkitTextStroke: "6px #000000",
            textShadow: "0 8px 24px rgba(0,0,0,0.95)",
            lineHeight: 1.1,
          }}
        >
          {item.line1}
        </div>
      )}

      {/* Line 2: Big Yellow Text with thick black stroke */}
      {item.line2 && (
        <div
          style={{
            fontFamily: "'Montserrat', Impact, 'Arial Black', sans-serif",
            fontSize: 66,
            fontWeight: 900,
            textTransform: "uppercase",
            letterSpacing: "0.02em",
            color: item.color2 || "#FFE600",
            WebkitTextStroke: "5px #000000",
            textShadow: "0 8px 24px rgba(0,0,0,0.95)",
            lineHeight: 1.15,
            marginTop: 8,
          }}
        >
          {item.line2}
        </div>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Giant Stat Center Punch (Cú đấm số liệu cực đại giữa màn hình)
// e.g. "22,9 TRIỆU"
// ---------------------------------------------------------------------------
const StatPunchItem: React.FC<{ item: StatPunch; durationFrames: number }> = ({
  item,
  durationFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 150, mass: 0.7 },
    from: 0.65,
    to: 1.0,
  });

  const opacity = interpolate(
    frame,
    [durationFrames - 5, durationFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute",
        top: "47%",
        left: "4%",
        right: "4%",
        transform: `translateY(-50%) scale(${scale})`,
        opacity,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        zIndex: 48,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          fontFamily: "'Montserrat', Impact, 'Arial Black', sans-serif",
          fontSize: 108,
          fontWeight: 900,
          color: item.statColor || "#FFFFFF",
          WebkitTextStroke: "7px #000000",
          textShadow: "0 10px 32px rgba(0,0,0,0.98)",
          lineHeight: 1.0,
          letterSpacing: "0.01em",
        }}
      >
        {item.stat}
      </div>

      {item.label && (
        <div
          style={{
            fontFamily: "'Montserrat', 'Inter', sans-serif",
            fontSize: 42,
            fontWeight: 900,
            textTransform: "uppercase",
            color: item.labelColor || "#FFE600",
            WebkitTextStroke: "3px #000000",
            textShadow: "0 6px 18px rgba(0,0,0,0.9)",
            letterSpacing: "0.04em",
            marginTop: 8,
          }}
        >
          {item.label}
        </div>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Yellow Highlight Banner (Thanh vàng chữ đen kiểu Douyin)
// ---------------------------------------------------------------------------
const YellowBannerItem: React.FC<{
  item: YellowBanner;
  durationFrames: number;
}> = ({ item, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    config: { damping: 15, stiffness: 150 },
    from: 0.85,
    to: 1.0,
  });

  const opacity = interpolate(
    frame,
    [durationFrames - 5, durationFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute",
        top: "56%",
        left: "8%",
        right: "8%",
        transform: `translateY(-50%) scale(${scale})`,
        opacity,
        display: "flex",
        justifyContent: "center",
        zIndex: 40,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          background: "#F5C518",
          color: "#000000",
          padding: "12px 32px",
          borderRadius: 8,
          fontFamily: "'Montserrat', 'Inter', sans-serif",
          fontSize: 44,
          fontWeight: 900,
          textTransform: "uppercase",
          letterSpacing: "0.02em",
          boxShadow: "0 10px 30px rgba(0,0,0,0.6)",
          textAlign: "center",
        }}
      >
        {item.text}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Single Media Clip Renderer (Image / Video / Letterbox Blur / News Mockup)
// ---------------------------------------------------------------------------
const MediaClipRenderer: React.FC<{
  clip: VideoClipItem;
  durationFrames: number;
  muteOriginalVideo: boolean;
}> = ({ clip, durationFrames, muteOriginalVideo }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const isImage =
    clip.mediaType === "image" ||
    /\.(jpe?g|png|webp|avif)$/i.test(clip.src);

  const resolved = resolveAsset(clip.src);
  const startFromFrame = Math.round((clip.startAt || 0) * fps);

  // Slow Ken Burns zoom for images
  const kenBurnsScale = interpolate(frame, [0, durationFrames], [1.0, 1.09], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // 1. News Article Mockup View (giống Tân Hoa Xã / Phượng Hoàng)
  if (clip.layout === "news_mockup" || clip.mediaType === "news_mockup") {
    return (
      <AbsoluteFill
        style={{
          backgroundColor: "#0B0F19",
          justifyContent: "center",
          alignItems: "center",
          overflow: "hidden",
        }}
      >
        {/* Blurred ambient background */}
        {isImage ? (
          <Img
            src={resolved}
            style={{
              position: "absolute",
              width: "120%",
              height: "120%",
              objectFit: "cover",
              filter: "blur(32px) brightness(0.28)",
              transform: "scale(1.2)",
            }}
          />
        ) : (
          <Video
            src={resolved}
            volume={0}
            style={{
              position: "absolute",
              width: "120%",
              height: "120%",
              objectFit: "cover",
              filter: "blur(32px) brightness(0.28)",
              transform: "scale(1.2)",
            }}
          />
        )}

        {/* Browser Mockup Card */}
        <div
          style={{
            width: "92%",
            height: "82%",
            borderRadius: 24,
            overflow: "hidden",
            backgroundColor: "#FFFFFF",
            boxShadow:
              "0 30px 80px rgba(0,0,0,0.85), 0 0 0 2px rgba(255,255,255,0.18)",
            display: "flex",
            flexDirection: "column",
            position: "relative",
          }}
        >
          {/* Browser Top Navigation Bar */}
          <div
            style={{
              height: 72,
              backgroundColor: "#F1F5F9",
              borderBottom: "1px solid #E2E8F0",
              display: "flex",
              alignItems: "center",
              padding: "0 24px",
              gap: 16,
            }}
          >
            {/* Window control dots */}
            <div style={{ display: "flex", gap: 8 }}>
              <div
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: "50%",
                  backgroundColor: "#EF4444",
                }}
              />
              <div
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: "50%",
                  backgroundColor: "#F59E0B",
                }}
              />
              <div
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: "50%",
                  backgroundColor: "#10B981",
                }}
              />
            </div>

            {/* Address bar pill */}
            <div
              style={{
                flex: 1,
                height: 42,
                backgroundColor: "#FFFFFF",
                borderRadius: 21,
                border: "1px solid #CBD5E1",
                display: "flex",
                alignItems: "center",
                padding: "0 18px",
                fontSize: 20,
                color: "#475569",
                fontFamily: "monospace",
                fontWeight: 600,
                gap: 8,
              }}
            >
              <span style={{ color: "#10B981" }}>🔒</span>
              <span>https://{clip.newsDomain || "news.cn"}</span>
            </div>
          </div>

          {/* Article Header & Main Content */}
          <div
            style={{
              flex: 1,
              position: "relative",
              overflow: "hidden",
              backgroundColor: "#0F172A",
            }}
          >
            {isImage ? (
              <Img
                src={resolved}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  transform: `scale(${kenBurnsScale})`,
                }}
              />
            ) : (
              <Video
                src={resolved}
                startFrom={startFromFrame}
                volume={muteOriginalVideo ? 0 : 1}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                }}
              />
            )}

            {/* Optional headline banner overlay */}
            {clip.newsHeadline && (
              <div
                style={{
                  position: "absolute",
                  bottom: 0,
                  left: 0,
                  right: 0,
                  padding: "24px 28px",
                  background:
                    "linear-gradient(180deg, rgba(15,23,42,0) 0%, rgba(15,23,42,0.92) 80%)",
                  color: "#FFFFFF",
                  fontSize: 32,
                  fontWeight: 800,
                  lineHeight: 1.25,
                  fontFamily: "'Montserrat', sans-serif",
                }}
              >
                {clip.newsHeadline}
              </div>
            )}
          </div>
        </div>
      </AbsoluteFill>
    );
  }

  // 2. Letterbox Blur View (cho clip ngang 16:9 / video YouTuber như Elliot Page)
  if (clip.layout === "letterbox_blur") {
    return (
      <AbsoluteFill
        style={{
          backgroundColor: "#000000",
          justifyContent: "center",
          alignItems: "center",
          overflow: "hidden",
        }}
      >
        {/* Blurred background filling 9:16 vertical canvas */}
        {isImage ? (
          <Img
            src={resolved}
            style={{
              position: "absolute",
              width: "120%",
              height: "120%",
              objectFit: "cover",
              filter: "blur(32px) brightness(0.35)",
              transform: "scale(1.2)",
            }}
          />
        ) : (
          <Video
            src={resolved}
            startFrom={startFromFrame}
            volume={0}
            style={{
              position: "absolute",
              width: "120%",
              height: "120%",
              objectFit: "cover",
              filter: "blur(32px) brightness(0.35)",
              transform: "scale(1.2)",
            }}
          />
        )}

        {/* Foreground 16:9 media */}
        <div
          style={{
            width: "94%",
            maxHeight: "68%",
            borderRadius: 20,
            overflow: "hidden",
            boxShadow:
              "0 25px 60px rgba(0,0,0,0.9), 0 0 0 2px rgba(255,255,255,0.15)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            position: "relative",
            zIndex: 10,
          }}
        >
          {isImage ? (
            <Img
              src={resolved}
              style={{
                width: "100%",
                height: "auto",
                objectFit: "contain",
                transform: `scale(${kenBurnsScale})`,
              }}
            />
          ) : (
            <Video
              src={resolved}
              startFrom={startFromFrame}
              volume={muteOriginalVideo ? 0 : 1}
              style={{
                width: "100%",
                height: "auto",
                objectFit: "contain",
              }}
            />
          )}
        </div>
      </AbsoluteFill>
    );
  }

  // 3. Fullscreen View (Default)
  let layoutStyle: React.CSSProperties = {
    width: "100%",
    height: "100%",
    objectFit: "cover",
  };

  if (clip.layout === "split_top") {
    layoutStyle = {
      position: "absolute",
      top: 0,
      left: 0,
      width: "100%",
      height: "50%",
      objectFit: "cover",
    };
  } else if (clip.layout === "split_bottom") {
    layoutStyle = {
      position: "absolute",
      bottom: 0,
      left: 0,
      width: "100%",
      height: "50%",
      objectFit: "cover",
    };
  } else if (clip.layout === "pip") {
    layoutStyle = {
      position: "absolute",
      top: 140,
      right: 40,
      width: 380,
      height: 540,
      objectFit: "cover",
      borderRadius: 20,
      border: "3px solid #FFE600",
      boxShadow: "0 20px 40px rgba(0,0,0,0.8)",
      zIndex: 35,
    };
  }

  return (
    <AbsoluteFill style={{ backgroundColor: "#000000", overflow: "hidden" }}>
      {isImage ? (
        <Img
          src={resolved}
          style={{
            ...layoutStyle,
            transform: `scale(${kenBurnsScale})`,
          }}
        />
      ) : (
        <Video
          src={resolved}
          startFrom={startFromFrame}
          volume={muteOriginalVideo ? 0 : 1}
          style={layoutStyle}
        />
      )}
      {/* Subtle top/bottom vignette gradient for contrast */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(180deg, rgba(0,0,0,0.45) 0%, rgba(0,0,0,0) 20%, rgba(0,0,0,0) 75%, rgba(0,0,0,0.7) 100%)",
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Main DouyinRemake Composition
// ---------------------------------------------------------------------------
export const DouyinRemake: React.FC<DouyinRemakeProps> = ({
  videoSrc,
  videoClips = [],
  muteOriginalVideo = true,
  voiceSrc,
  voiceVolume = 1.0,
  bgmSrc,
  bgmVolume = 0.1,
  sourceText = "Nguồn: Douyin",
  punchTexts = [],
  yellowBanners = [],
  statPunches = [],
  captions = [],
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentSec = frame / fps;

  // Active clip determines current dynamic source attribution pill
  const activeClip = videoClips.find(
    (c) => currentSec >= c.in_seconds && currentSec < c.out_seconds
  );
  const currentSource = activeClip?.source || sourceText;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000000", overflow: "hidden" }}>
      {/* LAYER 1: Background Media Footage (Multi-Clip Montage or Single Video) */}
      {videoClips && videoClips.length > 0 ? (
        videoClips.map((clip, i) => {
          const fromFrame = Math.round(clip.in_seconds * fps);
          const durFrames = Math.max(
            1,
            Math.round((clip.out_seconds - clip.in_seconds) * fps)
          );

          return (
            <Sequence
              key={clip.id || `clip-${i}`}
              from={fromFrame}
              durationInFrames={durFrames}
            >
              <MediaClipRenderer
                clip={clip}
                durationFrames={durFrames}
                muteOriginalVideo={muteOriginalVideo}
              />
            </Sequence>
          );
        })
      ) : videoSrc ? (
        <Video
          src={resolveAsset(videoSrc)}
          volume={muteOriginalVideo ? 0 : 1}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
        />
      ) : null}

      {/* LAYER 2: Big Punch Kinetic Texts (2-Tier White + Yellow) */}
      {punchTexts.map((pt, i) => {
        const fromFrame = Math.round(pt.in_seconds * fps);
        const durFrames = Math.max(
          1,
          Math.round((pt.out_seconds - pt.in_seconds) * fps)
        );
        return (
          <Sequence
            key={pt.id || `punch-${i}`}
            from={fromFrame}
            durationInFrames={durFrames}
          >
            <PunchTextItem item={pt} durationFrames={durFrames} />
          </Sequence>
        );
      })}

      {/* LAYER 3: Giant Stat Center Punches (e.g. 22,9 TRIỆU) */}
      {statPunches.map((sp, i) => {
        const fromFrame = Math.round(sp.in_seconds * fps);
        const durFrames = Math.max(
          1,
          Math.round((sp.out_seconds - sp.in_seconds) * fps)
        );
        return (
          <Sequence
            key={sp.id || `stat-${i}`}
            from={fromFrame}
            durationInFrames={durFrames}
          >
            <StatPunchItem item={sp} durationFrames={durFrames} />
          </Sequence>
        );
      })}

      {/* LAYER 4: Yellow Highlight Banners */}
      {yellowBanners.map((yb, i) => {
        const fromFrame = Math.round(yb.in_seconds * fps);
        const durFrames = Math.max(
          1,
          Math.round((yb.out_seconds - yb.in_seconds) * fps)
        );
        return (
          <Sequence
            key={yb.id || `yb-${i}`}
            from={fromFrame}
            durationInFrames={durFrames}
          >
            <YellowBannerItem item={yb} durationFrames={durFrames} />
          </Sequence>
        );
      })}

      {/* LAYER 5: Word-by-word Subtitles in Safe Zone (y: 200px from bottom) */}
      {captions && captions.length > 0 && (
        <div
          style={{
            position: "absolute",
            bottom: 200,
            left: 0,
            right: 0,
            zIndex: 50,
          }}
        >
          <CaptionOverlay
            words={captions}
            wordsPerPage={3}
            fontSize={52}
            color="#FFFFFF"
            highlightColor="#FFE600"
            backgroundColor="rgba(0, 0, 0, 0.45)"
          />
        </div>
      )}

      {/* LAYER 6: Dynamic Source Attribution Pill at Bottom Left (changes per clip) */}
      {currentSource && (
        <div
          style={{
            position: "absolute",
            bottom: 80,
            left: 40,
            zIndex: 60,
            padding: "8px 22px",
            background: "rgba(0, 0, 0, 0.8)",
            backdropFilter: "blur(12px)",
            borderRadius: 24,
            border: "1px solid rgba(255, 255, 255, 0.22)",
            color: "#FFFFFF",
            fontFamily: "'Space Grotesk', Montserrat, sans-serif",
            fontSize: 22,
            fontWeight: 700,
            letterSpacing: "0.02em",
            boxShadow: "0 8px 24px rgba(0,0,0,0.65)",
            transition: "all 0.3s ease",
          }}
        >
          {currentSource}
        </div>
      )}

      {/* LAYER 7: Audio Layer (Vietnamese Voiceover + Optional BGM) */}
      {voiceSrc && (
        <Audio src={resolveAsset(voiceSrc)} volume={voiceVolume} />
      )}
      {bgmSrc && (
        <Audio src={resolveAsset(bgmSrc)} volume={bgmVolume} loop />
      )}
    </AbsoluteFill>
  );
};
