import sys
import unittest

from src.opal_agent.agent_client import run_tool
from src.opal_agent.configs import AGENT_HOST, AGENT_PORT
from src.opal_agent.main import main
from src.opal_agent.tools import say_name


class TestTool(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestTool, self).__init__(*args, **kwargs)
        self.thread = main()

    def test_simple_tool(self):
        ret = run_tool(say_name, host=AGENT_HOST, port=AGENT_PORT)[0]
        assert isinstance(ret, str)

    def tearDown(self):
        self.thread.join()


if __name__ == "__main__":
    unittest.main()
