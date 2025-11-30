import sys
import os
from ui.logger import Logger

# 로컬 모듈 경로 인식 (Dev 모드용)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # 핵심 컨트롤러 불러오기
    from core.controller import AppController
except ImportError as e:
    print(f"[Critical Error] 필수 모듈 로드 실패: {e}")
    sys.exit(1)

def main():
    """
    프로그램 진입점
    모든 로직은 AppController에게 위임합니다.
    """
    try:
        app = AppController()
        app.run()
    except KeyboardInterrupt:
        print("\n[System] 프로그램이 강제 종료되었습니다.")
        sys.exit(0)
    except Exception as e:
        Logger.error(f"예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        if os.name == 'nt':
            try: input("종료하려면 엔터 키를 누르세요...")
            except: pass

if __name__ == "__main__":
    main()