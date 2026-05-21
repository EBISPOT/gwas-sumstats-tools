// This script is setting up a way to run Python scripts asynchronously in a web worker. It sends the Python script to the worker and sets up a callback to handle the result when the worker has finished executing the script.
const pyodideWorker = new Worker("./webworker.js");

const callbacks = {};

pyodideWorker.onmessage = (event) => {
  const { id, ...data } = event.data;
  const onSuccess = callbacks[id];
  delete callbacks[id];
  onSuccess(data);
};
//This id is incremented each time the function is invoked and is kept within the safe integer limit.


const asyncRun = (() => {
  let id = 0; // identify a Promise
  return (script, context) => {
    // the id could be generated more carefully
    id = (id + 1) % Number.MAX_SAFE_INTEGER;
    return new Promise((onSuccess) => {
      callbacks[id] = onSuccess;
      pyodideWorker.postMessage({
        ...context,
        python: script,
        id,
      });
    });
  };
})();

export { asyncRun };