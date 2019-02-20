$(function(){
  // video.js
  var player = videojs('main-player', {
    language: 'ko',
    //playbackRates: [1, 0.75, 0.5, 0.25],
    //liveui: true,
    controls: true,
    autoplay: true,
    preload: 'auto',
    aspectRatio: '16:9',
    fluid: true,
  });
  player.ready(function() {
    var promise = player.play();
    if (promise !== undefined) {
      promise.then(function() {
        player.play();
      }).catch(function(error) {
        videojs.log.warn('Autoplay was prevented by your browser. Trying muted autoplay...')
        player.muted(true);
        player.play();
      });
    }
  });
  //lazy load
  var myLazyLoad = new LazyLoad({
    elements_selector: ".lazy"
  });

  // pip
  var pip = function(){
    var $window = $(window);
    var $videoWrap = $('#main-video-wrap');
    var $video = $('#main-video');
    var videoHeight = $video.outerHeight();
    var windowScrollTop = $window.scrollTop();
    var videoBottom = videoHeight + $videoWrap.offset().top;
    if (windowScrollTop > videoBottom) {
      $videoWrap.height(videoHeight);
      $video.addClass('stuck');
    } else {
      $videoWrap.height('auto');
      $video.removeClass('stuck');
    }
  }
  window.addEventListener('scroll', pip);
  window.addEventListener('resize', pip);
});

function loadFromUrl(element){
  var player = videojs('main-player');
  player.pause();
  var url = element.value;
  player.src({type: "application/x-mpegURL", src: url});
}

function loadFromUrlEnter(element){
  if(event.keyCode == 13){
    loadFromUrl(element);
  }
}

function playChannel(streamer, channel){
  var url = streamer + '/' + channel + '/streams';
  var player = videojs('main-player');
  player.src({type: "application/x-mpegURL", src: url});
}

function markStreamer(streamer){
  if (streamer != ''){
    var current = $('#'+streamer);
    current.addClass("active");
  }
}

function toastbar(msg) {
    // Get the snackbar DIV
    var x = window.parent.document.getElementById('toastbar');
    x.innerHTML = msg;
    // Add the "show" class to DIV
    x.className = "show";
    // After 5 seconds, remove the show class from DIV
    setTimeout(function(){ x.className = x.className.replace("show", ""); }, 5000);
}


//videojs language
videojs.addLanguage('ko', {
  "Play": "재생",
  "Pause": "일시중지",
  "Current Time": "현재 시간",
  "Duration": "지정 기간",
  "Remaining Time": "남은 시간",
  "Stream Type": "스트리밍 유형",
  "LIVE": "라이브",
  "Loaded": "로드됨",
  "Progress": "진행",
  "Fullscreen": "전체 화면",
  "Non-Fullscreen": "전체 화면 해제",
  "Mute": "음소거",
  "Unmute": "음소거 해제",
  "Playback Rate": "재생 비율",
  "Subtitles": "서브타이틀",
  "subtitles off": "서브타이틀 끄기",
  "Captions": "자막",
  "captions off": "자막 끄기",
  "Chapters": "챕터",
  "You aborted the media playback": "비디오 재생을 취소했습니다.",
  "A network error caused the media download to fail part-way.": "네트워크 오류로 인하여 비디오 일부를 다운로드하지 못 했습니다.",
  "The media could not be loaded, either because the server or network failed or because the format is not supported.": "비디오를 로드할 수 없습니다. 서버 혹은 네트워크 오류 때문이거나 지원되지 않는 형식 때문일 수 있습니다.",
  "The media playback was aborted due to a corruption problem or because the media used features your browser did not support.": "비디오 재생이 취소됐습니다. 비디오가 손상되었거나 비디오가 사용하는 기능을 브라우저에서 지원하지 않는 것 같습니다.",
  "No compatible source was found for this media.": "비디오에 호환되지 않는 소스가 있습니다."
});