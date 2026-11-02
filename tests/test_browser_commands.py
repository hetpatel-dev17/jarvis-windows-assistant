from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import browser_commands as browser


class BrowserCommandsTest(unittest.TestCase):
    def test_short_followups(self):
        for words in ['Play the first one','Start playing first video','Play first video S','Play number one']:
            tool,params=browser.parse(words)
            self.assertEqual(tool,'browser_control');self.assertEqual(params['action'],'first')
        self.assertEqual(browser.parse('Play it')[1]['action'],'play')
    def test_file_choices_keep_their_context(self):
        self.assertEqual(browser.parse('Open the first one','files'),('windows_operator',{'action':'open_match','target':'1'}))
        self.assertEqual(browser.parse('Open the first one','browser')[0],'browser_control')
    def test_site_names_and_urls(self):
        for name in ['Claude','Claudia','Google AI Studio','Google studios','Google Photos','example.org']:
            self.assertEqual(browser.parse('Open '+name)[1]['action'],'open')
        self.assertIsNone(browser.parse('Open Desktop'))
        self.assertIsNone(browser.parse('Open the PDF'))
    def test_search_and_play_intent(self):
        tool,params=browser.parse('Search Kishore Kumar on YouTube and play the first one')
        self.assertEqual(params,{'action':'search','target':'youtube','query':'Kishore Kumar','play':True})
        self.assertEqual(browser.parse('Play Kishore Kumar on YouTube')[1]['play'],True)
        self.assertEqual(browser.parse('Search YouTube for Kishore Kumar')[1]['query'],'Kishore Kumar')
        self.assertEqual(browser.parse('Search holiday in Google Photos')[1]['target'],'google photos')
        self.assertEqual(browser.parse('Search for holiday on it')[1],{'action':'search','query':'holiday'})
    def test_scroll_without_url_readout(self):
        self.assertEqual(browser.parse('Scroll down')[1]['direction'],'down')
        self.assertEqual(browser.parse('A little more')[1]['direction'],'down')
        self.assertEqual(browser.parse('Scroll up please')[1]['direction'],'up')
        self.assertIsNone(browser.parse('Tell me more about this idea'))

if __name__=='__main__':unittest.main()
