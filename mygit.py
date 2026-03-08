#!/usr/bin/env python3
"""
MyGit - Git-система для Pydroid
"""

import os
import sys
import json
import base64
import hashlib
import requests
from datetime import datetime
from pathlib import Path

class MyGit:
    def __init__(self, repo_path):
        self.repo_path = Path(repo_path)
        self.git_dir = self.repo_path / ".mygit"
        self.remote_url = "https://api.github.com/repos/Komod88/sturdy-engine"
        
    def init(self):
        print("📦 Инициализация MyGit...")
        
        (self.git_dir / "commits").mkdir(parents=True, exist_ok=True)
        (self.git_dir / "objects").mkdir(parents=True, exist_ok=True)
        (self.git_dir / "refs" / "heads").mkdir(parents=True, exist_ok=True)
        
        index_path = self.git_dir / "index.json"
        if not index_path.exists():
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2, ensure_ascii=False)
            print("✅ index.json создан")
        
        head_path = self.git_dir / "HEAD"
        if not head_path.exists():
            with open(head_path, 'w', encoding='utf-8') as f:
                f.write("ref: refs/heads/main")
            print("✅ HEAD создан")
        
        config_path = self.git_dir / "config.json"
        if not config_path.exists():
            config = {
                "user": {
                    "name": "Komod88",
                    "email": "komod88@github.com"
                },
                "remote": {
                    "url": self.remote_url
                }
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print("✅ config.json создан")
        
        print("✅ MyGit инициализирован")
        return True
    
    def add(self, pattern="."):
        print("📝 Добавляю файлы...")
        
        files = []
        if pattern == ".":
            for root, dirs, filenames in os.walk(self.repo_path):
                if ".mygit" in dirs:
                    dirs.remove(".mygit")
                if "__pycache__" in dirs:
                    dirs.remove("__pycache__")
                for filename in filenames:
                    if filename.endswith('.pyc') or filename.startswith('.'):
                        continue
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, self.repo_path)
                    files.append(rel_path)
        
        index_path = self.git_dir / "index.json"
        with open(index_path, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        for rel_path in files:
            full_path = self.repo_path / rel_path
            if not full_path.exists():
                continue
            
            with open(full_path, 'rb') as f:
                content = f.read()
                file_hash = hashlib.sha256(content).hexdigest()
            
            found = False
            for item in index:
                if item["path"] == rel_path:
                    if item["hash"] != file_hash:
                        item["hash"] = file_hash
                        item["modified"] = datetime.now().isoformat()
                        print(f"✅ Обновлён: {rel_path}")
                    found = True
                    break
            
            if not found:
                index.append({
                    "path": rel_path,
                    "hash": file_hash,
                    "added": datetime.now().isoformat()
                })
                print(f"✅ Добавлен: {rel_path}")
        
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        
        return True
    
    def commit(self, message):
        print(f"💾 Создаю коммит: {message}")
        
        index_path = self.git_dir / "index.json"
        with open(index_path, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        if not index:
            print("⚠️ Нет файлов в индексе")
            return False
        
        config_path = self.git_dir / "config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        head_path = self.git_dir / "HEAD"
        with open(head_path, 'r', encoding='utf-8') as f:
            head_ref = f.read().strip().replace("ref: ", "")
        
        ref_path = self.git_dir / head_ref
        parent = None
        if ref_path.exists():
            with open(ref_path, 'r', encoding='utf-8') as f:
                parent = f.read().strip()
        
        now = datetime.now()
        commit_id = hashlib.sha256(f"{now}{message}".encode()).hexdigest()[:12]
        
        commit_data = {
            "id": commit_id,
            "message": message,
            "timestamp": now.isoformat(),
            "author": config["user"]["name"],
            "email": config["user"]["email"],
            "files": index,
            "parent": parent
        }
        
        commit_path = self.git_dir / "commits" / f"{commit_data['id']}.json"
        with open(commit_path, 'w', encoding='utf-8') as f:
            json.dump(commit_data, f, indent=2, ensure_ascii=False)
        
        with open(ref_path, 'w', encoding='utf-8') as f:
            f.write(commit_data['id'])
        
        print(f"✅ Коммит создан: {commit_data['id']}")
        return commit_data
    
    def push(self, token):
        print("📤 Отправляю на GitHub...")
        
        head_path = self.git_dir / "HEAD"
        with open(head_path, 'r', encoding='utf-8') as f:
            head_ref = f.read().strip().replace("ref: ", "")
        
        ref_path = self.git_dir / head_ref
        if not ref_path.exists():
            print("❌ Нет коммитов")
            return False
        
        with open(ref_path, 'r', encoding='utf-8') as f:
            last_commit_id = f.read().strip()
        
        commit_path = self.git_dir / "commits" / f"{last_commit_id}.json"
        with open(commit_path, 'r', encoding='utf-8') as f:
            commit = json.load(f)
        
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        success = 0
        for file_info in commit["files"]:
            file_path = self.repo_path / file_info["path"]
            if not file_path.exists():
                continue
            
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            
            url = f"https://api.github.com/repos/Komod88/sturdy-engine/contents/{file_info['path']}"
            
            check_response = requests.get(url, headers=headers)
            
            data = {
                "message": commit["message"],
                "content": content,
                "branch": "main"
            }
            
            if check_response.status_code == 200:
                data["sha"] = check_response.json()["sha"]
            
            try:
                response = requests.put(url, headers=headers, json=data)
                if response.status_code in [200, 201]:
                    print(f"✅ Отправлен: {file_info['path']}")
                    success += 1
                else:
                    print(f"❌ Ошибка {file_info['path']}: {response.status_code}")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
        
        print(f"✅ Отправлено {success} из {len(commit['files'])} файлов")
        return success > 0
