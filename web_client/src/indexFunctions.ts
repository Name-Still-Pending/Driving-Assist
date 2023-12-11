let camBool = true;
let outBool = true;

function toggleCam() {
    var x = document.getElementById("CamToggle");
    if (x.innerHTML == "Camera") {
        x.innerHTML = "Utility";
        camBool = false;
    } else {
        x.innerHTML = "Camera";
        camBool = true;
    }
}

function toggleEnv() {
    var x = document.getElementById("EnvToggle");
    if (x.innerHTML == "Outside") {
        x.innerHTML = "Inside";
        outBool = false;
    } else {
        x.innerHTML = "Outside";
        outBool = true;
    }
}

function selectFunc(text) {
    var x = document.getElementById("currentFunc");
    x.innerHTML = text;
}

