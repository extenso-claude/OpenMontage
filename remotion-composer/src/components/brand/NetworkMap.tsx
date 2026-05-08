/**
 * NetworkMap — node-edge relational diagram.
 *
 * Used for "who knew whom" diagrams in MM (Rothschild network, Medici clients,
 * Pentagon-defense-contractor links) and philosophical schools / lineages
 * in Huxley (Socrates → Plato → Aristotle student trees).
 *
 * Nodes get explicit { x, y } in 0–1000 normalized space (similar to map base).
 * Edges connect node ids and reveal sequentially.
 *
 * @version 0.1.0
 */
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BrandTheme, resolveTheme } from "./theme";

export interface NetworkNode {
  id: string;
  label: string;
  /** x in 0–1000 normalized space. */
  x: number;
  /** y in 0–600 normalized space. */
  y: number;
  /** Optional subtitle/role. */
  role?: string;
  /** Optional portrait image. */
  portraitSrc?: string;
  /** Center node — gets larger size and earlier reveal. */
  isCenter?: boolean;
  /** When (seconds from scene start) this node appears. */
  revealAtSeconds?: number;
}

export interface NetworkEdge {
  fromId: string;
  toId: string;
  /** Edge type — affects color and dash style. */
  type?: "ally" | "rival" | "mentor" | "transaction" | "neutral";
  /** Optional label on the edge (e.g. "1815 — bond market"). */
  label?: string;
  /** When (seconds) the edge animates in. Default = max of source/target reveal + 0.5s. */
  revealAtSeconds?: number;
}

export interface NetworkMapProps {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  /** Optional title above the map. */
  title?: string;
  durationFrames?: number;
  theme?: Partial<BrandTheme>;
}

const EDGE_COLORS: Record<NonNullable<NetworkEdge["type"]>, { strokeStyle: string; dash: string }> = {
  ally: { strokeStyle: "solid", dash: "0" },
  rival: { strokeStyle: "dashed", dash: "8 6" },
  mentor: { strokeStyle: "solid", dash: "0" },
  transaction: { strokeStyle: "dotted", dash: "2 6" },
  neutral: { strokeStyle: "solid", dash: "0" },
};

export const NetworkMap: React.FC<NetworkMapProps> = ({
  nodes,
  edges,
  title,
  durationFrames,
  theme: themeOverride,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = resolveTheme(themeOverride);

  const fadeFrames = theme.fadeFrames ?? 36;
  const total = durationFrames ?? 9 * fps;
  const fadeOutStart = total - fadeFrames;

  const opacity = interpolate(frame, [0, fadeFrames, fadeOutStart, total], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const nodesById = new Map(nodes.map((n) => [n.id, n]));

  // Compute reveal times — center first, then peripheral
  const centerNodes = nodes.filter((n) => n.isCenter);
  const peripheralNodes = nodes.filter((n) => !n.isCenter);
  const usable = total - fadeFrames * 2;
  const peripheralStart = fadeFrames + 0.6 * fps;
  const peripheralWindow = Math.max(usable * 0.6, peripheralNodes.length * 0.4 * fps);

  const nodeRevealFrame = (n: NetworkNode, index: number): number => {
    if (n.revealAtSeconds !== undefined) return Math.round(n.revealAtSeconds * fps);
    if (n.isCenter) return Math.round(fadeFrames);
    const slot =
      peripheralNodes.length > 1
        ? index / (peripheralNodes.length - 1)
        : 0.5;
    return Math.round(peripheralStart + slot * peripheralWindow);
  };

  return (
    <AbsoluteFill
      style={{
        background: theme.bg,
        opacity,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: 60,
      }}
    >
      {title ? (
        <div
          style={{
            fontFamily: theme.fontHeading,
            fontWeight: theme.headingWeight ?? 700,
            fontSize: 28,
            color: theme.accent,
            letterSpacing: "0.05em",
            marginBottom: 24,
            textTransform: "uppercase",
          }}
        >
          {title}
        </div>
      ) : null}

      <div style={{ position: "relative", width: 1400, height: 760 }}>
        <svg
          viewBox="0 0 1000 600"
          width={1400}
          height={760}
          style={{ position: "absolute", inset: 0 }}
        >
          {/* edges */}
          {edges.map((e, idx) => {
            const from = nodesById.get(e.fromId);
            const to = nodesById.get(e.toId);
            if (!from || !to) return null;

            const fromIdx = nodes.indexOf(from);
            const toIdx = nodes.indexOf(to);
            const fromReveal = nodeRevealFrame(from, peripheralNodes.indexOf(from));
            const toReveal = nodeRevealFrame(to, peripheralNodes.indexOf(to));
            const edgeReveal =
              e.revealAtSeconds !== undefined
                ? Math.round(e.revealAtSeconds * fps)
                : Math.max(fromReveal, toReveal) + 8;

            const draw = interpolate(frame, [edgeReveal, edgeReveal + 18], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });
            if (draw === 0) return null;

            const edgeStyle = EDGE_COLORS[e.type ?? "neutral"];
            const isRival = e.type === "rival";
            const stroke = isRival ? (theme.stampRed ?? "#b41e1e") : theme.accent;

            return (
              <g key={`e-${idx}`}>
                <line
                  x1={from.x}
                  y1={from.y}
                  x2={from.x + (to.x - from.x) * draw}
                  y2={from.y + (to.y - from.y) * draw}
                  stroke={stroke}
                  strokeWidth={2}
                  strokeOpacity={0.85}
                  strokeDasharray={edgeStyle.dash}
                />
                {e.label && draw > 0.7 ? (
                  <text
                    x={(from.x + to.x) / 2}
                    y={(from.y + to.y) / 2 - 8}
                    fontFamily={theme.fontBody}
                    fontSize={11}
                    fill={theme.text}
                    textAnchor="middle"
                    stroke={theme.bg}
                    strokeWidth={3}
                    paintOrder="stroke"
                    opacity={(draw - 0.7) / 0.3}
                  >
                    {e.label}
                  </text>
                ) : null}
              </g>
            );
          })}
        </svg>

        {/* nodes (rendered as positioned divs above the SVG so portraits work) */}
        {nodes.map((n, idx) => {
          const peripheralIdx = peripheralNodes.indexOf(n);
          const reveal = nodeRevealFrame(n, peripheralIdx);
          const scale = interpolate(frame, [reveal, reveal + 18], [0.6, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const opacityNode = interpolate(frame, [reveal, reveal + 18], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          if (opacityNode === 0) return null;

          const size = n.isCenter ? 96 : 72;
          const xPercent = (n.x / 1000) * 100;
          const yPercent = (n.y / 600) * 100;

          return (
            <div
              key={n.id}
              style={{
                position: "absolute",
                left: `${xPercent}%`,
                top: `${yPercent}%`,
                transform: `translate(-50%, -50%) scale(${scale})`,
                opacity: opacityNode,
                pointerEvents: "none",
              }}
            >
              <div
                style={{
                  width: size,
                  height: size,
                  borderRadius: "50%",
                  background: theme.bg,
                  border: `${n.isCenter ? 3 : 2}px solid ${theme.accent}`,
                  overflow: "hidden",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontFamily: theme.fontHeading,
                  fontWeight: 700,
                  fontSize: n.isCenter ? 28 : 22,
                  color: theme.accent,
                  boxShadow: `0 0 ${n.isCenter ? 24 : 12}px ${theme.accent}66`,
                }}
              >
                {n.portraitSrc ? (
                  <Img src={n.portraitSrc} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                ) : (
                  n.label.charAt(0).toUpperCase()
                )}
              </div>
              <div
                style={{
                  position: "absolute",
                  top: size + 6,
                  left: "50%",
                  transform: "translateX(-50%)",
                  whiteSpace: "nowrap",
                  textAlign: "center",
                  fontFamily: theme.fontBody,
                  fontSize: n.isCenter ? 16 : 14,
                  color: theme.text,
                  fontWeight: n.isCenter ? 700 : 400,
                  textShadow: `0 1px 4px ${theme.bg}`,
                }}
              >
                {n.label}
                {n.role ? (
                  <div style={{ fontSize: 11, color: theme.muted ?? theme.text, marginTop: 2 }}>
                    {n.role}
                  </div>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
