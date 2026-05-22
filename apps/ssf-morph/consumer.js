import "https://cdn.datatables.net/2.0.3/js/dataTables.js"
import { asyncRun, stopWorker } from "./py-worker.js";

const read_input = await fetch('./python_bin/read_input.py').then(response => response.text());
const generate_config = await fetch('./python_bin/generate_config.py').then(response => response.text());
const test_config = await fetch('./python_bin/test_config.py').then(response => response.text());
const apply_config = await fetch('./python_bin/apply_config.py').then(response => response.text());
const validate = await fetch('./python_bin/validation.py').then(response => response.text());
const validation_out = document.getElementById('validation_out');

let inputFile = null;
let inputFileBuffer = null;
let fileInWorker = false;   // true once inputFile has been written to worker MEMFS
let validateFile = null;
let validateFileBuffer = null;
let delimiter;
let removecomments;
let analysisSoftware;
let nrows;
let zeropvalues;
let validateAll = true;
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

function buildNewFieldControl(val) {
    // val can be null, a string, or an array
    const values = Array.isArray(val) ? val : (val ? [val] : []);
    const wrap = document.createElement('div');
    wrap.className = 'new-field-list';

    const addBtn = document.createElement('button');
    addBtn.type = 'button';
    addBtn.className = 'btn btn-sm btn-outline-secondary py-0 px-1 mt-1';
    addBtn.textContent = '+';
    wrap.appendChild(addBtn);

    function addEntry(v) {
        const row = document.createElement('div');
        row.className = 'new-field-entry d-flex gap-1 mb-1';
        const inp = document.createElement('input');
        inp.type = 'text';
        inp.className = 'form-control form-control-sm';
        inp.placeholder = 'null';
        inp.value = v || '';

        // If user types/pastes a JSON array string, expand it into multiple entries
        inp.addEventListener('change', () => {
            const raw = inp.value.trim();
            if (raw.startsWith('[') && raw.endsWith(']')) {
                try {
                    const parsed = JSON.parse(raw);
                    if (Array.isArray(parsed) && parsed.length > 0) {
                        row.remove();
                        for (const item of parsed) addEntry(String(item));
                        return;
                    }
                } catch (_) { /* not valid JSON, leave as-is */ }
            }
        });

        const rmBtn = document.createElement('button');
        rmBtn.type = 'button';
        rmBtn.className = 'btn btn-sm btn-outline-danger py-0 px-1';
        rmBtn.innerHTML = '&times;';
        rmBtn.addEventListener('click', () => row.remove());
        row.append(inp, rmBtn);
        wrap.insertBefore(row, addBtn);
    }

    addBtn.addEventListener('click', () => addEntry(''));

    const initialValues = values.length > 0 ? values : [''];
    for (const v of initialValues) addEntry(v);

    return wrap;
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
    tdNewField.appendChild(buildNewFieldControl(data.new_field));

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
        const newFieldVals = Array.from(tds[3].querySelectorAll('.new-field-entry input'))
            .flatMap(i => {
                const raw = i.value.trim();
                if (raw.startsWith('[') && raw.endsWith(']')) {
                    try {
                        const parsed = JSON.parse(raw);
                        if (Array.isArray(parsed)) return parsed.map(String).filter(v => v);
                    } catch (_) {}
                }
                return raw ? [raw] : [];
            });
        return {
            field:            tds[0].querySelector('select').value || null,
            separator:        getSepValue(tds[1]),
            capture:          tds[2].querySelector('input').value || null,
            new_field:        newFieldVals.length > 0 ? newFieldVals : null,
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
        btn.textContent = '▲ View / Copy JSON';
    } else {
        panel.style.display = 'none';
        btn.textContent = '▼ View / Copy JSON';
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
    if (inputColumns.length === 0 && inputFile) {
        try {
            delimiter      = document.getElementById('delimiter').value;
            removecomments = document.getElementById('comments').value;
            const input = await read(inputFile);
            if (!input) return;
            const indata = JSON.parse(input);
            inputColumns = indata.title.map(col => col.title);
        } catch (e) {
            console.warn('Could not read input file columns:', e);
        }
    }
};

// ── File helpers ──────────────────────────────────────────────────

function triggerDownload(data, filename) {
    const blob = new Blob([data], { type: 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Build the worker context for format operations.
// Includes fileBuffer only on the first call after a new file is selected,
// avoiding repeated large-buffer clones for test/apply/generate calls.
function formatContext(extra) {
    const ctx = { inputFileName: inputFile.name, ...extra };
    if (!fileInWorker) {
        ctx.fileBuffer = inputFileBuffer;
    }
    return ctx;
}

// ── Python runner wrappers ────────────────────────────────────────

async function read(file) {
    if (!file) { console.error('inputFile is not defined'); return; }
    const context = formatContext({ delimiter, removecomments });
    try {
        const { results, error } = await asyncRun(read_input, context);
        if (results) { fileInWorker = true; return results; }
        if (error) {
            console.log("pyodideWorker error: ", error);
            appendAlertToElement("step2error", 'Error: ' + error, 'danger');
        }
    } catch (e) {
        console.log(`Error in pyodideWorker at ${e.filename}, Line: ${e.lineno}, ${e.message}`);
    }
}

async function generate(file) {
    if (!file) { error('inputFile is not defined'); return; }
    const context = formatContext({ delimiter, removecomments, analysisSoftware });
    try {
        const { results, error } = await asyncRun(generate_config, context);
        if (results) {
            fileInWorker = true;
            console.log("pyodideWorker return results: ", results);
            alert("Generating configure file finish!");
            return results;
        }
        if (error) {
            console.log("pyodideWorker error: ", error);
            appendAlertToElement("step2error", 'Error: ' + error, 'danger');
        }
    } catch (e) {
        console.log(`Error in pyodideWorker at ${e.filename}, Line: ${e.lineno}, ${e.message}`);
        appendAlertToElement("step2error", 'Error in pyodideWorker', 'danger');
    }
}

async function test(file, config) {
    if (!file) { console.error('inputFile is not defined'); return; }
    const context = formatContext({ config });
    try {
        const { results, error } = await asyncRun(test_config, context);
        if (results) {
            fileInWorker = true;
            console.log("pyodideWorker return results: ", results);
            alert("Format test finish!");
            return results;
        }
        if (error) {
            console.log("pyodideWorker error: ", error);
            appendAlertToElement("step3error", 'Error: ' + error, 'danger');
        }
    } catch (e) {
        console.log(`Error in pyodideWorker at ${e.filename}, Line: ${e.lineno}, ${e.message}`);
    }
}

// writableStream: FileSystemWritableFileStream to stream chunks directly to disk,
// or null to accumulate chunks in memory and trigger a Blob download at the end.
async function apply(outputFileName, config, writableStream) {
    if (!inputFile) { console.error('inputFile is not defined'); return {}; }
    const context = formatContext({ outputFileName, config, returnOutput: true });
    const chunks = writableStream ? null : [];
    const onChunk = writableStream
        ? (chunk) => writableStream.write(chunk)
        : (chunk) => chunks.push(chunk);
    try {
        const result = await asyncRun(apply_config, context, undefined, onChunk);
        if (result.stopped) {
            if (writableStream) await writableStream.abort().catch(() => {});
            return { stopped: true };
        }
        const { results, error } = result;
        if (!error) {
            // Input was deleted from MEMFS in the worker; reset so the next
            // call re-sends the file rather than assuming it is cached.
            fileInWorker = false;
            inputFileBuffer = await inputFile.slice(0, 1048576).arrayBuffer();
            console.log("pyodideWorker return results: ", results);
            if (writableStream) {
                await writableStream.close();
            } else {
                triggerDownload(new Blob(chunks), outputFileName);
            }
            alert("Format apply finish!");
            return { results };
        }
        if (writableStream) await writableStream.abort().catch(() => {});
        console.log("pyodideWorker error: ", error);
        appendAlertToElement("step4error", 'Error: ' + error, 'danger');
    } catch (e) {
        if (writableStream) await writableStream.abort().catch(() => {});
        console.log(`Error in pyodideWorker at ${e.filename}, Line: ${e.lineno}, ${e.message}`);
        appendAlertToElement("step4error", 'Error in pyodideWorker', 'danger');
    }
    return {};
}

async function validation() {
    if (!validateFile) { console.error('validateFile is not defined'); return {}; }
    const context = {
        validateBuffer: validateFileBuffer,
        outputFileName: validateFile.name,
        zeropvalues,
        nrows,
        validateAll: validateAll ? 'True' : 'False',
    };
    try {
        const result = await asyncRun(validate, context, (msg) => {
            validation_out.value += msg + '\n';
        });
        if (result.stopped) return { stopped: true };
        const { results, error } = result;
        if (results) {
            validation_out.value = results;
            console.log("pyodideWorker return results: ", results);
            alert("Validation finish!");
            return results;
        }
        if (error) {
            validation_out.value = error;
            console.log("pyodideWorker error: ", error);
            appendAlertToElement("step5error", 'Error: ' + error, 'danger');
        }
    } catch (e) {
        validation_out.value = `Error in pyodideWorker at ${e.filename}, Line: ${e.lineno}, ${e.message}`;
        console.log(`Error in pyodideWorker at ${e.filename}, Line: ${e.lineno}, ${e.message}`);
    }
    return {};
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

// ── Drop zone setup ───────────────────────────────────────────────

function setupDropZone(zoneId, inputId, onFile) {
    const zone  = document.getElementById(zoneId);
    const input = document.getElementById(inputId);

    zone.addEventListener('click', () => input.click());
    zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file) onFile(file);
    });
    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) onFile(file);
        e.target.value = '';
    });
}

// Format wizard — input file
setupDropZone('format-drop-zone', 'format-file-input', async (file) => {
    inputFile       = file;
    // Read only the first 1MB for fast generate/read/test operations.
    // Apply loads the full file lazily when the button is clicked.
    inputFileBuffer = await file.slice(0, 1048576).arrayBuffer();
    fileInWorker    = false;
    appendAlertToElement('selectdiv', 'You have selected the file ' + file.name, 'success');
    document.querySelector('#generate').disabled     = false;
    document.querySelector('#download').disabled     = false;
    document.querySelector('#test').disabled         = false;
    document.querySelector('#apply').disabled        = false;
    document.querySelector('#format-next-1').disabled = false;
});

// Validate wizard — file to validate
setupDropZone('validate-drop-zone', 'validate-file-input', async (file) => {
    validateFile       = file;
    validateFileBuffer = await file.arrayBuffer();
    appendAlertToElement('validatediv', 'You have selected the file ' + file.name + ' for validation', 'success');

    const compressionFactor = file.name.endsWith('.gz') ? 5 : 1;
    const sizeGB = (file.size * compressionFactor) / (1024 * 1024 * 1024);
    const fullMinutes = Math.max(10, Math.round(sizeGB * 15));
    const estEl = document.getElementById('validate-full-estimate');
    estEl.textContent = sizeGB < 0.1
        ? '~5 min'
        : `~${fullMinutes} min for ${sizeGB.toFixed(1)} GB file`;

    if (sizeGB > 1) {
        document.getElementById('validate-large-file-hint').style.display = 'block';
    }

    document.querySelector('#validate-quick').disabled = false;
    document.querySelector('#validate-full').disabled  = false;
});

// ── Generate ──────────────────────────────────────────────────────

document.querySelector('#generate').addEventListener('click', async () => {
    delimiter      = document.getElementById('delimiter').value;
    removecomments = document.getElementById('comments').value;
    analysisSoftware = document.getElementById('analysis_software').value;

    appendAlertToElement("step2error", 'Please Note: This is not guaranteed to return a valid standard file, because mandatory data fields could be missing in the input.', 'warning');

    $('#generate').html('<span class="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></span> Analyzing...');

    let input = await read(inputFile);
    if (!input) {
        $('#generate').html('Generate configuration');
        return;
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
    });

    if ($.fn.dataTable.isDataTable('#your_input')) {
        $('#your_input').DataTable().destroy();
        $('#your_input').empty();
    }
    inputTablePending = { columns: indata.title, data: dataSet };
    $('#generate').html('Generate configuration');

    let output = await generate(inputFile);
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

// ── Test ──────────────────────────────────────────────────────────

document.querySelector('#test').addEventListener('click', async () => {
    test_example.value = "Preparing the result example...\n";
    var config = formToConfig();
    let test_output = await test(inputFile, config);
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
        });

        if ($.fn.dataTable.isDataTable('#your_output')) {
            $('#your_output').DataTable().destroy();
            $('#your_output').empty();
        }
        $('#your_output').DataTable({
            columns:  test_out.title,
            data:     dataSet,
            paging:   false,
            ordering: false,
            searching: false,
            autoWidth: true,
            scrollX:  "600px"
        });
    } catch (err) {
        test_example.value = "Test configure on the input data: There is an error";
    }
});

// ── Download config ───────────────────────────────────────────────

document.querySelector('#download').addEventListener('click', async () => {
    $('#download').removeClass('btn-outline-secondary').addClass('btn-primary')
                  .html('<span class="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></span> Downloading...');
    const config = formToConfig();
    const filename = inputFile ? `config_${inputFile.name}.json` : 'config.json';
    triggerDownload(new TextEncoder().encode(config), filename);
    $('#download').removeClass('btn-primary').addClass('btn-success').text('Done');
});

// ── Apply ─────────────────────────────────────────────────────────

document.querySelector('#apply').addEventListener('click', async () => {
    const applyBtn = document.querySelector('#apply');
    const stopBtn  = document.querySelector('#stop-apply');
    document.getElementById('stop-apply-suggestion').style.display = 'none';

    const config    = formToConfig();
    const configObj = JSON.parse(config);
    const suffix    = (configObj.fileConfig && configObj.fileConfig.outFileSuffix)
                      ? configObj.fileConfig.outFileSuffix : 'formatted_';
    const outputFileName = suffix + inputFile.name;

    // showSaveFilePicker requires a synchronous user-gesture context — call it
    // before any unrelated awaits so the browser allows it.
    let writableStream = null;
    if (window.showSaveFilePicker) {
        try {
            const handle = await window.showSaveFilePicker({ suggestedName: outputFileName });
            writableStream = await handle.createWritable();
        } catch (_) { /* user cancelled or API unavailable — fall back to Blob */ }
    }

    // Apply needs the whole file — reload if we only have the 1MB preview slice.
    // Also catches the case where the buffer was transferred (byteLength becomes 0).
    if (inputFile && inputFile.size > (inputFileBuffer ? inputFileBuffer.byteLength : 0)) {
        inputFileBuffer = await inputFile.arrayBuffer();
        fileInWorker = false;  // force re-write to MEMFS with the full file
    }

    $(applyBtn).removeClass('btn-success').addClass('btn-primary')
               .html('<span class="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></span> Formatting...');
    applyBtn.disabled = true;
    stopBtn.style.display = 'inline-block';
    $('#apply_configure').text('Applying configuration to ' + inputFile.name + '...');

    const { stopped } = await apply(outputFileName, config, writableStream);
    stopBtn.style.display = 'none';
    applyBtn.disabled = false;
    if (stopped) return;
    $('#apply_configure').text(writableStream ? 'File saved: ' + outputFileName : 'Download started: ' + outputFileName);
    $(applyBtn).removeClass('btn-primary').addClass('btn-success').text('Done');
});

document.querySelector('#stop-apply').addEventListener('click', async () => {
    stopWorker();
    fileInWorker = false;
    // Restore preview slice so generate/test don't re-send the full file next time
    if (inputFile) inputFileBuffer = await inputFile.slice(0, 1048576).arrayBuffer();
    const applyBtn = document.querySelector('#apply');
    const stopBtn  = document.querySelector('#stop-apply');
    $(applyBtn).removeClass('btn-primary').addClass('btn-success').text('Apply & Download');
    applyBtn.disabled = false;
    stopBtn.style.display = 'none';
    document.getElementById('apply_configure').textContent = '';
    document.getElementById('stop-apply-suggestion').style.display = 'block';
});

window.downloadConfigAfterStop = function () {
    const config = formToConfig();
    const filename = inputFile ? `config_${inputFile.name}.json` : 'config.json';
    triggerDownload(new TextEncoder().encode(config), filename);
};

// ── Validate ──────────────────────────────────────────────────────

function validateStart(btn) {
    document.querySelector('#validate-quick').disabled = true;
    document.querySelector('#validate-full').disabled  = true;
    document.querySelector('#stop-validate').style.display = 'inline-block';
    document.getElementById('stop-validate-suggestion').style.display = 'none';
    btn.innerHTML = '<span class="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></span> Validating...';
}

function validateEnd(btn, label) {
    document.querySelector('#validate-quick').disabled = false;
    document.querySelector('#validate-full').disabled  = false;
    document.querySelector('#stop-validate').style.display = 'none';
    btn.textContent = label;
}

document.querySelector('#validate-quick').addEventListener('click', async () => {
    zeropvalues = document.getElementById('zeropvalues').value;
    nrows       = document.getElementById('nrows').value;
    validateAll = false;
    validation_out.value = "Initializing quick validation (first 1M rows)...\n";
    const btn = document.querySelector('#validate-quick');
    validateStart(btn);
    const result = await validation();
    if (result && result.stopped) return;
    validateEnd(btn, 'Quick Validate');
});

document.querySelector('#validate-full').addEventListener('click', async () => {
    zeropvalues = document.getElementById('zeropvalues').value;
    nrows       = document.getElementById('nrows').value;
    validateAll = true;
    validation_out.value = "Initializing full validation...\n";
    const btn = document.querySelector('#validate-full');
    validateStart(btn);
    const result = await validation();
    if (result && result.stopped) return;
    validateEnd(btn, 'Full Validate');
});

document.querySelector('#stop-validate').addEventListener('click', () => {
    stopWorker();
    fileInWorker = false;
    document.querySelector('#validate-quick').disabled = false;
    document.querySelector('#validate-full').disabled  = false;
    document.querySelector('#validate-quick').textContent = 'Quick Validate';
    document.querySelector('#validate-full').textContent  = 'Full Validate';
    document.querySelector('#stop-validate').style.display = 'none';
    validation_out.value = '';
    document.getElementById('stop-validate-suggestion').style.display = 'block';
});

// ── DataTable lazy-init ───────────────────────────────────────────

$(document).ready(function() {
    // Lazy-init: initialise #example_table only on first open so DataTables
    // can measure real dimensions (initialising while hidden gives 0-px columns).
    var exampleTableInitialized = false;

    $("#collapseExample").on("shown.bs.collapse", function() {
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

    $("#collapseInput").on("shown.bs.collapse", function() {
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
});
