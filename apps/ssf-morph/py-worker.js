// This script is setting up a way to run Python scripts asynchronously in a web worker. It sends the Python script to the worker and sets up a callback to handle the result when the worker has finished executing the script.
let pyodideWorker = new Worker("./webworker.js");

const callbacks = {};
const stdoutCallbacks = {};
const chunkCallbacks = {};

function handleMessage(event) {
  const { id, type, msg, chunk, ...data } = event.data;
  if (type === 'stdout') {
    if (stdoutCallbacks[id]) stdoutCallbacks[id](msg);
    return;
  }
  if (type === 'chunk') {
    if (chunkCallbacks[id]) chunkCallbacks[id](chunk);
    return;
  }
  const onSuccess = callbacks[id];
  delete callbacks[id];
  delete stdoutCallbacks[id];
  delete chunkCallbacks[id];
  onSuccess(data);
}

pyodideWorker.onmessage = handleMessage;

// Terminates the running worker, resolves all pending promises with {stopped:true},
// then recreates a fresh worker ready for the next operation.
function stopWorker() {
  pyodideWorker.terminate();
  for (const id of Object.keys(callbacks)) {
    callbacks[id]({ stopped: true });
    delete callbacks[id];
    delete stdoutCallbacks[id];
    delete chunkCallbacks[id];
  }
  pyodideWorker = new Worker("./webworker.js");
  pyodideWorker.onmessage = handleMessage;
}

//This id is incremented each time the function is invoked and is kept within the safe integer limit.
const asyncRun = (() => {
  let id = 0; // identify a Promise
  return (script, context, onProgress, onChunk) => {
    // the id could be generated more carefully
    id = (id + 1) % Number.MAX_SAFE_INTEGER;
    if (onProgress) stdoutCallbacks[id] = onProgress;
    if (onChunk)    chunkCallbacks[id]  = onChunk;
    // Transfer large buffers instead of copying them to save memory
    const transferables = [];
    if (context.fileBuffer     instanceof ArrayBuffer) transferables.push(context.fileBuffer);
    if (context.validateBuffer instanceof ArrayBuffer) transferables.push(context.validateBuffer);
    return new Promise((onSuccess) => {
      callbacks[id] = onSuccess;
      pyodideWorker.postMessage({
        ...context,
        python: script,
        id,
      }, transferables);
    });
  };
})();

export { asyncRun, stopWorker };
