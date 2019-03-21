# -*- coding: utf-8 -*-

import os
import copy


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

    FETCHER = copy.deepcopy(Flask.FETCHER)
    FETCHER['COOKIE_PATH'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies')

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
                # 제외 채널 (채널 이름은 옵션)
                'EXCEPT_CHANNELS': {
                    'C4102': '현대홈쇼핑+샵',
                    'C4901': '쇼핑엔T',
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
    FETCHER = copy.deepcopy(Localhost.FETCHER)
    FETCHER['COOKIE_PATH'] = None
    #APPS = [Localhost.SCRAPMATE, Localhost.CALLMEWHEN]

LOCALHOST_CLASS = Localhost()
GOOGLEAPPENGINE_CLASS = GoogleAppEngine()

# cid : 채널 매핑에 사용할 채널 ID (e.g. tvg-id)
# only : EPG 검색시 필요한 그래버(화이트리스트). 복수 입력시 '|'로 구분
# skip : EPG 검색시 제외할 그래버(블랙리스트). 복수 입력시 '|'로 구분
CHANNELS = [
dict(cid='ALLKPOP-1',name='ALL THE K-POP',chnum=607,pooq='M10',only='pooq',logo='img.pooq.co.kr/BMS/ChannelImg/19_all the KPOP.png'),
dict(cid='ANIBOX-1',name='ANIBOX',chnum=993,kt=993,lg=695,pooq='C4401',logo='http://img.pooq.co.kr/BMS/ChannelImg/32_애니박스.png'),
dict(cid='ANIMAX-1',name='애니맥스',chnum=155,kt=995,lg=703,pooq='A01',logo='http://img.pooq.co.kr/BMS/ChannelImg/31_anymax.png'),
dict(cid='ASIAN-1',name='AsiaN',chnum=111,kt=111,lg=658,pooq='C5101',logo='http://img.pooq.co.kr/BMS/ChannelImg/AsiaN.png'),
dict(cid='BLENDING-1',name='블렌딩 뮤직 비디오',chnum=600,pooq='C7801',only='pooq',logo='img.pooq.co.kr/BMS/Channelimage30/image/vlending-2.png'),
dict(cid='CCTV-4',name='CCTV4',chnum=280,kt=280,lg=178,pooq='K12',skip='daum',logo='http://img.pooq.co.kr/BMS/ChannelImg/10_CCTV.png'),
dict(cid='CHANNELA-1',name='채널A',chnum=18,kt=18,lg=749,pooq='C2501',tving='C01583',logo='http://img.pooq.co.kr/BMS/ChannelImg/04_channelA.png'),
dict(cid='CHANNELA-2',name='채널A플러스',chnum=98,kt=98,lg=784,tving='C17141',skip='naver',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C17141.png'),
dict(cid='CHANNELJ-1',name='CHANNEL J',chnum=108,kt=108,lg=656,pooq='C5501',logo='http://img.pooq.co.kr/BMS/ChannelImg/CH_J_TV.png'),
dict(cid='CHANNELW-1',name='채널W',chnum=116,kt=116,lg=161,pooq='C3901',logo='http://img.pooq.co.kr/BMS/ChannelImg/33_채널w.png'),
dict(cid='DIATV-1',name='다이아 TV',chnum=72,kt=72,lg=690,tving='C15152',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C15152.png'),
dict(cid='DISNEY-1',name='디즈니 채널',chnum=998,kt=998,lg=645,pooq='D01',tving='C05661',logo='http://img.pooq.co.kr/BMS/ChannelImg/30_disney.png'),
dict(cid='DISNEY-2',name='디즈니 주니어',chnum=978,kt=978,lg=646,pooq='D02',logo='http://img.pooq.co.kr/BMS/ChannelImg/36_disney Junior.png'),
dict(cid='DONGA-1',name='동아TV',chnum=82,kt=82,lg=660,pooq='C7301',logo='http://img.pooq.co.kr/BMS/Channelimage30/image/donga-2.png'),
dict(cid='EBS-1',name='EBS 1',chnum=13,kt=13,lg=505,pooq='E01',logo='http://img.pooq.co.kr/BMS/ChannelImg/ebs1.png'),
dict(cid='EBS-2',name='EBS 2',chnum=95,kt=95,lg=506,pooq='E07',logo='http://img.pooq.co.kr/BMS/ChannelImg/ebs2.png'),
dict(cid='EBS-3',name='EBS KIDS',chnum=983,kt=983,lg=608,pooq='E05',logo='http://img.pooq.co.kr/BMS/ChannelImg/ebs키즈.png'),
dict(cid='EBS-4',name='라디오 EBS 교육방송',chnum=500,pooq='E06',logo='http://img.pooq.co.kr/BMS/ChannelImg/50_EBS fm.png'),
dict(cid='HISTORY-1',name='히스토리 채널',chnum=169,kt=169,lg=664,pooq='C5901',tving='C17341',logo='http://img.pooq.co.kr/BMS/Channelimage30/image/history-2.png'),
dict(cid='IBSPORTS-1',name='IB SPORTS',chnum=53,kt=53,lg=637,pooq='C7101',logo='http://img.pooq.co.kr/BMS/Channelimage30/image/IB_SPORTS-2.png'),
dict(cid='JTBC-1',name='JTBC',chnum=15,kt=15,lg=747,pooq='C2301',tving='C01582',logo='http://img.pooq.co.kr/BMS/ChannelImg/01_jtbc.png'),
dict(cid='JTBC-2',name='JTBC2',chnum=39,kt=39,lg=606,pooq='C2303',tving='C15741',logo='http://img.pooq.co.kr/BMS/ChannelImg/jtbc2_180x24.png'),
dict(cid='JTBC-3',name='JTBC3 FOX Sports',chnum=62,kt=62,lg=795,pooq='C2304',tving='C00805',logo='http://img.pooq.co.kr/BMS/ChannelImg/jtbc3_180x24.png'),
dict(cid='JTBC-4',name='JTBC4',chnum=75,kt=75,lg=767,pooq='C2309',logo='http://img.pooq.co.kr/BMS/Channelimage30/image/JTBC4-2.png'),
dict(cid='JTBC-5',name='JTBC Golf',chnum=56,kt=56,lg=602,pooq='C2302',tving='C00588',logo='http://img.pooq.co.kr/BMS/ChannelImg/43_jtbc Golf.png'),
dict(cid='JTBC-6',name='JTBC 아는형님',chnum=430,pooq='C2306',only='pooq',logo='img.pooq.co.kr/BMS/Channelimage30/image/brother-2.png'),
dict(cid='JTBC-7',name='JTBC 냉장고를 부탁해',chnum=431,pooq='C2307',only='pooq',logo='img.pooq.co.kr/BMS/Channelimage30/image/refrigerator-2.png'),
dict(cid='KBS-1',name='KBS 1',chnum=9,kt=9,lg=501,pooq='K01',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/9.png'),
dict(cid='KBS-2',name='KBS 2',chnum=7,kt=7,lg=502,pooq='K02',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/7.png'),
dict(cid='KBS-3',name='KBS DRAMA',chnum=35,kt=35,pooq='K06',logo='http://img.pooq.co.kr/BMS/ChannelImg/11_kbs Drama.png'),
dict(cid='KBS-4',name='KBS JOY',chnum=41,kt=41,lg=619,pooq='K04',logo='http://img.pooq.co.kr/BMS/ChannelImg/12_kbs Joy.png'),
dict(cid='KBS-5',name='KBSN Life',chnum=281,kt=281,lg=582,pooq='K05',logo='http://img.pooq.co.kr/BMS/ChannelImg/13_kbs N life.png'),
dict(cid='KBS-6',name='KBSN PLUS',chnum=23,pooq='K23',skip='naver',logo='http://img.pooq.co.kr/BMS/Channelimage30/image/KBSN-2.png'),
dict(cid='KBS-7',name='KBS W',chnum=83,kt=83,lg=620,pooq='K09',logo='http://img.pooq.co.kr/BMS/ChannelImg/14_kbs W.png'),
dict(cid='KBS-8',name='KBS1 RADIO',chnum=501,pooq='K07',logo='http://img.pooq.co.kr/BMS/ChannelImg/44_kbs 1 radio.png'),
dict(cid='KBS-9',name='KBS2 FM',chnum=502,pooq='K08',logo='http://img.pooq.co.kr/BMS/ChannelImg/45_KBS coolFM.png'),
dict(cid='KBS-10',name='KBS 1박 2일',chnum=400,pooq='K15',only='pooq',logo='img.pooq.co.kr/BMS/ChannelImg/25_kbs1박2일.png'),
dict(cid='KBS-11',name='KBS 남자의 자격',chnum=401,pooq='K18',only='pooq',logo='img.pooq.co.kr/BMS/ChannelImg/K18.png'),
dict(cid='KBS-12',name='KBS 슈퍼맨이 돌아왔다',chnum=402,pooq='K24',only='pooq',logo='img.pooq.co.kr/BMS/Channelimage30/image/superman-2.png'),
dict(cid='KISS-1',name='KISS - 최신인기가요',chnum=601,pooq='C2701',only='pooq',logo='img.pooq.co.kr/BMS/ChannelImg/51_Kiss 최신인기가요.png'),
dict(cid='KISS-2',name='KISS - 발라드',chnum=602,pooq='C2702',only='pooq',logo='img.pooq.co.kr/BMS/ChannelImg/52_Kiss 발라드.png'),
dict(cid='KISS-3',name='KISS - 8090인기가요',chnum=603,pooq='C2703',only='pooq',logo='img.pooq.co.kr/BMS/ChannelImg/unnamed.png'),
dict(cid='KISS-4',name='KISS - K-POP 아이돌',chnum=604,pooq='C2704',only='pooq',logo='img.pooq.co.kr/BMS/ChannelImg/C2704.png'),
dict(cid='KISS-5',name='KISS - 2000년대 인기가요',chnum=605,pooq='C2705',only='pooq',logo='img.pooq.co.kr/BMS/ChannelImg/55_Kiss 2000년대인기가요.png'),
dict(cid='KISS-6',name='KISS - 재즈 라운지',chnum=606,pooq='C2706',only='pooq',logo='img.pooq.co.kr/BMS/ChannelImg/56_Kiss all that jazz.png'),
dict(cid='LIFETIME-1',name='라이프타임',chnum=78,kt=78,lg=603,pooq='C5902',tving='C00611',logo='http://img.pooq.co.kr/BMS/Channelimage30/image/lifetime-2.png'),
dict(cid='MBC-1',name='MBC',chnum=11,kt=11,lg=503,pooq='M01',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/11.png'),
dict(cid='MBC-2',name='MBC 드라마넷',chnum=3,kt=3,lg=621,pooq='M02',logo='http://img.pooq.co.kr/BMS/ChannelImg/17_MBC drama.png'),
dict(cid='MBC-3',name='MBC EVERY1',chnum=0,kt=1,lg=626,pooq='M03',logo='http://img.pooq.co.kr/BMS/ChannelImg/18_MBC every1.png'),
dict(cid='MBC-4',name='MBC Music',chnum=97,kt=97,lg=624,pooq='M06',logo='http://img.pooq.co.kr/BMS/ChannelImg/16_MBC music.png'),
dict(cid='MBC-5',name='MBC 표준 FM',chnum=503,pooq='M07',logo='http://img.pooq.co.kr/BMS/ChannelImg/46_MBC 표준fm.png'),
dict(cid='MBC-6',name='MBC FM4U',chnum=504,pooq='M08',logo='http://img.pooq.co.kr/BMS/ChannelImg/47_MBC fm4U.png'),
dict(cid='MBC-7',name='MBC 무한도전',chnum=410,pooq='PM1',only='pooq',logo='img.pooq.co.kr/BMS/ChannelImg/23_MBC 무한도전.png'),
dict(cid='MBC-8',name='MBC 나 혼자 산다',chnum=411,pooq='PM2',only='pooq',logo='img.pooq.co.kr/BMS/ChannelImg/alone_tv.png'),
dict(cid='MBC-9',name='MBC 라디오스타',chnum=412,pooq='M12',only='pooq',logo='img.pooq.co.kr/BMS/ChannelImg/radiostar.png'),
dict(cid='MBC-10',name='MBC 서프라이즈',chnum=413,pooq='M13',only='pooq',logo='img.pooq.co.kr/BMS/ChannelImg/surprise_2.png'),
dict(cid='MBN-1',name='MBN',chnum=16,kt=16,lg=750,pooq='C2401',tving='C00708',logo='http://img.pooq.co.kr/BMS/ChannelImg/02_MBN.png'),
dict(cid='MBN-2',name='MBN Plus',chnum=99,kt=99,lg=787,tving='C17142',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C17142.png'),
dict(cid='MNET-1',name='Mnet',chnum=27,kt=27,lg=687,tving='C00579',logo='http://image.tving.com/upload/cms/caic/CAIC0300/C00579.png'),
dict(cid='NICKELODEON-1',name='Nickelodeon',chnum=992,kt=992,lg=635,pooq='S10',logo='http://img.pooq.co.kr/BMS/ChannelImg/35_nick.png'),
dict(cid='TVN-1',name='tvN',chnum=17,kt=17,lg=682,tving='C00551',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C00551.png'),
dict(cid='TVN-2',name='XtvN',chnum=76,kt=76,lg=671,tving='C01141',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C01141.png'),
dict(cid='TVN-3',name='O tvN',chnum=45,kt=45,lg=689,tving='C01143',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C01143.png'),
dict(cid='OGN-1',name='OGN',chnum=123,kt=123,lg=681,tving='C00590',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C00590.png'),
dict(cid='OLIVE-1',name='Olive',chnum=34,kt=34,lg=696,tving='C00575',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C00575.png'),
dict(cid='ONSTYLE-1',name='ONSTYLE',chnum=77,kt=77,lg=778,tving='C01142',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C01142.png'),
dict(cid='PLAYY-1',name='PLAYY 웰메이드 영화',chnum=440,pooq='H01',only='pooq',logo='img.pooq.co.kr/BMS/ChannelImg/28_playy월메이드영화.png'),
dict(cid='PLAYY-2',name='PLAYY 액션영화',chnum=441,pooq='H07',only='pooq',logo='img.pooq.co.kr/BMS/ChannelImg/29_playy액션영화.png'),
dict(cid='POLARIS-1',name='폴라리스TV',chnum=253,kt=253,lg=726,pooq='C6901',skip='daum',logo='http://img.pooq.co.kr/BMS/Channelimage30/image/Polaris-2.png'),
dict(cid='SBS-1',name='SBS',chnum=5,kt=5,lg=504,pooq='S01',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/5.png'),
dict(cid='SBS-2',name='SBS funE',chnum=43,kt=43,lg=615,pooq='S04',logo='http://img.pooq.co.kr/BMS/ChannelImg/20_sbs FunE.png'),
dict(cid='SBS-3',name='SBS Plus',chnum=37,kt=37,lg=612,pooq='S03',logo='http://img.pooq.co.kr/BMS/ChannelImg/21_sbs Plus.png'),
dict(cid='SBS-4',name='SBS MTV',chnum=96,kt=96,lg=634,pooq='S09',logo='http://img.pooq.co.kr/BMS/ChannelImg/22_sbs MTV.png'),
dict(cid='SBS-5',name='SBS Sports',chnum=58,kt=58,lg=613,pooq='S02',logo='http://img.pooq.co.kr/BMS/ChannelImg/42_sbs Sports.png'),
dict(cid='SBS-6',name='SBS CNBC',chnum=25,kt=25,lg=616,pooq='S06',logo='http://img.pooq.co.kr/BMS/ChannelImg/06_sbs CNBC.png'),
dict(cid='SBS-7',name='SBS 파워FM',chnum=505,pooq='S07',logo='http://img.pooq.co.kr/BMS/ChannelImg/48_sbs 파워fm.png'),
dict(cid='SBS-8',name='SBS 러브FM',chnum=506,pooq='S08',logo='http://img.pooq.co.kr/BMS/ChannelImg/49_sbs 러브fm.png'),
dict(cid='SBS-9',name='SBS Mobidic',chnum=420,pooq='S13',only='pooq',logo='img.pooq.co.kr/BMS/ChannelImg/mobidic.png'),
dict(cid='SBS-10',name='SBS THE K-POP',chnum=421,pooq='S14',only='pooq',logo='img.pooq.co.kr/BMS/Channelimage30/image/THE_K-POP-2.png'),
dict(cid='SBS-11',name='SBS TV동물농장',chnum=422,pooq='S15',only='pooq',logo='img.pooq.co.kr/BMS/Channelimage30/image/S15-2.png'),
dict(cid='SBS-12',name='SBS 런닝맨',chnum=423,pooq='S16',only='pooq',logo='img.pooq.co.kr/BMS/Channelimage30/image/S16-2.png'),
dict(cid='SPOTV-1',name='SPOTV GAMES',chnum=124,kt=124,lg=727,pooq='C5401',logo='http://img.pooq.co.kr/BMS/ChannelImg/스포TV.png'),
dict(cid='TVCHOSUN-1',name='TV 조선',chnum=19,kt=19,lg=746,pooq='C2601',tving='C01581',logo='http://img.pooq.co.kr/BMS/Channelimage30/image/180_24.png'),
dict(cid='TVCHOSUN-2',name='TV 조선 2',chnum=69,kt=69,lg=775,tving='C00585',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C00585.png'),
dict(cid='TOONIVERSE-1',name='투니버스',chnum=996,kt=996,lg=693,tving='C06941',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C06941.png'),
dict(cid='YONHAPNEWS-1',name='연합뉴스TV',chnum=23,kt=23,lg=734,pooq='Y01',tving='C01723',logo='http://img.pooq.co.kr/BMS/ChannelImg/05_연합뉴스TV.png'),
dict(cid='YTN-1',name='YTN',chnum=24,kt=24,lg=698,pooq='C2101',tving='C00593',logo='http://img.pooq.co.kr/BMS/ChannelImg/07_ytn.png'),
dict(cid='YTN-2',name='YTN Life',chnum=190,kt=190,lg=655,tving='C01101',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C01101.png'),
dict(cid='YTN-3',name='YTN사이언스',chnum=175,kt=175,lg=755,tving='C15347',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C15347.png'),
dict(cid='ZHTV-1',name='중화TV',chnum=110,kt=110,lg=725,tving='C00544',logo='http://image.tving.com/upload/cms/caic/CAIC0400/C00544.png'),
dict(cid='GSSHOP-1',name='GS SHOP',chnum=8,kt=8,lg=676,pooq='C4201',logo='http://img.pooq.co.kr/BMS/ChannelImg/59_GSshop.png'),
dict(cid='GSSHOP-2',name='GS MY SHOP',chnum=38,kt=38,lg=740,pooq='C4202',only='kt|lg|pooq',logo='http://img.pooq.co.kr/BMS/ChannelImg/60_GSmyshop.png'),
dict(cid='HYUNDAI-1',name='현대홈쇼핑',chnum=10,kt=10,lg=675,pooq='C4101',logo='http://img.pooq.co.kr/BMS/ChannelImg/61_현대홈쇼핑.png'),
dict(cid='HYUNDAI-2',name='현대홈쇼핑+샵',chnum=36,kt=36,lg=760,pooq='C4102',only='kt|lg|pooq',logo='http://img.pooq.co.kr/BMS/ChannelImg/62_현대홈쇼핑plus샵.png'),
dict(cid='CJOSHOP-1',name='CJ오쇼핑',chnum=6,kt=6,lg=672,pooq='C4701',logo='http://img.pooq.co.kr/BMS/ChannelImg/CJO_2_180_24.png'),
dict(cid='CJOSHOP-2',name='CJ오쇼핑 플러스',chnum=28,kt=28,lg=781,pooq='C4702',only='kt|lg|pooq',logo='http://img.pooq.co.kr/BMS/ChannelImg/CJOP2_180_24.png'),
dict(cid='SHOPANDT-1',name='쇼핑엔T',chnum=33,kt=33,lg=782,pooq='C4901',only='kt|lg|pooq',logo='http://img.pooq.co.kr/BMS/ChannelImg/63_쇼핑엔티.png'),
dict(cid='SHINSEGAE-1',name='신세계TV쇼핑',chnum=2,kt=2,lg=780,pooq='C4801',only='kt|lg|pooq',logo='http://img.pooq.co.kr/BMS/ChannelImg/shin_180x24_re.png'),
dict(cid='LOTTESHOP-1',name='롯데홈쇼핑',chnum=30,kt=30,lg=674,pooq='C5601',logo='http://img.pooq.co.kr/BMS/Channelimage30/image/lotte-2.png'),
]
