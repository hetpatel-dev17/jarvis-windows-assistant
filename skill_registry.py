"""Project-owned Jarvis skills, with explicit enabled and verification states."""
from pathlib import Path
import json,re


class SkillRegistry:
    def __init__(self,root=None):
        self.root=Path(root or Path(__file__).resolve().parent/'skills').resolve()
        data=json.loads((self.root/'catalog.json').read_text(encoding='utf-8'))
        self.order=data['development_order'];self.entries={item['id']:item for item in data['skills']}
        if len(self.entries)!=len(self.order) or set(self.entries)!=set(self.order):raise ValueError('Skill catalog order does not match its entries.')
        for key in self.order:
            if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',key):raise ValueError('Invalid skill identifier.')
            if not (self.root/key/'SKILL.md').is_file():raise ValueError('Skill instructions are missing: '+key)
    def listing(self):return [dict(self.entries[key],order=i) for i,key in enumerate(self.order,1)]
    def load(self,name):
        if name not in self.entries:raise ValueError('Choose a skill from the catalog.')
        item=dict(self.entries[name])
        item['instructions']=(self.root/name/'SKILL.md').read_text(encoding='utf-8')
        item['message']=item['name']+': '+item['status']+'. '+item['verification']
        return item
    def guidance(self,name):
        item=self.load(name)
        return item['instructions'] if item['enabled'] else item['message']+' This skill has no active execution tools.'
    def control(self,action,name=''):
        if action=='list':return {'status':'ok','skills':self.listing(),'message':'Browser automation is first. Skills: '+', '.join(item['name']+' ('+item['status']+')' for item in self.listing())+'.'}
        if action=='load':return {'status':'ok',**self.load(name)}
        raise ValueError('Unknown skills action.')
