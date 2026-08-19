// create a temporary file that can be accessd by url
async function obj_to_virtual_file(objfile) {
    const blob = new Blob([objfile], { type: "model/obj" });
    const url = URL.createObjectURL(blob);
    return url;
}

var sc = 1.0;

async function create_model(model_elem, objfile_url, color, opa) {
    // use the virtual/temporary file by its url
    model_elem.setAttribute('obj-model', {obj: objfile_url});
    // model_elem.setAttribute('position', `0 1.5 -0.3`);
    model_elem.setAttribute('transparent', `true`);
    model_elem.setAttribute('scale', `${sc} ${sc} ${sc}`);
    // model_elem.setAttribute('material', `color: ${color}; opacity: ${opa}; transparent: true; depthWrite: false;`);
    model_elem.setAttribute('material', `color: ${color}; opacity: ${opa}; transparent: true;`);
}

async function show_button_pressed() {
    const status_span = document.getElementById("status-show");

    status_span.innerHTML += '<br>' + "start loading scan file";
    await spjs_setup();
    status_span.innerHTML += '<br>' + "loaded scan file";
}

function sajs_setup() {
    document.getElementById("show-mosmed-0205").addEventListener('click', show_button_pressed);
}

document.addEventListener('DOMContentLoaded', sajs_setup);
