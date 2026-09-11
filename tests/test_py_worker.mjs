// Run with: node tests/test_py_worker.mjs
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { runInNewContext } from 'node:vm';

// Exercise the actual worker's startup notification on success and failure.
const workerSource = await readFile(new URL('../apps/ssf-morph/webworker.js', import.meta.url), 'utf8');
for (const fail of [false, true]) {
  let notify;
  const notification = new Promise((resolve) => { notify = resolve; });
  const sandbox = {
    URL,
    location: { href: 'https://pages.example.org/project/webworker.js' },
    importScripts() {},
    postMessage: notify,
    loadPyodide: async () => ({
      loadPackage: async () => {},
      pyimport: () => ({ install: async () => {
        if (fail) throw new Error('InvalidWheelFilename');
      } }),
    }),
  };
  sandbox.self = sandbox;
  runInNewContext(workerSource, sandbox);
  const status = await notification;
  assert.equal(status.type, 'ready');
  assert.equal(status.error, fail ? 'InvalidWheelFilename' : undefined);
}

const workers = [];
globalThis.Worker = class {
  constructor() { workers.push(this); }
  terminate() {}
  postMessage(message, transfer) {
    structuredClone(message, { transfer });
    queueMicrotask(() => this.onmessage({ data: { id: message.id, results: 'ok' } }));
  }
};
const source = await readFile(new URL('../apps/ssf-morph/py-worker.js', import.meta.url));
const { asyncRun, stopWorker } = await import(`data:text/javascript;base64,${source.toString('base64')}`);

// A failed startup and repeated attempts must leave both upload buffers intact.
const context = { fileBuffer: new ArrayBuffer(8), validateBuffer: new ArrayBuffer(16) };
const first = asyncRun('pass', context);
assert.equal(context.fileBuffer.byteLength, 8);
workers.at(-1).onmessage({ data: { type: 'ready', error: 'InvalidWheelFilename' } });
assert.deepEqual(await first, { error: 'InvalidWheelFilename' });
assert.deepEqual(await asyncRun('pass', context), { error: 'InvalidWheelFilename' });
assert.equal(context.fileBuffer.byteLength, 8);
assert.equal(context.validateBuffer.byteLength, 16);

// Stopping during startup must release waiting calls without transferring data.
stopWorker();
const cancelled = asyncRun('pass', context);
stopWorker();
assert.deepEqual(await cancelled, { stopped: true });
assert.equal(context.fileBuffer.byteLength, 8);

// A replacement worker that starts successfully still uses zero-copy transfer.
workers.at(-1).onmessage({ data: { type: 'ready' } });
assert.deepEqual(await asyncRun('pass', context), { results: 'ok' });
assert.equal(context.fileBuffer.byteLength, 0);
assert.equal(context.validateBuffer.byteLength, 0);
console.log('Worker startup and transfer checks passed');
