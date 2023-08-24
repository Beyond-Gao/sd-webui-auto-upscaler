
function auFirstStart() {

    var idTaskEle = getEleIdTask();
    var taskInfo = getEleTaskInfo();
    var showInfo = getEleShowInfoP();
    var res = create_submit_args(arguments);

    if (idTaskEle.value == "" || idTaskEle.value == "Stopped") {

    } else if (idTaskEle.value != "WaitStart" || idTaskEle.value != "Stopping") {
        console.log("重复任务！")
        res[0] = "repetitive" + idTaskEle.value;
        return res;
    }

    setDisabled();
    setStartBtnHidden();
    setInterruptBtnVisible();
    localStorage.setItem("auWaitstartCount", 0);

    idTaskEle.value = "WaitStart";
    taskInfo.value = "normal";
    showInfo.textContent = "Waiting for start...";

    res[0] = idTaskEle.value;
    res[1] = taskInfo.value;

    var process_btn = getEleProcessBtn();
    clickBtn(process_btn);

    return res;
}

function auLoopStart() {

    var idTaskEle = getEleIdTask();
    var taskInfo = getEleTaskInfo();
    var showInfo = getEleShowInfoP();
    var processCurrEle = getEleProcessCurr();
    var processCountEle = getEleProcessCount();
    var res = create_submit_args(arguments);

    res[1] = processCountEle.value;

    if (idTaskEle.value == "WaitStart") {

        var waitCount = localStorage.getItem("auWaitstartCount");

        if (waitCount >= 3) {
            setTimeout(function() {
                var interruptBtn = gradioApp().getElementById('auto_upscaler_end_btn');
                interruptBtn.click();
            }, 3000);

            res[0] = idTaskEle.value;
            return res;

        } else {
            localStorage.setItem("auWaitstartCount", waitCount + 1);
        }

        res[0] = idTaskEle.value;
        var process_btn = getEleProcessBtn();
        clickBtn(process_btn);
        return res;

    } else if (idTaskEle.value == "Stopping") {
        res[0] = idTaskEle.value;

        if (taskInfo.value != "normal") {
            showInfo.textContent = taskInfo.value;
            setStartBtnVisible();
            setInterruptBtnHidden();

        }else if (showInfo.textContent != "All Complete.") {
            showInfo.textContent = "Stopped.";
        }

        return res;

    } else if (idTaskEle.value == "Stopped") {
        res[0] = "Stopping";
        if (showInfo.textContent != "All Complete.") {
            showInfo.textContent = "Stopped."
        }
        return res;
    }

    var id = randomId();

    res[0] = id;
    res[2] += 1;
    processCurrEle.value = res[2].toString();
    showInfo.textContent = "(" + res[2] + "/" + res[1] + ") " + "Processing...";

    requestProgress(res[0], gradioApp().getElementById('auto_upscaler_gallery_container'), gradioApp().getElementById('auto_upscaler_gallery'), function() {

        var idTaskEle = getEleIdTask();
        var showInfo = getEleShowInfoP();
        var processCurrEle = getEleProcessCurr();
        var processCountEle = getEleProcessCount();

        showInfo.textContent = "(" + res[2] + "/" + res[1] + ") " + "Complete.";

        if (idTaskEle.value == "Stopping" || idTaskEle.value == "Stopped" || parseInt(processCurrEle.value) >= parseInt(processCountEle.value)) {

            if (showInfo.textContent != "Stopping...") {
                showInfo.textContent = "All Complete.";
            }

            setStartBtnVisible();
            setInterruptBtnHidden();

            if (parseInt(processCurrEle.value) >= parseInt(processCountEle.value)) {
                var interruptBtn = gradioApp().getElementById('auto_upscaler_end_btn');
                interruptBtn.click();
            }

        } else {
            var processBtn = getEleProcessBtn();
            clickBtn(processBtn);
        }

    });

    return res;

}

function auInterrupt() {

    var idTaskEle = getEleIdTask();
    var showInfo = getEleShowInfoP();
    var res = create_submit_args(arguments);

    console.log("idTaskEle.value" + idTaskEle.value);
    if (idTaskEle.value == "WaitStart" || idTaskEle.value == "Starting") {
        idTaskEle.value = "WaitStart";
        console.log("iiiiiii")
        setInterruptBtnHidden();
        setStartBtnVisible();
        showInfo.textContent = "Stopped.";
    }

    idTaskEle.value = "Stopping"
    localStorage.setItem("auWaitstartCount", 0);

    if (showInfo.textContent != "All Complete." && showInfo.textContent != "Stopped.") {
        showInfo.textContent = "Stopping...";
    }

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

function getEleIdTask() {
    return document.querySelector('#auto_upscaler_id_task textarea');
}

function getEleTaskInfo() {
    return document.querySelector('#auto_upscaler_task_info textarea');
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

function clickBtn(process_btn) {
    setTimeout(function() {
        process_btn.click();
    }, 10000);
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

function setDisabled() {
    startBtn = gradioApp().getElementById("auto_upscaler_start_btn");
    startBtn.disabled = true;
    startBtn.style.cursor = "pointer";

    endBtn = gradioApp().getElementById("auto_upscaler_end_btn");
    endBtn.disabled = true;
    endBtn.style.cursor = "pointer";

    setTimeout(function() {
        startBtn = gradioApp().getElementById("auto_upscaler_start_btn");
        endBtn = gradioApp().getElementById("auto_upscaler_end_btn");
        startBtn.disabled = false;
        endBtn.disabled = false;
    }, 3500)
}


