function toggleCam() {
    var x = document.getElementById("CamToggle");
    if (x.innerHTML === "Camera") {
        x.innerHTML = "Utility";
    } else {
        x.innerHTML = "Camera";
    }
}

function toggleEnv() {
    var x = document.getElementById("EnvToggle");
    if (x.innerHTML === "Outside") {
        x.innerHTML = "Inside";
    } else {
        x.innerHTML = "Outside";
    }
}

function selectFunc(text) {
    var x = document.getElementById("currentFunc");
    x.innerHTML = text;
}