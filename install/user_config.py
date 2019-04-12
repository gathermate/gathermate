# -*- coding: utf-8 -*-

import os
import copy


class Flask(object):
    # 이 클래스를 기반으로 실제 설정값을 설정합니다.
    NAME = 'Flask @ user_config.py'
    SECRET_KEY = os.urandom(8).encode('hex')

    # Flask 개발 서버의 로그 레벨입니다.
    # gunicorn과 GAE는 해당 서버의 로그 레벨을 따릅니다.
    LOG_LEVEL = 'DEBUG'

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
        # 사용할 fetcher 모듈
        'MODULE': 'requests',

        # 목표 웹 페이지의 캐쉬 지속시간(초) 입니다.
        # 목표 웹 페이지에 대한 너무 잦은 요청과 불필요한 트래픽 발생을
        # 방지하기 위해서 각 목표 웹페이지는 캐쉬로 저장됩니다.
        # 0으로 설정시 캐쉬가 계속 유지됩니다.
        'CACHE_TIMEOUT': 60,

        # 목표 웹페이지의 응답을 기다리는 최대 시간(초)입니다.
        'DEADLINE': 60,

        # 쿠키를 파일로 저장하려면 경로를 설정하세요.
        # None 입력시 캐쉬에 저장.
        # e.g. /opt/apps/gathermate/instance/cookies
        #'COOKIE_PATH': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies'),
        'COOKIE_PATH': None,

        # 쿠키를 캐시에 저장할 경우 지속 시간
        'COOKIE_TIMEOUT' : 0,
    }


class Localhost(Flask):
    # 이 설정의 이름입니다.
    NAME = 'Localhost @ user_config.py'

    # 이 설정에만 적용되는 값으로 수정하기 위해
    # 기본 설정값(Flask 클래스)을 복사합니다.
    FETCHER = copy.deepcopy(Flask.FETCHER)
    FETCHER['COOKIE_PATH'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies')

    SCRAPMATE = copy.deepcopy(Flask.SCRAPMATE)
    STREAMATE = copy.deepcopy(Flask.STREAMATE)
    CALLMEWHEN = copy.deepcopy(Flask.CALLMEWHEN)

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
        RSS_ASYNC=True,
        # RSS_ASYNC 값이 True일 때 적용되는 쓰레드 수 입니다.
        # 반드시 0 보다 큰 값이어야 합니다.
        RSS_WORKERS=5,
        # RSS를 생성할 때 참고할 게시물의 수 입니다.
        # RSS_AGGRESSIVE가 True일 경우 5가 적당합니다. (5일 경우 대상 사이트에 총 6번 접속)
        # RSS_AGGRESSIVE가 False일 경우 대상 사이트의 페이지별 게시물 수를 고려해서 입력하세요.
        # (페이지별 게시물 수가 15, RSS_LENGTH가 20인 경우 총 2 페이지를 접속하고 수집한 30개 중 20개만 출력)
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
                'LOGIN_INFO': {
                    'ID': os.environ.get('GATHERMATE_SITE_ID', None),
                    'PW': os.environ.get('GATHERMATE_SITE_PW', None),
                },
                'ENCODING': 'utf-8',
                'RSS_AGGRESSIVE': True,
                'RSS_ASYNC': True,
                'RSS_WORKERS' : 15,
                'RSS_LENGTH' : 15,
                'RSS_WANT': ['720p'],
            },
            'Etoland': {
                'ENCODING': 'euc-kr',
                'LOGIN_INFO': {
                    'mb_id': os.environ.get('GATHERMATE_ETO_ID', None),
                    'mb_password': os.environ.get('GATHERMATE_ETO_PW', None),
                },
            },
            'Cineaste': {
                'LOGIN_INFO': {
                    'mb_id': 'myid',
                    'mb_password': 'mypassword',
                },
            },
        },
    )

    STREAMATE.update(
        # m3u의 스트림 주소를 pipe 형태로 출력할 경우(m3u 요청시 쿼리에 ffmpeg path 지정) 사용되는 포맷입니다.
        FFMPEG_COMMAND = 'pipe://{ffmpeg} -i {url} -c copy -f mpegts pipe:1',
        STREAMERS = {
            'Pooq': {
                'ID': '',
                'PW': '',
                # 720p 이상은 유료 계정 필요.
                'QUALITIES': ['100p', '270p', '360p', '480p'],
                # 제외 채널 (채널 이름은 옵션)
                'EXCEPTED_CHANNELS': {
                    'C4102': '현대홈쇼핑+샵 (예시 제외 채널)',
                    'C4901': '쇼핑엔T (예시 제외 채널)',
                },
                # 채널 번호가 지정되지 않은 채널의 시작 채널 번호
                'CHANNEL_NUMBERS_FROM': 10000,
            },
            'Tving': {
                'ID': '',
                'PW': '',
                # CJ One 회원: 10, Tvning 회원: 20
                'LOGIN_TYPE': 20,
                'QUALITIES': ['stream20', 'stream25', 'stream30', 'stream40', 'stream50'],
                'EXCEPTED_CHANNELS': {
                    'C05661': '디즈니채널 (DRM 필요)',
                },
                'CHANNEL_NUMBERS_FROM': 10000,
            },
            'Oksusu': {
                'ID': '',
                'PW': '',
                # Oksusu 회원: 'oksusu', T 아이디: 'tid'
                'LOGIN_TYPE': 'oksusu',
                'QUALITIES': [],
                'EXCEPTED_CHANNELS': {
                },
                'CHANNEL_NUMBERS_FROM': 10000,
            }
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
    # GAE에서 사용할 환경 설정입니다.
    NAME = 'GoogleAppEngine @ user_config.py'
    # GAE는 파일 쓰기 권한이 없으므로 쿠키를 캐시에 저장
    FETCHER = copy.deepcopy(Localhost.FETCHER)
    FETCHER['COOKIE_PATH'] = None
    FETCHER['MODULE'] = 'google.appengine.api.urlfetch'
    SCRAPMATE = copy.deepcopy(Localhost.SCRAPMATE)
    SCRAPMATE['RSS_AGGRESSIVE'] = True
    #APPS = [Localhost.SCRAPMATE, Localhost.CALLMEWHEN]

LOCALHOST_INSTANCE = Localhost()
GOOGLEAPPENGINE_INSTANCE = GoogleAppEngine()

'''
사용자 등록 채널 목록

- 각 스트리머의 채널은 사용자 등록 채널 목록에서 지정된 채널 이름, 채널 번호, 채널 로고를 사용하게 됩니다.
- 채널을 등록하지 않으면 스트리머의 기본값 사용.
- 등록된 채널만 EPG 검색을 시도합니다.
- 형식 : '사용자채널ID':dict(name='채널이름',chnum=채널번호,그래버='그래버채널ID',그래버='그래버검색어',skip='그래버|그래버',only='그래버|그래버',logo='아이콘주소'),
- 사용자채널ID : 채널 매핑에 사용할 채널 ID (e.g. tvg-id)
- 그래버 : ID 기반 그래버(e.g kt, lg, sky ...)의 채널ID, 혹은 검색어 기반 그래버(e.g. naver, daum)의 채널 검색어
- only : EPG 검색시 필요한 그래버(화이트리스트). 복수 입력시 '|'로 구분
- skip : EPG 검색시 제외할 그래버(블랙리스트). 복수 입력시 '|'로 구분
'''
CHANNELS = {
# 지상파/종편: 1-
'OBS':dict(name='OBS',chnum=1,kt=26,lg=648,sky=935,epgcokr=816,oksusu=70,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_70.png'),
'SBS':dict(name='SBS',chnum=6,epgcokr=6,kt=5,lg=504,sky=794,pooq='S01',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/5.png'),
'KBS2':dict(name='KBS 2',chnum=7,epgcokr=7,kt=7,lg=502,sky=795,pooq='K02',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/7.png'),
'KBS1':dict(name='KBS 1',chnum=9,epgcokr=9,kt=9,lg=501,sky=796,pooq='K01',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/9.png'),
'MBC':dict(name='MBC',chnum=11,epgcokr=11,kt=11,lg=503,sky=797,pooq='M01',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/11.png'),
'EBS1':dict(name='EBS 1',chnum=13,epgcokr=13,kt=13,lg=505,sky=798,pooq='E01',oksusu=15,logo='http://img.pooq.co.kr/BMS/ChannelImg/ebs1.png'),
'EBS2':dict(name='EBS 2',chnum=14,epgcokr=546,kt=95,lg=506,pooq='E07',logo='http://img.pooq.co.kr/BMS/ChannelImg/ebs2.png'),
'JTBC':dict(name='JTBC',chnum=15,epgcokr=570,kt=15,lg=747,sky=563,pooq='C2301',tving='C01582',oksusu=240,logo='http://img.pooq.co.kr/BMS/ChannelImg/01_jtbc.png'),
'MBN':dict(name='MBN',chnum=16,epgcokr=20,kt=16,lg=750,sky=562,pooq='C2401',tving='C00708',oksusu=241,logo='http://img.pooq.co.kr/BMS/ChannelImg/02_MBN.png'),
'CHANNELA':dict(name='채널A',chnum=18,epgcokr=571,kt=18,lg=749,sky=564,pooq='C2501',tving='C01583',oksusu=242,logo='http://img.pooq.co.kr/BMS/ChannelImg/04_channelA.png'),
'TVCHOSUN':dict(name='TV 조선',chnum=19,epgcokr=569,kt=19,lg=746,sky=549,pooq='C2601',tving='C01581',oksusu=243,logo='http://img.pooq.co.kr/BMS/Channelimage30/image/180_24.png'),
# 뉴스/경제: 20-
'YONHAPNEWS':dict(name='연합뉴스TV',chnum=23,epgcokr=573,kt=23,lg=734,sky=566,pooq='Y01',tving='C01723',oksusu=571,logo='https://tv.kt.com/relatedmaterial/ch_logo/live/23.png'),
'YTN':dict(name='YTN',chnum=24,epgcokr=24,kt=24,lg=698,sky=551,pooq='C2101',tving='C00593',oksusu=570,logo='http://img.pooq.co.kr/BMS/ChannelImg/07_ytn.png'),
'SBS-CNBC':dict(name='SBS CNBC',chnum=25,epgcokr=622,kt=25,lg=616,sky=622,pooq='S06',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/25.png'),
'MTN':dict(name='MTN',chnum=26,kt=181,lg=630,sky=132,epgcokr=132,oksusu=627,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_627.png'),
'TOMATOTV':dict(name='토마토TV',chnum=27,kt=185,lg=771,sky=359,epgcokr=359,oksusu=620,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_620.png'),
'PAXETV':dict(name='팍스경제TV',chnum=28,kt=186,lg=742,oksusu=622,daum='팍스TV',logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_622.png'),
'WOWTV':dict(name='한국경제TV',chnum=29,kt=180,lg=604,sky=171,epgcokr=106,oksusu=626,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_626.png'),
# 영화/시리즈: 40-
'PLAYY-WELLMADE':dict(name='PLAYY 웰메이드 영화',chnum=40,pooq='H01',only='pooq',logo='http://img.pooq.co.kr/BMS/ChannelImg/28_playy%EC%9B%94%EB%A9%94%EC%9D%B4%EB%93%9C%EC%98%81%ED%99%94.png'),
'PLAYY-ACTION':dict(name='PLAYY 액션영화',chnum=41,pooq='H07',only='pooq',logo='http://img.pooq.co.kr/BMS/ChannelImg/29_playy%EC%95%A1%EC%85%98%EC%98%81%ED%99%94.png'),
'ASIAN':dict(name='AsiaN',chnum=42,kt=111,lg=658,sky=976,pooq='C5101',oksusu=177,logo='http://img.pooq.co.kr/BMS/ChannelImg/AsiaN.png'),
'CHANNELJ':dict(name='CHANNEL J',chnum=43,epgcokr=290,kt=108,lg=656,sky=973,pooq='C5501',logo='http://img.pooq.co.kr/BMS/ChannelImg/CH_J_TV.png'),
'CHANNELW':dict(name='채널W',chnum=44,epgcokr=518,kt=116,lg=161,sky=518,pooq='C3901',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/116.png'),
# 다큐/교양: 70-
'KBSN-LIFE':dict(name='KBSN Life',chnum=70,epgcokr=168,kt=281,lg=582,sky=291,pooq='K05',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/281.png'),
'YTN-LIFE':dict(name='YTN Life',chnum=71,kt=190,lg=655,sky=502,tving='C01101',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C01101.png'),
'YTN-SCIENCE':dict(name='YTN사이언스',chnum=72,kt=175,lg=755,sky=792,tving='C15347',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C15347.png'),
'HISTORY':dict(name='히스토리 채널',chnum=73,kt=169,lg=664,sky=575,pooq='C5901',tving='C17341',logo='http://img.pooq.co.kr/BMS/Channelimage30/image/history-2.png'),
'NATGEO-WILD':dict(name='Natgeo Wild HD',chnum=64,kt=170,lg=718,sky=63,oksusu=773,daum='HD Nat Geo Wild',logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_773.png'),
# 드라마/오락/음악: 100-
'SBS-FUNE':dict(name='SBS funE',chnum=100,epgcokr=684,kt=43,lg=615,sky=858,pooq='S04',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/43.png'),
'SBS-PLUS':dict(name='SBS Plus',chnum=101,epgcokr=54,kt=37,lg=612,sky=767,pooq='S03',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/37.png'),
'SBS-MTV':dict(name='SBS MTV',chnum=102,epgcokr=130,kt=96,lg=634,sky=130,pooq='S09',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/96.png'),
'MBC-EVERYONE':dict(name='MBC EVERY1',chnum=103,epgcokr=335,kt=1,lg=626,sky=58,pooq='M03',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/1.png'),
'MBC-DRAMANET':dict(name='MBC 드라마넷',chnum=104,epgcokr=253,kt=3,lg=621,sky=857,pooq='M02',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/3.png'),
'MBC-MUSIC':dict(name='MBC Music',chnum=105,epgcokr=126,kt=97,lg=624,sky=126,pooq='M06',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/97.png'),
'KBS-JOY':dict(name='KBS JOY',chnum=106,epgcokr=754,kt=41,lg=619,sky=968,pooq='K04',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/41.png'),
'KBS-DRAMA':dict(name='KBS DRAMA',chnum=107,epgcokr=148,kt=35,sky=910,pooq='K06',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/35.png'),
'KBSW':dict(name='KBS W',chnum=108,epgcokr=509,kt=83,lg=620,sky=509,pooq='K09',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/83.png'),
'TVN':dict(name='tvN',chnum=109,epgcokr=743,kt=17,lg=682,sky=60,tving='C00551',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C00551.png'),
'TVN-O':dict(name='O tvN',chnum=110,epgcokr=705,kt=45,lg=689,sky=555,tving='C01143',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C01143.png'),
'TVN-X':dict(name='XtvN',chnum=111,kt=76,lg=671,sky=282,tving='C01141',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C01141.png'),
'JTBC2':dict(name='JTBC2',chnum=112,kt=39,lg=606,sky=62,pooq='C2303',tving='C15741',oksusu=874,logo='http://img.pooq.co.kr/BMS/ChannelImg/jtbc2_180x24.png'),
'JTBC4':dict(name='JTBC4',chnum=113,kt=75,lg=767,sky=923,pooq='C2309',logo='http://img.pooq.co.kr/BMS/Channelimage30/image/JTBC4-2.png'),
'OLIVE':dict(name='Olive',chnum=114,kt=34,lg=696,sky=272,tving='C00575',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C00575.png'),
'MBN-PLUS':dict(name='MBN Plus',chnum=115,kt=99,lg=787,sky=658,pooq='C2402',tving='C17142',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C17142.png'),
'CHANNELA-PLUS':dict(name='채널A플러스',chnum=116,kt=98,lg=784,sky=627,tving='C17141',skip='naver',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C17141.png'),
'TVCHOSUN2':dict(name='TV 조선 2',chnum=117,kt=69,lg=775,tving='C00585',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C00585.png'),
'DONGATV':dict(name='동아TV',chnum=118,epgcokr=247,kt=82,lg=660,sky=247,pooq='C7301',logo='http://img.pooq.co.kr/BMS/Channelimage30/image/donga-2.png'),
'ONSTYLE':dict(name='ONSTYLE',chnum=119,epgcokr=414,kt=77,lg=778,sky=553,tving='C01142',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C01142.png'),
'DRAMAX':dict(name='드라맥스',chnum=120,kt=47,lg=797,sky=285,epgcokr=285,oksusu=904,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_904.png'),
'LIFETIME':dict(name='라이프타임',chnum=121,kt=78,lg=603,sky=556,pooq='C5902',tving='C00611',oksusu=271,logo='http://img.pooq.co.kr/BMS/Channelimage30/image/lifetime-2.png'),
'KSTAR':dict(name='K star',chnum=122,kt=87,lg=662,sky=85,epgcokr=37,oksusu=884,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_884.png'),
'CUBETV':dict(name='큐브 TV',chnum=123,lg=563,epgcokr=598,oksusu=905,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_905.png'),
'DIATV':dict(name='다이아 TV',chnum=124,kt=72,lg=690,sky=912,tving='C15152',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C15152.png'),
'ZHTV':dict(name='중화TV',chnum=125,epgcokr=664,kt=110,lg=725,sky=664,tving='C00544',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C00544.png'),
'MNET':dict(name='Mnet',chnum=126,epgcokr=27,kt=27,lg=687,sky=273,tving='C00579',logo='http://image.tving.com/upload/cms/caic/CAIC0300/C00579.png'),
'KBSN-PLUS':dict(name='KBSN PLUS',chnum=129,pooq='K23',skip='naver',logo='http://img.pooq.co.kr/BMS/Channelimage30/image/KBSN-2.png'),
# 스포츠/레저: 200-
'SBS-SPORTS':dict(name='SBS Sports',chnum=200,kt=58,lg=613,sky=977,pooq='S02',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/58.png'),
'SBS-GOLF':dict(name='SBS 골프',chnum=201,kt=57,lg=614,sky=769,epgcokr=44,oksusu=350,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_350.png'),
'SPOTV':dict(name='SPOTV',chnum=202,kt=51,lg=667,sky=109,oksusu=125,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_125.png'),
'SPOTV2':dict(name='SPOTV2',chnum=203,kt=52,lg=638,sky=922,oksusu=424,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_424.png'),
'SPOTVPLUS':dict(name='SPOTV+',chnum=204,kt=125,lg=650,sky=713,oksusu=134,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_134.png'),
'SPOTV-GAMES':dict(name='SPOTV GAMES',chnum=205,kt=124,lg=727,pooq='C5401',oksusu=254,logo='https://tv.kt.com/relatedmaterial/ch_logo/live/124.png'),
'JTBC-GOLF':dict(name='JTBC Golf',chnum=206,epgcokr=487,kt=56,lg=602,sky=974,pooq='C2302',tving='C00588',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/56.png'),
'JTBC3-FOXSPORTS':dict(name='JTBC3 FOX Sports',chnum=207,epgcokr=407,kt=62,lg=795,sky=407,pooq='C2304',tving='C00805',oksusu=436,logo='http://img.pooq.co.kr/BMS/ChannelImg/jtbc3_180x24.png'),
'IBSPORTS':dict(name='IB SPORTS',chnum=208,kt=53,lg=637,sky=515,pooq='C7101',oksusu=123,logo='http://img.pooq.co.kr/BMS/Channelimage30/image/IB_SPORTS-2.png'),
'OGN':dict(name='OGN',chnum=209,epgcokr=55,kt=123,lg=681,sky=55,tving='C00590',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C00590.png'),
'BILLIARDSTV':dict(name='Billiards TV',chnum=210,kt=126,lg=668,sky=615,epgcokr=615,oksusu=122,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_122.png'),
'EUROSPORT':dict(name='Eurosport',chnum=211,oksusu=120,sky=578,epgcokr=578,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_120.png'),
'FISHINGTV':dict(name='FISHING TV',chnum=212,kt=119,sky=254,epgcokr=254,oksusu=273,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_273.png'),
'FTV':dict(name='FTV',chnum=213,kt=118,lg=665,sky=969,epgcokr=262,oksusu=530,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_530.png'),
'THEGOLFCHANNEL':dict(name='Golf Channel Korea',chnum=214,kt=55,lg=647,oksusu=135,skip='naver|daum',logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_135.png'),
'STARSPORTS':dict(name='Star Sports',chnum=215,kt=63,sky=122,epgcokr=122,oksusu=781,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_781.png'),
'BRAINTV':dict(name='브레인TV',chnum=216,kt=122,lg=707,sky=488,epgcokr=488,oksusu=279,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_279.png'),
'POLARIS':dict(name='폴라리스TV',chnum=217,kt=253,lg=726,pooq='C6901',skip='daum',logo='http://img.pooq.co.kr/BMS/Channelimage30/image/Polaris-2.png'),
# 애니/유아/교육: 300-
'ANIBOX':dict(name='ANIBOX',chnum=300,epgcokr=740,kt=993,lg=695,sky=84,pooq='C4401',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/135.png'),
'ANIMAX':dict(name='애니맥스',chnum=301,kt=995,lg=703,sky=725,pooq='A01',oksusu=371,logo='http://img.pooq.co.kr/BMS/ChannelImg/31_anymax.png'),
'DISNEY-CHANNEL':dict(name='디즈니 채널',chnum=302,epgcokr=172,kt=998,lg=645,sky=503,pooq='D01',tving='C05661',oksusu=334,logo='http://img.pooq.co.kr/BMS/ChannelImg/30_disney.png'),
'DISNEY-JUNIOR':dict(name='디즈니 주니어',chnum=303,epgcokr=430,kt=978,lg=646,sky=504,pooq='D02',oksusu=335,logo='http://img.pooq.co.kr/BMS/ChannelImg/36_disney%20Junior.png'),
'EBS-KIDS':dict(name='EBS KIDS',chnum=304,kt=245,lg=608,pooq='E05',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/7ab0db0280105184910.png'),
'NICKELODEON':dict(name='Nickelodeon',chnum=305,epgcokr=685,kt=992,lg=635,sky=685,pooq='S10',logo='http://img.pooq.co.kr/BMS/ChannelImg/35_nick.png'),
'TOONIVERSE':dict(name='투니버스',chnum=306,epgcokr=38,kt=996,lg=693,sky=526,tving='C06941',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C06941.png'),
'EBS-PLUS1':dict(name='EBS 플러스1',chnum=307,kt=972,lg=714,sky=113,epgcokr=113,oksusu=820,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_820.png'),
'EBS-PLUS2':dict(name='EBS 플러스2',chnum=308,kt=971,lg=715,sky=114,epgcokr=114,oksusu=821,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_821.png'),
'EBS-ENGLISH':dict(name='EBS English',chnum=309,kt=973,lg=768,sky=777,epgcokr=777,oksusu=822,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_822.png'),
'JEITV':dict(name='JEI 재능TV',chnum=310,kt=986,lg=776,sky=23,epgcokr=23,oksusu=378,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_378.png',),
'DAEKYO-KIDSTV':dict(name='대교 어린이TV',chnum=311,kt=987,lg=761,sky=17,epgcokr=17,oksusu=374,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_374.png'),
'PLAYLEARNTV':dict(name='플레이런TV',chnum=312,kt=974,lg=772,oksusu=824,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_824.png'),
# 해외: 400-449
'CNN-INTERNATIONAL':dict(name='CNN Int’l',chnum=400,kt=191,lg=729,sky=117,epgcokr=117,oksusu=774,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_774.png'),
'CCTV4':dict(name='CCTV4',chnum=401,kt=280,lg=178,sky=159,pooq='K12',skip='daum',logo='http://img.pooq.co.kr/BMS/ChannelImg/10_CCTV.png'),
# 공공/공익/정보: 450-499
'NATV':dict(name='국회방송',chnum=450,kt=65,lg=717,sky=427,epgcokr=427,oksusu=221,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_221.png'),
# 홈쇼핑/기타: 500-549
'GS-SHOP':dict(name='GS SHOP',chnum=500,epgcokr=45,kt=8,lg=676,sky=497,pooq='C4201',oksusu=320,logo='http://img.pooq.co.kr/BMS/ChannelImg/59_GSshop.png'),
'GS-MYSHOP':dict(name='GS MY SHOP',chnum=501,kt=38,lg=740,sky=634,pooq='C4202',skip='naver|daum',logo='http://img.pooq.co.kr/BMS/ChannelImg/60_GSmyshop.png'),
'HYUNDAI':dict(name='현대홈쇼핑',chnum=502,epgcokr=140,kt=10,lg=675,sky=493,pooq='C4101',oksusu=321,logo='https://tv.kt.com/relatedmaterial/ch_logo/live/10.png'),
'HYUNDAI-PLUSSHOP':dict(name='현대홈쇼핑+샵',chnum=503,kt=36,lg=760,sky=930,pooq='C4102',skip='naver|daum',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/36.png'),
'CJOSHOP':dict(name='CJ오쇼핑',chnum=504,epgcokr=250,kt=6,lg=672,sky=975,pooq='C4701',oksusu=324,logo='http://img.pooq.co.kr/BMS/ChannelImg/CJO_2_180_24.png'),
'CJOSHOP-PLUS':dict(name='CJ오쇼핑 플러스',chnum=505,kt=28,lg=781,sky=619,pooq='C4702',skip='naver|daum',logo='http://img.pooq.co.kr/BMS/ChannelImg/CJOP2_180_24.png'),
'SHOPPINGANDT':dict(name='쇼핑엔T',chnum=506,kt=33,lg=782,sky=41,pooq='C4901',skip='naver|daum',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/33.png'),
'SHINSEGAE':dict(name='신세계TV쇼핑',chnum=507,kt=2,lg=780,sky=521,pooq='C4801',skip='naver|daum',logo='http://img.pooq.co.kr/BMS/ChannelImg/shin_180x24_re.png'),
'LOTTE-SHOP':dict(name='롯데홈쇼핑',chnum=508,epgcokr=138,kt=30,lg=674,sky=278,pooq='C5601',oksusu=323,logo='http://img.pooq.co.kr/BMS/Channelimage30/image/lotte-2.png'),
'HNSMALL':dict(name='홈&쇼핑',chnum=509,kt=14,lg=649,sky=567,epgcokr=567,oksusu=327,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_327.png'),
'NSMALL':dict(name='NS홈쇼핑',chnum=510,kt=12,lg=673,sky=496,epgcokr=133,oksusu=322,logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_322.png'),
'SKSTOA':dict(name='SK stoa',chnum=511,kt=4,lg=738,sky=529,oksusu=330,skip='daum|naver',logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_330.png'),
'GONGYOUNGSHOP':dict(name='공영쇼핑',chnum=512,kt=22,lg=737,sky=632,oksusu=332,skip='naver',logo='http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/nsepg_332.png'),
# 오디오: 1000-
'KBS1-RADIO':dict(name='KBS1 RADIO',chnum=1000,pooq='K07',logo='http://img.pooq.co.kr/BMS/ChannelImg/44_kbs%201%20radio.png'),
'KBS2-RADIO':dict(name='KBS2 FM',chnum=1001,pooq='K08',logo='http://img.pooq.co.kr/BMS/ChannelImg/45_KBS%20coolFM.png'),
'MBC-RADIO':dict(name='MBC 표준 FM',chnum=1002,pooq='M07',logo='http://img.pooq.co.kr/BMS/ChannelImg/46_MBC%20%ED%91%9C%EC%A4%80fm.png'),
'MBC-FM4U':dict(name='MBC FM4U',chnum=1003,pooq='M08',logo='http://img.pooq.co.kr/BMS/ChannelImg/47_MBC%20fm4U.png'),
'SBS-POWERFM':dict(name='SBS 파워FM',chnum=1004,pooq='S07',logo='http://img.pooq.co.kr/BMS/ChannelImg/48_sbs%20%ED%8C%8C%EC%9B%8Cfm.png'),
'SBS-LOVEFM':dict(name='SBS 러브FM',chnum=1005,pooq='S08',logo='http://img.pooq.co.kr/BMS/ChannelImg/49_sbs%20%EB%9F%AC%EB%B8%8Cfm.png'),
'EBS-FM':dict(name='라디오 EBS 교육방송',chnum=1006,pooq='E06',logo='http://img.pooq.co.kr/BMS/ChannelImg/50_EBS%20fm.png'),
}
