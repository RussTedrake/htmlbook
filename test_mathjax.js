// Run with: node --test test_mathjax.js
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function deferred() {
  let resolve;
  const promise = new Promise(r => { resolve = r; });
  return {promise, resolve};
}

function context(values = {}) {
  const ctx = vm.createContext(values);
  ctx.window = ctx;
  return ctx;
}

function run(ctx, name) {
  vm.runInContext(fs.readFileSync(path.join(__dirname, name), 'utf8'), ctx);
}

test('loader waits for startup and loads only the CDN runtime on success', async () => {
  const startup = deferred();
  const scripts = [];
  const ctx = context({
    MathJax: {startup: {promise: startup.promise}},
    document: {
      createElement: () => ({}),
      head: {appendChild: script => scripts.push(script)}
    }
  });
  run(ctx, 'mathjax-loader.js');
  assert.equal(scripts.length, 1);
  assert.match(scripts[0].src, /mathjax@4\.1\.3\/tex-chtml\.js$/);
  let ready = false;
  ctx.mathjaxReady.then(() => { ready = true; });
  scripts[0].onload();
  await Promise.resolve();
  assert.equal(ready, false);
  startup.resolve();
  await ctx.mathjaxReady;
  assert.equal(scripts.length, 1);
});

test('loader falls back to the local v4 runtime only on CDN failure', async () => {
  const scripts = [];
  let removed = 0;
  const ctx = context({
    MathJax: {startup: {promise: Promise.resolve()}},
    document: {
      createElement: () => ({remove: () => { removed++; }}),
      head: {appendChild: script => scripts.push(script)}
    }
  });
  run(ctx, 'mathjax-loader.js');
  scripts[0].onerror();
  await Promise.resolve();
  assert.equal(removed, 1);
  assert.equal(scripts.length, 2);
  assert.equal(scripts[1].src, 'htmlbook/MathJax/node_modules/mathjax/tex-chtml.js');
  scripts[1].onload();
  await ctx.mathjaxReady;
});

test('loader reports failure if neither runtime can be loaded', async () => {
  const scripts = [];
  const ctx = context({MathJax: {}, document: {
    createElement: () => ({remove() {}}),
    head: {appendChild: script => scripts.push(script)}
  }});
  run(ctx, 'mathjax-loader.js');
  const rejected = assert.rejects(ctx.mathjaxReady, /Unable to load MathJax/);
  scripts[0].onerror();
  await Promise.resolve();
  scripts[1].onerror();
  await rejected;
});

for (const useLoader of [false, true]) {
  test(`typesetting waits for readiness and exposes completion (loader=${useLoader})`, async () => {
    const ready = deferred();
    const typeset = deferred();
    let called = false;
    const ctx = context({MathJax: {
      startup: {promise: ready.promise},
      typesetPromise: () => { called = true; return typeset.promise; }
    }});
    if (useLoader) ctx.mathjaxReady = ready.promise;
    run(ctx, 'book.js');
    const result = ctx.typesetMath();
    assert.equal(result, ctx.mathTypesetPromise);
    assert.equal(called, false);
    ready.resolve();
    await new Promise(setImmediate);
    assert.equal(called, true);
    let finished = false;
    result.then(() => { finished = true; });
    await Promise.resolve();
    assert.equal(finished, false);
    typeset.resolve();
    await result;
    assert.equal(finished, true);
  });
}
