// Requires puppeteer and nodejs
// cd ~
// curl -sL https://deb.nodesource.com/setup_10.x -o nodesource_setup.sh
// sudo bash nodesource_setup.sh
// sudo apt install -y nodejs
// npm i puppeteer puppeteer-extra
// or sudo npm i -g puppeteer puppeteer-extra
//
// Then run it with e.g. 
// node deepnote_check_notebooks.js


'use strict';

const { executablePath } = require('puppeteer');
const puppeteer = require('puppeteer-extra');

const fs = require('fs');

(async function main() {
  try {
    const browser = await puppeteer.launch({executablePath: executablePath()});
    // or, for debugging:
    //const browser = await puppeteer.launch({headless:false, devtools:true});

    // Close the default page that the browser always opens:
    const pages = await browser.pages();
    pages[0].close();

    const page = await browser.newPage();
    const url = process.argv[2];
    //const url = "https://deepnote.com/workspace/Manipulation-ac8201a1-470a-4c77-afd0-2cc45bc229ff/project/56-Simulation-Tuning-3ac7c471-008c-4512-a37c-8338b9790d6e/";
    await page.goto(url);
    await page.waitForSelector('[data-cy^=file-sidebar-item]', 0);

    var filenames = await page.evaluate(() => {
      files = document.querySelectorAll('[data-cy^=file-sidebar-item]');
      filenames = [];
      for (i=0; i<files.length; i++) {
        filenames.push(files[i].getAttribute('title'));
      }
      return filenames;
    })

    for (var i=0; i<filenames.length; i++) {
      console.log(filenames[i]);
    }

    await browser.close();
  } catch (err) {
    console.error(err);
  }
})();