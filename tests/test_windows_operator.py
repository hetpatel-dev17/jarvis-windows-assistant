import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from windows_operator import WindowsOperator,score
import command_routes


class WindowsFilesTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        (self.root/'Engineering').mkdir()
        (self.root/'Engineering'/'Hardware Roadmap.pdf').write_bytes(b'fixture')
        (self.root/'Engineering'/'Software Roadmap.txt').write_text('fixture')
        (self.root/'Summer song.mp3').write_bytes(b'fixture')
        (self.root/'api-key.txt').write_text('NOT A REAL KEY')
        (self.root/'program.exe').write_bytes(b'fixture')
        self.opened=[]
        self.operator=WindowsOperator({'Desktop':self.root},self.opened.append)
    def tearDown(self):self.temp.cleanup()
    def test_fragment_and_typo_are_ranked(self):
        result=self.operator.search('hardwre roadmap','Desktop')
        self.assertEqual(result['matches'][0]['name'],'Hardware Roadmap.pdf')
        self.assertEqual(self.opened,[])
    def test_search_ambiguity_requires_a_chosen_result(self):
        result=self.operator.search('roadmap','Desktop')
        self.assertEqual(len(result['matches']),2)
        self.assertEqual(self.opened,[])
        chosen=result['matches'][0]
        self.operator.control('open_match',match_id=chosen['id'])
        self.assertEqual(self.opened,[chosen['path']])
    def test_stale_result_cannot_open(self):
        old=self.operator.search('roadmap','Desktop')['matches'][0]['id']
        self.operator.search('song','Desktop')
        with self.assertRaises(ValueError):self.operator.control('open_match',match_id=old)
        self.assertEqual(self.opened,[])
    def test_deleted_match_is_rechecked(self):
        match=self.operator.search('song','Desktop')['matches'][0]
        Path(match['path']).unlink()
        with self.assertRaises(FileNotFoundError):self.operator.control('open_match',match_id=match['id'])
        self.assertEqual(self.opened,[])
    def test_documents_media_and_folders_open(self):
        for name in ['Engineering','Engineering/Hardware Roadmap.pdf','Summer song.mp3']:
            self.operator.open_path(self.root/name)
        self.assertEqual(len(self.opened),3)
    def test_private_paths_execution_and_traversal_blocked(self):
        for path in [self.root/'api-key.txt',self.root/'program.exe',self.root.parent]:
            with self.assertRaises(ValueError):self.operator.open_path(path)
        self.assertEqual(self.operator.search('api key','Desktop')['matches'],[])
        self.assertEqual(self.opened,[])
    def test_partial_search_is_not_reported_complete(self):
        result=self.operator.search('missing','Desktop',max_entries=1)
        self.assertTrue(result['partial'])
        self.assertIn('partial',result['message'])
    def test_cancel_does_not_open(self):
        with self.assertRaises(RuntimeError):self.operator.search('roadmap','Desktop',cancelled=lambda:True)
        self.assertEqual(self.opened,[])
    def test_user_phrases_reach_the_operator(self):
        for phrase,action in [('Find something like roadmap on Desktop','search'),('Look for hardwre roadmap in Documents','search'),('Open match one','open_match'),('Open folder Engineering','open'),('Open Downloads','open')]:
            result=command_routes.parse(phrase)
            self.assertEqual((result[0],result[1]['action']),('windows_operator',action),phrase)
        for phrase in ['Search Kishore Kumar on YouTube and play the first video','Ask ChatGPT: Find a file','Attach selected file to ChatGPT']:
            self.assertNotEqual(command_routes.parse(phrase)[0],'windows_operator')

if __name__=='__main__':unittest.main()
