// Run with 
// node render_html.js url output_file

'use strict';

const puppeteer = require('puppeteer');
const fs = require('fs');

(async function main() {
  let browser;
  try {
    browser = await puppeteer.launch();
    const page = await browser.newPage();
    
    const url = process.argv[2];
    const output_file = process.argv[3];
    await page.goto(url);
    // The load event can precede MathJax's asynchronous font loading/typesetting.
    await page.evaluate(async () => {
      await window.mathTypesetPromise;
      await document.fonts.ready;
    });
    const html = await page.content();
    fs.writeFileSync(output_file, html);
  } catch (err) {
    console.error(err);
    process.exitCode = 1;
  } finally {
    if (browser) await browser.close();
  }
})();