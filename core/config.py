import json
import os
from ui.logger import Logger

CONFIG_FILE = 'settings.json'

DEFAULT_CONFIG = {
    'default_output_dir': os.path.join(os.path.expanduser('~'), 'Downloads'),
    'max_retries': 3,
    'max_workers': 3,
    'presets': {
        "FHD 60fps (MP4)": "1080p 60fps mp4",
        "High Quality Audio": "mp3 BR_320k",
        "Archive (MKV Best)": "bestQuality mkv"
    }
}

class ConfigManager:
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.config.update(loaded)
                    if 'presets' not in self.config:
                        self.config['presets'] = DEFAULT_CONFIG['presets']
            except Exception as e:
                Logger.warning(f"설정 로드 중 오류: {e}")

    def save(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            Logger.error(f"설정 저장 실패: {e}")

    # --- 기본 설정 Getter/Setter ---
    def get(self, key):
        return self.config.get(key, DEFAULT_CONFIG.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save()

    # --- 프리셋 관리 (CRUD) ---
    def get_presets(self):
        return self.config.get('presets', {})

    def add_preset(self, name, command):
        """프리셋 생성"""
        self.config.setdefault('presets', {})
        self.config['presets'][name] = command
        self.save()

    def delete_preset(self, name):
        """프리셋 삭제"""
        presets = self.config.get('presets', {})
        if name in presets:
            del presets[name]
            self.save()

    def update_preset(self, old_name, new_name, new_command):
        """프리셋 수정 (이름 변경 포함)"""
        presets = self.config.get('presets', {})
        # 이름이 바뀌었다면 기존 키 삭제 후 재생성
        if old_name in presets:
            if old_name != new_name:
                del presets[old_name]
            presets[new_name] = new_command
            self.save()