function sendValue(dev, sen, val) {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) 
        {
            console.log(this.responseText);
            el = document.getElementById(dev +"&" + sen);
            el.classList.add("success");
            setTimeout(function(){ 
                el.classList.remove("success"); 
            }, 500);
        }
    }

    xhttp.open("POST", "/?device="+dev+"&sensor="+sen+"&value="+val+"&ajax=1", true);
    xhttp.send();
};

function update(event){
    if (event.key === "Enter" && event.target.value.trim() != "") 
    {
        event.preventDefault();
        const parts = event.target.id.split("&");
        console.log(parts);
        sendValue(parts[0], parts[1], event.target.value);
    }
}

function chkclk(event){
    const parts = event.target.id.split("&");
    console.log(parts);
    
    let value = 0;
    if (event.target.checked) { 
        value = 1; 
    }
    sendValue(parts[0], parts[1], value);
}

function delSensor(obj){
    const parts = obj.id.split("&");
    console.log(parts);
    
    if (confirm("Delete " + parts[1] + " in " + parts[0] + "?" )){
        window.location.href = '/' + parts[0] + '/' + parts[1] + '/delete';
    }
}

function unsubscribe(obj){
    const parts = obj.name.split("/");
    console.log(parts);
    
    if (confirm("Delete " + obj.name + "?" )){
        window.location.href = '/unsubscribe?ip=' + parts[0] + '&device=' + parts[1] + '&sensor=' +parts[2];
    }
}

function refreshSrc(element) {
    element.src = element.src.split('?')[0] + '?' + new Date().getTime();
}