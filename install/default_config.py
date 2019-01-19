# -*- coding: utf-8 -*-

import os
import copy

class Flask(object):
    '''
    Flask의 설정은 Flask 문서를 참조해 주세요.
    '''
    SECRET_KEY = os.urandom(32).encode('hex')

class Localhost(Flask):
    '''
    로컬호스트에서 운영시 불러오는 설정 값입니다.
    '''
    # 이 설정 클래스의 이름입니다.
    NAME = 'Localhost @ default'

    # 서버 주소의 PATH에 해당하는 값입니다.
    # http://www.yourserver.com/PATH/list?query=2
    PATH = '/gather'

    # Manager 모듈을 불러오기 위한 값입니다.
    # 다른 매니저로 교체하고 싶을 경우 해당 모듈의 패키지를 입력해 주세요.
    MANAGER = 'apps.gathermate.manager'

    # 시작시 아래 딕셔너리의 블루프린트가 등록됩니다.
    # instance는 해당 'package'에 명시된 블루프린트 객체의 변수명을 입력하세요.
    BLUEPRINTS = {
        'Gathermate': {
            'package': 'apps.gathermate.views',
            'instance': 'gathermate',
            'url_prefix': PATH,
        },
    }

    # 개발 서버와 GAE의 로그 레벨입니다.
    # gunicorn으로 실행시 gunicorn의 로그 레벨을 따릅니다.
    LOG_LEVEL = 'DEBUG'

    # 플라스크 서버로부터 받는 응답(RSS 또는 웹페이지)의 캐쉬 지속시간(초)입니다.
    # 동일한 요청이라 판단될 경우 캐쉬된 결과물로 응답합니다.
    # 0으로 설정시 캐쉬가 계속 유지됩니다.
    TIMEOUT = 5

    # HTTP Basic Authentication에 사용될 아이디와 비밀번호입니다.
    # gunicorn 실행 파일에 export로 설정해 주거나 여기에 직접 입력하세요.
    AUTH_ID = os.environ.get('GATHERMATE_AUTH_ID', None)
    AUTH_PW = os.environ.get('GATHERMATE_AUTH_PW', None)

    # True일 경우 RSS 생성시 대상으로 선정된 게시물에 추가로 접속하여
    # 미리 내용물을 가져옵니다. 대상 사이트에 부담이 될 수 있습니다.
    # False일 경우 다운로드 과정에서 내용물을 확인하고 예측하여 다운로드 합니다.
    RSS_AGGRESSIVE = False

    # RSS_AGGRESSIVE가 True일 때 적용됩니다.
    # False일 경우 여러 게시물을 순차적으로 접속하여 파싱합니다.
    # True일 경우 여러 게시물을 동시에 접속하여 파싱합니다.
    RSS_ASYNC = False

    # RSS_ASYNC 값이 True일 때 적용되는 쓰레드 수 입니다.
    # 반드시 0 보다 큰 값이어야 합니다.
    RSS_WORKERS = 5

    # RSS를 생성할 때 참고할 게시물의 수 입니다.
    # RSS_AGGRESSIVE가 True일 경우 5가 적당합니다. (5일 경우 대상 사이트에 총 6번 접속)
    # 대상 사이트의 페이지별 게시물 수를 고려해서 입력하세요.
    RSS_LENGTH = 5

    # RSS_AGGRESSIVE가 False일 때 다운로드할 파일의 우선 순위입니다.
    # 아래 리스트의 정규 표현식으로 파일 이름을 순차적으로 검사합니다.
    # 제일 먼저 매치되는 파일을 다운로드 하거나 매치되는 파일이 없으면
    # 첫번째 파일을 다운로드 합니다.
    RSS_WANT = ['1080(?i)P', '(?i)bluray']

    # 아래의 확장자를 가진 파일만 표시합니다.
    ACCEPTED_EXT = ['.torrent', '.smi', '.srt', '.zip', '.rar']

    # 사이트별 설정입니다.
    # 사이트의 이름은 해당 사이트의 클래스명과 같아야 합니다.
    # 사이트의 인코딩이나 ASYNC, 로그인 정보 등을 설정할 수 있습니다.
    GATHERERS = {
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
            'mb_id': os.environ.get('GATHERMATE_CINE_ID', None),
            'mb_password': os.environ.get('GATHERMATE_CINE_PW', None),
        },
    }
    FETCHER = {
        # 목표 웹 페이지의 캐쉬 지속시간(초) 입니다.
        # 목표 웹 페이지에 대한 너무 잦은 요청과 불필요한 트래픽 발생을
        # 방지하기 위해서 각 목표 웹페이지는 캐쉬로 저장됩니다.
        # 0으로 설정시 캐쉬가 계속 유지됩니다.
        'CACHE_TIMEOUT': 120,

        # 목표 웹 페이지에서 받아온 쿠키가 유지되는 시간(초)입니다.
        # 쿠키도 캐쉬에 저장됩니다.
        'COOKIE_TIMEOUT': 3600,

        # 목표 웹페이지의 응답을 기다리는 최대 시간(초)입니다.
        'DEADLINE': 60,
    }


# Localhost의 설정을 불러올때 사용합니다.
LOCALHOST = Localhost()


class GoogleAppEngine(Localhost):
    '''
    만약 구글 앱 엔진에서 운영할 계획이 없다면 이 클래스는 없어도 무방합니다.
    삭제시 아래의 GOOGLEAPPENGINE = GoogleAppEngine() 도 함께 삭제해 주세요.
    사용한다면 app.yaml에서 export 값을 지정하거나 여기에 직접 입력하세요.
    아래는 설정 예시입니다.
    '''
    NAME = 'GoogleAppEngine @ default'
    AUTH_ID = 'Please change me and keep me a secret.'
    AUTH_PW = 'Please change me and keep me a secret.'

    GATHERERS = copy.deepcopy(Localhost.GATHERERS)

    GATHERERS['Etoland'] = {
        'mb_id': 'Please change me and keep me a secret.',
        'mb_password': 'Please change me and keep me a secret.',
    }


# GoogleAppEngine의 설정을 불러올때 사용합니다.
GOOGLEAPPENGINE = GoogleAppEngine()
