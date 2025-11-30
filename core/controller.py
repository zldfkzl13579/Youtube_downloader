import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.metadata import MetadataAnalyzer
from core.parser import parse_quality_string
from core.downloader import Downloader
from core.config import ConfigManager
from ui.console import ConsoleUI
from ui.logger import Logger
from utils.system import get_clipboard_url, parse_input_string, open_file_explorer

class AppController:
    def __init__(self):
        self.config = ConfigManager()
        self.ui = ConsoleUI()
        self.analyzer = MetadataAnalyzer()
        self.downloader = Downloader()

    def run(self):
        """메인 루프"""
        while True:
            choice = self.ui.show_main_menu()
            
            if not choice or "Exit" in choice:
                Logger.info("프로그램을 종료합니다.")
                sys.exit(0)
                
            elif "Download" in choice:
                self._flow_download()
                
            elif "Settings" in choice:
                self._flow_settings()

    # =========================================================
    # 1. 다운로드 워크플로우
    # =========================================================
    def _flow_download(self):
        while True:
            # 1-1. 입력
            clip_url = get_clipboard_url()
            input_str = None
            if clip_url:
                print(f"[Smart] 클립보드 링크 감지: {clip_url}")
                if self.ui.ask_confirm("이 링크를 다운로드하시겠습니까?"):
                    input_str = clip_url
            
            if not input_str:
                input_str = self.ui.ask_input_source()

            if not input_str or input_str.lower() == 'q': break

            # 1-2. 분석
            tasks = parse_input_string(input_str)
            if not tasks: continue

            final_queue_items = self._prepare_download_items(tasks)
            if not final_queue_items: continue 

            first_url = final_queue_items[0]['url']
            Logger.info("영상 분석 중...")
            meta = self.analyzer.get_video_info(first_url)
            if not meta:
                Logger.error("분석 실패. URL을 확인하세요.")
                continue
            
            self.ui.show_video_info(meta)

            # 1-3. 모드 및 옵션
            mode_choice = self.ui.ask_download_mode()
            if not mode_choice or "Cancel" in mode_choice: continue

            target_mode = "video" if "Video" in mode_choice else "audio"
            final_options = self._subflow_select_options(target_mode)
            
            if not final_options: continue 

            # 1-4. 실행
            self._execute_download(final_queue_items, final_options)

            # 1-5. 완료
            print("-" * 40)
            next_action = self.ui.ask_select("다음 작업:", ["1. 다른 영상 다운로드", "2. 메인 메뉴로"])
            if "메인" in next_action: break

    def _prepare_download_items(self, tasks):
        queue_items = []
        base_dir = self.config.get('default_output_dir')

        for group in tasks:
            save_path = base_dir
            if group['source'] == 'file':
                save_path = os.path.join(base_dir, group['group_name'])
            
            for url in group['urls']:
                if 'list=' in url and group['source'] == 'arg':
                    Logger.ask(f"재생목록 링크 감지: {url}")
                    
                    if self.ui.ask_confirm("전체 목록을 다운로드하시겠습니까?"):
                        Logger.info("목록 정보를 가져오는 중...")
                        items = self.analyzer.get_playlist_items(url)
                        if items:
                            pl_path = os.path.join(save_path, "Playlist_Download")
                            for item in items:
                                queue_items.append({'url': item['url'], 'path': pl_path, 'flags': {}})
                            continue
                        else:
                            Logger.warning("목록을 가져오지 못해 단일 영상으로 처리합니다.")
                    else:
                        queue_items.append({'url': url, 'path': save_path, 'flags': {'noplaylist': True}})
                        continue
                
                queue_items.append({'url': url, 'path': save_path, 'flags': {}})
        
        return queue_items

    def _subflow_select_options(self, mode):
        """옵션 선택 -> 파싱 -> [제한] -> 확인"""
        while True:
            # A. 방식 선택
            method = self.ui.ask_option_method(mode)
            input_str = None

            if not method or "Back" in method: return None

            # B. 입력
            if "Custom" in method:
                input_str = self.ui.ask_custom_option(mode)
            elif "Preset" in method:
                presets = self.config.get_presets()
                p_name = self.ui.ask_preset_select(presets)
                if p_name:
                    input_str = presets[p_name]
                    Logger.info(f"프리셋 '{p_name}' 로드됨")
            
            if not input_str: continue 

            # C. 파싱
            options = parse_quality_string(input_str)

            # [Logic] Audio 모드일 때 Video 옵션 강제 제거 및 경고
            if mode == 'audio':
                blocked_keys = ['height', 'fps', 'video_codec', 'hdr', 'chroma_subsampling']
                removed = []
                for key in blocked_keys:
                    if options.get(key):
                        removed.append(key)
                        options[key] = None
                
                # 비디오 전용 확장자가 들어왔을 경우 오디오로 변경하지 않고 경고만 (사용자 의도일 수 있음)
                # 하지만 보통은 mp3 등으로 변환을 원하므로, 
                # ext가 비디오 확장자(mp4, mkv 등)라면 None으로 초기화하여 default audio format을 쓰게 유도할 수 있음.
                # 여기서는 명시적인 옵션만 지움.
                
                if removed:
                    Logger.warning(f"[Auto-Correction] 오디오 모드이므로 다음 비디오 설정이 무시되었습니다: {removed}")

            # D. 확인
            confirm_action = self.ui.confirm_options(options)
            
            if confirm_action == "CONTINUE": return options
            elif confirm_action == "MODIFY": continue
            elif confirm_action == "BACK": return None

    def _execute_download(self, queue_items, global_options):
        if not queue_items: return
        max_workers = self.config.get('max_workers')
        
        with self.ui.get_progress_bar() as progress:
            total_task = progress.add_task("[magenta]Total", total=len(queue_items), filename="Batch Processing")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}
                for item in queue_items:
                    final_item_opts = global_options.copy()
                    if item.get('flags'):
                        final_item_opts.update(item['flags'])

                    tid = progress.add_task("Waiting...", total=100, filename="Pending")
                    
                    def mk_cb(t):
                        def cb(d):
                            if d['status']=='downloading':
                                progress.update(t, description="[cyan]DL", completed=d.get('percent',0), filename=d.get('filename','Downloading...'))
                            elif d['status']=='finished':
                                progress.update(t, description="[green]Conv", completed=100)
                        return cb
                    
                    if not os.path.exists(item['path']):
                        os.makedirs(item['path'])

                    fut = executor.submit(
                        self.downloader.download, 
                        [item['url']], item['path'], final_item_opts, mk_cb(tid)
                    )
                    futures[fut] = tid
                
                for fut in as_completed(futures):
                    tid = futures[fut]
                    try:
                        res = fut.result()
                        progress.update(tid, description="[bold green]Done")
                    except Exception as e:
                        progress.update(tid, description="[bold red]Error", filename="System Error")
                    progress.advance(total_task)
        
        Logger.success("다운로드 작업 완료!")
        last_dir = queue_items[-1]['path'] if queue_items else self.config.get('default_output_dir')
        if self.ui.ask_confirm("폴더를 여시겠습니까?"):
            open_file_explorer(last_dir)

    # =========================================================
    # 2. 설정 워크플로우
    # =========================================================
    def _flow_settings(self):
        while True:
            choice = self.ui.show_settings_menu()
            if not choice or "돌아가기" in choice: break

            if "디렉토리" in choice:
                curr = self.config.get('default_output_dir')
                new_path = self.ui.ask_settings_directory(curr)
                if new_path:
                    self.config.set('default_output_dir', new_path)
                    Logger.success("저장되었습니다.")

            elif "작업 수" in choice:
                curr = self.config.get('max_workers')
                val = self.ui.ask_settings_workers(curr)
                if val and val.isdigit():
                    self.config.set('max_workers', int(val))
                    Logger.success("저장되었습니다.")

            elif "프리셋" in choice:
                self._subflow_manage_presets()

    def _subflow_manage_presets(self):
        while True:
            action = self.ui.show_preset_manager()
            presets = self.config.get_presets()

            if not action or "뒤로" in action: break

            if "조회" in action:
                print("\n[ Preset List ]")
                for k, v in presets.items(): print(f" - {k} : {v}")
                print("")

            elif "생성" in action:
                name = self.ui.ask_preset_name()
                if not name: continue
                cmd = self.ui.ask_preset_command()
                if not cmd: continue
                
                self.config.add_preset(name, cmd)
                Logger.success(f"프리셋 '{name}' 생성됨.")

            elif "삭제" in action:
                target = self.ui.ask_preset_select(presets)
                if target:
                    self.config.delete_preset(target)
                    Logger.success("삭제되었습니다.")

            elif "수정" in action:
                target = self.ui.ask_preset_select(presets)
                if target:
                    name = self.ui.ask_preset_name() or target
                    cmd = self.ui.ask_preset_command() or presets[target]
                    self.config.update_preset(target, name, cmd)
                    Logger.success("수정되었습니다.")