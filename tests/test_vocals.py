import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from wake_listener import WakeListener, strip_wake, is_greeting, PREFIX


class VocalsTests(unittest.TestCase):
    def test_wake_is_a_prefix_not_room_speech(self):
        self.assertEqual(strip_wake('Hey Jarvis, open YouTube'),'open YouTube')
        self.assertEqual(strip_wake('hello jarvis'),'')
        self.assertIsNone(PREFIX.match('I was talking about Jarvis yesterday'))
        self.assertFalse(is_greeting('open YouTube'))
        self.assertTrue(is_greeting("what's up"))

    def test_microphone_is_not_started_by_import_or_settings(self):
        with tempfile.TemporaryDirectory() as folder:
            listener=WakeListener(lambda _:None,lambda *_:'',None,data_dir=folder)
            self.assertFalse(listener.status()['enabled'])
            self.assertIsNone(listener.thread)
            self.assertEqual(listener.stop()['phase'],'off')
            with self.assertRaises(ValueError):listener.start()
