from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from skill_registry import SkillRegistry


class SkillRegistryTest(unittest.TestCase):
    def setUp(self):self.skills=SkillRegistry()
    def test_all_requested_skills_have_instructions(self):
        entries=self.skills.listing()
        self.assertEqual([x['id'] for x in entries],['browser-automation','chatgpt','claude','arduino-cli','multimedia-operation','esp-idf','jarvis-vocals'])
        for entry in entries:
            loaded=self.skills.load(entry['id'])
            self.assertTrue(loaded['instructions'].startswith('---\n'))
    def test_hardware_pipelines_have_no_active_execution_tools(self):
        for name in ['arduino-cli','esp-idf']:
            entry=self.skills.load(name)
            self.assertFalse(entry['enabled']);self.assertEqual(entry['tools'],[])
            self.assertIn('no active execution tools',self.skills.guidance(name))
    def test_arbitrary_file_cannot_be_loaded_as_a_skill(self):
        for name in ['../key_store.py','../../secrets','unknown']:
            with self.assertRaises(ValueError):self.skills.load(name)
    def test_browser_guidance_is_available_to_the_agent(self):
        text=self.skills.guidance('browser-automation')
        self.assertIn('current snapshot',text)
        self.assertIn('uncertain send',text)

if __name__=='__main__':unittest.main()
