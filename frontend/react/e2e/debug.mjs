import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

try {
    await page.goto('http://localhost:3000/', { timeout: 60000, waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(5000);

    const bodyText = await page.locator('body').textContent();
    console.log('=== BODY TEXT (first 4000 chars) ===');
    console.log(bodyText.substring(0, 4000));

    const rootHTML = await page.locator('#root').innerHTML().catch(() => 'NO_ROOT');
    console.log('\n=== ROOT HTML (first 3000 chars) ===');
    console.log(rootHTML.toString().substring(0, 3000));
    console.log(`\nRoot HTML length: ${rootHTML.length}`);

    const title = await page.title();
    console.log(`\nPage title: ${title}`);

    // Check for common elements
    const inputCount = await page.locator('textarea, input[type="text"]').count();
    console.log(`\nText inputs found: ${inputCount}`);

    const buttonCount = await page.locator('button').count();
    console.log(`Buttons found: ${buttonCount}`);

    const buttonTexts = [];
    const buttons = await page.locator('button').all();
    for (const btn of buttons) {
        const txt = await btn.textContent().catch(() => '');
        if (txt.trim()) buttonTexts.push(txt.trim());
    }
    console.log(`Button texts: ${JSON.stringify(buttonTexts)}`);
} catch (err) {
    console.error('Error:', err.message);
}

await browser.close();
