// Requires puppeteer and nodejs
// cd ~
// curl -sL https://deb.nodesource.com/setup_10.x -o nodesource_setup.sh
// sudo bash nodesource_setup.sh
// sudo apt install -y nodejs
// npm i puppeteer --save
// # Note: I had to manually npm i some of the missing deps on my first try to /// # the installer to complete without errors.
// npm install puppeteer-extra puppeteer-extra-plugin-stealth

'use strict';

exports.login_to_google = async function(browser) {
  try {
    const password = process.env.UNDERACTUATED_AUTOMATION_PWD;
    if (!password) {
      console.log("ERROR: You must set the UNDERACTUATED_AUTOMATION_PWD environment variable.");
      process.exit(1);
    }

    const page = await browser.newPage();

    // username page
    await page.goto('https://accounts.google.com/signin/v2/identifier');
    await page.waitForSelector('input[type="email"]');
    await page.type('input[type="email"]', 'underactuatedautomation@gmail.com');
    await page.waitForSelector('#identifierNext');
    await page.click('#identifierNext');
    await page.waitForNavigation(0); 

    // password page
    await page.waitForTimeout(1000);
    await page.waitForSelector('input[type="password"]');  // i think this sometimes fires on the first page.  
    await page.evaluate((password) => {
      document.querySelector('input[type="password"]').value = password;
    }, password);
    await page.waitForTimeout(500);
    await page.keyboard.press('Enter');

    // user account page
    await page.waitForNavigation(0); 
  } catch (err) {
    console.error(err);
  }
}
