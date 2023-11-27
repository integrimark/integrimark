const { execSync } = require('child_process');
const fs = require('fs');

const htmlMailerInput = './web/integrimark.solutions-email.jinja2.html';
const htmlMailerOutput = './integrimark/integrimark.solutions-email.jinja2.html';
const integrimarkPackFilePath = './integrimark/integrimark.pack.html';

function runCommand(command) {
    try {
        execSync(command, { stdio: 'inherit' });
    } catch (error) {
        console.error(`Failed to execute ${command}: ${error}`);
        process.exit(1);
    }
}

console.log('Updating integrimark.solutions-email.jinja2.html');
fs.copyFileSync(htmlMailerInput, htmlMailerOutput);

console.log('Running build-integrimark-pack.js...');
runCommand('node build-integrimark-pack.js');

console.log('Checking for integrimark.pack.html...');
if (!fs.existsSync(integrimarkPackFilePath)) {
    console.error('Error: integrimark.pack.html was not created.');
    process.exit(1);
}

console.log('integrimark.pack.html exists. Proceeding with Poetry build...');
runCommand('poetry build');

console.log('Running Poetry publish...');
runCommand('poetry publish');

console.log('Build and publish process completed.');
