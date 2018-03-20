import unittest
import os
from conans.test.utils.tools import TestClient
from conans.tools import os_info

class ExecTest(unittest.TestCase):

    def _env_cmd(self):
        if os_info.is_windows and not os_info.is_posix:
            return "SET"
        return "env"

    def _setup_recipies(self, client):
        toolA = """
import os
from conans import ConanFile

class ToolAConan(ConanFile):
    name = "toola"
    version = "0.1"

    def package_info(self):
        self.env_info.PATH = [os.path.join("bin")]
"""

        toolB = """
class ToolBConan(ConanFile):
    name = "toolb"
    version = "0.1"

    def package_info(self):
        self.env_info.PATH = [os.path.join("bin")]
"""

        client.save({"conanfile.py": toolA})
        client.run("export . lasote/testing")
        client.save({"conanfile.py": toolB}, clean_first=True)
        client.run("export . lasote/testing")

    def no_ref_test(self):
        client = TestClient()
        client.run_in_external_process("exec %s" % self._env_cmd())
