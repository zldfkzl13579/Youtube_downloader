import subprocess
import os
import shutil
import sys

class FFmpegHandler:
    def __init__(self):
        """
        시스템에 설치된 FFmpeg보다, 프로젝트 내부의 bin 폴더에 있는 FFmpeg를 우선적으로 사용합니다.
        """
        self.ffmpeg_path = self._find_ffmpeg_binary()
        self._check_ffmpeg()
    
    def _find_ffmpeg_binary(self) -> str | None:
        """FFmpeg 실행 파일의 경로를 찾습니다. (Dev / OneDir / OneFile 모두 호환)"""
        
        # 1. [OneFile 모드] 임시 폴더(_MEIPASS) 우선 확인
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller가 압축을 해제한 임시 경로
            base_path = sys._MEIPASS
            local_bin_path = os.path.join(base_path, 'bin', 'ffmpeg.exe')
            if os.path.exists(local_bin_path):
                return local_bin_path

        # 2. [OneDir 모드 / Dev 모드]
        if getattr(sys, 'frozen', False):
            # exe 파일 옆에 있는 bin 폴더
            base_path = os.path.dirname(sys.executable)
        else:
            # 파이썬 소스 코드 기준
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        local_bin_path = os.path.join(base_path, 'bin', 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg')

        if os.path.exists(local_bin_path):
            return local_bin_path

        # 3. 시스템 환경변수 확인
        if shutil.which("ffmpeg"):
            return "ffmpeg"

        return None

    def _check_ffmpeg(self):
        if not self.ffmpeg_path:
            # exe 실행 시 콘솔이 바로 꺼지는 것을 방지하기 위해 input() 추가 가능
            print("[Error] FFmpeg를 찾을 수 없습니다.")
            print(f"현재 실행 위치: {os.getcwd()}")
            print("해결법: 실행 파일과 같은 폴더에 'bin' 폴더를 두고 그 안에 ffmpeg.exe를 넣으세요.")
            return # 혹은 raise

    def process_media(self, input_files: list, output_path: str, options: dict):
        """
        입력된 미디어 파일들에 필터와 변환 옵션을 적용하여 최종 파일을 생성합니다.
        """
        if not self.ffmpeg_path:
            return False

        cmd = [self.ffmpeg_path, '-y']
        for f in input_files: cmd.extend(['-i', f])

        # --- 비디오 필터 및 코덱 설정 ---
        vf_filters = []

        # 1. Upscale (강제 확대) 로직
        if options.get('use_upscale') and options.get('height'):
            target_h = options['height']
            vf_filters.append(f"scale=-2:{target_h}:flags=lanczos")
            print(f"[Info] Video Upscale 적용: 높이 {target_h}p (Lanczos)")

        # 2. 비디오 코덱 및 필터 적용
        if vf_filters:
            cmd.extend(['-vf', ','.join(vf_filters)])
            v_codec = options.get('video_codec', 'libx264')
            cmd.extend(['-c:v', v_codec])
            
            if 'libx264' in v_codec or 'libx265' in v_codec:
                cmd.extend(['-pix_fmt', 'yuv420p'])
        else:
            if len(input_files) > 1 and not options.get('video_codec'):
                 cmd.extend(['-c:v', 'copy']) 
            elif options.get('video_codec'):
                 cmd.extend(['-c:v', options['video_codec']])

        # 3. 오디오 옵션 적용
        cmd.extend(self._build_audio_options(options))
        
        cmd.append(output_path)

        # 4. 실행
        print(f"[FFmpeg] 처리 시작: {output_path}")
        
        try:
            # subprocess 실행 시 콘솔 창 숨기기 (윈도우용) - 선택 사항
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            subprocess.run(cmd, check=True, stderr=subprocess.PIPE, startupinfo=startupinfo)
            print("[FFmpeg] 변환 성공!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[Error] FFmpeg 변환 실패: {e.stderr.decode('utf-8', errors='replace')}")
            return False

    def _build_audio_options(self, options: dict) -> list:
        cmds = []
        ext = options.get('ext', 'mp3')
        
        # --- A. 오디오 필터 (DSP) ---
        af_filters = []
        
        if options.get('use_enhance'):
            af_filters.append("crystalizer=i=2.0")
            print("[Info] DSP: Crystalizer 필터 적용됨")

        channels = options.get('audio_channels')
        if channels:
            mapping = {'1': '1', '2': '2', '5.1': '6', '7.1': '8'}
            if channels in mapping:
                cmds.extend(['-ac', mapping[channels]])

        if af_filters:
            cmds.extend(['-af', ','.join(af_filters)])

        # --- B. 충돌 우선순위 로직 ---
        is_lossless = ext in ['wav', 'flac', 'alac', 'aiff']
        
        if is_lossless:
            if options.get('sample_rate'):
                cmds.extend(['-ar', str(options['sample_rate'])])
            
            if options.get('bit_depth'):
                if ext == 'wav':
                    depth_map = {24: 'pcm_s24le', 16: 'pcm_s16le', 32: 'pcm_s32le'}
                    if options['bit_depth'] in depth_map:
                        cmds.extend(['-c:a', depth_map[options['bit_depth']]])
        else:
            if options.get('audio_bitrate'):
                cmds.extend(['-b:a', f"{options['audio_bitrate']}k"])
            
            if options.get('sample_rate'):
                cmds.extend(['-ar', str(options['sample_rate'])])

        return cmds