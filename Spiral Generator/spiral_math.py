"""Pure geometry for the spiral. Kept free of Fusion imports so it can be unit tested."""

import math

TWO_PI = 2 * math.pi


def revolutions_to_angle(revolutions):
    """Convert a number of revolutions to an angle in radians."""
    return revolutions * TWO_PI


def angle_to_revolutions(angle):
    """Convert an angle in radians to a number of revolutions."""
    return angle / TWO_PI


def total_segments(segments_per_revolution, sweep):
    """Number of segments for a ``sweep`` (radians) at a density of segments per revolution.

    Rounded to the nearest whole segment and never below one. The sign of the sweep is
    ignored, so a clockwise spiral gets the same count as an anticlockwise one.
    """
    return max(1, round(segments_per_revolution * abs(angle_to_revolutions(sweep))))


def segments_per_revolution(total, sweep):
    """Segments per revolution that ``total`` segments give over ``sweep`` (radians).

    Rounded to the nearest whole segment and never below one. Used when switching the
    segment input from an absolute count to a per-revolution density.
    """
    revolutions = abs(angle_to_revolutions(sweep))
    if revolutions == 0:
        return max(1, total)
    return max(1, round(total / revolutions))


def spiral_points(initial_distance, initial_angle, final_distance, final_angle, flare, num_segments):
    """Return ``num_segments + 1`` (x, y) tuples from the start to the end of the spiral.

    The curve sweeps from ``initial_angle`` to ``final_angle`` (radians) while the radius
    moves from ``initial_distance`` to ``final_distance``.

    ``flare`` controls how the radius growth is distributed along the sweep. With a flare
    of 1 the radius grows at a constant rate per unit angle, which is a true logarithmic
    spiral. Above 1 the curve stays close to the initial distance for longer and opens
    out towards the end. Below 1 it opens out early and then settles. The start and end
    points are the same for every flare value.
    """
    if initial_distance <= 0 or final_distance <= 0:
        raise ValueError('distances must be positive')
    if flare <= 0:
        raise ValueError('flare must be positive')
    if num_segments <= 0:
        raise ValueError('num_segments must be positive')

    ratio = final_distance / initial_distance
    sweep = final_angle - initial_angle

    points = []
    for i in range(num_segments + 1):
        t = i / num_segments
        r = initial_distance * ratio**(t**flare)
        angle = initial_angle + t * sweep
        points.append((r * math.cos(angle), r * math.sin(angle)))

    return points
