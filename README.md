Gathermate
==========

`Gathermate`는 특정 웹페이지의 콘텐츠를 수집 및 재가공하여 서버 형태로 제공하는 프로그램입니다. 서버이긴 하지만 반드시 **본인**만 접속할 수 있도록 설정하시길 바랍니다. 웹 상에서 수집한 콘텐츠를 타인에게 노출시킬 경우 법적으로 문제가 될 수 있기 때문입니다.

`Gathermate`는 `python 2.7`로 작성되었습니다.

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

### 개별 설치하기 (Entware @ ASUS RT-AC68U aka T-mobile AC1900)

#### 1. 소스파일 복사
Git에서 소스 파일을 받아 `/opt/apps/my-flask-server` 폴더에 저장합니다.

```shell
opkg update
opkg install git git-http    
git clone https://github.com/gathermate/gathermate.git /opt/apps/my-flask-server
```
#### 2. 파이썬 설치

`python`, `python-pip`, `python-lxml`을 설치합니다. `lxml`을 [Entware][entware] 패키지에서 설치하는 이유는 `pip`으로 설치할 경우 컴파일 오류가 발생하기 때문입니다. `lxml`을 컴파일하려면 헤더 파일이 필요한데 [Entware][entware]에는 기본 탑재되어 있지 않습니다. 그래도 정말 컴파일 하기를 원한다면 [Using gcc](https://github.com/Entware/Entware-ng/wiki/Using-gcc-(native-compilation))를 참조하세요.

[entware]: https://github.com/Entware/Entware
    
```shell
opkg install python-light python-pip python-lxml
```

#### 3. 파이썬 가상환경 만들기

```shell
pip install virtualenv
virtualenv -p python2 /opt/apps/my-flask-server/venv
source /opt/apps/my-flask-server/venv/bin/activate
```

#### 4. 파이썬 패키지 설치

가상환경 내에서 `python` 추가 패키지를 설치합니다. 또한 `opkg`로 설치한 `lxml` 패키지도 가상환경 폴더에 복사해 주세요.
   
```shell 
pip install -r /opt/apps/my-flask-server/install/requirements_entware.txt
cp -r /opt/lib/python2.7/site-packages/lxml* /opt/apps/my-flask-server/venv/lib/python2.7/site-packages/ 
```

#### 5. 실행하기

**설정하기를 읽어본 후 실행하기를 권장합니다.**

기본 설정 파일 `/opt/apps/my-flask-server/install/default_config.py`를 `/opt/apps/my-flask-server/instance/` 폴더로 복사하면서 파일 이름을 `config.py`로 변경합니다.

```shell
mkdir /opt/apps/my-flask-server/instance
cp /opt/apps/my-flask-server/install/default_config.py /opt/apps/my-flask-server/instance/config.py
```

`/opt/apps/my-flask-server/install` 폴더의 `daemon-entware` 스크립트를 `/opt/etc/init.d` 폴더로 복사하면서 파일 이름을 `S89my-flask-server`로 변경합니다. 
```shell
cp /opt/apps/my-flask-server/install/daemon-entware /opt/etc/init.d/S89my-flask-server
```

**`S89my-flask-server` 스크립트 내 포트 번호를 확인 후 변경해 주세요.**
```shell
BIND=0.0.0.0:8181
```

`/opt/etc/init.d/S89my-flask-server` 스크립트에 실행권한을 부여합니다.
```shell
chmod +x /opt/etc/init.d/S89my-flask-server
```
   
실행하기 

```shell
/opt/etc/init.d/S89my-flask-server start
```

`공유기_주소:8181`로 접속하여 "Welcome" 페이지가 나오는지 확인.

#### 6. 외부 접속 차단

`/jffs/scripts/firewall-start`에 아래 내용을 추가

`Insert`로 입력하기 때문에 역순으로 규칙이 적용됩니다.

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

### 개별 설치하기 (Debian/Ubuntu on WSL)
Debian, Ubuntu는 `Windows Subsystem for Linux` 환경에서 테스트 했습니다.

#### 1. 소스파일 복사

Git에서 소스 파일을 받아 `/opt/apps/my-flask-server` 폴더에 저장합니다.
```shell
apt update
apt install git
git clone https://github.com/gathermate/gathermate.git /opt/apps/my-flask-server
```

#### 2. 파이썬 설치
```shell
apt install python-minimal python-pip
```

#### 3. 파이썬 가상환경 만들기
```shell
pip install virtualenv
virtualenv -p python2 /opt/apps/my-flask-server/venv
source /opt/apps/my-flask-server/venv/bin/activate 
```

#### 4. 파이썬 패키지 설치
```shell
pip install -r /opt/apps/my-flask-server/install/requirements.txt
```

#### 5. 실행하기
**설정하기를 읽어본 후 실행하기를 권장합니다.**


기본 설정 파일 `/opt/apps/my-flask-server/install/default_config.py`를 `/opt/apps/my-flask-server/instance/` 폴더로 복사하면서 파일 이름을 `config.py`로 변경합니다.
```shell
mkdir /opt/apps/my-flask-server/instance
cp /opt/apps/my-flask-server/install/default_config.py /opt/apps/my-flask-server/instance/config.py
```

`/opt/apps/my-flask-server/install` 폴더의 `daemon-debian` 스크립트를 `/etc/init.d` 폴더로 복사하면서 파일 이름을 `my-flask-server`로 변경합니다. 
```shell
cp /opt/apps/my-flask-server/install/daemon-debian /etc/init.d/my-flask-server
```

**`S89my-flask-server` 스크립트 내 포트 번호를 확인 후 변경해 주세요.**
```shell
BIND=0.0.0.0:8181
```

`/etc/init.d/my-flask-server` 스크립트에 실행권한을 부여합니다.
```shell
chmod +x /etc/init.d/my-flask-server
```

실행하기     
```shell
service my-flask-server start
```

설정하기
--------

실행하기 전에 **반드시** 해야 할 작업이 있습니다.

먼저 `default_config.py`를 `instance`폴더로 복사하면서 `config.py`로 이름을 변경해 주세요.
스크립트로 자동 설치했다면 건너뛰어도 됩니다.

```shell
mkdir /opt/apps/my-flask-server/instance
cp /opt/apps/my-flask-server/install/default_config.py /opt/apps/my-flask-server/instance/config.py 
```

 그런 다음 `instance/config.py` 내의 민감한 정보를 즉시 변경해 주세요.

#### 꼭 변경해야 하는 값들

아래의 값은 반드시 기본 설정과 다르게 설정하세요.

- **AUTH_ID** : 서버 접속시 사용하는 **아이디** 입니다.
- **AUTH_PW** : 서버 접속시 사용하는 **비밀번호** 입니다.
- **PATH** : 서버 URL의 path에 적용됩니다. `http://www.yourserver.com/PATH/?query=2`

#### 설정 값 입력하기

민감한 정보는 기본적으로 `os.environ.get()` 를 통해 `export`된 값을 불러오도록 되어 있습니다. `os.environ.get()`이 어떤 이름의 환경변수를 가져오는지 확인한 다음 `gunicorn` 스크립트에서 `export` 해 주면 됩니다. 이 방법이 어려울 경우 직접 `instance/config.py`에 입력하세요.

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

#### 어떤 클래스의 설정을 변경해야 하나

로컬호스트에서 운영한다면 `Localhost` 클래스를 수정해 주세요. `Localhost` 클래스는 `Flask` 클래스를 상속 받기 때문에 `Flask` 클래스의 설정을 모두 갖게 됩니다.

Google App Engine에서 운영한다면 `GoogleAppEngine` 클래스를 수정해 주세요. `GoogleAppEngine` 클래스는 `LocalHost` 클래스를 상속 받기 때문에 불필요한 중복 입력을 피할 수 있습니다.

사용법
------
**당연한 이야기이지만 해당 사이트의 콘텐츠 수집 코드가 `Gatherer`의 서브 클래스로 구현되어 있어야 합니다.**

#### 현재 버전에서 서버가 처리할 수 있는 요청의 형태는 아래와 같습니다.

유형|사이트 이름으로 요청
:------:|-------
**리스트**|gather/**사이트**/**게시판**?search=**검색어**&page=**3**
**RSS**|gather/**사이트**/**게시판**/rss?search=**검색어**&page=**3**&length=**5**


- `Gatherer`의 `URL` 속성에 `사이트`의 문자가 포함되어 있다면 해당 클래스로 작업하게 됩니다. 예를 들어 `ple-1`은 `https://www.sample-1.co.kr`, `https://www.samplesample.com` 중에서 첫번째와 매치됩니다.
- `게시판`은 해당 사이트에서 사용하는 게시판 아이디를 그대로 입력해 주세요.


유형|인코딩 된 URL로 요청 
:----:|----
**리스트**|gather/list?url=**encoded-url**&search=**검색어**&page=**2**
**게시물 내용**|gather/item?url=**encoded-url**
**다운로드**|gather/down?url=**encoded-url**&ticket=**encoded-payload**
**RSS**|gather/rss?url=**encoded-url**&search=**검색어**&page=**1**&length=**5**
**사용자 정의**|gather/page?url=**encoded-url**


- **url** 파라미터 값에는 인코딩된 URL 을 넣어야 합니다. URL 인코딩이란 ':'과 '/' 처럼 URL을 인식하는데 방해가 되는 문자들을 16진수로 변환시키는 것을 말합니다. 예를 들어 `https://www.google.com`를 인코딩 할 경우 `https%3A%2F%2Fwww.google.com`의 형태가 됩니다. `http://서버주소:8181/gather/encode` 페이지에서 간단한 URL 인코딩이 가능합니다.
- **search** 파라미터에 입력된 값은 목표 사이트의 URL 쿼리에 삽입됩니다. 
- **page** 파라미터 역시 목표 사이트의 URL 쿼리에 삽입됩니다.
- **ticket** 파라미터는 파일을 다운로드 할 때 필요한 정보입니다.
- **length** 파라미터는 RSS에서만 적용되며 해당 리스트에서 수집할 게시물의 수 입니다.

RSS는 `RSS_AGGRESSIVE`가 `True`일 경우 `리스트 페이지 접속 및 수집` -> `각 게시물에 접속 및 수집`의 과정을 거칩니다. 한번에 여러 페이지를 접속하기 때문에 되도록이면 `length`값을 5 이하로 사용하시길 바랍니다. 만약 `length` 값이 5라면 리스트 페이지 1, 게시물 5, 총 6 개의 페이지를 한번에 접속하게 됩니다.

`RSS_AGGRESSIVE`가 `False`일 경우 리스트 페이지에서 게시물만 수집을 하며 이후 다운로드시 해당 게시물에 접속해 첨부된 링크 혹은 파일 중 조건에 맞는 아이템을  다운로드 합니다. RSS에 다운 가능한 파일을 명시할 수 없기 때문에 다운로드에 실패할 가능성이 높습니다.
 
#### RSS를 생성하기 위한 주소는 아래의 형태를 가집니다. 

```
http://127.0.0.1:8181/gather/사이트/게시판/rss
```

```
http://127.0.0.1:8181/gather/rss?url=목표-게시판의-인코딩된-주소
```

##### 다음은 `length`와 `search`가 포함된 예시입니다.

```script
http://127.0.0.1:8181/gather/google/drama/rss?length=5&search=구글
```

```script
http://127.0.0.1:8181/gather/rss?length=5&search=구글&url=https%3A%2F%2Fwww.google.com
```

#### Flexget 설정
```yaml
inputs:
  - rss:          
      url: 'http://127.0.0.1:8181/gather/google/drama/rss'
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
Google App Engine의 Python 2 Standard 환경에 맞추어져 있습니다. 

##### GAE 파이썬 패키지 설치

```shell
pip install -t /opt/apps/my-flask-server/venv/gae/lib -r /opt/apps/my-flask-server/install/requirements_gae.txt --no-dependencies
```

##### GAE 테스트 서버
```shell
dev_appserver.py --log_level=debug app.yaml
```

##### GAE 배포
```shell
gcloud app deploy --version=20181201-my-version --verbosity=info
```
