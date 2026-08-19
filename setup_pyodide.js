// for loading and setting up pyodide

var pyodide;
var micropip;

// init Pyodide
async function main() {
    pyodide = await loadPyodide();
    // load the micropip package
    await pyodide.loadPackage("micropip");
    micropip = await pyodide.pyimport("micropip");
    return pyodide;
}
let pyodideReadyPromise;

async function install_needed_packages() {
    // load the packages needed
    await micropip.install('scikit-image');
    console.log('load success: scikit-image');
    await micropip.install('nibabel');
    console.log('load success: nibabel');

    // load the script library specific to this site
    let response = await fetch("scripts.py");
    let code = await response.text();
    await pyodide.runPythonAsync(code);
    console.log('loaded local scripts');
}

async function spjs_setup() {
    const status_span = document.getElementById("status-show");

    await main();
    status_span.innerHTML += '<br>' + 'pyodide setup complete';
    await install_needed_packages();
    console.log('pyodide setup complete');
    status_span.innerHTML += '<br>' + 'pyodide dependencies installed';

    // load the file using pyodide which then returns an obj model file
    const file_url = "examples/mosmed_covid19_0205.nii";
    pyodide.globals.set("file_url", file_url);
    await pyodide.runPythonAsync('await test_load_scan_model(file_url)');
    console.log('python side loaded file and created .obj model file');
    status_span.innerHTML += '<br>' + 'python side loaded file and created .obj model file';
    // Get the string from Python global scope
    let objfile = pyodide.globals.get("loaded_model");
    console.log('.obj model file transfered to js side');
    status_span.innerHTML += '<br>' + '.obj model file transfered to js side';

    // call these funcs from setup_aframe.js
    // create element for aframe scene same as usual html elements
    let objfile_url = obj_to_virtual_file(objfile);
    const main_parent_obj = document.getElementById("model-obj-parent");
    const ch = document.createElement('a-entity');
    create_model(ch, objfile_url, "#bfbfcf", 0.90);
    main_parent_obj.appendChild(ch);
    console.log('subject body scan model created');
    status_span.innerHTML += '<br>' + 'subject body scan model created';
}

// document.addEventListener("DOMContentLoaded", spjs_setup);
