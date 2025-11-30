# 📺 Python YouTube Downloader Pro (CLI)

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)
![FFmpeg](https://img.shields.io/badge/Dependency-FFmpeg-007808?logo=ffmpeg&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

> **강력한 성능, 섬세한 제어, 완벽한 사용자 경험.**
>
> 단순한 다운로더가 아닙니다. **MVC 패턴**으로 구조화된 전문가용 유튜브 다운로더입니다.
> 4K/8K 초고화질, 무손실 오디오 추출, DSP 음질 향상은 물론, **프리셋 관리**와 **스마트 클립보드 감지** 기능으로 반복 작업을 획기적으로 줄여줍니다.

---

## ✨ 주요 기능 (Key Features)

| 카테고리 | 기능 설명 |
| :--- | :--- |
| **🚀 워크플로우** | **스마트 감지**: 클립보드에 유튜브 링크가 있으면 자동으로 인식하여 다운로드를 제안합니다.<br>**무한 루프**: 프로그램 종료 없이 연속적으로 여러 작업을 수행할 수 있습니다.<br>**네비게이션**: 작업 도중 언제든지 `뒤로 가기`, `취소`, `설정 변경`이 가능합니다. |
| **⚙️ 설정 관리** | **프리셋(Preset)**: 자주 쓰는 복잡한 옵션(예: 4K+AV1+자막)을 저장해두고 1초 만에 불러오세요.<br>**환경 설정**: 저장 경로, 동시 작업 수(스레드) 등을 앱 내부 메뉴에서 바로 변경합니다. |
| **📺 화질/음질** | **초고화질**: 8K/4K 해상도, 60fps, **AV1/VP9 코덱** 완벽 지원.<br>**Audiophile**: `Crystalizer` DSP 필터 및 FLAC/WAV 무손실 변환 지원.<br>**Upscaling**: 저화질 영상을 `Lanczos` 알고리즘으로 업스케일링합니다. |
| **📂 편의성** | **자동 분류**: 재생목록(Playlist) 감지 시 전용 폴더를 생성하여 정리합니다.<br>**폴더 열기**: 다운로드가 끝나면 바로 탐색기를 열어 파일을 확인할 수 있습니다. |

---

## 🛠 시스템 구성 (Architecture)

이 프로젝트는 유지보수와 확장성을 위해 **MVC (Model-View-Controller)** 패턴을 따릅니다.

```text
YouTubeDownloader/
├── bin/                 # FFmpeg 바이너리 폴더
├── core/                # [Model & Controller]
│   ├── controller.py    # 전체 흐름 제어 (Workflow)
│   ├── downloader.py    # 다운로드 엔진 (yt-dlp)
│   ├── config.py        # 설정 및 프리셋 관리
│   └── parser.py        # 옵션 파싱 로직
├── ui/                  # [View]
│   ├── console.py       # 사용자 입출력 (Rich/Questionary)
│   └── logger.py        # 로그 출력
├── utils/               # [Utils] 시스템 유틸리티
└── main.py              # 프로그램 진입점
```

---

## 🚀 설치 방법 (Installation)

### 1. FFmpeg 설정 (필수)
영상 병합 및 변환을 위해 **FFmpeg**가 반드시 필요합니다.
1. [FFmpeg 다운로드 (gyan.dev)](https://www.gyan.dev/ffmpeg/builds/)에서 `release-essentials.7z`를 받습니다.
2. 압축 해제 후 `bin` 폴더 안의 **`ffmpeg.exe`** 파일을 프로젝트의 `bin/` 폴더에 넣습니다.

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

---

## 💻 사용법 (Usage)

### 1. 실행 및 대화형 모드
```bash
python main.py
```
* **URL 입력**: 유튜브 링크를 붙여넣거나, `settings`를 입력하여 설정 메뉴로 진입합니다.
* **클립보드**: 실행 시 링크를 복사한 상태라면 자동으로 감지합니다.

### 2. 고급 옵션 키워드 (Custom Input)
메뉴에서 **`3. Custom`**을 선택하거나 **프리셋**을 만들 때 사용하세요.

| 분류 | 키워드 규칙 | 예시 |
| :--- | :--- | :--- |
| **해상도** | `숫자` + `p` | `2160p`, `1080p`, `720p` |
| **프레임** | `숫자` + `fps` | `60fps`, `30fps` |
| **코덱** | `av1`, `vp9`, `h264`, `hevc` | `av1` (고효율), `h264` (호환성) |
| **오디오** | `BR_`+`숫자`+`k` (비트레이트)<br>`SR_`+`숫자`+`k` (샘플링) | `BR_320k`, `SR_48k`, `flac`, `mp3` |
| **특수** | `original`, `best`, `upscale`, `enhance` | `enhance` (음질향상), `sub` (자막) |

> **입력 예시:** `1080p 60fps av1 enhance sub`

---

## ⚠️ 주의사항 (Disclaimer)

* 본 프로그램으로 다운로드한 콘텐츠의 저작권 책임은 **사용자 본인**에게 있습니다.
* 반드시 **개인 소장용**으로만 이용해 주십시오.

