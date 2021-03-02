
// Usage: node test_colab_noteboox.js [--terminate]
//
// Requires puppeteer and nodejs
// cd ~
// curl -sL https://deb.nodesource.com/setup_10.x -o nodesource_setup.sh
// sudo bash nodesource_setup.sh
// sudo apt install -y nodejs
// npm i puppeteer --save
// # Note: I had to manually npm i some of the missing deps on my first try to /// # the installer to complete without errors.
// npm install puppeteer-extra puppeteer-extra-plugin-stealth

'use strict';

const puppeteer = require('puppeteer-extra');

// Add stealth plugin to allow authenticating to google
const StealthPlugin = require('puppeteer-extra-plugin-stealth')
puppeteer.use(StealthPlugin())

const fs = require('fs');
const colab = require('./colab.js');

(async function main() {
  try {
    //const browser = await puppeteer.launch();
    // or, for debugging:
    const browser = await puppeteer.launch({headless:false, devtools:true});

    // Close the default page that the browser always opens:
    const pages = await browser.pages();
    pages[0].close();

    console.log('logging in to google');
    await colab.login_to_google(browser);

    const relative_path = process.argv[2];

    const page = await browser.newPage();
    page.setDefaultTimeout(180000);
    const url = "https://colab.research.google.com/github/RussTedrake/underactuated/blob/master/" + relative_path;
    await page.goto(url);
    await page.waitForSelector('.codecell-input-output');

    await page.evaluate(async () => {
      window.colab.global.notebook.connectToKernel();
    })

    await page.waitForFunction(
      () => window.colab.global.notebook.kernel.isConnected());

    await page.evaluate(async () => {
      var notebook = window.colab.global.notebook;

      //debugger;
      notebook.clearAllOutputs();

      await notebook.kernel.execute('import os');
      await notebook.kernel.execute('os.environ["COLAB_TESTING"] = "True"');

      window.colab.global.notebook.runAll();
    })
  
    // Because the notebook was not authored by this user, I have to click 'ok'.
    await page.waitForSelector('#ok');
    await page.evaluate(() => {
      document.querySelector('#ok').click()
    })

    console.log('running all cells');
    await page.waitForFunction(
      () => window.colab.global.notebook.busyCellIds.size > 0);
    await page.waitForFunction(
      () => window.colab.global.notebook.busyCellIds.size == 0);

    console.log('checking outputs');
    await page.evaluate(() => {
      var cells = window.colab.global.notebook.cells;

      for (var i=0; i<cells.length; i++) {
        if (cells[i].lastExecutionFailed) {
          return cells[i].outputArea.element_.innerText;
        }
      }
      return undefined;
    }).then(output => {
      if (output) {
        console.log("Execution failed.");
        console.log(output);
      } else {
        console.log("Success!  All notebook cells ran successfully.");
      }
    })

    // Terminate session (otherwise I'll run out).
    if (process.argv.length > 3 && process.argv[3] === '--terminate') {
      await page.evaluate(async () => {
        id = window.colab.global.notebook.kernel.connection.session.kernelSessionId;
        s = await window.colab.global.notebook.kernel.listNotebookSessions();
        for (var i=0; i<s.length; i++) {
          if (s[i].sessionId == id) {
            await window.colab.global.notebook.kernel.terminateSession(s[i]);
          }
        }
      })
    }

    await browser.close();
  } catch (err) {
    console.error(err);
  }
})();