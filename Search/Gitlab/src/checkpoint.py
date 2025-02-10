import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

class CheckpointService:
    def __init__(self):
        self.file = Path('checkpoints/progress.json')
        self.file.parent.mkdir(exist_ok=True)
        self._data = self._load()
        
    def _load(self) -> Dict[str, Any]:
        if self.file.exists():
            with open(self.file, 'r') as f:
                return json.load(f)
        return {'projects': {}, 'last_update': None}
    
    def save(self):
        # Converte sets para listas antes de salvar
        data_to_save = {
            'projects': {},
            'last_update': datetime.now().isoformat()
        }
        
        for project_id, project_data in self._data['projects'].items():
            data_to_save['projects'][project_id] = {
                'completed': project_data.get('completed', False),
                'branches': {}
            }
            
            for branch_name, branch_data in project_data.get('branches', {}).items():
                data_to_save['projects'][project_id]['branches'][branch_name] = {
                    'completed': branch_data.get('completed', False),
                    'files': list(branch_data.get('files', set()))
                }
        
        with open(self.file, 'w') as f:
            json.dump(data_to_save, f)
    
    def is_project_completed(self, project_id: str) -> bool:
        return str(project_id) in self._data['projects'] and \
               self._data['projects'][str(project_id)].get('completed', False)
    
    def is_branch_completed(self, project_id: str, branch: str) -> bool:
        project = self._data['projects'].get(str(project_id), {})
        branches = project.get('branches', {})
        return branch in branches and branches[branch].get('completed', False)
    
    def is_file_completed(self, project_id: str, branch: str, file_path: str) -> bool:
        project = self._data['projects'].get(str(project_id), {})
        branches = project.get('branches', {})
        branch_data = branches.get(branch, {})
        files = branch_data.get('files', set())
        return file_path in files
    
    def mark_project_completed(self, project_id: str):
        project_id = str(project_id)
        if project_id not in self._data['projects']:
            self._data['projects'][project_id] = {'branches': {}}
        self._data['projects'][project_id]['completed'] = True
        self.save()
    
    def mark_branch_completed(self, project_id: str, branch: str):
        project_id = str(project_id)
        if project_id not in self._data['projects']:
            self._data['projects'][project_id] = {'branches': {}}
        if 'branches' not in self._data['projects'][project_id]:
            self._data['projects'][project_id]['branches'] = {}
        if branch not in self._data['projects'][project_id]['branches']:
            self._data['projects'][project_id]['branches'][branch] = {'files': set()}
        self._data['projects'][project_id]['branches'][branch]['completed'] = True
        self.save()
    
    def mark_file_completed(self, project_id: str, branch: str, file_path: str):
        project_id = str(project_id)
        if project_id not in self._data['projects']:
            self._data['projects'][project_id] = {'branches': {}}
        if 'branches' not in self._data['projects'][project_id]:
            self._data['projects'][project_id]['branches'] = {}
        if branch not in self._data['projects'][project_id]['branches']:
            self._data['projects'][project_id]['branches'][branch] = {'files': set()}
        if 'files' not in self._data['projects'][project_id]['branches'][branch]:
            self._data['projects'][project_id]['branches'][branch]['files'] = set()
        self._data['projects'][project_id]['branches'][branch]['files'].add(file_path)