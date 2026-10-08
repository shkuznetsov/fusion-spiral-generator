import math
import os
import sys
import unittest

# The add-in lives in the sibling 'Spiral Generator' folder.
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Spiral Generator')
)

from spiral_math import (  # noqa: E402
    angle_to_revolutions,
    revolutions_to_angle,
    segments_per_revolution,
    spiral_points,
    total_segments,
)


class SpiralPointsTest(unittest.TestCase):
    def test_returns_num_points_plus_one_points(self):
        points = spiral_points(1.0, 0.0, 2.0, math.pi, 1.0, 10)
        self.assertEqual(len(points), 11)

    def test_starts_and_ends_at_requested_polar_coordinates(self):
        points = spiral_points(1.0, 0.0, 2.0, math.pi, 1.0, 10)
        self.assertAlmostEqual(points[0][0], 1.0)
        self.assertAlmostEqual(points[0][1], 0.0)
        self.assertAlmostEqual(points[-1][0], -2.0)
        self.assertAlmostEqual(points[-1][1], 0.0)

    def test_endpoints_respected_when_initial_angle_is_nonzero(self):
        a0, a1 = math.pi / 2, 2 * math.pi
        points = spiral_points(1.0, a0, 3.0, a1, 1.0, 8)
        self.assertAlmostEqual(math.hypot(*points[0]), 1.0)
        self.assertAlmostEqual(math.atan2(points[0][1], points[0][0]), a0)
        self.assertAlmostEqual(math.hypot(*points[-1]), 3.0)

    def test_flare_one_is_a_logarithmic_spiral(self):
        # For a logarithmic spiral, log(r) is linear in the angle,
        # so successive radius ratios are constant.
        points = spiral_points(1.0, 0.0, 4.0, 2 * math.pi, 1.0, 20)
        radii = [math.hypot(x, y) for x, y in points]
        ratios = [b / a for a, b in zip(radii, radii[1:])]
        for ratio in ratios:
            self.assertAlmostEqual(ratio, ratios[0])

    def test_flare_does_not_move_endpoints(self):
        for flare in (0.25, 0.5, 2.0, 4.0):
            points = spiral_points(1.0, 0.0, 2.0, math.pi, flare, 10)
            self.assertAlmostEqual(math.hypot(*points[0]), 1.0)
            self.assertAlmostEqual(math.hypot(*points[-1]), 2.0)

    def test_high_flare_stays_tight_then_opens(self):
        base = spiral_points(1.0, 0.0, 2.0, math.pi, 1.0, 10)
        flared = spiral_points(1.0, 0.0, 2.0, math.pi, 2.0, 10)
        # Interior points of a high-flare spiral have smaller radii than
        # the classic spiral at the same angle.
        for (bx, by), (fx, fy) in zip(base[1:-1], flared[1:-1]):
            self.assertLess(math.hypot(fx, fy), math.hypot(bx, by))

    def test_low_flare_opens_early(self):
        base = spiral_points(1.0, 0.0, 2.0, math.pi, 1.0, 10)
        flared = spiral_points(1.0, 0.0, 2.0, math.pi, 0.5, 10)
        for (bx, by), (fx, fy) in zip(base[1:-1], flared[1:-1]):
            self.assertGreater(math.hypot(fx, fy), math.hypot(bx, by))

    def test_shrinking_spiral_is_supported(self):
        points = spiral_points(2.0, 0.0, 1.0, math.pi, 2.0, 10)
        self.assertAlmostEqual(math.hypot(*points[0]), 2.0)
        self.assertAlmostEqual(math.hypot(*points[-1]), 1.0)


class SweepConversionTest(unittest.TestCase):
    def test_one_revolution_is_two_pi(self):
        self.assertAlmostEqual(revolutions_to_angle(1.0), 2 * math.pi)
        self.assertAlmostEqual(revolutions_to_angle(2.0), 4 * math.pi)

    def test_round_trip(self):
        for revs in (0.25, 0.5, 1.0, 2.75, -1.5):
            self.assertAlmostEqual(angle_to_revolutions(revolutions_to_angle(revs)), revs)

    def test_half_revolution_is_180_degrees(self):
        self.assertAlmostEqual(math.degrees(revolutions_to_angle(0.5)), 180.0)


class SegmentCountTest(unittest.TestCase):
    def test_total_from_per_revolution(self):
        self.assertEqual(total_segments(36, revolutions_to_angle(1.0)), 36)
        self.assertEqual(total_segments(36, revolutions_to_angle(2.0)), 72)
        self.assertEqual(total_segments(36, revolutions_to_angle(0.5)), 18)

    def test_total_rounds_to_nearest(self):
        self.assertEqual(total_segments(36, revolutions_to_angle(0.26)), 9)
        self.assertEqual(total_segments(36, revolutions_to_angle(0.24)), 9)

    def test_total_never_below_one(self):
        self.assertEqual(total_segments(36, revolutions_to_angle(0.001)), 1)

    def test_total_uses_sweep_magnitude(self):
        self.assertEqual(total_segments(36, revolutions_to_angle(-1.0)), 36)

    def test_per_revolution_from_total(self):
        self.assertEqual(segments_per_revolution(72, revolutions_to_angle(2.0)), 36)
        self.assertEqual(segments_per_revolution(18, revolutions_to_angle(0.5)), 36)

    def test_per_revolution_rounds_and_never_below_one(self):
        self.assertEqual(segments_per_revolution(10, revolutions_to_angle(3.0)), 3)
        self.assertEqual(segments_per_revolution(1, revolutions_to_angle(10.0)), 1)

    def test_per_revolution_uses_sweep_magnitude(self):
        self.assertEqual(segments_per_revolution(72, revolutions_to_angle(-2.0)), 36)


if __name__ == '__main__':
    unittest.main()
