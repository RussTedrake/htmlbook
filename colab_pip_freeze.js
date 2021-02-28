// npm install puppeteer puppeteer-extra
// npm install puppeteer-extra-plugin-stealth
'use strict';

const puppeteer = require('puppeteer-extra');

// Add stealth plugin to allow authenticating to google
const StealthPlugin = require('puppeteer-extra-plugin-stealth')
puppeteer.use(StealthPlugin())

const fs = require('fs');

(async function main() {
  try {
    const browser = await puppeteer.launch({headless:false, devtools:true});

    const google_login_page = await browser.newPage();
    const pages = await browser.pages();
    pages[0].close();

    await google_login_page.goto('https://accounts.google.com/signin/v2/identifier');
    // Once for the password page.
    await google_login_page.waitForNavigation(0); 
    // Again to see that i'm actually logged in.
    await google_login_page.waitForNavigation(0); 
    // And again for 2FA.
    await google_login_page.waitForNavigation(0); 

    const page = await browser.newPage();
    const url = "https://colab.research.google.com/drive/1Y6QZK0D_8Df9ATCa8pWiUq4ANn-_hrJa";
    const output_file = "colab_pip_freeze.txt";
    await page.goto(url);
    await page.waitForSelector('.stream');
    await page.waitForTimeout(10000);  // would be better to find a selector.
    await page.keyboard.down('Control');
    await page.keyboard.press('F9');
    await page.keyboard.up('Control');
    await page.waitForSelector('.code-has-output', 0);

    await page.evaluate(() => {
//      debugger;
      let element = document.querySelector('.stream');
      return element.innerText;
    }).then(text => {
        fs.writeFileSync("colab-pip-freeze.txt", text);
    })

    await browser.close();
  } catch (err) {
    console.error(err);
  }
})();