import math
import traceback

import adsk.cam
import adsk.core
import adsk.fusion

# Fusion loads every add-in folder as a package in one shared interpreter. Importing the
# sibling module relative to this package keeps it namespaced under the add-in name, so it
# cannot collide with a module of the same name cached by another add-in.
from .spiral_math import (
    angle_to_revolutions,
    revolutions_to_angle,
    segments_per_revolution,
    spiral_points,
    total_segments,
)

COMMAND_PANEL = "SketchCreatePanel"

COMMAND_BUTTON_ID = "fusionSpiralGeneratorButton"

CENTRE_INPUT_ID = "centre"
INITIAL_DISTANCE_INPUT_ID = "initialdistance"
INITIAL_ANGLE_INPUT_ID = "initialangle"
FINAL_DISTANCE_INPUT_ID = "finaldistance"
SWEEP_MODE_INPUT_ID = "sweepmode"
SWEEP_REVOLUTIONS_INPUT_ID = "sweeprevolutions"
SWEEP_ANGLE_INPUT_ID = "sweepangle"
FLARE_INPUT_ID = "flare"
SEGMENTS_MODE_INPUT_ID = "segmentsmode"
SEGMENTS_PER_REVOLUTION_INPUT_ID = "segmentsperrevolution"
SEGMENTS_TOTAL_INPUT_ID = "segmentstotal"

SWEEP_MODE_REVOLUTIONS = 'Revolutions'
SWEEP_MODE_DEGREES = 'Degrees'
SEGMENTS_MODE_PER_REVOLUTION = 'Per revolution'
SEGMENTS_MODE_TOTAL = 'Total'

DEFAULT_REVOLUTIONS = 3.0
DEFAULT_SEGMENTS_PER_REVOLUTION = 16
REVOLUTIONS_SPIN_STEP = 0.5
REVOLUTIONS_LIMIT = 10000.0

# Global list to keep all event handlers in scope.
# This is only needed with Python.
handlers = []


def read_centre(inputs, sketch):
    """The centre of the spiral as a Point3D in sketch space.

    Falls back to the sketch origin if nothing is selected yet, which validation prevents
    from reaching the preview.
    """
    selection = inputs.itemById(CENTRE_INPUT_ID)
    if selection.selectionCount == 0:
        return adsk.core.Point3D.create(0, 0, 0)

    entity = selection.selection(0).entity
    if entity.objectType == adsk.fusion.SketchPoint.classType():
        return entity.geometry
    # Construction points and vertices report their position in model space.
    return sketch.modelToSketchSpace(entity.geometry)


def sketch_direction(sketch, angle):
    """A model-space unit vector lying in the sketch plane at ``angle`` from the sketch X axis."""
    x = sketch.xDirection.copy()
    y = sketch.yDirection.copy()
    x.scaleBy(math.cos(angle))
    y.scaleBy(math.sin(angle))
    x.add(y)
    return x


def refresh_handle(commandInput):
    """Force Fusion to redraw an input's drag handle after setManipulator.

    Fusion only builds the handle when the input becomes visible, so a handle moved after
    the dialog opened keeps its old position until the input is hidden and shown again.
    """
    if commandInput.isVisible:
        commandInput.isVisible = False
        commandInput.isVisible = True


def place_handles(inputs, sketch):
    """Anchor every drag handle at the current centre, oriented in the sketch plane."""
    origin = sketch.sketchToModelSpace(read_centre(inputs, sketch))
    initialAngle = inputs.itemById(INITIAL_ANGLE_INPUT_ID).value
    endAngle = initialAngle + read_sweep(inputs)
    startDirection = sketch_direction(sketch, initialAngle)
    startNormal = sketch_direction(sketch, initialAngle + math.pi / 2)

    initialDistanceInput = inputs.itemById(INITIAL_DISTANCE_INPUT_ID)
    initialDistanceInput.setManipulator(origin, startDirection)
    refresh_handle(initialDistanceInput)

    finalDistanceInput = inputs.itemById(FINAL_DISTANCE_INPUT_ID)
    finalDistanceInput.setManipulator(origin, sketch_direction(sketch, endAngle))
    refresh_handle(finalDistanceInput)

    initialAngleInput = inputs.itemById(INITIAL_ANGLE_INPUT_ID)
    initialAngleInput.setManipulator(origin, sketch.xDirection, sketch.yDirection)
    refresh_handle(initialAngleInput)

    sweepAngleInput = inputs.itemById(SWEEP_ANGLE_INPUT_ID)
    sweepAngleInput.setManipulator(origin, startDirection, startNormal)
    refresh_handle(sweepAngleInput)


def has_centre(inputs):
    return inputs.itemById(CENTRE_INPUT_ID).selectionCount == 1


def update_visibility(inputs):
    """Show only the Centre selection until a centre exists, then the rest by mode.

    Inputs with drag handles must stay hidden until the centre is known, otherwise their
    handles appear at the sketch origin. Hiding everything else too keeps the first step
    of the dialog to one question.
    """
    ready = has_centre(inputs)
    useRevolutions = (
        inputs.itemById(SWEEP_MODE_INPUT_ID).selectedItem.name == SWEEP_MODE_REVOLUTIONS
    )
    usePerRevolution = (
        inputs.itemById(SEGMENTS_MODE_INPUT_ID).selectedItem.name
        == SEGMENTS_MODE_PER_REVOLUTION
    )

    for inputId in (
        INITIAL_DISTANCE_INPUT_ID,
        INITIAL_ANGLE_INPUT_ID,
        FINAL_DISTANCE_INPUT_ID,
        SWEEP_MODE_INPUT_ID,
        FLARE_INPUT_ID,
        SEGMENTS_MODE_INPUT_ID,
    ):
        inputs.itemById(inputId).isVisible = ready

    inputs.itemById(SWEEP_REVOLUTIONS_INPUT_ID).isVisible = ready and useRevolutions
    inputs.itemById(SWEEP_ANGLE_INPUT_ID).isVisible = ready and not useRevolutions
    inputs.itemById(SEGMENTS_PER_REVOLUTION_INPUT_ID).isVisible = ready and usePerRevolution
    inputs.itemById(SEGMENTS_TOTAL_INPUT_ID).isVisible = ready and not usePerRevolution


def read_sweep(inputs):
    """The sweep in radians, read from whichever sweep input is currently active."""
    mode = inputs.itemById(SWEEP_MODE_INPUT_ID).selectedItem.name
    if mode == SWEEP_MODE_REVOLUTIONS:
        return revolutions_to_angle(inputs.itemById(SWEEP_REVOLUTIONS_INPUT_ID).value)
    return inputs.itemById(SWEEP_ANGLE_INPUT_ID).value


def read_segments(inputs, sweep):
    """The total number of segments, read from whichever segments input is active."""
    mode = inputs.itemById(SEGMENTS_MODE_INPUT_ID).selectedItem.name
    if mode == SEGMENTS_MODE_PER_REVOLUTION:
        return total_segments(inputs.itemById(SEGMENTS_PER_REVOLUTION_INPUT_ID).value, sweep)
    return inputs.itemById(SEGMENTS_TOTAL_INPUT_ID).value


# Event handler for the commandCreated event.
class SpiralCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
        cmd = eventArgs.command
        inputs = cmd.commandInputs

        centreInput = inputs.addSelectionInput(
            CENTRE_INPUT_ID,
            'Centre',
            'Select the point to draw the spiral around. The sketch origin is a valid choice.',
        )
        centreInput.addSelectionFilter('SketchPoints')
        centreInput.addSelectionFilter('ConstructionPoints')
        centreInput.addSelectionFilter('Vertices')
        centreInput.setSelectionLimits(1, 1)

        initialDistanceInput = inputs.addDistanceValueCommandInput(
            id=INITIAL_DISTANCE_INPUT_ID,
            name='Initial Distance',
            initialValue=adsk.core.ValueInput.createByString('1'),
        )

        initialAngleInput = inputs.addAngleValueCommandInput(
            id=INITIAL_ANGLE_INPUT_ID,
            name='Initial Angle',
            initialValue=adsk.core.ValueInput.createByString('0 degree'),
        )

        finalDistanceInput = inputs.addDistanceValueCommandInput(
            id=FINAL_DISTANCE_INPUT_ID,
            name='Final Distance',
            initialValue=adsk.core.ValueInput.createByString('2'),
        )

        sweepModeInput = inputs.addDropDownCommandInput(
            SWEEP_MODE_INPUT_ID, 'Sweep', adsk.core.DropDownStyles.TextListDropDownStyle
        )
        sweepModeInput.listItems.add(SWEEP_MODE_REVOLUTIONS, True)
        sweepModeInput.listItems.add(SWEEP_MODE_DEGREES, False)
        sweepModeInput.tooltip = 'How far the spiral turns from its initial angle.'

        inputs.addFloatSpinnerCommandInput(
            id=SWEEP_REVOLUTIONS_INPUT_ID,
            name='Revolutions',
            unitType='',
            min=-REVOLUTIONS_LIMIT,
            max=REVOLUTIONS_LIMIT,
            spinStep=REVOLUTIONS_SPIN_STEP,
            initialValue=DEFAULT_REVOLUTIONS,
        )

        sweepAngleInput = inputs.addAngleValueCommandInput(
            id=SWEEP_ANGLE_INPUT_ID,
            name='Degrees',
            initialValue=adsk.core.ValueInput.createByReal(
                revolutions_to_angle(DEFAULT_REVOLUTIONS)
            ),
        )
        sweepAngleInput.hasMinimumValue = False
        sweepAngleInput.hasMaximumValue = False

        flareInput = inputs.addValueInput(
            id=FLARE_INPUT_ID,
            name='Flare',
            unitType='',
            initialValue=adsk.core.ValueInput.createByReal(1.0),
        )
        flareInput.tooltip = 'How the spiral unfolds between its start and end.'
        flareInput.tooltipDescription = (
            '1 gives a true logarithmic spiral. Above 1 the curve stays tight for longer '
            'and opens out towards the end. Below 1 it opens out early and then settles. '
            'The start and end points do not move.'
        )

        segmentsModeInput = inputs.addDropDownCommandInput(
            SEGMENTS_MODE_INPUT_ID, 'Segments', adsk.core.DropDownStyles.TextListDropDownStyle
        )
        segmentsModeInput.listItems.add(SEGMENTS_MODE_PER_REVOLUTION, True)
        segmentsModeInput.listItems.add(SEGMENTS_MODE_TOTAL, False)
        segmentsModeInput.tooltip = (
            'How many points are generated along the spiral before the spline is fitted. '
            'More segments give better dimensional accuracy.'
        )

        inputs.addIntegerSpinnerCommandInput(
            id=SEGMENTS_PER_REVOLUTION_INPUT_ID,
            name='Per revolution',
            min=1,
            max=2**31 - 1,
            spinStep=1,
            initialValue=DEFAULT_SEGMENTS_PER_REVOLUTION,
        )

        segmentsTotalInput = inputs.addIntegerSpinnerCommandInput(
            id=SEGMENTS_TOTAL_INPUT_ID,
            name='Total',
            min=1,
            max=2**31 - 1,
            spinStep=1,
            initialValue=total_segments(
                DEFAULT_SEGMENTS_PER_REVOLUTION, revolutions_to_angle(DEFAULT_REVOLUTIONS)
            ),
        )
        update_visibility(inputs)

        onInputChanged = SpiralCommandInputChangedHandler()
        cmd.inputChanged.add(onInputChanged)
        handlers.append(onInputChanged)

        onValidate = SpiralCommandValidateInputsHandler()
        cmd.validateInputs.add(onValidate)
        handlers.append(onValidate)

        onExecutePreview = SpiralCommandExecutePreviewHandler()
        cmd.executePreview.add(onExecutePreview)
        handlers.append(onExecutePreview)


# Event handler for the inputChanged event.
# Switching a mode dropdown converts the current value into the other input and swaps
# which of the pair is visible. Plain value edits are left alone.
class SpiralCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def notify(self, args):
        eventArgs = adsk.core.InputChangedEventArgs.cast(args)
        inputs = eventArgs.inputs
        changed = eventArgs.input

        if changed.id == SWEEP_MODE_INPUT_ID:
            revolutionsInput = inputs.itemById(SWEEP_REVOLUTIONS_INPUT_ID)
            angleInput = inputs.itemById(SWEEP_ANGLE_INPUT_ID)
            useRevolutions = changed.selectedItem.name == SWEEP_MODE_REVOLUTIONS
            if useRevolutions:
                revolutionsInput.value = angle_to_revolutions(angleInput.value)
            else:
                angleInput.value = revolutions_to_angle(revolutionsInput.value)

        elif changed.id == SEGMENTS_MODE_INPUT_ID:
            perRevolutionInput = inputs.itemById(SEGMENTS_PER_REVOLUTION_INPUT_ID)
            totalInput = inputs.itemById(SEGMENTS_TOTAL_INPUT_ID)
            sweep = read_sweep(inputs)
            usePerRevolution = changed.selectedItem.name == SEGMENTS_MODE_PER_REVOLUTION
            if usePerRevolution:
                perRevolutionInput.value = segments_per_revolution(totalInput.value, sweep)
            else:
                totalInput.value = total_segments(perRevolutionInput.value, sweep)

        update_visibility(inputs)

        app = adsk.core.Application.get()
        if has_centre(inputs) and app.activeEditObject.objectType == adsk.fusion.Sketch.classType():
            place_handles(inputs, adsk.fusion.Sketch.cast(app.activeEditObject))


# Event handler for the validateInputs event.
class SpiralCommandValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    def notify(self, args):
        eventArgs = adsk.core.ValidateInputsEventArgs.cast(args)
        inputs = eventArgs.inputs

        hasCentre = has_centre(inputs)
        initialDistance = inputs.itemById(INITIAL_DISTANCE_INPUT_ID).value
        finalDistance = inputs.itemById(FINAL_DISTANCE_INPUT_ID).value
        sweep = read_sweep(inputs)
        flare = inputs.itemById(FLARE_INPUT_ID).value
        num_segments = read_segments(inputs, sweep)

        if (
            not hasCentre
            or num_segments <= 0
            or initialDistance <= 0
            or finalDistance <= 0
            or flare <= 0
            or sweep == 0
        ):
            eventArgs.areInputsValid = False


# Event handler for the executePreview event.
class SpiralCommandExecutePreviewHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        # Verify that a sketch is active.
        app = adsk.core.Application.get()
        if app.activeEditObject.objectType != adsk.fusion.Sketch.classType():
            ui = app.userInterface
            ui.messageBox('A sketch must be active for this command.')
            return False

        eventArgs = adsk.core.CommandEventArgs.cast(args)
        inputs = eventArgs.command.commandInputs
        sketch = adsk.fusion.Sketch.cast(app.activeEditObject)

        centre = read_centre(inputs, sketch)
        initialDistance = inputs.itemById(INITIAL_DISTANCE_INPUT_ID).value
        initialAngle = inputs.itemById(INITIAL_ANGLE_INPUT_ID).value
        finalDistance = inputs.itemById(FINAL_DISTANCE_INPUT_ID).value
        sweep = read_sweep(inputs)
        finalAngle = initialAngle + sweep
        flare = inputs.itemById(FLARE_INPUT_ID).value
        num_segments = read_segments(inputs, sweep)

        points = adsk.core.ObjectCollection.create()

        for x, y in spiral_points(
            initialDistance, initialAngle, finalDistance, finalAngle, flare, num_segments
        ):
            points.add(adsk.core.Point3D.create(centre.x + x, centre.y + y, 0))

        sketch.sketchCurves.sketchFittedSplines.add(points)

        # Set the isValidResult property to use these results at the final result.
        # This will result in the execute event not being fired.
        eventArgs.isValidResult = True


def run(context):
    ui = None

    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        button = ui.commandDefinitions.addButtonDefinition(
            COMMAND_BUTTON_ID,
            'Spiral',
            'Create a spiral as a sketch curve.',
            '.\\Resources\\Logo',
        )

        spiralCommandCreated = SpiralCommandCreatedEventHandler()
        button.commandCreated.add(spiralCommandCreated)
        handlers.append(spiralCommandCreated)

        addInsPanel = ui.allToolbarPanels.itemById(COMMAND_PANEL)
        addInsPanel.controls.addCommand(button)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    ui = None

    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        cmdDef = ui.commandDefinitions.itemById(COMMAND_BUTTON_ID)
        if cmdDef:
            cmdDef.deleteMe()

        addinsPanel = ui.allToolbarPanels.itemById(COMMAND_PANEL)
        cntrl = addinsPanel.controls.itemById(COMMAND_BUTTON_ID)
        if cntrl:
            cntrl.deleteMe()

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
