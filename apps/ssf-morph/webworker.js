// webworker.js
importScripts("https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js");

async function loadPyodideAndPackages() {
    self.pyodide = await loadPyodide();
    await pyodide.loadPackage("micropip");
    const micropip = pyodide.pyimport("micropip");

    // C-extension packages from Pyodide's curated builds (no pure-Python wheel on PyPI)
    await pyodide.loadPackage(["ssl", "numpy", "pytz", "ruamel.yaml", "pyyaml", "pandas", "pydantic", "click", "requests"]);

    // petl: local wheel (specific version)
    await micropip.install("./wheels/petl-1.7.14-py3-none-any.whl");

    // bsub has no wheel on PyPI (sdist only) and is unused in the browser.
    // Install the local stub so micropip's dependency resolution accepts it.
    await micropip.install("./wheels/bsub-0.3.5-py3-none-any.whl");

    // pandera and its transitive deps are bundled locally to avoid PyPI fetches at
    // runtime. micropip in Pyodide can fail with BadZipFile when the network returns
    // an error page instead of a wheel, so we pre-install the full chain here:
    //   mypy_extensions <- typing_inspect <- pandera
    //   typeguard <- pandera
    await micropip.install([
        "./wheels/mypy_extensions-1.1.0-py3-none-any.whl",
        "./wheels/typing_inspect-0.9.0-py3-none-any.whl",
        "./wheels/typeguard-4.3.0-py3-none-any.whl",
        "./wheels/pandera-0.26.1-py3-none-any.whl",
    ]);

    // Install gwas_sumstats_tools; pass keep_going=true (second positional arg) so
    // a transient PyPI failure for one dep doesn't abort the whole init.
    await micropip.install("./wheels/gwas_sumstats_tools-1.0.24-py3-none-any.whl", true);

    await micropip.install("tabulate");
}
let pyodideReadyPromise = loadPyodideAndPackages();

self.onmessage = async (event) => {
    const { id, python, ...context } = event.data;
    for (const key of Object.keys(context)) {
        self[key] = context[key];
    }
    try {
        // Inside the try-catch so any init failure is reported back as an error
        // rather than hanging silently (pyodideReadyPromise rejection was previously
        // outside the try-catch, causing asyncRun to never resolve).
        await pyodideReadyPromise;
        await self.pyodide.loadPackagesFromImports(python);

        // Create /data directory once
        if (!self.dataReady) {
            self.pyodide.FS.mkdir('/data');
            self.dataReady = true;
        }

        // Write input file to MEMFS if a buffer was sent, then free it
        if (self.fileBuffer && self.inputFileName) {
            const t0 = performance.now();
            self.pyodide.FS.writeFile('/data/' + self.inputFileName, new Uint8Array(self.fileBuffer));
            self.fileBuffer = undefined;
            console.log(`MEMFS writeFile took ${((performance.now() - t0) / 1000).toFixed(1)}s`);
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

        // Free input from MEMFS only during apply (returnOutput) so the MEMFS
        // cache remains valid for subsequent read/generate/test calls.
        if (self.returnOutput && self.inputFileName) {
            try { self.pyodide.FS.unlink('/data/' + self.inputFileName); } catch (_) {}
        }

        // Stream output file back in 4 MiB chunks (transferable, zero-copy)
        if (self.returnOutput && self.outputFileName) {
            const CHUNK = 4 << 20; // 4 MiB
            try {
                const stat = self.pyodide.FS.stat('/data/' + self.outputFileName);
                const fd   = self.pyodide.FS.open('/data/' + self.outputFileName, 'r');
                for (let off = 0; off < stat.size; off += CHUNK) {
                    const len = Math.min(CHUNK, stat.size - off);
                    const buf = new Uint8Array(len);
                    self.pyodide.FS.read(fd, buf, 0, len, off);
                    const ab = buf.buffer;
                    self.postMessage({ type: 'chunk', id, chunk: ab }, [ab]);
                }
                self.pyodide.FS.close(fd);
                self.pyodide.FS.unlink('/data/' + self.outputFileName);
            } catch (e) {
                console.warn('Could not stream output file from MEMFS:', e);
            }
        }

        self.postMessage({ results, id });
    } catch (error) {
        self.postMessage({ error: error.message, id });
    }
};
