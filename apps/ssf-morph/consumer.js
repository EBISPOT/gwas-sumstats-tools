import "https://cdn.datatables.net/2.0.3/js/dataTables.js"
import { asyncRun } from "./py-worker.js";

const read_input = await fetch('./python_bin/read_input.py').then(response => response.text());
const generate_config = await fetch('./python_bin/generate_config.py').then(response => response.text());
const test_config = await fetch('./python_bin/test_config.py').then(response => response.text());
const apply_config = await fetch('./python_bin/apply_config.py').then(response => response.text());
const validate = await fetch('./python_bin/validation.py').then(response => response.text());
const validation_out = document.getElementById('validation_out');

let dirHandle;
let inputFileHandle;
let outputFileHandle;
let validateFileHandle;
let delimiter;
let removecomments;
let analysisSoftware;
let nrows;
let zeropvalues;
window.configGenerated = false;

// ── Config form helpers ───────────────────────────────────────────

let inputColumns = [];       // populated from input file header
let inputTablePending = null; // { columns, data } stored for lazy DataTable init

const MANDATORY_RENAME_FIELDS = [
    'chromosome',
    'base_pair_location',
    'effect_allele',
    'other_allele',
    'beta',
    'odds_ratio',
    'standard_error',
    'effect_allele_frequency',
    'p_value',
];

const SEP_PRESETS = [
    { value: '',          label: '— (null)' },
    { value: ',',         label: 'Comma (,)' },
    { value: '_',         label: 'Underscore (_)' },
    { value: ';',         label: 'Semicolon (;)' },
    { value: ':',         label: 'Colon (:)' },
    { value: '__custom__',label: 'Other…' },
];

function buildFieldSelect(selectedVal) {
    const sel = document.createElement('select');
    sel.className = 'form-select form-select-sm';
    const placeholder = new Option('— select —', '');
    sel.appendChild(placeholder);
    for (const col of inputColumns) {
        const opt = new Option(col, col);
        if (col === selectedVal) opt.selected = true;
        sel.appendChild(opt);
    }
    return sel;
}

function buildSepControl(selectedVal) {
    const wrap = document.createElement('div');
    const sel = document.createElement('select');
    sel.className = 'form-select form-select-sm sep-preset';
    for (const p of SEP_PRESETS) {
        const opt = new Option(p.label, p.value);
        sel.appendChild(opt);
    }
    const inp = document.createElement('input');
    inp.type = 'text';
    inp.className = 'form-control form-control-sm sep-custom mt-1 d-none';
    inp.placeholder = 'Enter separator';

    const isPreset = SEP_PRESETS.some(p => p.value !== '__custom__' && p.value === selectedVal);
    if (selectedVal !== null && selectedVal !== undefined && !isPreset) {
        sel.value = '__custom__';
        inp.value = selectedVal;
        inp.classList.remove('d-none');
    } else {
        sel.value = selectedVal ?? '';
    }

    sel.addEventListener('change', () => {
        if (sel.value === '__custom__') {
            inp.classList.remove('d-none');
        } else {
            inp.classList.add('d-none');
            inp.value = '';
        }
    });
    wrap.appendChild(sel);
    wrap.appendChild(inp);
    return wrap;
}

function getSepValue(td) {
    const sel = td.querySelector('.sep-preset');
    const inp = td.querySelector('.sep-custom');
    if (sel.value === '__custom__') return inp.value || null;
    if (sel.value === '') return null;
    return sel.value;
}

function buildNullableInput(val) {
    const inp = document.createElement('input');
    inp.type = 'text';
    inp.className = 'form-control form-control-sm';
    inp.placeholder = 'null';
    inp.value = (val !== null && val !== undefined) ? val : '';
    return inp;
}

function buildDeleteBtn(tr) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-sm btn-outline-danger';
    btn.innerHTML = '&times;';
    btn.addEventListener('click', () => tr.remove());
    return btn;
}

function buildSplitRow(data = {}) {
    const tr = document.createElement('tr');
    const tdField    = document.createElement('td');
    const tdSep      = document.createElement('td');
    const tdCapture  = document.createElement('td');
    const tdNewField = document.createElement('td');
    const tdInclOrig = document.createElement('td');
    const tdDel      = document.createElement('td');

    tdField.appendChild(buildFieldSelect(data.field ?? ''));
    tdSep.appendChild(buildSepControl(data.separator ?? null));
    tdCapture.appendChild(buildNullableInput(data.capture));
    tdNewField.appendChild(buildNullableInput(data.new_field));

    const selInclOrig = document.createElement('select');
    selInclOrig.className = 'form-select form-select-sm';
    [['', '— (null)'], ['true', 'true'], ['false', 'false']].forEach(([v, l]) => {
        const opt = new Option(l, v);
        if (data.include_original === null || data.include_original === undefined) {
            if (v === '') opt.selected = true;
        } else if (String(data.include_original) === v) {
            opt.selected = true;
        }
        selInclOrig.appendChild(opt);
    });
    tdInclOrig.appendChild(selInclOrig);
    tdDel.appendChild(buildDeleteBtn(tr));

    tr.append(tdField, tdSep, tdCapture, tdNewField, tdInclOrig, tdDel);
    return tr;
}

function buildEditRow(data = {}) {
    const tr = document.createElement('tr');
    const tdField   = document.createElement('td');
    const tdRename  = document.createElement('td');
    const tdFind    = document.createElement('td');
    const tdReplace = document.createElement('td');
    const tdExtract = document.createElement('td');
    const tdDel     = document.createElement('td');

    tdField.appendChild(buildFieldSelect(data.field ?? ''));
    const renameVal = (data.rename && data.rename !== data.field) ? data.rename : '';
    tdRename.appendChild(buildNullableInput(renameVal));
    tdFind.appendChild(buildNullableInput(data.find));
    tdReplace.appendChild(buildNullableInput(data.replace));
    tdExtract.appendChild(buildNullableInput(data.extract));
    tdDel.appendChild(buildDeleteBtn(tr));

    tr.append(tdField, tdRename, tdFind, tdReplace, tdExtract, tdDel);
    return tr;
}

function formToConfig() {
    const sepPreset = document.getElementById('cfg-fieldSeparator-preset').value;
    const sepCustom = document.getElementById('cfg-fieldSeparator-custom').value;
    const sep = sepPreset === '__custom__' ? (sepCustom || '\t') : sepPreset;

    const naRaw = document.getElementById('cfg-naValue').value;
    const fileConfig = {
        outFileSuffix:           document.getElementById('cfg-outFileSuffix').value,
        fieldSeparator:          sep,
        naValue:                 naRaw === '' ? null : naRaw,
        convertNegLog10Pvalue:   document.getElementById('cfg-convertNegLog10Pvalue').checked,
        removeComments:          document.getElementById('cfg-removeComments').value,
    };

    const splitRules = Array.from(document.querySelectorAll('#split-rules-body tr')).map(tr => {
        const tds = tr.querySelectorAll('td');
        const inclOrigVal = tds[4].querySelector('select').value;
        return {
            field:            tds[0].querySelector('select').value || null,
            separator:        getSepValue(tds[1]),
            capture:          tds[2].querySelector('input').value || null,
            new_field:        tds[3].querySelector('input').value || null,
            include_original: inclOrigVal === '' ? null : inclOrigVal === 'true',
        };
    });

    const editRules = Array.from(document.querySelectorAll('#edit-rules-body tr')).map(tr => {
        const tds = tr.querySelectorAll('td');
        return {
            field:   tds[0].querySelector('select').value || null,
            rename:  tds[1].querySelector('input').value || null,
            find:    tds[2].querySelector('input').value || null,
            replace: tds[3].querySelector('input').value || null,
            extract: tds[4].querySelector('input').value || null,
        };
    });

    return JSON.stringify({ fileConfig, columnConfig: { split: splitRules, edit: editRules } }, null, 2);
}

function configToForm(obj) {
    const fc = obj.fileConfig || {};
    document.getElementById('cfg-outFileSuffix').value = fc.outFileSuffix ?? 'formatted_';

    const sepVal = fc.fieldSeparator ?? '\t';
    const sepPresetEl = document.getElementById('cfg-fieldSeparator-preset');
    const sepCustomEl = document.getElementById('cfg-fieldSeparator-custom');
    const presetVals  = Array.from(sepPresetEl.options).map(o => o.value).filter(v => v !== '__custom__');
    if (presetVals.includes(sepVal)) {
        sepPresetEl.value = sepVal;
        sepCustomEl.classList.add('d-none');
        sepCustomEl.value = '';
    } else {
        sepPresetEl.value = '__custom__';
        sepCustomEl.classList.remove('d-none');
        sepCustomEl.value = sepVal;
    }

    document.getElementById('cfg-naValue').value = fc.naValue ?? '';
    document.getElementById('cfg-convertNegLog10Pvalue').checked = !!fc.convertNegLog10Pvalue;
    document.getElementById('cfg-removeComments').value = fc.removeComments ?? '';

    const cc = obj.columnConfig || {};
    const splitBody = document.getElementById('split-rules-body');
    splitBody.innerHTML = '';
    const splitRulesList = cc.split || [];
    if (splitRulesList.length > 0) splitBody.appendChild(buildSplitRow(splitRulesList[0]));

    const editBody = document.getElementById('edit-rules-body');
    editBody.innerHTML = '';
    const existingEditRules = cc.edit || [];
    for (const rule of existingEditRules) editBody.appendChild(buildEditRow(rule));

    const coveredRenames = new Set(existingEditRules.map(r => r.rename).filter(Boolean));
    for (const mandatory of MANDATORY_RENAME_FIELDS) {
        if (!coveredRenames.has(mandatory)) {
            editBody.appendChild(buildEditRow({ rename: mandatory }));
        }
    }

    syncJsonPreview();
}

// Deduplicates edit rows by field name (keeps row with most filled-in values),
// sorts by field name, and returns the list of field names whose duplicates were removed.
window.deduplicateEditRules = function () {
    const tbody = document.getElementById('edit-rules-body');
    const entries = Array.from(tbody.querySelectorAll('tr')).map(tr => {
        const tds = tr.querySelectorAll('td');
        return {
            tr,
            field:   tds[0].querySelector('select').value || null,
            rename:  tds[1].querySelector('input').value  || null,
            find:    tds[2].querySelector('input').value  || null,
            replace: tds[3].querySelector('input').value  || null,
            extract: tds[4].querySelector('input').value  || null,
        };
    });

    const groups = new Map();
    const noField = [];
    for (const e of entries) {
        if (!e.field) { noField.push(e); continue; }
        if (!groups.has(e.field)) groups.set(e.field, []);
        groups.get(e.field).push(e);
    }

    const removedFields = [];
    const kept = [];
    for (const [field, group] of groups) {
        if (group.length === 1) {
            kept.push(group[0]);
        } else {
            const scored = group.map(e => ({
                e,
                score: [e.rename, e.find, e.replace, e.extract].filter(v => v).length,
            }));
            scored.sort((a, b) => b.score - a.score);
            kept.push(scored[0].e);
            for (let i = 1; i < scored.length; i++) removedFields.push(field);
        }
    }

    // Sort kept rows by MANDATORY_RENAME_FIELDS order; non-mandatory go at the end alphabetically
    const mandatoryIndex = name => {
        const i = MANDATORY_RENAME_FIELDS.indexOf(name);
        return i === -1 ? Infinity : i;
    };
    kept.sort((a, b) => {
        const ai = mandatoryIndex(a.rename || a.field || '');
        const bi = mandatoryIndex(b.rename || b.field || '');
        if (ai !== bi) return ai - bi;
        return (a.field || '').localeCompare(b.field || '');
    });
    const removedNullCount = noField.length;

    tbody.innerHTML = '';
    for (const e of kept) tbody.appendChild(e.tr);

    // Check which mandatory fields have no source column assigned.
    // A mandatory field is covered if a kept row has rename === mandatory,
    // or rename is null and field === mandatory (column keeps its own name).
    const isCovered = mandatory => kept.some(e => e.rename === mandatory || (!e.rename && e.field === mandatory));
    const betaCovered = isCovered('beta') || isCovered('odds_ratio');
    const missingMandatory = MANDATORY_RENAME_FIELDS.filter(mandatory => {
        if (mandatory === 'beta' || mandatory === 'odds_ratio') return !betaCovered;
        return !isCovered(mandatory);
    });

    return { removedFields, removedNullCount, missingMandatory };
};

function syncJsonPreview() {
    const preview = document.getElementById('config_out');
    if (preview) preview.value = formToConfig();
}
// Expose for the inline script's update-config handler
window.syncJsonPreview = syncJsonPreview;

// Field separator custom-input toggle
document.getElementById('cfg-fieldSeparator-preset').addEventListener('change', function () {
    const customEl = document.getElementById('cfg-fieldSeparator-custom');
    if (this.value === '__custom__') {
        customEl.classList.remove('d-none');
    } else {
        customEl.classList.add('d-none');
        customEl.value = '';
    }
});

// JSON preview toggle — driven by JS directly (no Bootstrap collapse dependency)
document.getElementById('json-preview-btn').addEventListener('click', () => {
    const panel = document.getElementById('json-preview-collapse');
    const btn   = document.getElementById('json-preview-btn');
    const isHidden = panel.style.display === 'none';
    if (isHidden) {
        syncJsonPreview();
        panel.style.display = 'block';
        btn.textContent = '\u25b2 View / Copy JSON';
    } else {
        panel.style.display = 'none';
        btn.textContent = '\u25bc View / Copy JSON';
    }
});

// Copy JSON button
document.getElementById('copy-json').addEventListener('click', () => {
    navigator.clipboard.writeText(document.getElementById('config_out').value);
    const btn = document.getElementById('copy-json');
    const orig = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(() => { btn.textContent = orig; }, 1500);
});

// ── Add-row buttons ───────────────────────────────────────────────
document.getElementById('add-split-rule').addEventListener('click', () => {
    document.getElementById('split-rules-body').appendChild(buildSplitRow());
});
document.getElementById('add-edit-rule').addEventListener('click', () => {
    document.getElementById('edit-rules-body').appendChild(buildEditRow());
});

// Expose column-loader so the inline step wizard can call it when navigating to Step 3
// without having gone through "Generate" first.
window.ensureInputColumns = async function () {
    if (inputColumns.length === 0 && inputFileHandle) {
        try {
            // Mirror what the generate handler does — read delimiter/comments from the form
            // so Python receives valid (possibly empty-string) values rather than undefined.
            delimiter    = document.getElementById('delimiter').value;
            removecomments = document.getElementById('comments').value;
            const input = await read(inputFileHandle);
            if (!input) return;
            const indata = JSON.parse(input);
            inputColumns = indata.title.map(col => col.title);
        } catch (e) {
            console.warn('Could not read input file columns:', e);
        }
    }
};


async function mountLocalDirectory() {
    // use the same ID crypt4gh to open pickers in the same directory
    dirHandle = await showDirectoryPicker();

    if ((await dirHandle.queryPermission({ mode: "readwrite" })) !== "granted") {
        if (
            (await dirHandle.requestPermission({ mode: "readwrite" })) !== "granted"
        ) {
            throw Error("Unable to read and write directory");
        }
    }
} 

async function saveFile(blob) {
    try {
      let outputConfig = `config_${inputFileHandle.name}.json`;
      
      const handle = await window.showSaveFilePicker({
        suggestedName: outputConfig,
        types: [
          {
            description: 'JSON files',
            accept: {
              'application/json': ['.json'],
            },
          },
        ],
      });
  
      // Write the blob to the file
      const writable = await handle.createWritable();
      await writable.write(blob);
      await writable.close();
  
      console.log('File saved successfully!');
    } catch (error) {
      console.error('Error saving file:', error);
    }
  }

async function getNewFileHandle() {
    let outputFileName = `${inputFileHandle.name}_formatted.tsv`;

    const options = {
        suggestedName: outputFileName,
        types: [
            {
                description: 'formatted file',
                accept: {
                    'application/octet-stream': ['.tsv'],
                },
            },
        ],
    };
    return window.showSaveFilePicker(options);
}

async function generate(inputFileHandle) {
    if (!inputFileHandle) {
        error('inputFileHandle is not defined');
        return;
    }

    let context = {
        dirHandle: dirHandle,
        inputFileName: inputFileHandle.name,
        delimiter: delimiter,
        removecomments: removecomments,
        analysisSoftware: analysisSoftware
    };
    try {
        const { results, error } = await asyncRun(generate_config, context);
        if (results) {
            console.log("pyodideWorker return results: ", results);
            alert("Generating configure file finish!");
            return results;
        } else if (error) {
            console.log("pyodideWorker error: ", error);
            appendAlertToElement("step2error",'Error: '+error,'danger' )
        }
    } catch (e) {
        console.log(
            `Error in pyodideWorker at ${e.filename}, Line: ${e.lineno}, ${e.message}`,
        );
        appendAlertToElement("step2error",'Error in pyodideWorker','danger')
    }
}

async function read(inputFileHandle) {
    if (!inputFileHandle) {
        console.error('inputFileHandle is not defined');
        return;
    }

    let context = {
        dirHandle: dirHandle,
        inputFileName: inputFileHandle.name,
        delimiter: delimiter,
        removecomments: removecomments,
    };
    try {
        const { results, error } = await asyncRun(read_input, context);
        if (results) {
            console.log("pyodideWorker return results: ", results);
            return results;
        } else if (error) {
            console.log("pyodideWorker error: ", error);
            appendAlertToElement("step2error",'Error: '+error,'danger')
        }
    } catch (e) {
        console.log(
            `Error in pyodideWorker at ${e.filename}, Line: ${e.lineno}, ${e.message}`,
        );
    }
}


async function test (inputFileHandle, config) {
    if (!inputFileHandle) {
        console.error('inputFileHandle is not defined');
        return;
    }
    let context = {
        dirHandle: dirHandle,
        inputFileName: inputFileHandle.name,
        config: config,
    };
    try {
        const { results, error } = await asyncRun(test_config, context);
        if (results) {
            console.log("pyodideWorker return results: ", results);
            alert("Format test finish!");
            return results;
        } else if (error) {
            console.log("pyodideWorker error: ", error);
            appendAlertToElement("step3rror",'Error: '+error,'danger')
        }
    } catch (e) {
        console.log(
            `Error in pyodideWorker at ${e.filename}, Line: ${e.lineno}, ${e.message}`,
        );
    }
}

async function apply (inputFileHandle, outputFileHandle, config) {
    if (!inputFileHandle) {
        console.error('inputFileHandle is not defined');
        return;
    }
    let context = {
        dirHandle: dirHandle,
        inputFileName: inputFileHandle.name,
        outputFileName: outputFileHandle.name,
        config: config,
    };
    try {
        const { results, error } = await asyncRun(apply_config, context);
        if (results) {
            $('#apply_configure').text("Please check the result in " + dirHandle + "/" + outputFileHandle.name);
            console.log("pyodideWorker return results: ", results);
            alert("Format test finish!");
            return results;
        } else if (error) {
            $('#apply_configure').text("pyodideWorker error: ", error)
            console.log("pyodideWorker error: ", error);
            appendAlertToElement("step4rror",'Error: '+error,'danger')
        }
    } catch (e) {
        $('#apply_configure').text(`Error in pyodideWorker at ${e.filename}, Line: ${e.lineno}, ${e.message}`)
        console.log(
            `Error in pyodideWorker at ${e.filename}, Line: ${e.lineno}, ${e.message}`,
        );
    }
}

async function validation(validateFileHandle) {
    if (!validateFileHandle) {
        console.error('formatted data is not defined');
        return;
    }
    console.log(dirHandle);
    let context = {
        dirHandle: dirHandle,
        outputFileName: validateFileHandle.name,
        zeropvalues: zeropvalues,
        nrows: nrows
    };
    try {
        const { results, error } = await asyncRun(validate, context);
        if (results) {
            validation_out.value =results;
            console.log("pyodideWorker return results: ", results);
            alert("Validation finish!");
            return results;
        } else if (error) {
            validation_out.value =error;
            console.log("pyodideWorker error: ", error);
            appendAlertToElement("step5error",'Error: '+error,'danger')
        }
    } catch (e) {
        validation_out.value =`Error in pyodideWorker at ${e.filename}, Line: ${e.lineno}, ${e.message}`;
        console.log(
            `Error in pyodideWorker at ${e.filename}, Line: ${e.lineno}, ${e.message}`,
        );
    }
}

async function appendAlertToElement(elementId, message, type) {
    const alertPlaceholder = document.getElementById(elementId);
    if (!alertPlaceholder) {
        console.error("Element with ID '" + elementId + "' not found.");
        return;
    }

    const wrapper = document.createElement('div');
    wrapper.innerHTML = [
        `<div class="alert alert-${type} alert-dismissible" role="alert">`,
        `   <div>${message}</div>`,
        '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
        '</div>'
    ].join('');

    alertPlaceholder.append(wrapper);
}

document.querySelector('#mount').addEventListener("click", async () => {
    if (!('showDirectoryPicker' in window)) {
        alert('Your browser does not support the File System Access API. Please use a supported browser.');
        return; // Stop execution if the API is not supported
    }
    else {
        await mountLocalDirectory();
        appendAlertToElement('mountdiv','Nice, you have granted the permission to the local directory '+dirHandle.name,'success' )
        document.querySelector('#select').disabled = false;
        document.querySelector('#select_validate').disabled = false;
        document.querySelector('#mountvalidate').disabled = true;
    }
  });

document.querySelector('#select').addEventListener('click', async () => {
    // Destructure the one-element array.
    [inputFileHandle] = await window.showOpenFilePicker();
    appendAlertToElement('selectdiv','You have selected the file '+ inputFileHandle.name,'success' )
    document.querySelector('#generate').disabled = false;
    document.querySelector('#download').disabled = false;
    document.querySelector('#test').disabled = false;
    document.querySelector('#apply').disabled = false;
    document.querySelector('#format-next-1').disabled = false;
});

document.querySelector('#generate').addEventListener('click', async () => {
    delimiter = document.getElementById('delimiter').value;
    removecomments = document.getElementById('comments').value;
    analysisSoftware= document.getElementById('analysis_software').value;

    appendAlertToElement("step2error",'Please Note: This is not guaranteed to return a valid standard file, because mandatory data fields could be missing in the input.','warning' )

    $('#generate').html('<span class="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></span> Analyzing...');

    let input = await read(inputFileHandle);
    if (!input) {
        $('#generate').html('Generate configuration');
        return;   // read() already showed the error alert
    }
    let indata;
    try {
        indata = JSON.parse(input);
    } catch (e) {
        appendAlertToElement('step2error', 'Could not parse file data: ' + e, 'danger');
        $('#generate').html('Generate configuration');
        return;
    }

    // Store column names for the config form dropdowns
    inputColumns = indata.title.map(col => col.title);

        var dataSet = indata.data;
        dataSet.forEach(r => {
            var div1 = document.createElement('div');
            div1.innerHTML = r[1];
            r[1] = div1;
         
            var div3 = document.createElement('div');
            div3.innerHTML = r[3];
            r[3] = div3;
        })

        // Store for lazy init — the table is inside a hidden panel so DataTables
        // can't measure widths here. It will be initialised on first open instead.
        if ($.fn.dataTable.isDataTable('#your_input')) {
            $('#your_input').DataTable().destroy();
            $('#your_input').empty();
        }
        inputTablePending = { columns: indata.title, data: dataSet };
        $('#generate').html('Generate configuration');


    let output = await generate(inputFileHandle);
    try {
        configToForm(JSON.parse(output));
        window.configGenerated = true;
        document.querySelector('#test').disabled = false;
        document.querySelector('#apply').disabled = false;
        document.querySelector('#format-next-2').disabled = false;
    } catch (err) {
        appendAlertToElement('step2error', 'Error generating configuration: ' + err, 'danger');
    }
  
});

document.querySelector('#test').addEventListener('click', async () => {
    test_example.value = "Preparing the result example...\n";
    var config = formToConfig();
    //your_output = "Preparing the result example...\n";
    let test_output=await test(inputFileHandle,config);
    try {
        test_example.value = "formatting result example\n";
        var test_out = JSON.parse(test_output);

        var dataSet = test_out.data;
        dataSet.forEach(r => {
            var div1 = document.createElement('div');
            div1.innerHTML = r[1];
            r[1] = div1;
         
            var div3 = document.createElement('div');
            div3.innerHTML = r[3];
            r[3] = div3;
        })

        //if the table table exist, need to destroy it and reinitiliaze it.
       if($.fn.dataTable.isDataTable('#your_output') ){
        $('#your_output').DataTable().destroy();
        $('#your_output').empty();
       }
       // create the table on the UI side
       $('#your_output').DataTable({
        columns: test_out.title,
        data: dataSet,
        paging: false,
        ordering: false,
        searching: false,
        autoWidth: true,
        scrollX: "600px"
        });

    } catch (err) {
        test_example.value = "Test configure on the input data:There is an error";
    }
});

document.querySelector('#download').addEventListener('click', async () => {
    $('#download').removeClass('btn-outline-secondary').addClass('btn-primary')
                  .html('<span class="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></span> Downloading...');
    var config = formToConfig();
    const blob = new Blob([config], { type: 'application/json' });
    await saveFile(blob);
    $('#download').removeClass('btn-primary').addClass('btn-success').text('Done');
});

document.querySelector('#apply').addEventListener('click', async () => {
    apply_configure.value = "Preparing the result ...\n";
    $('#apply').removeClass('btn-success').addClass('btn-primary').html('<span class="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></span> Formatting...');
    $('#apply_configure').text("we are appliying the configure to " + inputFileHandle.name);
    var config = formToConfig();
    outputFileHandle = await getNewFileHandle(inputFileHandle);
    await apply(inputFileHandle,outputFileHandle,config);
    apply_configure.value ="Apply configure file finish!\n";
    $('#apply').removeClass('btn-primary').addClass('btn-success').text('Done');
});

document.querySelector('#mountvalidate').addEventListener('click', async () => {
    if (!('showDirectoryPicker' in window)) {
        alert('Your browser does not support the File System Access API. Please use a supported browser.');
        return; // Stop execution if the API is not supported
    }
    else {
        await mountLocalDirectory();
        appendAlertToElement('validatediv','Nice, you have granted the permission to the local directory '+dirHandle.name,'success' )
        document.querySelector('#mount').disabled = true;
        document.querySelector('#select_validate').disabled = false;
    }
});


document.querySelector('#select_validate').addEventListener('click', async () => {
    [validateFileHandle] = await window.showOpenFilePicker();
    appendAlertToElement('validatediv','You have selected the file '+ validateFileHandle.name + 'for validation','success' )
    document.querySelector('#validate').disabled = false;
});


document.querySelector('#validate').addEventListener('click', async () => {
    zeropvalues=document.getElementById('zeropvalues').value
    nrows=document.getElementById('nrows').value

    validation_out.value = "Initializing validation...\n";
    $('#validate').html('<span class="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></span> Validating...'); 
    await validation(validateFileHandle);
    $('#validate').html('<button id="validate" class="btn btn-primary" data-mdb-ripple-init>Validate the selected file</button>'); 
});

$(document).ready(function() {
    // Lazy-init: initialise #example_table only on first open so DataTables
    // can measure real dimensions (initialising while hidden gives 0-px columns).
    var exampleTableInitialized = false;

    $( "#collapseExample" ).on("shown.bs.collapse", function() {
        if (!exampleTableInitialized) {
            new DataTable('#example_table', {
                columns: [
                    { title: 'chromosome' },
                    { title: 'base_pair_location' },
                    { title: 'effect_allele' },
                    { title: 'other_allele' },
                    { title: 'beta' },
                    { title: 'standard_error' },
                    { title: 'effect_allele_frequency' },
                    { title: 'p_value' },
                    { title: '...' }
                ],
                data: [
                    ['1', '693731',  'A',   'G',        '-0.016619', '0.00806496', '0.997221', '0.1', '...'],
                    ['1', '935393',  'G',   'GCCACGGG', '-0.016619', '0.00806496', '0.997221', '0.1', '...'],
                    ['1', '935393',  'G',   'GCCACGGG', '-0.016619', '0.00806496', '0.997221', '0.1', '...'],
                    ['1', '935475',  'CGC', 'C',        '-0.016619', '0.00806496', '0.997221', '0.1', '...']
                ],
                paging:    false,
                ordering:  false,
                searching: false,
                autoWidth: true,
                scrollX:   '600px'
            });
            exampleTableInitialized = true;
        } else {
            $('#example_table').DataTable().columns.adjust().draw();
        }
    });

    $( "#collapseInput" ).on("shown.bs.collapse", function() {
        if (inputTablePending) {
            new DataTable('#your_input', {
                columns:   inputTablePending.columns,
                data:      inputTablePending.data,
                paging:    false,
                ordering:  false,
                searching: false,
            });
            inputTablePending = null;
        } else if ($.fn.dataTable.isDataTable('#your_input')) {
            $('#your_input').DataTable().columns.adjust().draw();
        }
    });
} );
