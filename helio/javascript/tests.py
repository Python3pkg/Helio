import unittest
import subprocess
import urllib.parse, urllib.request, urllib.parse, urllib.error
import os


def path2url(path):
    return urllib.parse.urljoin('file:', urllib.request.pathname2url(path))


class JavascriptTestRunner(unittest.TestCase):
    def test_run_controller_js_tests(self):
        return
        try:
            output = subprocess.check_output(['phantomjs', 'javascript/static/js/tests/jasminerunner.js',
                                              path2url(os.getcwd() + '/javascript/controller_tests.html')])
            self.assertIn(' 0 failures', output)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(e.output)

    def test_run_notification_js_tests(self):
        return
        try:
            output = subprocess.check_output(['phantomjs', 'javascript/static/js/tests/jasminerunner.js',
                                              path2url(os.getcwd() + '/javascript/controller_tests.html')])
            self.assertIn(' 0 failures', output)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(e.output)

