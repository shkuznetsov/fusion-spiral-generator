"""Load the add-in entry module the way Fusion does and check it survives a stale sibling.

Fusion runs every add-in in one Python interpreter and loads each add-in folder as a
package. If another add-in has already imported a module called ``spiral_math``, that
name is cached in ``sys.modules``, so the entry module must import its sibling relative
to its own package rather than by bare name.
"""

import importlib.util
import os
import sys
import types
import unittest

ADDIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Spiral Generator')
ADDIN_NAME = 'Spiral Generator'
ENTRY_FILE = os.path.join(ADDIN_DIR, ADDIN_NAME + '.py')


def install_fake_adsk():
    """Minimal stand-in for the Fusion API, enough for the entry module to import."""
    adsk = types.ModuleType('adsk')
    core = types.ModuleType('adsk.core')
    for name in (
        'CommandCreatedEventHandler',
        'InputChangedEventHandler',
        'ValidateInputsEventHandler',
        'CommandEventHandler',
    ):
        setattr(core, name, type(name, (), {}))
    adsk.core = core
    adsk.fusion = types.ModuleType('adsk.fusion')
    adsk.cam = types.ModuleType('adsk.cam')
    sys.modules['adsk'] = adsk
    sys.modules['adsk.core'] = core
    sys.modules['adsk.fusion'] = adsk.fusion
    sys.modules['adsk.cam'] = adsk.cam


def load_entry_as_package():
    """Import the entry file as Fusion does: a package named after the add-in folder."""
    spec = importlib.util.spec_from_file_location(
        ADDIN_NAME, ENTRY_FILE, submodule_search_locations=[ADDIN_DIR]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[ADDIN_NAME] = module
    spec.loader.exec_module(module)
    return module


class AddInImportTest(unittest.TestCase):
    def setUp(self):
        install_fake_adsk()
        for name in list(sys.modules):
            if name == 'spiral_math' or name.startswith(ADDIN_NAME):
                del sys.modules[name]

    def test_entry_module_imports_with_stale_spiral_math_cached(self):
        # Simulate another add-in having already imported an older spiral_math.
        stale = types.ModuleType('spiral_math')
        stale.spiral_points = lambda *args: []
        sys.modules['spiral_math'] = stale

        module = load_entry_as_package()

        self.assertIsNot(module.spiral_points, stale.spiral_points)
        self.assertTrue(
            os.path.samefile(
                os.path.dirname(sys.modules[module.spiral_points.__module__].__file__),
                ADDIN_DIR,
            )
        )
        self.assertTrue(callable(module.angle_to_revolutions))


if __name__ == '__main__':
    unittest.main()
