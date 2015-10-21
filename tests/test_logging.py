
import asynctest

from ats.util import logging


class LoggingTest(asynctest.TestCase):
    async def test_defaults(self):
        logging.setup_logging({'log': {'jsonformat': True}})
        logging.setup_logging({'log': {'jsonformat': False}})
