import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from wake_listener import WakeListener, strip_wake, is_greeting, PREFIX
from windows_dictation import interpret


class VocalsTests(unittest.TestCase):
    def test_windows_dictation_waits_for_explicit_marker(self):
        self.assertEqual(interpret('Open YouTube. Run task.'),('submit','Open YouTube'))
        self.assertEqual(interpret('A long question with several pauses.'),('draft','A long question with several pauses.'))
        self.assertEqual(interpret('Run task.'),('draft','Run task.'))
        self.assertEqual(interpret('Go to sleep.'),('sleep',''))
        self.assertEqual(interpret('Tell him to go to sleep')[0],'draft')
    def test_windows_session_has_no_conversation_timeout(self):
        with tempfile.TemporaryDirectory() as folder:
            listener=WakeListener(lambda _:self.fail('No task expected'),lambda *_:self.fail('No transcription expected'),None,data_dir=folder)
            self.assertEqual(listener.mode,'windows')
            self.assertTrue(listener.activate()['awake'])
            sequence=listener.status()['wake_sequence']
            self.assertTrue(listener.status()['awake'])
            self.assertFalse(listener.sleep()['awake'])
            self.assertEqual(listener.status()['wake_sequence'],sequence)
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
