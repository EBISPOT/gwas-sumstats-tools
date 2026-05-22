// webworker.js
importScripts("https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js");

async function loadPyodideAndPackages() {
    self.pyodide = await loadPyodide();
    await pyodide.loadPackage("micropip");
    const micropip = pyodide.pyimport("micropip");

    // C-extension packages from Pyodide's curated builds (no pure-Python wheel on PyPI)
    await pyodide.loadPackage(["ssl", "numpy", "pytz", "ruamel.yaml", "pyyaml", "pandas", "pydantic", "wrapt", "click"]);

    // petl: local wheel (specific version)
    await micropip.install("./wheels/petl-1.7.14-py3-none-any.whl");

    // bsub has no wheel on PyPI (sdist only) and is unused in the browser.
    // Install the local stub so micropip's dependency resolution accepts it.
    await micropip.install("./wheels/bsub-0.3.5-py3-none-any.whl");

    // Install gwas_sumstats_tools with full dep resolution — micropip fetches
    // remaining pure-Python deps (pandera, typer, requests, rich, etc.) from PyPI.
    await micropip.install("./wheels/gwas_sumstats_tools-1.0.24-py3-none-any.whl");

    await micropip.install("tabulate");
}
let pyodideReadyPromise = loadPyodideAndPackages();

self.onmessage = async (event) => {
    await pyodideReadyPromise;
    const { id, python, ...context } = event.data;
    for (const key of Object.keys(context)) {
        self[key] = context[key];
    }
    try {
        await self.pyodide.loadPackagesFromImports(python);

        // Create /data directory once
        if (!self.dataReady) {
            self.pyodide.FS.mkdir('/data');
            self.dataReady = true;
        }

        // Write input file to MEMFS if a buffer was sent, then free it
        if (self.fileBuffer && self.inputFileName) {
            self.pyodide.FS.writeFile('/data/' + self.inputFileName, new Uint8Array(self.fileBuffer));
            self.fileBuffer = undefined;
        }

        // Write validate file to MEMFS if a buffer was sent
        if (self.validateBuffer && self.outputFileName) {
            self.pyodide.FS.writeFile('/data/' + self.outputFileName, new Uint8Array(self.validateBuffer));
            self.validateBuffer = undefined;
        }

        self.pyodide.setStdout({
            batched: (msg) => self.postMessage({ type: 'stdout', id, msg })
        });

        var startTime = performance.now();
        let results = await self.pyodide.runPythonAsync(python);
        var endTime = performance.now();
        console.log(`Python execution took ${(endTime - startTime) / 1000} seconds`);

        self.pyodide.setStdout({ batched: (msg) => console.log(msg) });

        // Read output file back if the caller requested it (apply step)
        let outputData;
        if (self.returnOutput && self.outputFileName) {
            try {
                const bytes = self.pyodide.FS.readFile('/data/' + self.outputFileName);
                outputData = bytes.buffer;
            } catch (e) {
                console.warn('Could not read output file from MEMFS:', e);
            }
        }

        if (outputData) {
            self.postMessage({ results, id, outputData }, [outputData]);
        } else {
            self.postMessage({ results, id });
        }
    } catch (error) {
        self.postMessage({ error: error.message, id });
    }
};
