# Autodesk Fusion - Spiral Generator Add-In

Autodesk Fusion add-in for generating a spiral as a sketch curve, with control over how quickly it unfolds.

This is a fork of [log-spiral-generator](https://github.com/murar8/log-spiral-generator) by [Lorenzo Murarotto](https://github.com/murar8), which is now archived. The original design, controls and approach are his work. This fork, maintained by [Alexander Kuznetsov](https://github.com/shkuznetsov), continues development from there.

## Installation

The add-in is the `Spiral Generator` folder in this repository. Copy that folder, keeping its name, into the Fusion add-ins directory:

- Windows: `%AppData%\Autodesk\Autodesk Fusion 360\API\AddIns`
- macOS: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns`

Fusion loads an add-in by looking for a script with the same name as its folder, so the folder must stay named `Spiral Generator`.

### Using git from the command line

Clone the repository anywhere, then copy the `Spiral Generator` folder into the add-ins directory. On Windows:

```powershell
git clone https://github.com/shkuznetsov/fusion-spiral-generator
Copy-Item -Recurse ".\fusion-spiral-generator\Spiral Generator" "$env:APPDATA\Autodesk\Autodesk Fusion 360\API\AddIns\Spiral Generator"
```

On macOS:

```bash
git clone https://github.com/shkuznetsov/fusion-spiral-generator
cp -R "fusion-spiral-generator/Spiral Generator" "$HOME/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/Spiral Generator"
```

Alternatively, register the folder from `Utilities` > `Add-Ins` > `Scripts and Add-Ins` using the `+` button next to `My Add-Ins`. Fusion then loads it in place, which is convenient for development.

## Usage

1. ### Create a sketch

    - Go to `Solid` > `Create` > `Create Sketch`

2. ### Launch the command

    - Go to `Sketch` > `Create` > `Spiral`
    - Enter the desired parameters, described below, or play around with the handles if going by feel.

3. Done!

## Parameters

### Centre

The point the spiral is drawn around. Nothing is drawn until you select one. Click the sketch origin to centre the spiral there, or select any sketch point, construction point or model vertex. To centre it anywhere else, place a sketch point there first with `Sketch` > `Create` > `Point`, then select it.

### Initial Distance and Initial Angle

Polar coordinates of the start point relative to the centre: how far from the centre the spiral begins, and in which direction.

### Final Distance

The radius at the end of the spiral. A final distance smaller than the initial distance draws a spiral that winds inwards.

### Sweep

How far the spiral turns from its initial angle, entered either as a number of revolutions, with arrows stepping by half a turn, or as degrees. Switching between the two converts the value, so 2 revolutions becomes 720 degrees and back. A negative sweep turns clockwise.

### Flare

How the spiral unfolds between its start and end. `1` gives a true logarithmic spiral. Above `1` the curve stays tight for longer and opens out towards the end. Below `1` it opens out early and then settles. The start and end points stay where you set them.

### Segments

How many points are generated before the spline is fitted, either per revolution or as a total. Per revolution is the default at 16 and keeps the accuracy constant as the sweep changes. Switching to total converts the value. More segments give better dimensional accuracy.

## How it works

This add-in just generates one point per segment along the spiral, plus the end point, then interpolates them with a spline.

The radius at fraction `t` of the sweep, from `0` at the start to `1` at the end, is `r0 * (r1 / r0) ^ (t ^ flare)`. With `flare = 1` the exponent is linear in the angle, which is the definition of a logarithmic spiral. Other values redistribute the same overall growth along the sweep without moving the endpoints.

The geometry lives in `Spiral Generator/spiral_math.py` and has no Fusion dependency, so it can be tested outside Fusion:

```
python tests/test_spiral_math.py
```

## Credits

Original work by [Lorenzo Murarotto](https://github.com/murar8).

Fork maintained by [Alexander Kuznetsov](https://github.com/shkuznetsov).

## License

Copyright (c) 2021 Lorenzo Murarotto

Copyright (c) 2026 Alexander Kuznetsov

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
