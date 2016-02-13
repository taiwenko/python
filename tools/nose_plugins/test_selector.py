"""Test selector plugin.

Select tests based on what requirements you have provided and what is required by
a given test. This plugin is derived from the nose-attrs plugin, and differs by:
    - Command line flag changed to --using/-u, and only accepts comma separated
      lists
    - Requirements are saved in a 'requirements' attribute, as a set
    - Method and class level requirements are unioned before consideration
    - For a test to be considered, its requirements must be a subset of the
      provided components, as opposed to the previous behavior where a provided
      attributes must be a subset of a test's attributes.
    - Add a function 'provided' that allows you to query if a component is
      provided. If this plugin is not enabled, ie, no requirements are provided,
      this function always returns True

TODO(aaronfan): Ability to use additional logic in selecting tests, such as
requires pfc or half-stack

Usage

Specify test requirements with the requires decorator. Both methods and classes
can be decorated. Checking if a requirement is provided during runtime can be
done with the provided function. Specify which requirements are provided in the
command line. If a test or its class is not decorated, the test is not run when
this plugin is used.

Example

from tools.nose_plugins.test_selector import requires, provided

@requires('a')
class ReqDemo
    @requires('b')
    def btest():
        print 'b'

    @requires('c')
    def ctest():
        print 'c'

    @requires('b', 'c')
    def bctest():
        print 'bc'

    @requires()
    def dtest():
        if provided('d')
        print 'd'

$ ./nose_run.py --using=a,b ReqDemo
'b'
'c'

$ ./nose_run.py --using=b,c ReqDemo

$ ./nose_run.py --using=a,b,c ReqDemo
'b'
'c'
'bc'

$ ./nose_run.py --using=a,d ReqDemo
'd'

"""
from nose.plugins.base import Plugin
from nose.util import tolist
from sets import Set

import os

components = None
DUMMY_NOSE_PLUGIN_SCORE = 1

def selector_is_enabled():
    return components is not None

# TODO(craigt): Inject list of allowed using/provided items.
def provided(component):
    if component.startswith('-'):
        return component[1:] not in components
    return component in components

def requires(*args):
    """Decorator that adds attributes to classes or functions

    For use with the using flag (--using/-u)
    """
    def wrap_function(function):
        setattr(function, 'requirements', Set(args))
        return function
    return wrap_function

def get_method_requirements(method, cls):
    """Look up the requirements on a method/function.

    Merges the requirements listed at the function and class levels.
    """
    requirements = Set()
    if hasattr(method, 'requirements'):
        requirements.update(getattr(method, 'requirements'))
    if cls is not None and hasattr(cls, 'requirements'):
        requirements.update(getattr(cls, 'requirements'))
    return requirements

class TestSelector(Plugin):
    """Selects test cases to be run based on their attributes."""
    name='loon-test-deps'
    score = DUMMY_NOSE_PLUGIN_SCORE

    def __init__(self):
        Plugin.__init__(self)
        self.attribs = []

    def options(self, parser, env):
        """Register command line options"""
        parser.add_option("-u", "--using",
                          dest="components", action="append",
                          default=env.get('LOON_COMP'),
                          metavar="COMP",
                          help="Run only tests that have required components "
                               "provided by COMP [LOON_COMP]")

    def configure(self, options, config):
        """Configure the plugin and system, based on selected options.

        Add all of the found components into a big set. Tests whose requirements
        are a subset of this set of available components will be run.
        """
        global components

        # attribute requirements are a comma separated list of
        # 'key=value' pairs
        if options.components is not None:
            components = Set()
            for component_string in tolist(options.components):
                # all attributes within an attribute group must match
                for component in component_string.strip().split(","):
                    component = component.strip()
                    # don't die on trailing comma
                    if component:
                        # Add both the component as specified, and its prefix.
                        # components is a set, so adding duplicates isn't a
                        # problem.
                        components.add(component)
                        components.add(component.split(':')[0])
        self.enabled = True

    def validate_requirements(self, method, cls = None):
        """Verify whether a method has the required attributes

        The method is considered a match if it matches all attributes
        for any attribute group.
        """
        requirements = get_method_requirements(method, cls)
        must_not_have = filter(lambda x: x.startswith('-'), requirements)

        # Remove must-not-have elements from the must-have elements before
        # removing the dash because in the must-have set they still have the
        # leading dash.
        must_have = requirements - Set(must_not_have)

        # Remove leading dash to properly match elements in components set
        must_not_have = Set([component[1:] for component in must_not_have])

        # If we have any of the must-not-have components, reject the test.
        if components.intersection(must_not_have):
            return False

        # If we have all of the must-have components, accept the test.
        if must_have.issubset(components):
            # Not True because we don't want to FORCE the selection of the item,
            # only say that it is acceptable
            return None

        # Otherwise, we have a partial subset or a disjoint set of required
        # components.
        return False

    def wantFile(self, filename):
      if 'unit_test' in os.path.basename(filename):
        # Tell nose that we do not want this file.
        return False
      # Let nose use its default file choice mechanism.
      return None

    def wantFunction(self, function):
        """Accept the function if its attributes match."""
        return self.validate_requirements(function)

    def wantMethod(self, method):
        """Accept the method if its attributes match."""
        if hasattr(method, 'im_class'):
            return self.validate_requirements(method,
                                              getattr(method, 'im_class'))
        else:
            return self.validate_requirements(method)
