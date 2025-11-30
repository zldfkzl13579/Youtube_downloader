import os
import sys
import shlex
import subprocess
import pyperclip
from ui.logger import Logger

def open_file_explorer(path):
    """OS에 맞는 파일 탐색기를 엽니다."""
    if not os.path.exists(path):
        return
    try:
        if os.name == 'nt': os.startfile(path)
        elif sys.platform == 'darwin': subprocess.run(['open', path])
        else: subprocess.run(['xdg-open', path])
        Logger.info(f"폴더를 열었습니다: {path}")
    except Exception as e:
        Logger.warning(f"폴더 열기 실패: {e}")

def get_clipboard_url():
    """클립보드에서 유튜브 링크 감지"""
    try:
        content = pyperclip.paste().strip()
        if content.startswith('http') and ('youtube.com' in content or 'youtu.be' in content):
            return content
    except:
        pass
    return None

def parse_input_string(input_str: str) -> list:
    """사용자 입력 문자열(URL 또는 파일 경로)을 파싱하여 작업 목록 반환"""
    if not input_str: return []
    
    try:
        # Windows 경로의 백슬래시 처리를 위해 posix=False 설정
        is_posix = (os.name != 'nt')
        items = shlex.split(input_str, posix=is_posix)
    except:
        items = input_str.split()

    tasks = []
    for item in items:
        item = item.strip('"').strip("'")
        
        # 1. 파일인 경우
        if os.path.isfile(item):
            try:
                group_name = os.path.splitext(os.path.basename(item))[0]
                with open(item, 'r', encoding='utf-8') as f:
                    urls = [line.strip() for line in f.readlines() if line.strip()]
                if urls:
                    tasks.append({'source': 'file', 'group_name': group_name, 'urls': urls})
                    Logger.info(f"파일 로드: {group_name} ({len(urls)}개)")
            except Exception as e:
                Logger.error(f"파일 읽기 실패: {e}")
        
        # 2. URL인 경우
        elif item.startswith('http'):
            tasks.append({'source': 'arg', 'group_name': None, 'urls': [item]})
            
    return tasks