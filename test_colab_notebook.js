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

/*
    console.log('waiting for kernel');
    await page.waitForFunction(
      () => window.colab.global.notebook.kernel.state === 'connected' || window.colab.global.notebook.kernel.state === 'kernel idle');

    await page.evaluate(() => {
      var notebook = window.colab.global.notebook;
      notebook.clearAllOutputs();

      notebook.kernel.execute('import os');
      notebook.kernel.execute('os.environ["COLAB_TESTING"] = "True"');
    })

    await page.waitForFunction(
      () => window.colab.global.notebook.kernel.isConnected());
*/
    await page.evaluate(() => {
      window.colab.global.notebook.runAll();
    })
  
    // Because the notebook was not authored by this user, I have to click 'ok'.
    await page.waitForSelector('#ok');
    await page.evaluate(() => {
      document.querySelector('#ok').click()
    })

    console.log('running all cells');
    await page.waitForSelector('.code-has-output');
    await page.waitForFunction(
      () => window.colab.global.notebook.busyCellIds.size == 0);

    await page.evaluate(() => {
      var cells = window.colab.global.notebook.cells;

      var success = true;
      for (var i=0; i<cells.length; i++) {
        if (cells[i].lastExecutionFailed) {
          success = false;
        }
      }
      return success;
    }).then(success => {
      if (success) {
        console.log("Success!  All notebook cells ran successfully.");
      } else {
        console.log("One ore more cells had execution errors.")
      }
    })

    await browser.close();
  } catch (err) {
    console.error(err);
  }
})();