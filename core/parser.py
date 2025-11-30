import re

def parse_quality_string(input_str: str) -> dict:
    """
    사용자 입력 문자열을 파싱하여 옵션 딕셔너리로 변환합니다.
    FFmpeg 지원 포맷을 대폭 확장하여 지원합니다.
    """
    options = {
        # Video
        'height': None,
        'fps': None,
        'video_codec': None,
        'hdr': False,
        'chroma_subsampling': None,
        
        # Audio
        'audio_bitrate': None,
        'sample_rate': None,
        'bit_depth': None,
        'audio_channels': None,
        'audio_codec': None,
        
        # Common
        'ext': None,
        'use_enhance': False,
        'subtitles': False,
        'thumbnail': False,
        'metadata': False,
        'use_original': False,
        'use_best_quality': False,
        'use_upscale': False,
    }
    
    if not input_str:
        return options

    tokens = input_str.lower().split()
    
    # 확장 목록 정의
    VIDEO_EXTS = ['mp4', 'mkv', 'webm', 'avi', 'mov', 'wmv', 'flv', '3gp', 'ts', 'ogv', 'mpg']
    AUDIO_EXTS = ['mp3', 'm4a', 'flac', 'wav', 'aac', 'opus', 'ogg', 'wma', 'alac', 'aiff', 'pcm']
    
    VIDEO_CODECS = ['av1', 'vp9', 'vp8', 'h264', 'h265', 'hevc', 'prores', 'theora', 'mpeg4']
    AUDIO_CODECS = ['aac', 'opus', 'vorbis', 'mp3', 'flac', 'alac', 'pcm', 'ac3', 'eac3']

    for token in tokens:
        # [Video] Resolution (144p ~ 8k)
        if match := re.match(r'^(\d{3,4})p$', token):
            options['height'] = int(match.group(1))
            continue
            
        # [Video] FPS (Usually 24~144)
        if match := re.match(r'^(\d{2,3})fps$', token):
            options['fps'] = int(match.group(1))
            continue
            
        # [Video] Advanced
        if token == 'hdr':
            options['hdr'] = True; continue
        if token in ['444', '4:4:4']:
            options['chroma_subsampling'] = '4:4:4'; continue
            
        # [Audio] Bitrate (BR_64k ~ BR_1000k)
        if match := re.match(r'^br_(\d+)k$', token):
            options['audio_bitrate'] = int(match.group(1))
            continue

        # [Audio] Sample Rate (SR_8k ~ SR_192k)
        if match := re.match(r'^sr_([\d.]+)k$', token):
            val = float(match.group(1))
            options['sample_rate'] = int(val * 1000)
            continue
            
        # [Audio] Bit Depth (8bit ~ 64bit)
        if match := re.match(r'^(\d+)bit$', token):
            options['bit_depth'] = int(match.group(1))
            continue

        # [Audio] Channels
        if token in ['mono', '1ch']: options['audio_channels'] = '1'
        elif token in ['stereo', '2ch']: options['audio_channels'] = '2'
        elif token in ['5.1', 'surround']: options['audio_channels'] = '5.1'
        elif token == '7.1': options['audio_channels'] = '7.1'
        
        # [Format & Codec]
        elif token in VIDEO_EXTS + AUDIO_EXTS:
            options['ext'] = token
        elif token in VIDEO_CODECS:
            options['video_codec'] = token
        elif token in AUDIO_CODECS:
            options['audio_codec'] = token
            
        # [Flags]
        elif token in ['original', 'copy']: options['use_original'] = True
        elif token in ['best', 'bestquality']: options['use_best_quality'] = True
        elif token == 'upscale': options['use_upscale'] = True
        elif token == 'enhance': options['use_enhance'] = True
        elif token == 'sub': options['subtitles'] = True
        elif token == 'thumb': options['thumbnail'] = True
        elif token == 'meta': options['metadata'] = True

    return options