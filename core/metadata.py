import yt_dlp
from urllib.parse import parse_qs, urlparse

class MetadataAnalyzer:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False, 
            'ignoreerrors': True,
            # [핵심 수정] 재생목록 URL이 섞여 있어도(Mix 등) 단일 영상만 빠르게 분석하도록 설정
            # 이 옵션이 없으면 yt-dlp가 전체 목록을 다운로드하려 시도해서 프로그램이 멈춥니다.
            'noplaylist': True, 
        }

    def get_video_info(self, url: str) -> dict:
        """
        URL을 받아 영상의 제목, 썸네일, 그리고 사용 가능한 포맷 리스트를 반환합니다.
        ('noplaylist=True' 설정 덕분에 멈추지 않고 즉시 결과를 반환합니다.)
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info: return None

                # [Case 1] 만약 순수 재생목록 URL이라서 playlist 타입으로 잡힌 경우
                # (noplaylist=True여도 playlist?list=... 형태는 리스트로 인식될 수 있음)
                if info.get('_type') == 'playlist' or 'entries' in info:
                    if 'entries' in info:
                        # 첫 번째 영상의 정보를 찾아서 반환 (옵션 선택용)
                        for entry in info['entries']:
                            if entry and 'formats' in entry:
                                return {
                                    'id': entry.get('id'),
                                    'title': entry.get('title'),
                                    '_type': 'video', # UI가 단일 영상처럼 처리하도록 video로 설정
                                    'thumbnail': entry.get('thumbnail'),
                                    'duration': entry.get('duration'),
                                    'formats': self._parse_formats(entry.get('formats', []))
                                }
                    return None

                # [Case 2] 일반적인 단일 영상 (대부분 여기로 옴)
                return {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    '_type': 'video',
                    'duration': info.get('duration'),
                    'thumbnail': info.get('thumbnail'),
                    'view_count': info.get('view_count'),
                    'formats': self._parse_formats(info.get('formats', []))
                }

        except Exception as e:
            # print(f"[Error] 메타데이터 분석 실패: {e}")
            return None

    def _parse_formats(self, raw_formats: list) -> dict:
        parsed = { 'video': [], 'audio': [] }

        for f in raw_formats:
            if not f.get('format_id') or not f.get('ext'): continue
            filesize = f.get('filesize') or f.get('filesize_approx') or 0

            # Audio Only
            if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                parsed['audio'].append({
                    'id': f['format_id'],
                    'ext': f['ext'],
                    'abr': f.get('abr', 0),
                    'codec': f.get('acodec'),
                    'asr': f.get('asr'),
                    'filesize': filesize
                })
            # Video
            elif f.get('vcodec') != 'none':
                if not f.get('height'): continue
                parsed['video'].append({
                    'id': f['format_id'],
                    'ext': f['ext'],
                    'res': f"{f.get('height')}p",
                    'fps': f.get('fps'),
                    'codec': f.get('vcodec'),
                    'vbr': f.get('vbr', 0),
                    'filesize': filesize,
                    'hdr': 'HDR' in f.get('dynamic_range', '') 
                })

        parsed['video'].sort(key=lambda x: (int(x['res'][:-1]), x['fps']), reverse=True)
        parsed['audio'].sort(key=lambda x: x['abr'] or 0, reverse=True)
        return parsed
    
    def get_playlist_items(self, url: str) -> list:
        """
        재생목록 URL을 받아 포함된 모든 영상의 정보(URL, 제목) 리스트를 반환합니다.
        (main.py에서 사용자가 전체 다운로드를 승인했을 때만 호출됩니다.)
        """
        try:
            parsed_url = urlparse(url)
            qs = parse_qs(parsed_url.query)
            
            target_url = url
            if 'list' in qs:
                playlist_id = qs['list'][0]
                target_url = f"https://www.youtube.com/playlist?list={playlist_id}"

            # 재생목록 추출용 별도 옵션 (noplaylist를 쓰면 안 됨)
            list_opts = {
                'extract_flat': True, 
                'quiet': True,
                'ignoreerrors': True,
            }
            
            with yt_dlp.YoutubeDL(list_opts) as ydl:
                info = ydl.extract_info(target_url, download=False)
                
                if not info: return []
                
                items = []
                if 'entries' in info:
                    for entry in info['entries']:
                        if not entry: continue

                        video_url = entry.get('url')
                        if not video_url and entry.get('id'):
                            video_url = f"https://www.youtube.com/watch?v={entry['id']}"

                        if video_url:
                            items.append({
                                'url': video_url,
                                'title': entry.get('title', 'Unknown')
                            })
                return items
                
        except Exception as e:
            print(f"[Error] 재생목록 추출 실패: {e}")
            return []