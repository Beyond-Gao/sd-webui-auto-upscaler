
function auFirstStart() {

    var idTaskEle = getEleIdTask();
    var showInfo = getEleShowInfoP();
    var res = create_submit_args(arguments);

    if (idTaskEle.value != "" && idTaskEle.value != "Stopped") {
        res[0] = "repetitive" + idTaskEle.value;
        return res;
    }

    setProcessingStatus();

    idTaskEle.value = "WaitStart";
    showInfo.textContent = "Waiting for start...";

    clickProcessBtn();

    res[0] = idTaskEle.value;
    return res;
}

function auLoopStart() {

    var idTaskEle = getEleIdTask();
    var showInfo = getEleShowInfoP();
    var processCurrEle = getEleProcessCurr();
    var processCountEle = getEleProcessCount();
    var res = create_submit_args(arguments);

    res[1] = processCountEle.value;

    if (idTaskEle.value == "WaitStart") {
        idTaskEle.value = "WaitStart2";
        res[0] = idTaskEle.value;
        clickProcessBtn();
        return res;

    } else if (idTaskEle.value == "WaitStart2") {
        idTaskEle.value = "Stopped";
        res[0] = "Stopping";
        showInfo.textContent = "任务启动失败，请重试。";
        setFinishedStatus();
        return res;

    } else if (idTaskEle.value == "Stopping") {
        idTaskEle.value = "Stopped";
        res[0] = "Stopping";

        var pLog = getEleHtmlLog();
        if (pLog && pLog.textContent.startsWith("启动错误")) {
            setFinishedStatus();
        }
        showInfo.textContent = "Stopped.";

        return res;

    } else if (idTaskEle.value == "Stopped") {
        res[0] = "Stopping";
        showInfo.textContent = "Stopped.";
        return res;

    } else if (idTaskEle.value == "Interrupt") {
        idTaskEle.value = "Stopped";
        res[0] = "Stopping";

        showInfo.textContent = "Stopped.";
        return res;
    }

    var id = randomId();
    idTaskEle.value == id;

    res[0] = id;
    res[2] += 1;
    processCurrEle.value = res[2].toString();
    showInfo.textContent = "(" + res[2] + "/" + res[1] + ") " + "Processing...";

    requestProgress(res[0], gradioApp().getElementById('auto_upscaler_gallery_container'), gradioApp().getElementById('auto_upscaler_gallery'), function() {

        var idTaskEle = getEleIdTask();
        var showInfo = getEleShowInfoP();
        var processCurrEle = getEleProcessCurr();
        var processCountEle = getEleProcessCount();

        if (showInfo.textContent.includes("Stop")) {
            showInfo.textContent = "Stopped.";
            if (idTaskEle.value.startsWith("task(")) {
                idTaskEle.value = "Stopped";
            }
            setFinishedStatus();
            clickImgBtn();
            return;
        }

        if (parseInt(processCurrEle.value) == parseInt(processCountEle.value)) {
            showInfo.textContent = "All Complete.";
            if (idTaskEle.value.startsWith("task(")) {
                idTaskEle.value = "Stopped";
            }
            var interruptBtn = gradioApp().getElementById('auto_upscaler_end_btn');
            interruptBtn.click();
            setFinishedStatus();
            clickImgBtn();
        } else {
            showInfo.textContent = "(" + res[2] + "/" + res[1] + ") " + "Complete.";
            clickProcessBtn();
        }

    });

    return res;

}

function auInterrupt() {

    var idTaskEle = getEleIdTask();
    var showInfo = getEleShowInfoP();
    var res = create_submit_args(arguments);

    if (idTaskEle.value == "Starting") {
        idTaskEle.value = "Stopped";
    }

    if (idTaskEle.value == "WaitStart" || idTaskEle.value == "WaitStart2") {
        setFinishedStatus();
        showInfo.textContent = "Stopped.";
    } else if (showInfo.textContent == "All Complete.") {

    } else {
        showInfo.textContent = "Stopping...";
    }

    idTaskEle.value = "Stopped";

    return res;
}

function getEleShowInfoP() {

    p = gradioApp().getElementById('auto_upscaler_show_info_p');

    if (!p) {
        box_div = gradioApp().getElementById('auto_upscaler_console');
        var p = document.createElement("p");
        p.setAttribute("id", "auto_upscaler_show_info_p");
        p.style.fontSize = "36px";
        box_div.appendChild(p);
    }

    return p;
}

function clickProcessBtn() {
    setTimeout(function() {
        var process_btn = getEleProcessBtn();
        process_btn.click();
    }, 3000)
}

function getEleIdTask() {
    return document.querySelector('#auto_upscaler_id_task textarea');
}

function getEleProcessBtn() {
    return gradioApp().getElementById('auto_upscaler_process_btn');
}

function getEleProcessCurr() {
    return document.querySelector('#auto_upscaler_process_curr input');
}

function getEleProcessCount() {
    return document.querySelector('#auto_upscaler_process_count input');
}

function getEleHtmlLog() {
    return document.querySelector('#html_log_auto_upscaler p')
}

function setStartBtnHidden() {
    gradioApp().getElementById("auto_upscaler_start_btn").style.display = "none";
}

function setStartBtnVisible() {
    gradioApp().getElementById("auto_upscaler_start_btn").style.display = "block";
}

function setInterruptBtnHidden() {
    gradioApp().getElementById("auto_upscaler_end_btn").style.display = "none";
}

function setInterruptBtnVisible() {
    gradioApp().getElementById("auto_upscaler_end_btn").style.display = "block";
}

function setProcessingStatus() {
    startBtn = gradioApp().getElementById("auto_upscaler_start_btn");
    startBtn.disabled = true;
    startBtn.style.cursor = "pointer";
    startBtn.style.display = "none";

    endBtn = gradioApp().getElementById("auto_upscaler_end_btn");
    endBtn.disabled = true;
    endBtn.style.cursor = "pointer";
    endBtn.style.display = "block";

    setTimeout(function() {
        startBtn = gradioApp().getElementById("auto_upscaler_start_btn");
        endBtn = gradioApp().getElementById("auto_upscaler_end_btn");
        startBtn.disabled = false;
        endBtn.disabled = false;
    }, 3500)
}

function setFinishedStatus() {
    startBtn = gradioApp().getElementById("auto_upscaler_start_btn");
    startBtn.disabled = true;
    startBtn.style.cursor = "pointer";
    startBtn.style.display = "block";

    endBtn = gradioApp().getElementById("auto_upscaler_end_btn");
    endBtn.disabled = true;
    endBtn.style.cursor = "pointer";
    endBtn.style.display = "none";

    setTimeout(function() {
        startBtn = gradioApp().getElementById("auto_upscaler_start_btn");
        endBtn = gradioApp().getElementById("auto_upscaler_end_btn");
        startBtn.disabled = false;
        endBtn.disabled = false;
    }, 3000)
}

function clickImgBtn() {
    var btns = document.getElementById('auto_upscaler_gallery').querySelectorAll('button');
    if (btns.length >= 1) {
        btns[0].click();
    }
}


