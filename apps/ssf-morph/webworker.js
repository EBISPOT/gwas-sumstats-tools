// webworker.js

// Setup your project to serve `py-worker.js`. You should also serve
// `pyodide.js`, and all its associated `.asm.js`, `.json`,
// and `.wasm` files as well:
importScripts("https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js");

async function loadPyodideAndPackages() {
    self.pyodide = await loadPyodide();
    await pyodide.loadPackage("micropip");
    const micropip = pyodide.pyimport("micropip");
    await pyodide.loadPackage(["ssl","numpy", "pytz", "ruamel.yaml", "pandas","pydantic"]);
    // manual workaround: docopt doesn't have a wheel file on python
    await micropip.install("./wheels/petl-1.7.14-py3-none-any.whl");
    await micropip.install("tabulate");
    await micropip.install("./wheels/gwas_sumstats_tools-1.0.24-py3-none-any.whl", keep_going=true);

    //await micropip.install("./wheels/stringcase-1.2.0-py3-none-any.whl");
    //await micropip.install("./wheels/frictionless-5.15.6-py3-none-any.whl");
    
}
let pyodideReadyPromise = loadPyodideAndPackages();


//This event is fired when the worker receives a message from the main thread via the postMessage method.
self.onmessage = async (event) => {
    var startTime = performance.now()
    // make sure loading is done
    await pyodideReadyPromise;
    // Don't bother yet with this line, suppose our API is built in such a way:
    const { id, python, ...context } = event.data;
    // The worker copies the context in its own "memory" (an object mapping name to values)
    for (const key of Object.keys(context)) {
      self[key] = context[key];
    }
    // Now is the easy part, the one that is similar to working in the main thread:
    try {
      var startTime = performance.now();

      await self.pyodide.loadPackagesFromImports(python);
      // mount local directory, make the nativefs as a global vaiable.
      if (! self.fsmounted){
        self.nativefs = await self.pyodide.mountNativeFS("/data", self.dirHandle);
        self.fsmounted = true;
      }
      // run python cript
      let results = await self.pyodide.runPythonAsync(python);
      // flush new files to disk
      await self.nativefs.syncfs();

      var endTime = performance.now();

      console.log(`Encryption web worker took ${(endTime - startTime) / 1000} seconds`)
      self.postMessage({ results, id });
    } catch (error) {
      self.postMessage({ error: error.message, id });
    }
  };
