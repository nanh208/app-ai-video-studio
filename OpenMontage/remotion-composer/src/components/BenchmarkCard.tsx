import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export interface BenchmarkItem {
  category: string;
  unit?: string;
  modelA: {
    name: string;
    score: string;
    value: number; // 0 - 100 for percentage bar
    color?: string;
    isWinner?: boolean;
  };
  modelB: {
    name: string;
    score: string;
    value: number;
    color?: string;
    isWinner?: boolean;
  };
}

export interface BenchmarkCardProps {
  title?: string;
  subtitle?: string;
  items?: BenchmarkItem[];
  sourceNote?: string;
}

export const BenchmarkCard: React.FC<BenchmarkCardProps> = ({
  title = "BẢNG ĐIỂM ĐỐI ĐẦU TRỰC DIỆN",
  subtitle = "THỬ NGHIỆM CHUẨN TOÁN HỌC & TƯ DUY LOGIC",
  items = [
    {
      category: "TOÁN OLYMPIC AIME 2024",
      unit: "Chính xác (%)",
      modelA: {
        name: "DeepSeek R1",
        score: "79.8%",
        value: 79.8,
        color: "#10B981",
        isWinner: true,
      },
      modelB: {
        name: "OpenAI o1",
        score: "79.2%",
        value: 79.2,
        color: "#FB7185",
      },
    },
    {
      category: "TOÁN CHUYÊN SÂU MATH-500",
      unit: "Chính xác (%)",
      modelA: {
        name: "DeepSeek R1",
        score: "97.3%",
        value: 97.3,
        color: "#10B981",
        isWinner: true,
      },
      modelB: {
        name: "OpenAI o1",
        score: "96.4%",
        value: 96.4,
        color: "#FB7185",
      },
    },
    {
      category: "LẬP TRÌNH THI ĐẤU CODEFORCES",
      unit: "Percentile (%)",
      modelA: {
        name: "DeepSeek R1",
        score: "96.3%",
        value: 96.3,
        color: "#38BDF8",
        isWinner: true,
      },
      modelB: {
        name: "OpenAI o1",
        score: "96.6%",
        value: 96.6,
        color: "#A78BFA",
      },
    },
  ],
  sourceNote = "Kiểm chứng độc lập: Stanford AI Lab & Technical Report",
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
          "linear-gradient(180deg, rgba(15, 23, 42, 0.95) 0%, rgba(10, 15, 29, 0.98) 100%)",
        borderRadius: 24,
        border: "1px solid rgba(56, 189, 248, 0.35)",
        boxShadow:
          "0 20px 50px rgba(0, 0, 0, 0.7), 0 0 40px rgba(56, 189, 248, 0.15)",
        fontFamily: "'Space Grotesk', Montserrat, Inter, system-ui, sans-serif",
        color: "#FFFFFF",
      }}
    >
      {/* Header Badge & Title */}
      <div
        style={{
          marginBottom: 28,
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
            background: "linear-gradient(135deg, #0284C7 0%, #0369A1 100%)",
            borderRadius: 20,
            fontSize: 20,
            fontWeight: 800,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            color: "#E0F2FE",
            marginBottom: 10,
            boxShadow: "0 4px 14px rgba(2, 132, 199, 0.4)",
          }}
        >
          <span>⚡ BENCHMARK CHÍNH THỨC</span>
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

      {/* Benchmark Metric Rows */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 22,
          flex: 1,
          justifyContent: "center",
        }}
      >
        {items.map((item, idx) => {
          const rowDelay = 8 + idx * 8;
          const rowSpring = spring({
            frame: frame - rowDelay,
            fps,
            config: { damping: 16, stiffness: 100 },
          });

          // Model A bar spring
          const barASpring = spring({
            frame: frame - rowDelay - 4,
            fps,
            config: { damping: 14, stiffness: 80 },
          });
          const widthA = interpolate(
            barASpring,
            [0, 1],
            [0, Math.min(100, Math.max(10, item.modelA.value))]
          );

          // Model B bar spring
          const barBSpring = spring({
            frame: frame - rowDelay - 8,
            fps,
            config: { damping: 14, stiffness: 80 },
          });
          const widthB = interpolate(
            barBSpring,
            [0, 1],
            [0, Math.min(100, Math.max(10, item.modelB.value))]
          );

          return (
            <div
              key={idx}
              style={{
                background: "rgba(255, 255, 255, 0.04)",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                borderRadius: 18,
                padding: "16px 20px",
                opacity: rowSpring,
                transform: `translateX(${interpolate(rowSpring, [0, 1], [-20, 0])}px)`,
              }}
            >
              {/* Category Name & Winner Pill */}
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
                    fontSize: 22,
                    fontWeight: 800,
                    color: "#F1F5F9",
                    letterSpacing: "0.02em",
                  }}
                >
                  {item.category}
                </span>
                {item.modelA.isWinner && (
                  <span
                    style={{
                      padding: "4px 10px",
                      background: "rgba(16, 185, 129, 0.2)",
                      border: "1px solid #10B981",
                      borderRadius: 12,
                      fontSize: 18,
                      fontWeight: 800,
                      color: "#34D399",
                      boxShadow: "0 0 12px rgba(16, 185, 129, 0.3)",
                    }}
                  >
                    🏆 R1 THẮNG
                  </span>
                )}
              </div>

              {/* Bar 1: DeepSeek R1 */}
              <div style={{ marginBottom: 10 }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: 20,
                    fontWeight: 700,
                    marginBottom: 5,
                    color: "#E2E8F0",
                  }}
                >
                  <span style={{ color: item.modelA.color || "#10B981" }}>
                    ● {item.modelA.name}
                  </span>
                  <span
                    style={{
                      fontSize: 22,
                      fontWeight: 900,
                      color: item.modelA.color || "#10B981",
                    }}
                  >
                    {item.modelA.score}
                  </span>
                </div>
                <div
                  style={{
                    height: 14,
                    width: "100%",
                    background: "rgba(255, 255, 255, 0.08)",
                    borderRadius: 7,
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      width: `${widthA}%`,
                      background: `linear-gradient(90deg, #059669 0%, ${item.modelA.color || "#10B981"} 100%)`,
                      borderRadius: 7,
                      boxShadow: `0 0 14px ${item.modelA.color || "#10B981"}`,
                    }}
                  />
                </div>
              </div>

              {/* Bar 2: OpenAI o1 */}
              <div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: 19,
                    fontWeight: 600,
                    marginBottom: 5,
                    color: "#94A3B8",
                  }}
                >
                  <span>● {item.modelB.name}</span>
                  <span
                    style={{
                      fontSize: 20,
                      fontWeight: 800,
                      color: item.modelB.color || "#FB7185",
                    }}
                  >
                    {item.modelB.score}
                  </span>
                </div>
                <div
                  style={{
                    height: 12,
                    width: "100%",
                    background: "rgba(255, 255, 255, 0.08)",
                    borderRadius: 6,
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      width: `${widthB}%`,
                      background: `linear-gradient(90deg, #BE123C 0%, ${item.modelB.color || "#FB7185"} 100%)`,
                      borderRadius: 6,
                    }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footnote Source Note */}
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
        <span style={{ color: "#38BDF8" }}>✓</span>
        <span>{sourceNote}</span>
      </div>
    </AbsoluteFill>
  );
};
