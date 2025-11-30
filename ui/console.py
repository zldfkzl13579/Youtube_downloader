import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn
from ui.logger import Logger

console = Console()

class ConsoleUI:
    """사용자 입력(Input)과 화면 출력(Output)을 전담하는 클래스"""

    # --- 1. 메인 메뉴 ---
    def show_main_menu(self):
        print("\n" + "="*50)
        print(" [ YouTube Downloader Pro ] - Main Menu")
        print("="*50 + "\n")
        
        return questionary.select(
            "원하는 작업을 선택하세요:",
            choices=[
                "1. 다운로드 시작 (Download)",
                "2. 상세 설정 (Settings & Presets)",
                "3. 프로그램 종료 (Exit)"
            ],
            use_indicator=True
        ).ask()

    # --- 2. 다운로드 관련 UI ---
    def ask_input_source(self):
        return questionary.text("URL 또는 파일 경로를 입력하세요 ('q' 취소):").ask()

    def ask_confirm(self, msg):
        return questionary.confirm(msg).ask()

    def show_video_info(self, info):
        if not info: return
        console.print(Panel(
            f"[bold white]{info.get('title')}[/bold white]\n[dim]길이: {info.get('duration')}초[/dim]",
            title="Target Info", border_style="blue"
        ))
        self._print_format_table(info.get('formats', {}))

    def _print_format_table(self, formats):
        v_table = Table(title="[Video]", show_header=True, header_style="bold magenta")
        v_table.add_column("ID", justify="center"); v_table.add_column("Res", style="green")
        v_table.add_column("FPS"); v_table.add_column("Codec", style="dim"); v_table.add_column("Ext", style="yellow")
        for f in formats.get('video', [])[:6]:
            v_table.add_row(f['id'], f['res'], str(f['fps']), f['codec'], f['ext'])
        
        a_table = Table(title="[Audio]", show_header=True, header_style="bold cyan")
        a_table.add_column("ID", justify="center"); a_table.add_column("Abr", style="green")
        a_table.add_column("Codec", style="dim"); a_table.add_column("Ext", style="yellow")
        for f in formats.get('audio', [])[:4]:
            a_table.add_row(f['id'], f"{f['abr']}k", f['codec'], f['ext'])

        console.print(v_table)
        console.print(a_table)
        console.print("")

    def ask_download_mode(self):
        return questionary.select(
            "다운로드 모드 선택:",
            choices=["Video (영상)", "Audio (오디오)", "Cancel (취소)"]
        ).ask()

    def ask_option_method(self, mode):
        return questionary.select(
            f"[{mode}] 옵션 선택 방식:",
            choices=["1. 키워드 직접 입력 (Custom)", "2. 프리셋 불러오기 (Preset)", "3. 뒤로 가기 (Back)"]
        ).ask()

    def ask_preset_select(self, presets):
        if not presets:
            Logger.warning("저장된 프리셋이 없습니다.")
            return None
        choices = list(presets.keys()) + ["<< Back"]
        choice = questionary.select("프리셋을 선택하세요:", choices=choices).ask()
        if choice == "<< Back": return None
        return choice

    def ask_custom_option(self, mode):
        Logger.ask(f"[{mode}] 옵션 키워드를 입력하세요. (도움말: '?help', 취소: 'b')")
        while True:
            val = questionary.text(">> ").ask()
            if not val: continue 
            
            if val == "?help":
                self._show_help_table(mode) # [Core Change] 모드 전달
                continue
            if val.lower() == 'b': 
                return None
            return val

    def confirm_options(self, options):
        # 보기 좋게 필터링해서 보여주기
        filtered = {k: v for k, v in options.items() if v}
        Logger.info(f"적용될 옵션 확인: {filtered}")
        
        choice = questionary.select(
            "이 설정으로 작업을 진행하시겠습니까?",
            choices=[
                "1. 네, 진행합니다 (Continue)",
                "2. 아니오, 옵션 수정 (Modify)",
                "3. 뒤로 가기 (Back)"
            ]
        ).ask()
        
        if not choice or "뒤로" in choice: return "BACK"
        if "네" in choice: return "CONTINUE"
        if "수정" in choice: return "MODIFY"
        return "BACK"

    def _show_help_table(self, mode):
        """[UX Upgrade] 모드에 따라 관련 키워드만 상세하게 표시"""
        is_video = (mode == 'video')
        title = f"[Keywords Reference for {mode.upper()}]"
        table = Table(title=title, border_style="green")
        
        table.add_column("Category", style="bold cyan", justify="left")
        table.add_column("Rule & Range", style="yellow")
        table.add_column("Supported Values / Examples", style="white")

        # 1. Video Specific
        if is_video:
            table.add_row("Resolution", "Number + 'p'", "4320p, 2160p, 1440p, 1080p, 720p, 480p, 360p...")
            table.add_row("Frame Rate", "Number + 'fps'", "60fps, 50fps, 30fps, 24fps")
            table.add_row("Video Codec", "Enum", "av1, vp9, h264, hevc(h265), prores, theora")
            table.add_row("Video Ext", "Enum", "mp4, mkv, webm, avi, mov, wmv, flv")
            table.add_row("Visual", "Flag", "hdr (HDR10), 444 (Chroma), upscale (AI/Lanczos)")
            table.add_section()

        # 2. Audio Specific
        table.add_row("Bitrate", "BR_ + Num + 'k'", "BR_320k ~ BR_64k (e.g. BR_192k, BR_256k)")
        table.add_row("Sample Rate", "SR_ + Num + 'k'", "SR_44.1k, SR_48k, SR_88.2k, SR_96k, SR_192k")
        if is_video:
            # 비디오 모드에서의 오디오 코덱은 컨테이너에 따라 제한됨
            table.add_row("Audio Codec", "Enum", "aac, opus, mp3, flac (Video container dependent)")
        else:
            # 오디오 전용 모드
            table.add_row("Audio Ext", "Enum", "mp3, flac, wav, m4a, aac, opus, ogg, alac, aiff")
            table.add_row("Audio Codec", "Enum", "mp3, aac, flac, opus, vorbis, alac, pcm")
            table.add_row("Bit Depth", "Number + 'bit'", "16bit, 24bit, 32bit (flac/wav only)")
            table.add_row("Channels", "Enum", "mono, stereo, 5.1, 7.1")
            table.add_row("DSP", "Flag", "enhance (Crystalizer Filter)")

        table.add_section()

        # 3. Common
        table.add_row("General", "Flag", "original (No Convert), bestQuality (Auto)")
        table.add_row("Extras", "Flag", "sub (Subtitle), thumb (Thumbnail), meta (Metadata)")

        console.print(table)
        console.print("[dim]※ Space separated (e.g. '1080p 60fps av1' or 'mp3 BR_320k enhance')[/dim]\n")

    # --- 3. 설정 관련 UI ---
    def show_settings_menu(self):
        print("\n[ 상세 설정 메뉴 ]")
        return questionary.select(
            "설정할 항목:",
            choices=[
                "1. 저장 디렉토리 변경",
                "2. 최대 동시 작업 수 변경",
                "3. 프리셋 관리 (Presets)",
                "4. 메인 메뉴로 돌아가기"
            ]
        ).ask()

    def show_preset_manager(self):
        return questionary.select(
            "프리셋 관리:",
            choices=[
                "1. 프리셋 조회 (List)",
                "2. 프리셋 생성 (Create)",
                "3. 프리셋 수정 (Edit)",
                "4. 프리셋 삭제 (Delete)",
                "5. 뒤로 가기"
            ]
        ).ask()

    def ask_settings_directory(self, current):
        console.print(f"[dim]현재 경로: {current}[/dim]")
        path = questionary.path("새 저장 경로 (취소하려면 엔터):").ask()
        return path if path and path.strip() else None

    def ask_settings_workers(self, current):
        console.print(f"[dim]현재 작업 수: {current}[/dim]")
        val = questionary.text("최대 동시 작업 수 (1~8) (취소: 'b'):").ask()
        if not val or val.lower() == 'b': return None
        return val

    def ask_preset_name(self):
        val = questionary.text("새 프리셋 이름 (취소: 'b'):").ask()
        if not val or val.lower() == 'b': return None
        return val

    def ask_preset_command(self):
        Logger.ask("옵션 키워드를 입력하세요. (도움말: '?help', 취소: 'b')")
        while True:
            val = questionary.text(">> ").ask()
            if not val: continue
            
            # [Tip] 프리셋 생성 시에는 모드를 알 수 없으므로 전체(비디오 기준) 도움말을 보여줌
            if val == "?help":
                self._show_help_table('video') 
                continue
            if val.lower() == 'b': 
                return None
            return val

    def ask_select(self, msg, choices): return questionary.select(msg, choices=choices).ask()

    def get_progress_bar(self):
        return Progress(
            SpinnerColumn(), TextColumn("[bold blue]{task.fields[filename]}"), BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%", DownloadColumn(), TransferSpeedColumn(),
            console=console
        )