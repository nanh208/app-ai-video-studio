import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Video,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { CaptionOverlay, WordCaption } from "./components/CaptionOverlay";
import { resolveAsset } from "./lib/resolveAsset";
import { StatCard } from "./components/StatCard";
import { ComparisonCard } from "./components/ComparisonCard";
import { CalloutBox } from "./components/CalloutBox";
import { HeroTitle } from "./components/HeroTitle";
import { TextCard } from "./components/TextCard";
import { BarChart } from "./components/charts/BarChart";
import { PieChart } from "./components/charts/PieChart";
import { BenchmarkCard, BenchmarkItem } from "./components/BenchmarkCard";
import { EconomicCard, EconomicMetric } from "./components/EconomicCard";
import { ParticleOverlay } from "./components/ParticleOverlay";

export interface NewsShot {
  id?: string;
  type:
    | "kenburns"
    | "image"
    | "video"
    | "stat_card"
    | "comparison"
    | "callout"
    | "hero_title"
    | "text_card"
    | "bar_chart"
    | "pie_chart"
    | "benchmark_card"
    | "economic_card";
  in_seconds: number;
  out_seconds: number;
  // Media props
  src?: string;
  scaleFrom?: number;
  scaleTo?: number;
  // Component props
  title?: string;
  subtitle?: string;
  stat?: string;
  text?: string;
  accentColor?: string;
  backgroundColor?: string;
  leftLabel?: string;
  rightLabel?: string;
  leftValue?: string;
  rightValue?: string;
  chartData?: any[];
  chartColors?: string[];
  callout_type?: "info" | "warning" | "tip" | "quote" | "success";
  benchmarkData?: {
    items?: BenchmarkItem[];
    sourceNote?: string;
  };
  economicData?: {
    metrics?: EconomicMetric[];
    footnote?: string;
  };
}

export interface NewsShortProps {
  [key: string]: unknown;
  headlineTag?: string;
  headlineTitle?: string;
  sourceText?: string;
  shots: NewsShot[];
  captions?: WordCaption[];
  audio?: {
    narration?: {
      src: string;
      volume?: number;
    };
    music?: {
      src: string;
      volume?: number;
      offsetSeconds?: number;
      fadeInSeconds?: number;
      fadeOutSeconds?: number;
      loop?: boolean;
    };
  };
  theme?: {
    primaryColor?: string;
    accentColor?: string;
    backgroundColor?: string;
    textColor?: string;
  };
}

// ---------------------------------------------------------------------------
// Ken Burns Animated Image (Slow push-in / Pan)
// ---------------------------------------------------------------------------
const KenBurnsShot: React.FC<{ shot: NewsShot; durationFrames: number }> = ({
  shot,
  durationFrames,
}) => {
  const frame = useCurrentFrame();
  const scale = interpolate(
    frame,
    [0, durationFrames],
    [shot.scaleFrom ?? 1.0, shot.scaleTo ?? 1.15],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const imgSrc = resolveAsset(shot.src || "");

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0A0F1D",
        overflow: "hidden",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {/* Blurred background layer */}
      {imgSrc && (
        <Img
          src={imgSrc}
          style={{
            position: "absolute",
            width: "120%",
            height: "120%",
            objectFit: "cover",
            filter: "blur(24px) brightness(0.35)",
            transform: "scale(1.2)",
          }}
        />
      )}

      {/* Main foreground image with push-in motion */}
      {imgSrc && (
        <div
          style={{
            width: "92%",
            height: "85%",
            borderRadius: 24,
            overflow: "hidden",
            boxShadow: "0 25px 60px rgba(0,0,0,0.7), 0 0 0 2px rgba(255,255,255,0.12)",
            transform: `scale(${scale})`,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            position: "relative",
            background: "rgba(15, 23, 42, 0.8)",
          }}
        >
          <Img
            src={imgSrc}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
            }}
          />
          {/* Subtle gradient scrim on bottom for text readability */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              background:
                "linear-gradient(180deg, rgba(15,23,42,0) 50%, rgba(15,23,42,0.85) 100%)",
            }}
          />
        </div>
      )}

      {/* Floating Stat Pill (top-right) if provided */}
      {shot.stat && (
        <div
          style={{
            position: "absolute",
            top: 48,
            right: 48,
            padding: "10px 24px",
            background: "linear-gradient(135deg, #FFE600 0%, #F59E0B 100%)",
            borderRadius: 30,
            color: "#0F172A",
            fontSize: 34,
            fontWeight: 900,
            boxShadow: "0 8px 30px rgba(255, 230, 0, 0.45)",
            zIndex: 10,
          }}
        >
          {shot.stat}
        </div>
      )}

      {/* Editorial frosted lower-third banner if title/subtitle/text provided */}
      {(shot.title || shot.subtitle || shot.text) && (
        <div
          style={{
            position: "absolute",
            bottom: 40,
            left: 48,
            right: 48,
            padding: "20px 28px",
            background: "rgba(15, 23, 42, 0.88)",
            backdropFilter: "blur(16px)",
            borderRadius: 20,
            border: "1px solid rgba(255,255,255,0.18)",
            color: "#FFF",
            boxShadow: "0 12px 36px rgba(0,0,0,0.6)",
            display: "flex",
            flexDirection: "column",
            gap: 6,
            zIndex: 10,
          }}
        >
          {shot.title && (
            <div style={{ fontSize: 32, fontWeight: 800, color: "#FFE600", textTransform: "uppercase" }}>
              {shot.title}
            </div>
          )}
          {(shot.subtitle || shot.text) && (
            <div style={{ fontSize: 26, fontWeight: 500, color: "#F8FAFC", lineHeight: 1.35 }}>
              {shot.subtitle || shot.text}
            </div>
          )}
        </div>
      )}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Video Shot (B-roll clip)
// ---------------------------------------------------------------------------
const VideoShot: React.FC<{ shot: NewsShot }> = ({ shot }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#0A0F1D", overflow: "hidden" }}>
      <Video
        src={resolveAsset(shot.src || "")}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          filter: "brightness(0.85)",
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(180deg, rgba(10,15,29,0.7) 0%, rgba(10,15,29,0) 25%, rgba(10,15,29,0) 75%, rgba(10,15,29,0.85) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Card Backdrop (Subtle visual texture behind text/stat cards)
// ---------------------------------------------------------------------------
const CardBackdrop: React.FC<{ src?: string; durationFrames: number }> = ({
  src,
  durationFrames,
}) => {
  const frame = useCurrentFrame();
  if (!src) return null;

  const scale = interpolate(
    frame,
    [0, durationFrames],
    [1.0, 1.14],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const isVideo = src.endsWith(".mp4") || src.endsWith(".webm");
  const resolved = resolveAsset(src);

  return (
    <AbsoluteFill style={{ overflow: "hidden", borderRadius: 24 }}>
      {isVideo ? (
        <Video
          src={resolved}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            filter: "brightness(0.28) saturate(1.2)",
          }}
        />
      ) : (
        <Img
          src={resolved}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            filter: "brightness(0.3) blur(2px)",
            transform: `scale(${scale})`,
          }}
        />
      )}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse at center, rgba(15,23,42,0.45) 0%, rgba(15,23,42,0.88) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Center Stage Shot Dispatcher
// ---------------------------------------------------------------------------
const ShotRenderer: React.FC<{ shot: NewsShot; durationFrames: number }> = ({
  shot,
  durationFrames,
}) => {
  const accent = shot.accentColor || "#FFE600";
  const bg = shot.backgroundColor || "#0F172A";

  switch (shot.type) {
    case "kenburns":
    case "image":
      return <KenBurnsShot shot={shot} durationFrames={durationFrames} />;

    case "video":
      return <VideoShot shot={shot} />;

    case "stat_card":
      return (
        <AbsoluteFill
          style={{
            backgroundColor: bg,
            borderRadius: 24,
            border: `2px solid rgba(255, 230, 0, 0.25)`,
            overflow: "hidden",
            boxShadow: `0 0 50px rgba(255, 230, 0, 0.15)`,
          }}
        >
          {shot.src && <CardBackdrop src={shot.src} durationFrames={durationFrames} />}
          <StatCard
            stat={shot.stat || "100%"}
            subtitle={shot.subtitle || shot.text}
            statFontSize={110}
            subtitleFontSize={36}
            accentColor={accent}
            color="#FFFFFF"
            backgroundColor="transparent"
          />
        </AbsoluteFill>
      );

    case "comparison":
      return (
        <AbsoluteFill
          style={{
            backgroundColor: bg,
            borderRadius: 24,
            padding: 30,
            overflow: "hidden",
            border: "1px solid rgba(255,255,255,0.1)",
          }}
        >
          {shot.src && <CardBackdrop src={shot.src} durationFrames={durationFrames} />}
          <ComparisonCard
            title={shot.title || "So sánh"}
            leftLabel={shot.leftLabel || "Trước"}
            rightLabel={shot.rightLabel || "Sau"}
            leftValue={shot.leftValue || ""}
            rightValue={shot.rightValue || ""}
            backgroundColor="transparent"
            cardBackgroundColor="rgba(255, 255, 255, 0.08)"
            textColor="#FFFFFF"
            leftColor="#FB7185"
            rightColor="#34D399"
            valueFontSize={36}
            labelFontSize={24}
          />
        </AbsoluteFill>
      );

    case "callout":
      return (
        <AbsoluteFill
          style={{
            backgroundColor: bg,
            borderRadius: 24,
            padding: 40,
            justifyContent: "center",
            overflow: "hidden",
            border: "1px solid rgba(56, 189, 248, 0.25)",
          }}
        >
          {shot.src && <CardBackdrop src={shot.src} durationFrames={durationFrames} />}
          <CalloutBox
            text={shot.text || ""}
            title={shot.title}
            type={shot.callout_type || "info"}
            borderColor={accent}
            backgroundColor="rgba(255, 255, 255, 0.06)"
            textColor="#FFFFFF"
            containerBackgroundColor="transparent"
          />
        </AbsoluteFill>
      );

    case "bar_chart":
      return (
        <AbsoluteFill
          style={{
            backgroundColor: bg,
            borderRadius: 24,
            padding: 30,
          }}
        >
          <BarChart
            title={shot.title || ""}
            data={shot.chartData || []}
            colors={shot.chartColors || ["#FFE600", "#38BDF8", "#34D399"]}
            backgroundColor="transparent"
            showValues
          />
        </AbsoluteFill>
      );

    case "pie_chart":
      return (
        <AbsoluteFill
          style={{
            backgroundColor: bg,
            borderRadius: 24,
            padding: 30,
          }}
        >
          <PieChart
            title={shot.title || ""}
            data={shot.chartData || []}
            colors={shot.chartColors || ["#FFE600", "#FB7185", "#38BDF8"]}
            donut
            backgroundColor="transparent"
          />
        </AbsoluteFill>
      );

    case "hero_title":
      return (
        <AbsoluteFill
          style={{
            backgroundColor: bg,
            borderRadius: 24,
            justifyContent: "center",
            alignItems: "center",
            padding: 40,
            overflow: "hidden",
            border: "1px solid rgba(255,255,255,0.1)",
          }}
        >
          {shot.src && <CardBackdrop src={shot.src} durationFrames={durationFrames} />}
          <HeroTitle
            title={shot.title || shot.text || ""}
            subtitle={shot.subtitle || ""}
          />
        </AbsoluteFill>
      );

    case "benchmark_card":
      return (
        <AbsoluteFill
          style={{
            backgroundColor: bg,
            borderRadius: 24,
            overflow: "hidden",
          }}
        >
          {shot.src && <CardBackdrop src={shot.src} durationFrames={durationFrames} />}
          <BenchmarkCard
            title={shot.title}
            subtitle={shot.subtitle}
            items={shot.benchmarkData?.items}
            sourceNote={shot.benchmarkData?.sourceNote}
          />
        </AbsoluteFill>
      );

    case "economic_card":
      return (
        <AbsoluteFill
          style={{
            backgroundColor: bg,
            borderRadius: 24,
            overflow: "hidden",
          }}
        >
          {shot.src && <CardBackdrop src={shot.src} durationFrames={durationFrames} />}
          <EconomicCard
            title={shot.title}
            subtitle={shot.subtitle}
            metrics={shot.economicData?.metrics}
            footnote={shot.economicData?.footnote}
          />
        </AbsoluteFill>
      );

    default:
      return (
        <AbsoluteFill
          style={{
            backgroundColor: bg,
            borderRadius: 24,
            justifyContent: "center",
            alignItems: "center",
            padding: 40,
          }}
        >
          <TextCard
            text={shot.text || ""}
            subtitle={shot.subtitle}
            fontSize={52}
            color="#FFFFFF"
            backgroundColor="transparent"
          />
        </AbsoluteFill>
      );
  }
};

// ---------------------------------------------------------------------------
// Animated Audio Waveform (Live commentary presence indicator)
// ---------------------------------------------------------------------------
const AudioWaveform: React.FC<{ frame: number; barCount?: number }> = ({
  frame,
  barCount = 18,
}) => {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 5,
        height: 40,
      }}
    >
      {Array.from({ length: barCount }).map((_, i) => {
        const height =
          12 +
          24 *
            Math.abs(
              Math.sin((frame * 0.15 + i * 0.45) % Math.PI)
            );
        return (
          <div
            key={i}
            style={{
              width: 5,
              height,
              borderRadius: 3,
              backgroundColor: i % 3 === 0 ? "#FFE600" : "#38BDF8",
              boxShadow: "0 0 8px rgba(255, 230, 0, 0.4)",
              transition: "height 0.05s ease",
            }}
          />
        );
      })}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Main NewsShort Composition
// ---------------------------------------------------------------------------
export const NewsShort: React.FC<NewsShortProps> = ({
  headlineTag = "🔥 TIN AI NÓNG",
  headlineTitle = "BƯỚC NGOẶT CÔNG NGHỆ MỚI",
  sourceText = "Nguồn: Tin Tổng Hợp",
  shots = [],
  captions = [],
  audio = {},
  theme = {},
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const primary = theme.primaryColor || "#0F172A";
  const accent = theme.accentColor || "#FFE600";

  return (
    <AbsoluteFill
      style={{
        backgroundColor: primary,
        fontFamily: "'Space Grotesk', Montserrat, Inter, system-ui, sans-serif",
        color: "#F8FAFC",
        overflow: "hidden",
      }}
    >
      {/* Background Gradient & Tech Grid */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(circle at 50% 15%, rgba(30, 58, 138, 0.45) 0%, rgba(15, 23, 42, 1) 75%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.035) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
          pointerEvents: "none",
        }}
      />

      {/* Cyber Aurora Glow Pulse */}
      <div
        style={{
          position: "absolute",
          top: "25%",
          left: "15%",
          width: "70%",
          height: "45%",
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(56, 189, 248, 0.14) 0%, rgba(139, 92, 246, 0.09) 50%, transparent 75%)",
          filter: "blur(60px)",
          pointerEvents: "none",
          transform: `scale(${1 + 0.12 * Math.sin(frame * 0.05)})`,
          opacity: 0.8 + 0.2 * Math.cos(frame * 0.04),
        }}
      />

      {/* Floating Sparkles / Fireflies in Background */}
      <ParticleOverlay type="sparkles" count={24} color="#38BDF8" intensity={0.4} />

      {/* TOP HEADER HUD (Always fixed at top) */}
      <div
        style={{
          position: "absolute",
          top: 60,
          left: 48,
          right: 48,
          zIndex: 50,
          display: "flex",
          flexDirection: "column",
          gap: 12,
        }}
      >
        {/* Category Pill Tag */}
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div
            style={{
              padding: "8px 20px",
              background: "linear-gradient(135deg, #FF4D4F 0%, #D9363E 100%)",
              borderRadius: 30,
              fontSize: 24,
              fontWeight: 800,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              boxShadow: "0 4px 16px rgba(255, 77, 79, 0.4)",
              color: "#FFF",
            }}
          >
            {headlineTag}
          </div>
          <div
            style={{
              height: 2,
              flex: 1,
              background:
                "linear-gradient(90deg, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0) 100%)",
            }}
          />
        </div>

        {/* 2-line Main Headline */}
        <div
          style={{
            fontSize: 46,
            fontWeight: 900,
            lineHeight: 1.25,
            letterSpacing: "-0.02em",
            textTransform: "uppercase",
            color: "#FFFFFF",
            textShadow: "0 4px 20px rgba(0, 0, 0, 0.8)",
          }}
        >
          {headlineTitle}
        </div>
      </div>

      {/* CENTER STAGE (Y: 270px to 1420px) — Switches seamlessly per shot */}
      <div
        style={{
          position: "absolute",
          top: 270,
          left: 48,
          right: 48,
          height: 1140,
          zIndex: 20,
        }}
      >
        {shots.map((shot, i) => {
          const fromFrame = Math.round(shot.in_seconds * fps);
          const durFrames = Math.max(
            1,
            Math.round((shot.out_seconds - shot.in_seconds) * fps)
          );

          return (
            <Sequence
              key={shot.id || `shot-${i}`}
              from={fromFrame}
              durationInFrames={durFrames}
            >
              <ShotRenderer shot={shot} durationFrames={durFrames} />
            </Sequence>
          );
        })}
      </div>

      {/* FOOTER BAR (Bottom: Live Waveform & Source Pill) */}
      <div
        style={{
          position: "absolute",
          bottom: 120,
          left: 48,
          right: 48,
          zIndex: 40,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        {/* Left: Waveform animation */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            padding: "8px 16px",
            background: "rgba(15, 23, 42, 0.75)",
            backdropFilter: "blur(12px)",
            borderRadius: 30,
            border: "1px solid rgba(255,255,255,0.12)",
          }}
        >
          <AudioWaveform frame={frame} barCount={12} />
          <span
            style={{
              fontSize: 20,
              fontWeight: 700,
              color: "#94A3B8",
              letterSpacing: "0.04em",
            }}
          >
            LIVE REPORT
          </span>
        </div>

        {/* Right: Source Pill */}
        <div
          style={{
            padding: "8px 18px",
            background: "rgba(0, 0, 0, 0.65)",
            borderRadius: 20,
            border: "1px solid rgba(255,255,255,0.15)",
            fontSize: 22,
            fontWeight: 600,
            color: "#CBD5E1",
          }}
        >
          {sourceText}
        </div>
      </div>

      {/* WORD-BY-WORD KARAOKE CAPTIONS (Safe zone: bottom 200px) */}
      {captions && captions.length > 0 && (
        <CaptionOverlay
          words={captions}
          wordsPerPage={3}
          fontSize={48}
          color="#FFFFFF"
          highlightColor={accent}
          backgroundColor="rgba(15, 23, 42, 0.88)"
          bottomOffset={200}
        />
      )}

      {/* AUDIO LAYER */}
      {audio?.narration?.src && (
        <Audio
          src={resolveAsset(audio.narration.src)}
          volume={audio.narration.volume ?? 1}
        />
      )}
      {audio?.music?.src && (
        <Audio
          src={resolveAsset(audio.music.src)}
          startFrom={Math.round((audio.music.offsetSeconds ?? 0) * fps)}
          loop={audio.music.loop ?? true}
          volume={(f) => {
            const baseVol = audio.music!.volume ?? 0.12;
            const fadeInDur = (audio.music!.fadeInSeconds ?? 2) * fps;
            const fadeOutDur = (audio.music!.fadeOutSeconds ?? 2) * fps;
            const fadeIn = interpolate(f, [0, fadeInDur], [0, baseVol], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });
            const fadeOut = interpolate(
              f,
              [durationInFrames - fadeOutDur, durationInFrames],
              [baseVol, 0],
              {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }
            );
            return Math.min(fadeIn, fadeOut);
          }}
        />
      )}
    </AbsoluteFill>
  );
};
