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

(async function main() {
  try {
    const password = process.env.UNDERACTUATED_AUTOMATION_PWD;
    if (!password) {
      console.log("ERROR: You must set the UNDERACTUATED_AUTOMATION_PWD environment variable.");
      process.exit(1);
    }

    const browser = await puppeteer.launch();
    // or, for debugging:
    //const browser = await puppeteer.launch({headless:false, devtools:true});

    const google_login_page = await browser.newPage();
    const pages = await browser.pages();
    pages[0].close();

    // log in to google
    // username page
    await google_login_page.goto('https://accounts.google.com/signin/v2/identifier');
    await google_login_page.waitForSelector('input[type="email"]');
    await google_login_page.type('input[type="email"]', 'underactuatedautomation@gmail.com');
    await google_login_page.waitForSelector('#identifierNext');
    await google_login_page.click('#identifierNext');
    await google_login_page.waitForNavigation(0); 

    // password page
    await google_login_page.waitForTimeout(500);
    await google_login_page.waitForSelector('input[type="password"]');
    await google_login_page.evaluate((password) => {
      document.querySelector('input[type="password"]').value = password;
    }, password);
    await google_login_page.waitForTimeout(500);
    await google_login_page.keyboard.press('Enter');
    // Again to see that i'm actually logged in.
    await google_login_page.waitForNavigation(0); 

    const page = await browser.newPage();
    const url = "https://colab.research.google.com/drive/1Y6QZK0D_8Df9ATCa8pWiUq4ANn-_hrJa";
    const output_file = "colab_pip_freeze.txt";
    await page.goto(url);
    await page.waitForSelector('.codecell-input-output', 0);

    //debugger;
    await page.waitForTimeout(10000);  // would be better to find a selector.
    await page.keyboard.down('Control');
    await page.keyboard.press('F9');
    await page.keyboard.up('Control');
    await page.waitForSelector('.code-has-output', 0);

    await page.evaluate(() => {
      let element = document.querySelector('.stream');
      return element.innerText;
    }).then(text => {
        fs.writeFileSync("colab-pip-freeze.txt", text);
        console.log("Success!  Wrote output to colab-pip-freeze.txt.");
    })

    await browser.close();
  } catch (err) {
    console.error(err);
  }
})();