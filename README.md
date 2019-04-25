Gathermate
==========

`Gathermate`는 특정 웹페이지의 콘텐츠를 수집 및 재가공하여 서버 형태로 제공하는 프로그램입니다. 서버이긴 하지만 반드시 **본인**만 접속할 수 있도록 설정하시길 바랍니다. 웹 상에서 수집한 콘텐츠를 타인에게 노출시킬 경우 법적으로 문제가 될 수 있기 때문입니다.

`Gathermate`는 [Google App Engine Python 2 Standard](https://cloud.google.com/appengine/docs/standard/python/)에 맞추어 `python 2.7`로 작성되었습니다.

파이썬 추가 패키지

- lxml
- requests
- futures
- flask
- flask-Caching
- gunicorn
- tld
- m3u8
- pycrypto
- gevent

---

설치하기
--------
### 디렉토리 계층
```plain
opt/
    apps/
        gathermate/
            apps/
                callmewhen/
                common/
                scrapmate/
                    boards/
                    static/
                    templates/
                streamate/
                    epggrabbers/
                    static/
                    streamers/
                    templates/
            install/
            instance/
                cookies/
            static/
            templates/
            venv/
                bin/
                gae/
                    lib/
                        chardet/
                        concurrent/
                        flask_caching/
                        tld/
                include/
                lib/
                local/
```

### 스크립트로 일괄 설치하기

##### 아래의 명령어 중 하나로 `/opt/apps`폴더에 `install-gathermate.sh` 스크립트를 다운로드합니다.
```shell
curl -L https://raw.githubusercontent.com/gathermate/gathermate/master/install/install-gathermate.sh > /opt/apps/install-gathermate.sh
```

```shell
wget -O /opt/apps/install-gathermate.sh https://raw.githubusercontent.com/gathermate/gathermate/master/install/install-gathermate.sh
```

##### 설치 스크립트에 실행권한을 부여합니다.
```shell
chmod +x /opt/apps/install-gathermate.sh
```

##### 설치하기
```shell
/opt/apps/install-gathermate.sh -i entware # 엔트웨어
/opt/apps/install-gathermate.sh -i debian # 데비안
```

##### 제거하기
```shell
/opt/apps/install-gathermate.sh -u entware # 엔트웨어
/opt/apps/install-gathermate.sh -u debian # 데비안
```

### 개별 설치하기
Debian, Ubuntu는 `Windows Subsystem for Linux` 환경에서 테스트 했습니다.

#### 1. 소스파일 복사
Git에서 소스 파일을 받아 `/opt/apps/gathermate` 폴더에 저장합니다.

##### Git 설치
```shell
# Entware on ASUS RT-AC68U aka T-mobile AC1900
opkg update
opkg install git git-http
```
```shell
# Debian/Ubuntu on WSL
apt update
apt install git
```

##### 저장소 복사
```shell
git clone https://github.com/gathermate/gathermate.git /opt/apps/gathermate
```

#### 2. 파이썬 2.7 및 추가 패키지 설치
`python 2.7`, `python-pip`을 설치합니다. [Entware][entware]는 추가로 `python-lxml`, `python-gevent`, `python-crypto`를 설치합니다. `pip`으로 설치할 경우 일부 파이썬 패키지는 설치 과정 중 컴파일에 필요한 헤더 파일을 찾을 수 없어 오류가 발생합니다. [Entware][entware]에는 컴파일에 필요한 헤더 파일이 기본 탑재되어 있지 않으므로 미리 컴파일된 패키지를 설치합니다. 자세한 [Entware][entware] 컴파일 정보는 [Using gcc](https://github.com/Entware/Entware-ng/wiki/Using-gcc-(native-compilation))를 참조하세요.

[entware]: https://github.com/Entware/Entware

```shell
# Entware on ASUS RT-AC68U aka T-mobile AC1900
opkg install python-light python-pip python-lxml python-gevent python-crypto ffmpeg
```
```shell
# Debian/Ubuntu on WSL
apt install python-minimal python-pip ffmpeg
```

#### 3. 파이썬 가상환경 만들기

```shell
pip install virtualenv
virtualenv -p python2 /opt/apps/gathermate/venv
source /opt/apps/gathermate/venv/bin/activate
```

#### 4. 파이썬 패키지 설치
가상환경 내에서 `python` 추가 패키지를 설치합니다. Entware는 `opkg`로 설치한 `lxml`, `crypto`, `gevent` 패키지도 가상환경 폴더에 복사해 주세요.

```shell
# Entware on ASUS RT-AC68U aka T-mobile AC1900
pip install -r /opt/apps/gathermate/install/requirements-entware.txt
cp -r /opt/lib/python2.7/site-packages/lxml* /opt/apps/gathermate/venv/lib/python2.7/site-packages/
cp -r /opt/lib/python2.7/site-packages/Crypto /opt/apps/gathermate/venv/lib/python2.7/site-packages/
cp -r /opt/lib/python2.7/site-packages/gevent /opt/lib/python2.7/site-packages/greenlet.so /opt/apps/gathermate/venv/lib/python2.7/site-packages/
```
```shell
# Debian/Ubuntu on WSL
pip install -r /opt/apps/gathermate/install/requirements.txt
```

##### GAE 파이썬 패키지 설치
GAE에서 서버를 운영할 경우 설치하세요.

```shell
pip install -t /opt/apps/gathermate/venv/gae/lib -r /opt/apps/gathermate/install/requirements-gae.txt --no-dependencies
```

혹은 가상환경 내 이미 설치한 일부 패키지 (chardet, concurrent, flask_caching)를 `venv/gae/lib` 폴더로 복사
```shell
mkdir -p /opt/apps/gathermate/venv/gae/lib
cd /opt/apps/gathermate/venv/lib/python2.7/site-packages
cp -r chardet concurrent flask_caching tld m3u8 iso8601 /opt/apps/gathermate/venv/gae/lib/
```

#### 5. 실행하기
**설정하기를 읽어본 후 실행하기를 권장합니다.**

##### 설정 파일 복사
사용자 설정 파일 `/opt/apps/gathermate/install/user_config.py`를 `/opt/apps/gathermate/instance/` 폴더로 복사하고 파일 이름을 `config.py`로 변경합니다.

```shell
mkdir /opt/apps/gathermate/instance
cp /opt/apps/gathermate/install/user_config.py /opt/apps/gathermate/instance/config.py
```

##### 데몬 스크립트 복사

`/opt/apps/gathermate/install` 폴더의 데몬 스크립트를 `init.d` 폴더로 복사하면서 파일 이름을 변경합니다. 실행권한도 부여합니다.
```shell
# Entware on ASUS RT-AC68U aka T-mobile AC1900
cp /opt/apps/gathermate/install/daemon-entware /opt/etc/init.d/S89gathermate
chmod +x /opt/etc/init.d/S89gathermate
```
```shell
# Debian/Ubuntu on WSL
cp /opt/apps/gathermate/install/daemon-debian /etc/init.d/gathermate
chmod +x /etc/init.d/gathermate
```

복사한 스크립트 내 포트 번호를 확인 후 원하는 포트로 변경해 주세요.
```shell
BIND=0.0.0.0:8181
```

##### 실행하기

```shell
# Entware on ASUS RT-AC68U aka T-mobile AC1900
/opt/etc/init.d/S89gathermate start
```
```shell
# Debian/Ubuntu on WSL
sudo service gathermate start
```

`공유기_주소:8181/scrap`로 접속하여 "Welcome" 페이지가 나오는지 확인.

설정하기
--------
실행시 `instance/config.py` 파일의 설정을 사용하게 됩니다. 설정 수정은 꼭 `instance/config.py`에서 해주세요. Google App Engine 환경이 아닌 직접 서버를 운영할 경우 Localhost 클래스의 설정을 수정하면 됩니다.

#### 꼭 변경해야 하는 값들

아래의 값은 반드시 기본 설정과 다르게 설정하세요.

- **AUTH_ID** : 서버에 요청을 보낼 때 요구되는 **아이디** 입니다.
- **AUTH_PW** : 서버에 요청을 보낼 때 요구되는 **비밀번호** 입니다.

#### 설정 값 입력하기

민감한 정보는 기본적으로 `os.environ.get()` 를 통해 `export`된 값을 불러오도록 되어 있습니다. `os.environ.get()`이 어떤 이름의 환경변수를 가져오는지 확인한 다음 데몬 스크립트에서 `export` 해 주면 됩니다. GAE는 `app.yaml`에서 `export`할 값을 입력할 수 있습니다. 또는 직접 `instance/config.py`에 입력하세요.

데몬 스크립트에는 아래의 환경 변수가 기본값으로 입력되어 있습니다.
```shell
export GATHERMATE_AUTH_ID=admin
export GATHERMATE_AUTH_PW=password
```

`export` 변수명을 바꿀 경우:
```shell
export MY_AUTH_ID="admin" # 데몬 스크립트
```
```python
AUTH_ID = os.environ.get('MY_AUTH_ID') # instance/config.py
```

`instance/config.py`에 직접 입력할 경우:

```python
AUTH_ID = 'admin' # instance/config.py
```

사용법
------
**당연한 이야기이지만 해당 사이트의 콘텐츠 수집 코드가 `Scraper`, `Streamer`, `EpgGrabber`의 서브 클래스로 구현되어 있어야 합니다.**

### Scrapmate

<table>
    <thead>
        <tr>
            <th>유형</th>
            <th>형식</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan="2"><b>목록</b></td>
            <td>scrap/<code>사이트</code>/<code>게시판</code>?search=<code>검색어</code>&page=<code>3</code><br/><code>scrap/wal/torrent_movie</code></td>
        </tr>
        <tr>
            <td>scrap/list?url=<code>encoded-url</code>&search=<code>검색어</code>&page=<code>2</code><br/><code>scrap/list?url=https%3A%2F%2Fwww.google.com%2F%3Fsearch%3Dtorrent</code></td>
        </tr>
        <tr>
            <td rowspan="2"><b>RSS</b></td>
            <td>scrap/<code>사이트</code>/<code>게시판</code>/rss?search=<code>검색어</code>&page=<code>3</code>&length=<code>5</code><br/><code>scrap/tfreeca/tent/rss</code></td>
        </tr>
        <tr>
            <td>scrap/rss?url=<code>encoded-url</code>&search=<code>검색어</code>&page=<code>1</code>&length=<code>5</code><br/><code>scrap/rss?url=https%3A%2F%2Fwww.google.com%2F%3Fsearch%3Drss</code></td>
        </tr>
        <tr>
            <td><b>글</b></td>
            <td>scrap/item?url=<code>encoded-url</code><br/><code>scrap/item?url=https%3A%2F%2Fwww.google.com%2F%3Fsearch%3Ditem</code></td>
        </tr>
        <tr>
            <td><b>다운로드</b></td>
            <td>scrap/down?url=<code>encoded-url</code>&ticket=<code>encoded-query-string</code><br/><code>scrap/down?url=https%3A%2F%2Fwww.google.com%2F%3Fsearch%3Dfile&ticket=referer...</code></td>
        </tr>
        <tr>
            <td><b>사용자 정의</b></td>
            <td>scrap/page?url=<code>encoded-url</code><br/><code>scrap/page?url=https%3A%2F%2Fwww.google.com%2F%3Fsearch%3Dpage</code></td>
        </tr>
    </tbody>
</table>


- `사이트`가 `Gatherer`의 `URL` 속성과 매치가 된다면 해당 클래스로 요청을 처리합니다. 예를 들어 `ple-1`은 `https://www.sample-1.co.kr`, `https://www.samplesample.com` 중에서 첫번째와 매치됩니다.
- `게시판`은 해당 사이트에서 사용하는 게시판 아이디를 그대로 입력해 주세요.
- `encoded-url`과 `encoded-query-string`에는 URL 인코딩된 값을 넣어야 합니다. URL 인코딩이란 `:`, `/`, `=` 등 URL을 인식하는데 방해가 되는 문자들을 16진수로 변환시키는 것을 말합니다. 예를 들어 `https://www.google.com/?search=torrent`를 인코딩 할 경우 `https%3A%2F%2Fwww.google.com%2F%3Fsearch%3Dtorrent`의 형태가 됩니다. `http://서버주소:8181/scrap/encode` 페이지에서 간단한 URL 인코딩이 가능합니다. 혹은 [G Suite 도구상자](https://toolbox.googleapps.com/apps/encode_decode/)를 이용하세요.
- `검색어`와 `page` 인수에 입력된 값은 목표 사이트의 설정에 따라 변환되어 URL 쿼리로 삽입됩니다.
- `ticket` 인수는 파일을 다운로드 할 때 필요한 정보입니다.
- `length` 인수는 RSS에서만 적용되며 해당 리스트에서 수집할 게시물의 수 입니다.

`RSS_AGGRESSIVE` 설정이 `True`인 상태에서 RSS 요청시 `리스트 페이지 접속 및 수집` -> `각 게시물에 접속 및 수집`의 과정을 거칩니다. 한번에 여러 페이지를 접속하기 때문에 되도록이면 `length`값을 5 이하로 사용하시길 바랍니다. 만약 `length` 값이 5라면 리스트 페이지 1, 게시물 5, 총 6 개의 페이지를 한번에 접속하게 됩니다.

`RSS_AGGRESSIVE`가 `False`인 상태에서 RSS 요청시 리스트 페이지에서 게시물만 수집합니다. 이후 다운로드 과정에서 해당 게시물에 접속해 첨부된 링크 혹은 파일 중 조건에 맞는 아이템을 다운로드 합니다. RSS에 다운 가능한 파일을 명시할 수 없기 때문에 다운로드에 실패할 가능성이 높습니다.

#### Flexget 설정
```yaml
inputs:
  - rss:
      url: 'http://127.0.0.1:8181/scrap/google/drama/rss?search=-NEXT'
      username: 'MY_ID'
      password: 'MY_PATH'
```
```yaml
download_auth:
- 127.0.0.1:8181:
    username: 'MY_ID'
    password: 'MY_PATH'
    type: basic
```

---

### Streamate

<table>
    <thead>
        <tr>
            <th>유형</th>
            <th>형식</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>모든 스트리머의 재생목록</td>
            <td>stream/<code>원하는파일이름</code>.m3u?ffmpeg=<code>ffmpeg실행경로</code><br/><code>stream/myserverplaylist.m3u?ffmpeg=/usr/bin/ffmpeg</code></td>
        </tr>
        <tr>
            <td>특정 스트리머의 재생목록</td>
            <td>stream/<code>사이트</code>/<code>원하는파일이름</code>.m3u?ffmpeg=<code>ffmpeg실행경로</code><br/><code>stream/pooq/pooq.m3u?ffmpeg=/opt/bin/ffmpeg</code></td>
        </tr>
        <tr>
            <td>EPG 수집</td>
            <td>stream/<code>원하는파일이름</code>.xml?grabber=<code>그래버이름</code>&grabber=<code>그래버이름</code>&days=<code>기간</code><br/><code>stream/all-epg.xml?grabber=naver&grabber=daum&grabber=pooq&days=2</code></td>
        </tr>
        <tr>
            <td>채널 정보</td>
            <td>stream/<code>사이트</code>/channels<br/><code>stream/tving/channels</code></td>
        </tr>
        <tr>
            <td>스트리밍</td>
            <td>stream/<code>사이트</code>/<code>채널아이디</code>?q=<code>퀄리티</code><br/><code>stream/pooq/K01?q=0</code></td>
        </tr>
    </tbody>
</table>

- 모든 쿼리는 생략 가능합니다.
- `m3u`와 `xml` 파일은 원하는 이름을 지정하여 다운로드 할 수 있습니다.
- `ffmpeg` 쿼리에 ffmpeg의 실행경로를 입력하면 재생목록의 스트리밍 주소를 `pipe://ffmpg경로 -i 스트리밍주소 -c copy -f mpegts pipe:1` 형태로 저장할 수 있습니다. `tvheadend`의 먹스로 등록할 경우 필요합니다.
- EPG 수집시 `grabber` 쿼리를 지정하지 않으면 등록된 모든 그래버를 활용하여 EPG를 수집합니다. `grabber` 쿼리는 여러번 지정 가능합니다.
- `days` 쿼리에 정수를 입력하면 해당 기간만큼의 EPG를 수집합니다. 수집에 많은 자원이 소모되므로 `1~2`를 추천합니다.
- 채널 정보는 단순히 해당 사이트에서 수집한 채널 목록을 보여줍니다.
- 스트리밍의 `채널아이디`는 해당 사이트에서 사용하는 `채널아이디`를 입력해야 합니다. 대상 사이트에서 여러 스트리밍 해상도를 제공할 경우 `q` 쿼리에 정수(0~n)를 입력하여 스트리밍 해상도를 지정할 수 있습니다.

---

그 밖에...
---------

#### GAE
현재 Google App Engine의 Python 3 환경은 무료 사용량의 초과분에 대한 결제가 필수입니다. 때문에 무료 사용량 초과시 차단되는 방식인 Python 2 Standard 환경에 맞추었습니다. [Google App Engine 시작하기](https://cloud.google.com/appengine/docs/standard/python/quickstart)

##### GAE 개발 서버 라이브러리 설치

플랫폼 패키지 관리자(apt, opkg)를 통해 lxml을 설치후 아래 GAE용 가상환경을 설치해 주세요.
```shell
pip install -t venv/gae/lib -r install/requirements-gae.txt
```