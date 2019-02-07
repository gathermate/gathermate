#!/bin/sh

# 필수 항목
TOKEN=
# 필수 항목. 메시지 전송 전에 자동으로 얻을 수 있으나 최근에 봇에게
# 보낸 메시지가 있어야 함. 주기적으로 봇에게 말을 걸 경우 없어도 됨.
CHAT_ID=
# 선택 항목. 마크다운이나 HTML 형식의 메시지를 보낼 때 입력 (Markdown|HTML)
PARSE_MODE=
# 선택 항목. 링크 미리보기 기능의 사용 여부 (true|false)
DISABLE_WEB_PAGE_PREVIEW=
# 선택 항목. 메시지 전송시 소리 알람의 사용 여부 (true|false)
DISABLE_NOTIFICATION=


BASE_URL="https://api.telegram.org/bot$TOKEN"


send_message(){
    if [ -z "$message" ]; then
        echo "You should input a MESSAGE."
    else
        for i in 1 2; do
            if [ -z "$CHAT_ID" ]; then
                get_updates
            else
                url="$BASE_URL/sendMESSAGE"
                curl -s -X POST $url -d chat_id=$CHAT_ID \
                                     -d text="$message" \
                                     -d parse_mode=$PARSE_MODE \
                                     -d disable_web_page_preview=$DISABLE_WEB_PAGE_PREVIEW \
                                     -d disalbe_notification=$DISABLE_NOTIFICATION \
                                     -d reply_to_message_id=$reply_id
                echo
                i=0
                break
            fi
        done
        if [ $i -ne 0 ]; then
            echo "You need to send a new message to bot."
        fi
    fi
}

get_updates(){
    url="$BASE_URL/getUpdates"
    response=$(curl -s $url)
    echo $response
    CHAT_ID=$(echo $response | sed -r -n -e "s@.*\"chat\":.+\"id\":([-0-9]+),.+}.*@\1@p;")
    echo "CHAT_ID: $CHAT_ID"
}

if [ -z "$TOKEN" ]; then
    echo "Token was not set."
    exit 1
fi

case "$1" in
    send)
        message=$2
        reply_id=$3
        send_message
        ;;
    update)
        get_updates
        ;;
    *)
        echo "Usage : $0 send MESSAGE [REPLY_ID]"
        echo "e.g.  : $0 send \"Hello, there?\""
        exit 0
        ;;
esac
