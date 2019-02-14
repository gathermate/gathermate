
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