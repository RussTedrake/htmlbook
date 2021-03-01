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
    const browser = await puppeteer.launch();
    // or, for debugging:
    //const browser = await puppeteer.launch({headless:false, devtools:true});

    // Close the default page that the browser always opens:
    const pages = await browser.pages();
    pages[0].close();

    await colab.login_to_google(browser);

    const page = await browser.newPage();
    const url = "https://colab.research.google.com/drive/1Y6QZK0D_8Df9ATCa8pWiUq4ANn-_hrJa";
    await page.goto(url);
    //await page.waitForSelector('.codecell-input-output', 0);
    await page.waitForSelector('.monaco-list.list_id_1', 0);

    await page.evaluate(() => {
      window.colab.global.notebook.clearAllOutputs();
      window.colab.global.notebook.runAll();
    })
    // This worked for running all cells, too:
    //await page.keyboard.down('Control');
    //await page.keyboard.press('F9');
    //await page.keyboard.up('Control');

    // Because the notebook was not authored by this user, I have to click 'ok'.
    await page.waitForSelector('#ok');
    await page.evaluate(() => {
      document.querySelector('#ok').click()
    })

    // debugger;
    await page.waitForSelector('.code-has-output', 0);
    await page.evaluate(() => {
      return window.colab.global.notebook.cells[0].outputArea.element_.innerText;
    }).then(text => {
        fs.writeFileSync("colab-pip-freeze.txt", text);
        console.log("Success!  Wrote output to colab-pip-freeze.txt.");
    })

    await browser.close();
  } catch (err) {
    console.error(err);
  }
})();