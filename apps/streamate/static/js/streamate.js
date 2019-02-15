$(function(){
  // video.js
  var player = videojs('video');
  player.qualityPickerPlugin();
  player.ready(function() {
    var promise = player.play();
    if (promise !== undefined) {
      promise.then(function() {
        player.play();
      }).catch(function(error) {
        // Autoplay was prevented.
      });
    }
  });
  //lazy load
  var myLazyLoad = new LazyLoad({
    elements_selector: ".lazy"
  });

  // pip
  var $window = $(window);
  var $videoWrap = $('.video-wrap');
  var $video = $('.player');
  var videoHeight = $video.outerHeight();
  $window.on('scroll',  function() {
    var windowScrollTop = $window.scrollTop();
    var videoBottom = videoHeight + $videoWrap.offset().top;
    if (windowScrollTop > videoBottom) {
      $videoWrap.height(videoHeight);
      $video.addClass('stuck');
    } else {
      $videoWrap.height('auto');
      $video.removeClass('stuck');
    }
  });

});


function loadFromUrl(element){
  var player = videojs('video');
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
  var url = streamer + '/live/' + channel;
  var player = videojs('video');
  player.src({type: "application/x-mpegURL", src: url});
}
