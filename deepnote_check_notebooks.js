/* Requires Node.js and Puppeteer
Linux installation:
cd /tmp
curl -sL https://deb.nodesource.com/setup_20.x -o nodesource_setup.sh
sudo bash nodesource_setup.sh
sudo apt install -y nodejs
npm init -y  # Initialize project
npm install puppeteer puppeteer-extra puppeteer-extra-plugin-stealth

macOS installation:
brew install node@20  # Specific version
npm init -y  # Initialize project
npm install puppeteer puppeteer-extra puppeteer-extra-plugin-stealth

Then run with:
node deepnote_check_notebooks.js "https://deepnote.com/workspace/{workspace}/project/{project_id}/"
*/

'use strict';

const { executablePath } = require('puppeteer');
const puppeteer = require('puppeteer-extra');

const fs = require('fs');

(async function main() {
  try {
    const url = process.argv[2];
    if (!url) {
      throw new Error('Please provide a Deepnote workspace URL as a command line argument.\nUsage: node deepnote_check_notebooks.js "https://deepnote.com/workspace/{workspace}/project/{project_id}/"');
    }

    const browser = await puppeteer.launch({executablePath: executablePath()});
    // or, for debugging:
    //const browser = await puppeteer.launch({headless:false, devtools:true});

    // Close the default page that the browser always opens:
    const pages = await browser.pages();
    await pages[0].close();

    const page = await browser.newPage();
    
    try {
      await page.goto(url);
    } catch (error) {
      throw new Error(`Failed to load URL: ${url}. Error: ${error.message}`);
    }

    try {
      await page.waitForSelector('[data-cy^=notebooks_upload-droparea] [data-cy^=file-sidebar-item]');
    } catch (error) {
      throw new Error('Could not find notebook elements on the page. Please check if the URL is correct and you have access to the workspace.');
    }

    const notebooks = await page.evaluate(() => {
      const books = document.querySelectorAll('[data-cy^=notebooks_upload-droparea] [data-cy^=file-sidebar-item]');
      const notebooks = [];
      for (let i = 0; i < books.length; i++) {
        notebooks.push(books[i].innerText);
      }
      return notebooks;
    });

    notebooks.forEach(notebook => {
      if (notebook) {
        console.log(notebook);
      }
    });

    console.log("---");  // delimiter

    const filenames = await page.evaluate(() => {
      const files = document.querySelectorAll('[data-cy^=file-explorer_upload-droparea] [data-cy^=file-sidebar-item]');
      const filenames = [];
      for (let i = 0; i < files.length; i++) {
        filenames.push(files[i].getAttribute('title'));
      }
      return filenames;
    });

    filenames.forEach(filename => {
      if (filename) {
        console.log(filename);
      }
    });

    await browser.close();
  } catch (err) {
    console.error(err.message);
    process.exit(1);  // Exit with error code
  }
})();