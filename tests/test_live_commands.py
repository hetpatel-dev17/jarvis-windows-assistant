import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from live_commands import candidate,next_command


class LiveCommandsTests(unittest.TestCase):
    def test_clear_media_and_navigation_need_no_send_marker(self):
        for text in ['open YouTube','Jarvis play the third video','skip this video','set volume to 10 percent','increase the volume to 100 percent','open Netflix','go back to Netflix','open Amazon']:
            with self.subTest(text=text):self.assertEqual(candidate(text)[0],'submit')
    def test_unfinished_and_long_drafts_stay_drafts(self):
        for text in ['open','search Kishore','set volume to','set volume to 1000 percent','I am thinking '+('about a project '*10000),'send hi to my friend','buy this product','delete all files']:
            self.assertIsNone(candidate(text))
    def test_search_needs_a_sentence_boundary(self):
        self.assertIsNone(candidate('search Kishore Kumar'))
        self.assertEqual(candidate('search Kishore Kumar.'),('submit','search Kishore Kumar on this website'))
    def test_preserves_next_sentence_in_order(self):
        text='Open YouTube. Search Kishore Kumar. Play the third video.'
        received=[]
        while text:
            action,command,end=next_command(text)
            received.append(command);text=text[end:]
        self.assertEqual(received,['Open YouTube','search Kishore Kumar on this website','Play the third video'])
    def test_sleep_does_not_become_windows_shutdown(self):
        self.assertEqual(candidate('Jarvis go to sleep'),('sleep',''))
        self.assertIsNone(candidate('shut down the computer'))
    def test_do_not_skip_unresolved_instruction(self):
        self.assertIsNone(next_command('I need help planning this. Open Amazon.'))
