const fs = require('fs');
const { execSync } = require('child_process');

const cssInput = './web/integrimark.css';
const cssOutput = './web/_build/integrimark.min.css';

const htmlInput = './web/integrimark.html';
const htmlOutput = './web/_build/integrimark.min.html';

const jsInput = './web/integrimark.js';
const jsOutput = './web/_build/integrimark.min.js';

const htmlPackedOutput = './web/_build/integrimark.pack.html';

const integrimarkFinalOutput = './integrimark/integrimark.pack.html';

// MINIFY

// Minify CSS
execSync(`npx cssnano ${cssInput} ${cssOutput}`);

// Minify HTML
execSync(`npx html-minifier --collapse-whitespace --remove-comments ${htmlInput} -o ${htmlOutput}`);

// Minify and obfuscate JS
execSync(`npx uglifyjs ${jsInput} -o ${jsOutput} -c -m reserved=['integrimarkRoutes','integrimarkBaseURL']`);

console.log('Minification complete!');

// STITCH TOGETHER

// Read the minified CSS and JS
const cssContent = fs.readFileSync(cssOutput, 'utf-8');
const jsContent = fs.readFileSync(jsOutput, 'utf-8');

// Read the minified HTML
let htmlContent = fs.readFileSync(htmlOutput, 'utf-8');

// Replace placeholders or specific tags with the content
// Assuming you have <style id="inline-css"></style> and <script id="inline-js"></script> in your HTML
htmlContent = htmlContent.replace('<link rel="stylesheet" href="integrimark.css"/>', `<style>${cssContent}</style>`);
htmlContent = htmlContent.replace('<link rel="stylesheet" href="integrimark.css">', `<style>${cssContent}</style>`);
htmlContent = htmlContent.replace('<script src="integrimark.js"></script>', `<script>${jsContent}</script>`);

// Save the modified HTML
fs.writeFileSync(htmlPackedOutput, htmlContent);

console.log('CSS and JS inlined into HTML!');

// COPY FROM htmlPackedOutput to "integrimark/integrimark.pack.html"
fs.copyFileSync(htmlPackedOutput, integrimarkFinalOutput);