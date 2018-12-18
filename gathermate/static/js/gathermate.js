$(function(){
  var mySidebar = $("#mySidebar");
  var overlayBg = $("#myOverlay");
  var searchOverlay = $("#searchOverlay");
  var menu = $("#menu");
  var myOverlay = $("#myOverlay");
  var serachOpen = $("#searchOpen");
  var searchInput = $("#searchInput");

  menu.on('click', function(e){
    if (mySidebar.is(":visible")){
      mySidebar.hide();
      overlayBg.hide();
    }else{
      mySidebar.show();
      overlayBg.show();
    }
  });

  myOverlay.on('click', function(e){
    mySidebar.hide();
    overlayBg.hide();
  });

  serachOpen.on('click', function(e){
    mySidebar.css('z-index', -1);
    searchOverlay.show();
    searchInput.focus();
  });

  searchOverlay.on('click', function(e){
    if (e.target !== this)
      return;
    mySidebar.css('z-index', 3);
    $(this).hide();
  });

});

function markIndex(index){
  if (index != ''){
    var current = $('#'+index);
    current.addClass("w3-red");
    scrollTo(index);
  }
}

function scrollTo(index){
  if (index != ''){
    var current = $('#'+index);
    if (!isScrolledIntoView(current)){
      location.href = "#";
      location.href = "#" + index;
    }
  }
}

function show_files(num){
  $(document).ready(function(){
    var file_div = $("#file_div_"+num);
    var file_a = $("#file_link_"+num);
    toggle(file_div);
    var remote_url = file_a.attr('url');
    if (!file_div.hasClass("w3-show") && typeof remote_url !== typeof undefined && remote_url !== false) {
      $.get(remote_url, function(data, status){
        if (status == 'success'){
          file_div.html(data);
        }else{
          file_div.text("Failed : " + status);
        }
      });
    }
  });
}

function toggle(target){
  $(function(){
    if (target.hasClass("w3-show")){
      target.removeClass("w3-show");
    }else{
      target.addClass("w3-show");
    }
  });
}

function down(a, link, ticket){
  $(function(){
    var input_down_url = $("#down_url");
    var input_down_ticket = $("#down_ticket");
    var form_down = $("#down_form");
    input_down_url.val('');
    input_down_ticket.val('');

    input_down_url.val(link);
    input_down_ticket.val(ticket);

    form_down.submit();
    input_down_url.val('');
    input_down_ticket.val('');

    $(a).css('color', 'Gray');
  });
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

function isScrolledIntoView(elem){
    var docViewTop = $(window).scrollTop();
    var docViewBottom = docViewTop + $(window).height();

    var elemTop = $(elem).offset().top;
    var elemBottom = elemTop + $(elem).height();

    return ((elemBottom >= docViewTop) && (elemTop <= docViewBottom)
      && (elemBottom <= docViewBottom) &&  (elemTop >= docViewTop) );
}