# -*- coding: utf-8 -*-

import os


class Flask(object):
    NAME = 'Flask @ user_config.py'
    SECRET_KEY = os.urandom(8).encode('hex')

    # Flask 개발 서버의 로그 레벨입니다.
    # gunicorn과 GAE는 해당 서버의 로그 레벨을 따릅니다.
    LOG_LEVEL = 'DEBUG'

    # 서버 응답(RSS 또는 웹페이지)의 캐쉬 지속시간(초)입니다.
    # 동일한 요청이라 판단될 경우 캐쉬된 결과물로 응답합니다.
    # 0으로 설정시 캐쉬가 계속 유지됩니다.
    TIMEOUT = 5

    # HTTP Basic Authentication에 사용될 아이디와 비밀번호입니다.
    # GAE은 app.yaml에서 환경 설정 값을 지정할 수 있으며
    # gunicorn은 데몬 스크립트에서 export로 설정해 줄 수 있습니다.
    # 여기에 직접 아이디와 비밀번호를 입력해도 됩니다.
    AUTH_ID = os.environ.get('GATHERMATE_AUTH_ID', None)
    AUTH_PW = os.environ.get('GATHERMATE_AUTH_PW', None)

    # 기본 모듈 세팅
    SCRAPMATE = {
        'NAME': 'Scrapmate',
        # 매니저 모듈의 패키지 주소입니다.
        'MANAGER': 'apps.scrapmate.manager',
        # 블루프린트 모듈의 패키지 주소입니다.
        'BLUEPRINT': 'apps.scrapmate.views',
        # 블루프린트 모듈에서 가져올 블루프린트 객체의 변수명입니다.
        'BLUEPRINT_INSTANCE': 'scrapmate',
        # 블루프린트에 사용될 주소입니다.
        'BLUEPRINT_URL_PREFIX':  '/scrap',
    }
    STREAMATE = {
        'NAME': 'Streamate',
        'MANAGER': 'apps.streamate.manager',
        'BLUEPRINT': 'apps.streamate.views',
        'BLUEPRINT_INSTANCE': 'streamate',
        'BLUEPRINT_URL_PREFIX':  '/stream',
    }
    CALLMEWHEN = {
        'NAME': 'Callmewhen',
        'MANAGER': 'apps.callmewhen.manager',
    }
    FETCHER = {
        # 목표 웹 페이지의 캐쉬 지속시간(초) 입니다.
        # 목표 웹 페이지에 대한 너무 잦은 요청과 불필요한 트래픽 발생을
        # 방지하기 위해서 각 목표 웹페이지는 캐쉬로 저장됩니다.
        # 0으로 설정시 캐쉬가 계속 유지됩니다.
        'CACHE_TIMEOUT': 60,

        # 목표 웹페이지의 응답을 기다리는 최대 시간(초)입니다.
        'DEADLINE': 60,

        # 쿠키를 파일로 저장하려면 경로를 설정하세요.
        # None 입력시 캐쉬에 저장. (GAE는 파일 쓰기 권한이 없으므로 None)
        # instance/cookies
        #'COOKIE_PATH': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies'),
        'COOKIE_PATH': None,

        # 쿠키를 캐시에 저장할 경우 지속 시간
        'COOKIE_TIMEOUT' : 0,
    }


class Localhost(Flask):
    # 이 설정의 이름입니다.
    NAME = 'Localhost @ user_config.py'

    SCRAPMATE = Flask.SCRAPMATE
    STREAMATE = Flask.STREAMATE
    CALLMEWHEN = Flask.CALLMEWHEN

    # 사용할 앱의 설정을 등록하세요.
    APPS = [SCRAPMATE, STREAMATE, CALLMEWHEN]

    SCRAPMATE.update(
        # True일 경우 RSS 생성시 대상으로 선정된 게시물에 추가로 접속하여
        # 미리 내용물을 가져옵니다. 대상 사이트에 부담이 될 수 있습니다.
        # False일 경우 다운로드 과정에서 내용물을 확인하고 예측하여 다운로드 합니다.
        RSS_AGGRESSIVE=False,
        # RSS_AGGRESSIVE가 True일 때 적용됩니다.
        # False일 경우 여러 게시물을 순차적으로 접속하여 파싱합니다.
        # True일 경우 여러 게시물을 동시에 접속하여 파싱합니다.
        # 대상 사이트에서 요청 횟수를 제한할 경우 효과가 없을 수 있습니다.
        RSS_ASYNC=False,
        # RSS_ASYNC 값이 True일 때 적용되는 쓰레드 수 입니다.
        # 반드시 0 보다 큰 값이어야 합니다.
        RSS_WORKERS=5,
        # RSS를 생성할 때 참고할 게시물의 수 입니다.
        # RSS_AGGRESSIVE가 True일 경우 5가 적당합니다. (5일 경우 대상 사이트에 총 6번 접속)
        # 대상 사이트의 페이지별 게시물 수를 고려해서 입력하세요.
        RSS_LENGTH=5,
        # RSS_AGGRESSIVE가 False일 때 다운로드할 파일의 우선 순위입니다.
        # 아래 리스트의 정규 표현식으로 파일 이름을 순차적으로 검사합니다.
        # 제일 먼저 매치되는 파일을 다운로드 하거나 매치되는 파일이 없으면
        # 첫번째 파일을 다운로드 합니다.
        RSS_WANT=['1080P', 'bluray', '\.torrent$'],
        # 아래의 확장자를 가진 파일만 표시합니다.
        ACCEPTED_EXT=['.torrent', '.smi', '.srt', '.zip', '.rar'],
        # 사이트별 인코딩이나 ASYNC, 로그인 정보 등을 설정할 수 있습니다.
        # 사이트의 키 값은 사이트의 클래스명을 입력하세요.
        SCRAPERS = {
            'Samplesite': {
                'ID': os.environ.get('GATHERMATE_SITE_ID', None),
                'PW': os.environ.get('GATHERMATE_SITE_PW', None),
                'ENCODING': 'utf-8',
                'RSS_AGGRESSIVE': True,
                'RSS_ASYNC': True,
                'RSS_WORKERS' : 15,
                'RSS_LENGTH' : 15,
                'RSS_WANT': ['720p'],
            },
            'Etoland': {
                'ENCODING': 'euc-kr',
                'mb_id': os.environ.get('GATHERMATE_ETO_ID', None),
                'mb_password': os.environ.get('GATHERMATE_ETO_PW', None),
            },
            'Cineaste': {
                'mb_id': 'myid',
                'mb_password': 'mypassword',
            },
        },
    )

    STREAMATE.update(
        STREAMERS = {
            'Pooq': {
                'ID': '',
                'PW': '',
                # 720p 이상은 유료 계정 필요.
                'QUALITY': ['100p', '270p', '360p', '480p'],
                'EXCEPT_CHANNELS': {

                },
                'EXCLUSIVE_CHANNELS': {
                    'K15': 'KBS 1박 2일',
                    'PM1': 'MBC 무한도전',
                    'M10': 'ALL THE K-POP',
                    'PM2': 'MBC 나 혼자 산다',
                    'S13': 'SBS Mobidic',
                    'S14': 'SBS THE K-POP',
                    'S15': 'SBS TV동물농장',
                    'K18': 'KBS 남자의 자격',
                    'C2306': 'JTBC 아는형님',
                    'C2307': 'JTBC 냉장고를 부탁해',
                    'M12': 'MBC 라디오스타',
                    'M13': 'MBC 서프라이즈',
                    'K24': 'KBS 슈퍼맨이 돌아왔다',
                    'S16': 'SBS 런닝맨',
                    'C7801': '블렌딩 뮤직 비디오',
                    'C2701': 'KISS - 최신인기가요',
                    'C2702': 'KISS - 발라드',
                    'C2703': 'KISS - 8090인기가요',
                    'C2704': 'KISS - K-POP 아이돌',
                    'C2705': 'KISS - 2000년대 인기가요',
                    'C2706': 'KISS - 재즈 라운지',
                    'D01': 'Disney',
                    'H01': 'PLAYY 웰메이드 영화',
                    'H07': 'PLAYY 액션영화',
                    'C4202': 'GS MY SHOP',
                    'C4102': '현대홈쇼핑+샵',
                    'C4901': '쇼핑엔T',
                    'C4801': '신세계TV쇼핑',
                },
                'ALTERNATIVE_CHANNEL_NAME': {
                    'K01': 'KBS1',
                    'K02': 'KBS2',
                    'D01': '디즈니채널',
                },
            },
            'Tving': {
                'ID': '',
                'PW': '',
                # CJ One 회원: 10, Tvning 회원: 20
                'LOGIN_TYPE': 20,
                'QUALITY': ['stream20', 'stream25', 'stream30', 'stream40', 'stream50'],
                'EXCEPT_CHANNELS': {

                },
                'EXCLUSIVE_CHANNELS': {
                    'C28041': '엠피디 직캠 - M2',
                },
                'ALTERNATIVE_CHANNEL_NAME': {
                },
            },
        }
    )

    CALLMEWHEN.update(
        # 메세지를 보낼 텔레그램 봇 토큰입니다.
        # 에러 발생시 봇을 통해 알람을 받을 수 있습니다.
        TELEGRAM_BOT_TOKEN='',
        # 자신의 텔레그램 chat_id를 입력해 주세요.
        # install 폴더의 telegram.sh 스크립트로 확인 가능.
        TELEGRAM_CHAT_ID=123456789,
        # 알림 온/오프 설정입니다.
        NOTIFY=False,
    )



class GoogleAppEngine(Localhost):
    NAME = 'GoogleAppEngine @ user_config.py'
    # GAE는 파일 쓰기 권한이 없으므로 쿠키를 캐시에 저장
    FETCHER = Localhost.FETCHER
    FETCHER['COOKIE_PATH'] = None
    APPS = [Localhost.SCRAPMATE, Localhost.CALLMEWHEN]

LOCALHOST_CLASS = Localhost
GOOGLEAPPENGINE_CLASS = GoogleAppEngine
