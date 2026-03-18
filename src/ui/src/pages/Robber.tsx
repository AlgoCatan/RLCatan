import {
  SQRT3,
  tilePixelVector,
  type CubeCoordinate,
} from "../utils/coordinates";
import { Paper } from "@mui/material";

type RobberProps = {
  center: [number, number];
  size: number;
  coordinate: CubeCoordinate;
};

export default function Robber({ center, size, coordinate }: RobberProps) {
  const [centerX, centerY] = center;
  const w = SQRT3 * size;
  const [tileX, tileY] = tilePixelVector(coordinate, size, centerX, centerY);
  const robberSize = Math.max(size * 0.42, 18);
  const robberFontSize = Math.max(robberSize * 0.45, 9);
  const x = tileX - w * 0.22 - robberSize / 2;
  const y = tileY - size * 0.2 - robberSize / 2;

  return (
    <Paper
      elevation={3}
      className="robber"
      style={{
        left: x,
        top: y,
        width: robberSize,
        height: robberSize,
        fontSize: robberFontSize,
      }}
    >
      R
    </Paper>
  );
}
