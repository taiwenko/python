"""
Provide ordered test execution by decorating with a phase/number.

Derived from http://stackoverflow.com/questions/17002707/a-nose-plugin-to-specify-the-order-of-unit-test-execution

def Foo(unittest.TestCase):

    @step(phase=1)
    def test_foo(self):
        pass

    @step(phase=2)
    def test_boo(self):
        pass

Methods without a defined phase are assigned to phase 0. Define your phases
accordingly.
"""

import logging
import os
from nose import loader

from nose.plugins.base import Plugin
from nose.suite import ContextList

log = logging.getLogger('nose.plugins.step')


def step(**kwargs):
    """
    Define ordered steps
    """
    def wrapped(obj):
        for key, value in kwargs.iteritems():
            setattr(obj, key, value)
        return obj
    return wrapped

class MyLoader(loader.TestLoader):
    def __init__(self, parent):
        super(MyLoader, self).__init__();
        self.parent_loader = parent

    def loadTestsFromTestClass(self, cls):
        """
        Return tests in this test case class, ordered by phase then by name.
        """
        tests_by_phase = {}
        # Build a mapping of tests to phase
        for test in self.parent_loader.loadTestsFromTestClass(cls):
            test_name = str(test)
            method_name = test_name.split('.')[-1]
            func = getattr(cls, method_name)
            phase = getattr(func, 'phase', 0);
            tests_this_phase = tests_by_phase.setdefault(phase, [])
            tests_this_phase.append((test_name, test))

        # For each phase in order, list out all tests.
        ordered = []
        for phase in sorted(tests_by_phase.keys()):
            for _, test in sorted(tests_by_phase[phase]):
                ordered.append(test)

        return self.suiteClass(ContextList(ordered, context=cls))

class Steps(Plugin):
    """
    Order the tests within a class defined by the @step decorator
    """
    name = 'steps'
    score = 1
    enabled = True

    def configure(self, options, conf):
        """
        Configure plugin.
        """
        self.enabled = True

    def prepareTestLoader(self, loader):
        return MyLoader(loader)
