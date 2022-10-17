
// Usage: node test_colab_notebook.js [--terminate]
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
const path = require('path');
const colab = require('./colab.js');

const argv = require('yargs')(process.argv.slice(2))
  .usage('node test_colab_notebook.js path_to_notebook.ipynb')
  .boolean('terminate_session')
  .boolean('browser')
  .boolean('debug')
  .default('terminate_session', true)
  .default('browser', false)
  .default('debug', false)
  .argv;

(async function main() {
  try {
    var browser_options = {};
    if (argv.browser || argv.debug) {
      browser_options = {headless:false, devtools:true};
    }
    const browser = await puppeteer.launch(browser_options);

    // Close the default page that the browser always opens:
    const pages = await browser.pages();
    pages[0].close();

    console.log('logging in to google');
    await colab.login_to_google(browser);

    // __dirname returns the directory containing this .js file.
    const repo = path.basename(path.dirname(__dirname));
    const relative_path = argv._[0];

    const page = await browser.newPage();
    const url = "https://colab.research.google.com/github/RussTedrake/" + repo + "/blob/master/" + relative_path;
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
    try {
      await page.waitForFunction(
        () => window.colab.global.notebook.busyCellIds.size > 0);
      // it gets stuck here sometimes (despite the console confirming that the
      // value of busyCellIds.size is zero).
      console.log('waiting for run to complete');
      await page.waitForFunction(
        () => window.colab.global.notebook.busyCellIds.size == 0, 
        { timeout: 600000 });  // 10 min timeout. 
        // TODO: Reduce this to 5 min pending 

      console.log('checking outputs');
      await page.evaluate(() => {
        var cells = window.colab.global.notebook.cells;

        for (var i=0; i<cells.length; i++) {
          if (cells[i].lastExecutionFailed) {
            return cells[i].lastExecutionError;
          }
        }
        return undefined;
      }).then(err => {
        if (err) {
          console.error("Execution failed.");
          if (err.traceback) {
            for (var i=0; i<err.traceback.length; i++) {
              console.error(err.traceback[i]);
            }
          } else {
            console.error(err);
          }
        } else {
          console.log("Success!  All notebook cells ran successfully.");
        }
      })
    } catch (err) {
      console.error("Execution failed.")
      console.error(err);
    }

    // Terminate session (otherwise I'll run out).
    if (argv.terminate_session) {
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

    if (!argv.debug) {
      await browser.close();
    }
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
})();