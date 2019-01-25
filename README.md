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

---

설치하기
--------
### 디렉토리 계층
```plain
opt/
    apps/
        my-flask-server/
            apps/
                common/
                gathermate/
                    gatherers/
                    static/
                    templates/
            install/
            instance/
            static/
            templates/            
            var/
                log/
                run/
            venv/
                bin/
                gae/
                    lib/
                        chardet/
                        concurrent/
                        flask_caching/
                include/
                lib/
                local/
```

### 스크립트로 일괄 설치하기

##### 아래의 명령어로 `/opt/apps`폴더에 `install-gathermate.sh` 스크립트를 다운로드합니다.
```shell
curl -L https://raw.githubusercontent.com/gathermate/gathermate/master/install/install-gathermate.sh > /opt/apps/install-gathermate.sh
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
##### 외부 접속 차단
개별 설치하기를 참고하세요.

### 개별 설치하기
Debian, Ubuntu는 `Windows Subsystem for Linux` 환경에서 테스트 했습니다.

#### 1. 소스파일 복사
Git에서 소스 파일을 받아 `/opt/apps/my-flask-server` 폴더에 저장합니다.

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
git clone https://github.com/gathermate/gathermate.git /opt/apps/my-flask-server
```

#### 2. 파이썬 2.7 설치
`python 2.7`, `python-pip`을 설치합니다. Entware는 추가로 `python-lxml`을 설치합니다. `lxml`을 [Entware][entware] 패키지에서 설치하는 이유는 `pip`으로 설치할 경우 컴파일 오류가 발생하기 때문입니다. `lxml`을 컴파일하려면 헤더 파일이 필요한데 [Entware][entware]에는 기본 탑재되어 있지 않습니다. 그래도 정말 컴파일 하기를 원한다면 [Using gcc](https://github.com/Entware/Entware-ng/wiki/Using-gcc-(native-compilation))를 참조하세요.
[entware]: https://github.com/Entware/Entware
    
```shell
# Entware on ASUS RT-AC68U aka T-mobile AC1900
opkg install python-light python-pip python-lxml
```
```shell
# Debian/Ubuntu on WSL
apt install python-minimal python-pip
```

#### 3. 파이썬 가상환경 만들기

```shell
pip install virtualenv
virtualenv -p python2 /opt/apps/my-flask-server/venv
source /opt/apps/my-flask-server/venv/bin/activate
```

#### 4. 파이썬 패키지 설치
가상환경 내에서 `python` 추가 패키지를 설치합니다. Entware는 `opkg`로 설치한 `lxml` 패키지도 가상환경 폴더에 복사해 주세요.
   
```shell 
# Entware on ASUS RT-AC68U aka T-mobile AC1900
pip install -r /opt/apps/my-flask-server/install/requirements-entware.txt
cp -r /opt/lib/python2.7/site-packages/lxml* /opt/apps/my-flask-server/venv/lib/python2.7/site-packages/ 
```
```shell
# Debian/Ubuntu on WSL
pip install -r /opt/apps/my-flask-server/install/requirements.txt
```

#### 5. 실행하기
**설정하기를 읽어본 후 실행하기를 권장합니다.**

##### 설정 파일 복사
사용자 설정 파일 `/opt/apps/my-flask-server/install/user_config.py`를 `/opt/apps/my-flask-server/instance/` 폴더로 복사하면서 파일 이름을 `config.py`로 변경합니다.

```shell
mkdir /opt/apps/my-flask-server/instance
cp /opt/apps/my-flask-server/install/user_config.py /opt/apps/my-flask-server/instance/config.py
```

##### 데몬 스크립트 복사

`/opt/apps/my-flask-server/install` 폴더의 데몬 스크립트를 `init.d` 폴더로 복사하면서 파일 이름을 변경합니다. 실행권한도 부여합니다.
```shell
# Entware on ASUS RT-AC68U aka T-mobile AC1900
cp /opt/apps/my-flask-server/install/daemon-entware /opt/etc/init.d/S89my-flask-server
chmod +x /opt/etc/init.d/S89my-flask-server
```
```shell
# Debian/Ubuntu on WSL
cp /opt/apps/my-flask-server/install/daemon-debian /etc/init.d/my-flask-server
chmod +x /etc/init.d/my-flask-server
```

복사한 스크립트 내 포트 번호를 확인 후 원하는 포트로 변경해 주세요.
```shell
BIND=0.0.0.0:8181
```
   
##### 실행하기 

```shell
# Entware on ASUS RT-AC68U aka T-mobile AC1900
/opt/etc/init.d/S89my-flask-server start
```
```shell
# Debian/Ubuntu on WSL
service my-flask-server start
```

`공유기_주소:8181`로 접속하여 "Welcome" 페이지가 나오는지 확인.

#### 6. 외부 접속 차단
##### Entware on ASUS RT-AC68U aka T-mobile AC1900
`/jffs/scripts/firewall-start`에 아래 내용을 추가합니다. `Insert`로 입력하기 때문에 역순으로 규칙이 적용됩니다.

```shell
#gunicorn
iptables -I INPUT -p tcp --dport 8181 -j DROP # 3. 그 외의 모든 접속 차단
iptables -I INPUT -p tcp -s 192.168.0.0/16 --dport 8181 -j ACCEPT # 2. 내부 아이피의 접속 허용
iptables -I INPUT -p tcp -s localhost --dport 8181 -j ACCEPT # 1. localhost의 접속 허용
```

firewall 서비스 재실행
```shell
service restart_firewall
```

확인
```shell
iptables -L
```

설정하기
--------
서버 실행시 `instance/config.py` 파일의 설정이 덮어씌우기 됩니다. 설정 수정은 꼭 `instance/config.py`에서 해주세요.
#### 꼭 변경해야 하는 값들

아래의 값은 반드시 기본 설정과 다르게 설정하세요.

- **AUTH_ID** : 서버에 요청을 보낼 때 요구되는 **아이디** 입니다.
- **AUTH_PW** : 서버에 요청을 보낼 때 요구되는 **비밀번호** 입니다.
- **PATH** : 서버 URL의 path에 적용됩니다. `http://www.yourserver.com/PATH/?query=2`

#### 설정 값 입력하기

민감한 정보는 기본적으로 `os.environ.get()` 를 통해 `export`된 값을 불러오도록 되어 있습니다. `os.environ.get()`이 어떤 이름의 환경변수를 가져오는지 확인한 다음 데몬 스크립트에서 `export` 해 주면 됩니다. GAE는 `app.yaml`에서 `export`할 값을 입력할 수 있습니다. 이 방법이 어려울 경우 직접 `instance/config.py`에 입력하세요.

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
**당연한 이야기이지만 해당 사이트의 콘텐츠 수집 코드가 `Gatherer`의 서브 클래스로 구현되어 있어야 합니다.**

#### 서버가 처리할 수 있는 요청의 형태는 아래와 같습니다.
<table>
    <thead>
        <tr>
            <th>유형</th>
            <th>형식</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan="2"><center><b>목록</b><center></td>
            <td>gather/<code style="background-color:mistyrose;">사이트</code>/<code style="background-color:mistyrose;">게시판</code>?search=<code style="background-color:mistyrose;">검색어</code>&page=<code style="background-color:mistyrose;">3</code></td>
        </tr>
        <tr>
            <td>gather/list?url=<code style="background-color:mistyrose;">encoded-url</code>&search=<code style="background-color:mistyrose;">검색어</code>&page=<code style="background-color:mistyrose;">2</code></td>
        </tr>
        <tr>
            <td rowspan="2"><center><b>RSS</b></center></td>
            <td>gather/<code style="background-color:mistyrose;">사이트</code>/<code style="background-color:mistyrose;">게시판</code>/rss?search=<code style="background-color:mistyrose;">검색어</code>&page=<code style="background-color:mistyrose;">3</code>&length=<code style="background-color:mistyrose;">5</code></td>
        </tr>
        <tr>
            <td>gather/rss?url=<code style="background-color:mistyrose;">encoded-url</code>&search=<code style="background-color:mistyrose;">검색어</code>&page=<code style="background-color:mistyrose;">1</code>&length=<code style="background-color:mistyrose;">5</code>
            </td>
        </tr>
        <tr>
            <td><center><b>글</b></center></td>
            <td>gather/item?url=<code style="background-color:mistyrose;">encoded-url</code></td>
        </tr>
        <tr>
            <td><center><b>다운로드</b></center></td>
            <td>gather/down?url=<code style="background-color:mistyrose;">encoded-url</code>&ticket=<code style="background-color:mistyrose;">encoded-query-string</code></td>
        </tr>
        <tr>
            <td><center><b>사용자 정의</b></center></td>
            <td>gather/page?url=<code style="background-color:mistyrose;">encoded-url</code></td>
        </tr>
    </tbody>
</table>

- <code style="background-color:mistyrose;">사이트</code>가 `Gatherer`의 `URL` 속성과 매치가 된다면 해당 클래스로 요청을 처리합니다. 예를 들어 `ple-1`은 `https://www.sample-1.co.kr`, `https://www.samplesample.com` 중에서 첫번째와 매치됩니다.
- <code style="background-color:mistyrose;">게시판</code>은 해당 사이트에서 사용하는 게시판 아이디를 그대로 입력해 주세요.
- <code style="background-color:mistyrose;">encoded-url</code>과 <code style="background-color:mistyrose;">encoded-query-string</code>에는 URL 인코딩된 값을 넣어야 합니다. URL 인코딩이란 `:`, `/`, `=` 등 URL을 인식하는데 방해가 되는 문자들을 16진수로 변환시키는 것을 말합니다. 예를 들어 `https://www.google.com/?search=torrent`를 인코딩 할 경우 `https%3A%2F%2Fwww.google.com%2F%3Fsearch%3Dtorrent`의 형태가 됩니다. `http://서버주소:8181/gather/encode` 페이지에서 간단한 URL 인코딩이 가능합니다. 혹은 [G Suite 도구상자](https://toolbox.googleapps.com/apps/encode_decode/)를 이용하세요.
- <code style="background-color:mistyrose;">검색어</code>와 `page` 인수에 입력된 값은 목표 사이트의 설정에 따라 변환되어 URL 쿼리로 삽입됩니다.
- `ticket` 인수는 파일을 다운로드 할 때 필요한 정보입니다.
- `length` 인수는 RSS에서만 적용되며 해당 리스트에서 수집할 게시물의 수 입니다.

`RSS_AGGRESSIVE` 설정이 `True`인 상태에서 RSS 요청시 `리스트 페이지 접속 및 수집` -> `각 게시물에 접속 및 수집`의 과정을 거칩니다. 한번에 여러 페이지를 접속하기 때문에 되도록이면 `length`값을 5 이하로 사용하시길 바랍니다. 만약 `length` 값이 5라면 리스트 페이지 1, 게시물 5, 총 6 개의 페이지를 한번에 접속하게 됩니다.

`RSS_AGGRESSIVE`가 `False`인 상태에서 RSS 요청시 리스트 페이지에서 게시물만 수집합니다. 이후 다운로드 과정에서 해당 게시물에 접속해 첨부된 링크 혹은 파일 중 조건에 맞는 아이템을 다운로드 합니다. RSS에 다운 가능한 파일을 명시할 수 없기 때문에 다운로드에 실패할 가능성이 높습니다. 

#### Flexget 설정
```yaml
inputs:
  - rss:          
      url: 'http://127.0.0.1:8181/gather/google/drama/rss?search=-NEXT'
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

웹 스크래핑 연습
-------
[quotes][quotes]는 스크래핑 연습용 사이트입니다. `gatherers`폴더의 `quotes.py`파일에 코드를 작성하고 아래의 서버 주소에서 결과를 확인해 보세요.

[quotes]: http://quotes.toscrape.com/

    http://localhost:8181/gather/page?url=http%3A%2F%2Fquotes.toscrape.com

##### xpath 및 css selector 테스트
http://videlibri.sourceforge.net/cgi-bin/xidelcgi

---

그 밖에...
---------
##### GAE
현재 Google App Engine의 Python 3 환경은 무료 사용량의 초과분에 대한 결제가 필수입니다. 때문에 무료 사용량 초과시 차단되는 방식인 Python 2 Standard 환경에 맞추었습니다. [Google App Engine 시작하기](https://cloud.google.com/appengine/docs/standard/python/quickstart)

##### GAE 파이썬 패키지 설치

```shell
pip install -t /opt/apps/my-flask-server/venv/gae/lib -r /opt/apps/my-flask-server/install/requirements-gae.txt --no-dependencies
```

혹은 가상환경 내 이미 설치한 일부 패키지 (chardet, concurrent, flask_caching)를 `venv/gae/lib` 폴더로 복사
```shell
mkdir -p /opt/apps/my-flask-server/venv/gae/lib
cp -r /opt/apps/my-flask-server/venv/lib/python2.7/site-packages/chardet /opt/apps/my-flask-server/venv/lib/python2.7/site-packages/concurrent /opt/apps/my-flask-server/venv/lib/python2.7/site-packages/flask_caching /opt/apps/my-flask-server/venv/gae/lib/
```

##### GAE 테스트 서버 ()
```shell
dev_appserver.py --log_level=debug app.yaml
```

##### GAE 배포
```shell
gcloud app deploy --version=20181201-my-version --verbosity=info
```
