// capture keydown events for easier navigation
document.onkeydown = function(event) {
    // if testing case
    if (context == 'eval') {
        // capture number keys 1-9 (option selection)
        if (event.keyCode >=49 && event.keyCode <= 57) {
            selectOption(event.keyCode - 49);
        }
        // capture space key (audio playback)
        if (event.keyCode == 32) {
            document.getElementsByTagName('audio')[0].play();
        }
        // capture return key (form submisson)
        if (event.keyCode == 13) {
            document.getElementById('options').submit();
        }
    }
};

function selectOption(oidx) {
    radioButtons = document.getElementsByName('choice');
    datumBoxes = document.getElementsByClassName('datum');

    // check if valid selection
    if (oidx >= radioButtons.length) {
        return;
    }

    // toggle appropriate radio button
    for (var i = 0; i < radioButtons.length; i++) {
        if (i == oidx) {
            radioButtons[i].checked = true;
            datumBoxes[i].classList.add('selected');
        } else {
            radioButtons[i].checked = false;
            datumBoxes[i].classList.remove('selected');
        }
    }
}

function playAllAudios(startIdx) {
    datumBoxes = document.getElementsByClassName('datum');
    if (startIdx >= datumBoxes.length) {
        return;
    }

    audioPlayer = playPairedAudio(datumBoxes[startIdx]);
    audioPlayer.onended = function() {
        window.setTimeout(function() {
            playAllAudios(startIdx + 1);
        }, 300);
        audioPlayer.onended = null;
    };
}

function playPairedAudio(el) {
    audioPlayer = el.getElementsByTagName('audio')[0];
    audioPlayer.play();
    el.classList.add('playing');
    audioPlayer.addEventListener('ended', function() {
        el.classList.remove('playing');
    }, false);
    return audioPlayer;
}