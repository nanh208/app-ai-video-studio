import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export interface EconomicMetric {
  title: string;
  legacyLabel: string;
  legacyValue: string;
  newLabel: string;
  newValue: string;
  badgeText: string;
  badgeColor?: string;
}

export interface EconomicCardProps {
  title?: string;
  subtitle?: string;
  metrics?: EconomicMetric[];
  footnote?: string;
}

export const EconomicCard: React.FC<EconomicCardProps> = ({
  title = "BÀI TOÁN KINH TẾ ĐẢO LỘN",
  subtitle = "SỰ KHÁC BIỆT GÂY CHẤN ĐỘNG THUNG LŨNG SILICON",
  metrics = [
    {
      title: "CHI PHÍ HUẤN LUYỆN (TRAINING BUDGET)",
      legacyLabel: "OpenAI & Big Tech",
      legacyValue: "$100M+ (2.500 TỶ)",
      newLabel: "DeepSeek R1",
      newValue: "$6M (~150 TỶ)",
      badgeText: "TIẾT KIỆM 95%",
      badgeColor: "#F59E0B",
    },
    {
      title: "GIÁ THÀNH API (1 TRIỆU TOKEN)",
      legacyLabel: "OpenAI o1 Reasoning",
      legacyValue: "$15.00",
      newLabel: "DeepSeek R1",
      newValue: "$0.55",
      badgeText: "RẺ HƠN 27 LẦN",
      badgeColor: "#10B981",
    },
    {
      title: "QUY MÔ CỤM GPU HUẤN LUYỆN",
      legacyLabel: "Cụm Siêu Máy Tính H100",
      legacyValue: "16.000+ Chip",
      newLabel: "Cụm Thuê H800 Tối Ưu",
      newValue: "2.048 Chip",
      badgeText: "ĐỘT PHÁ THUẬT TOÁN",
      badgeColor: "#38BDF8",
    },
  ],
  footnote = "Số liệu công bố chính thức · Financial Times & Technical Report",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({
    frame,
    fps,
    config: { damping: 18, stiffness: 120 },
  });

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "stretch",
        padding: "36px 44px",
        background:
          "linear-gradient(180deg, rgba(15, 23, 42, 0.96) 0%, rgba(10, 15, 29, 0.98) 100%)",
        borderRadius: 24,
        border: "1px solid rgba(245, 158, 11, 0.35)",
        boxShadow:
          "0 20px 50px rgba(0, 0, 0, 0.7), 0 0 40px rgba(245, 158, 11, 0.15)",
        fontFamily: "'Space Grotesk', Montserrat, Inter, system-ui, sans-serif",
        color: "#FFFFFF",
      }}
    >
      {/* Header Badge & Title */}
      <div
        style={{
          marginBottom: 24,
          opacity: titleSpring,
          transform: `translateY(${interpolate(titleSpring, [0, 1], [-15, 0])}px)`,
        }}
      >
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            padding: "6px 16px",
            background: "linear-gradient(135deg, #D97706 0%, #B45309 100%)",
            borderRadius: 20,
            fontSize: 20,
            fontWeight: 800,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            color: "#FEF3C7",
            marginBottom: 10,
            boxShadow: "0 4px 14px rgba(217, 119, 6, 0.4)",
          }}
        >
          <span>💰 CÚ SỐC CHI PHÍ</span>
        </div>
        <div
          style={{
            fontSize: 38,
            fontWeight: 900,
            letterSpacing: "-0.02em",
            lineHeight: 1.2,
            color: "#FFFFFF",
            textTransform: "uppercase",
          }}
        >
          {title}
        </div>
        <div
          style={{
            fontSize: 22,
            fontWeight: 600,
            color: "#94A3B8",
            marginTop: 4,
          }}
        >
          {subtitle}
        </div>
      </div>

      {/* Metric Cards */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 20,
          flex: 1,
          justifyContent: "center",
        }}
      >
        {metrics.map((m, idx) => {
          const delay = 8 + idx * 8;
          const cardSpring = spring({
            frame: frame - delay,
            fps,
            config: { damping: 16, stiffness: 100 },
          });

          return (
            <div
              key={idx}
              style={{
                background: "rgba(255, 255, 255, 0.04)",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                borderRadius: 18,
                padding: "16px 20px",
                opacity: cardSpring,
                transform: `translateX(${interpolate(cardSpring, [0, 1], [20, 0])}px)`,
              }}
            >
              {/* Row Header & Badge */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: 12,
                }}
              >
                <span
                  style={{
                    fontSize: 21,
                    fontWeight: 800,
                    color: "#F1F5F9",
                    letterSpacing: "0.02em",
                  }}
                >
                  {m.title}
                </span>
                <span
                  style={{
                    padding: "4px 12px",
                    background: `${m.badgeColor || "#10B981"}22`,
                    border: `1px solid ${m.badgeColor || "#10B981"}`,
                    borderRadius: 12,
                    fontSize: 18,
                    fontWeight: 900,
                    color: m.badgeColor || "#10B981",
                    boxShadow: `0 0 14px ${m.badgeColor || "#10B981"}44`,
                  }}
                >
                  {m.badgeText}
                </span>
              </div>

              {/* Two Column Values */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 14,
                }}
              >
                {/* Legacy / Competitor */}
                <div
                  style={{
                    background: "rgba(0, 0, 0, 0.3)",
                    padding: "10px 14px",
                    borderRadius: 12,
                    border: "1px solid rgba(244, 63, 94, 0.2)",
                  }}
                >
                  <div
                    style={{
                      fontSize: 18,
                      fontWeight: 600,
                      color: "#94A3B8",
                      marginBottom: 4,
                    }}
                  >
                    {m.legacyLabel}
                  </div>
                  <div
                    style={{
                      fontSize: 26,
                      fontWeight: 900,
                      color: "#FB7185",
                    }}
                  >
                    {m.legacyValue}
                  </div>
                </div>

                {/* DeepSeek Breakthrough */}
                <div
                  style={{
                    background: "rgba(0, 0, 0, 0.3)",
                    padding: "10px 14px",
                    borderRadius: 12,
                    border: "1px solid rgba(16, 185, 129, 0.3)",
                  }}
                >
                  <div
                    style={{
                      fontSize: 18,
                      fontWeight: 600,
                      color: "#94A3B8",
                      marginBottom: 4,
                    }}
                  >
                    {m.newLabel}
                  </div>
                  <div
                    style={{
                      fontSize: 26,
                      fontWeight: 900,
                      color: "#34D399",
                    }}
                  >
                    {m.newValue}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footnote */}
      <div
        style={{
          marginTop: 20,
          paddingTop: 12,
          borderTop: "1px solid rgba(255, 255, 255, 0.1)",
          display: "flex",
          alignItems: "center",
          gap: 10,
          fontSize: 18,
          fontWeight: 600,
          color: "#94A3B8",
        }}
      >
        <span style={{ color: "#F59E0B" }}>⚡</span>
        <span>{footnote}</span>
      </div>
    </AbsoluteFill>
  );
};
