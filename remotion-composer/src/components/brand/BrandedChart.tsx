/**
 * BrandedChart — channel-themed wrapper around the existing Remotion chart
 * components (BarChart, LineChart, PieChart, KPIGrid). Reads the active brand
 * theme and forwards channel-appropriate colors and fonts.
 *
 * For more direct control, import {BarChart, PieChart, ...} directly and
 * pass colors yourself.
 *
 * @version 0.1.0
 */
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BarChart, LineChart, PieChart, KPIGrid } from "../charts";
import { BrandTheme, resolveTheme } from "./theme";

type ChartKind = "bar" | "line" | "pie" | "kpi";

export interface BrandedChartProps {
  kind: ChartKind;
  /** Chart data — shape depends on kind:
   *    bar:  Array<{ label: string; value: number; color?: string }>
   *    line: LineSeries[] (see LineChart's prop signature)
   *    pie:  Array<{ label: string; value: number; color?: string }>
   *    kpi:  Metric[]
   */
  data: any;
  title?: string;
  /** Optional chart palette override — defaults to channel-appropriate. */
  colors?: string[];
  /** Total frames. Default = 8s @ fps. */
  durationFrames?: number;
  theme?: Partial<BrandTheme>;
}

/** Default chart palettes per channel — keyed off whether stampRed is set (MM). */
const PALETTE_HUXLEY = ["#c9a84c", "#d4a54a", "#8c6e23", "#f0e6d2", "#5a4a3a", "#2e5e4e"];
const PALETTE_MM = ["#c9a84c", "#4a6fa5", "#f5f0e4", "#b41e1e", "#3a3a4a", "#8c6e23"];

export const BrandedChart: React.FC<BrandedChartProps> = ({
  kind,
  data,
  title,
  colors,
  durationFrames,
  theme: themeOverride,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = resolveTheme(themeOverride);

  const fadeFrames = theme.fadeFrames ?? 36;
  const total = durationFrames ?? 8 * fps;
  const fadeOutStart = total - fadeFrames;

  const opacity = interpolate(frame, [0, fadeFrames, fadeOutStart, total], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const resolvedPalette = colors ?? (theme.stampRed ? PALETTE_MM : PALETTE_HUXLEY);

  const sharedProps = {
    title,
    colors: resolvedPalette,
    fontFamily: theme.fontBody,
    textColor: theme.text,
    backgroundColor: theme.bg,
  };

  return (
    <AbsoluteFill style={{ background: theme.bg, opacity }}>
      {kind === "bar" ? <BarChart {...sharedProps} data={data} /> : null}
      {kind === "pie" ? <PieChart {...sharedProps} data={data} /> : null}
      {kind === "line" ? <LineChart {...sharedProps} series={data} /> : null}
      {kind === "kpi" ? <KPIGrid {...sharedProps} metrics={data} /> : null}
    </AbsoluteFill>
  );
};
