async function main() {
    const integrimarkDebug = false;

    let canvas = document.createElement("canvas");
    let context = canvas.getContext("2d");

    function estimateTextWidth(text, size) {
        context.font = `${size}px Helvetica`;
        return context.measureText(text).width;
    }
    function estimateTextHeight(text, size) {
        context.font = `${size}px Helvetica`;
        return context.measureText(text).height;
    }

    function removeFirstFolder(path) {
        // Split the path by '/'
        const parts = path.split('/');
    
        // Remove the first non-empty part (which is the first folder)
        for (let i = 0; i < parts.length; i++) {
            if (parts[i]) {
                parts.splice(i, 1);
                break;
            }
        }
    
        // Join the parts back together
        return parts.join('/');
    }

    // Function to generate random text
    function generateRandomText(length) {
        const syllables = ['ba', 'la', 'na', 'mo', 'to', 'po', 'ki', 'ri',
            'mi', 'fu', 'lu', 'du', 'su', 'pu', 'ka', 'ta', 'pa', 'bo',
            ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '];
        let text = '';
        for (let i = 0; i < length; i++) {
            text += syllables[Math.floor(Math.random() * syllables.length)];
        }
        return text;
    }

    async function processPDF(pdfBytes, password, email, targetFilename) {
        try {
            let decryptedBytes = pdfBytes;

            if (password) {
                // Decrypt the PDF buffer
                const decrypted = CryptoJS.AES.decrypt(CryptoJS.lib.WordArray.create(pdfBytes).toString(CryptoJS.enc.Base64), password);
                decryptedBytes = new Uint8Array(decrypted.sigBytes);
                for (let i = 0; i < decrypted.sigBytes; i++) {
                    decryptedBytes[i] = decrypted.words[i >>> 2] >>> (24 - (i % 4) * 8) & 0xff;
                }
            }

            const pdfDoc = await PDFLib.PDFDocument.load(decryptedBytes);
            const pages = pdfDoc.getPages();

            // Get the current date and time in the format YYYY-MM-DD@HH:MM
            const currentDate = new Date();
            const formattedDate = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(currentDate.getDate()).padStart(2, '0')}@${String(currentDate.getHours()).padStart(2, '0')}:${String(currentDate.getMinutes()).padStart(2, '0')}`;

            // Watermark text (zero-char to make address unclickable)
            const watermarkText = email.replace("@", "[at]");
            const watermarkColor = [0.7, 1, 0.7]; // Light green pastel color in array format
            const watermarkFooter = `This document has been exclusively prepared for ${email} on ${formattedDate}. For any other person to view this document is a course violation.`;

            const textSize = 20;
            const textWidth = estimateTextWidth(watermarkText, textSize);
            //const textHeight = estimateTextHeight(watermarkText, textSize);
            const textHeight = textSize; //approximation

            for (const page of pages) {
                const { width, height } = page.getSize();
                
                // Tiling the watermark text across the page
                let shift = false; // To determine if we need to shift the line
                const shiftAmount = textWidth / 2; // Amount to shift every other line
                let secondaryShift = 0;
                let secondaryShiftAmount = 2;

                for (let y = height; y > 0; y -= textHeight * 1.2) {
                    let startX = 0; // Starting position for each line
                    
                    startX -= secondaryShift;

                    // If shift is true, adjust the starting position
                    if (shift) {
                        startX = -shiftAmount;
                        startX += secondaryShift;
                    }

                    for (let x = startX; x < width; x += textWidth) {
                        page.drawText(watermarkText, {
                            x: x,
                            y: y,
                            size: textSize,
                            color: new PDFLib.rgb(watermarkColor[0], watermarkColor[1], watermarkColor[2]),
                            opacity: 0.45,
                        });
                    }

                    // Toggle the shift for the next line
                    shift = !shift;

                    // Secondary shift
                    secondaryShift +=  secondaryShiftAmount;
                }

                // Bottom watermark
                page.drawText(watermarkFooter, {
                    x: 10,
                    y: 14,
                    size: 8,
                    opacity: 0.5,
                });
            }
            const useProtection = true;
            // ****************************************
            // Invisible text for copy-paste protection
            if (useProtection) {
                //const invisibleText = generateRandomText(5000); // Generate a long string
                const textSize = 10; // Very small font size
                const textHeight = textSize; // Estimation
                
                for (const page of pages) {
                    const { width, height } = page.getSize();

                    for (let y = height; y > 0; y -= textHeight * 0.15) {
                        let startX = 0; // Starting position for each line
                        
                        page.drawText(generateRandomText(400), {
                            x: startX,
                            y: y,
                            size: textSize,
                            color: PDFLib.rgb(1, 1, 1), // White color
                            opacity: 0, // Fully transparent
                        });
                    }
                }
            }
            // ****************************************

            // Extract basename and extension from the original filename
            const basename = originalFilename.split('.').slice(0, -1).join('.');
            const extension = originalFilename.split('.').pop();

            // Construct the new filename
            var newFilename = `${basename}-${email}.${extension}`;

            // Override if the target filename is specified
            if (targetFilename) {
                const lastPathComponent = targetFilename.split('/').pop();
                const targetBasename = lastPathComponent.split('.').slice(0, -1).join('.');
                newFilename = `${targetBasename}-${email}.${extension}`;
            }

            const watermarkedBytes = await pdfDoc.save();
            const blob = new Blob([watermarkedBytes], { type: 'application/pdf' });
            const url = URL.createObjectURL(blob);

            const downloadLink = document.getElementById('downloadLink');
            downloadLink.href = url;
            downloadLink.download = newFilename;  // Use the new filename here
            downloadLink.style.display = 'block';
            downloadLink.click();
        }
        catch (error) {
            throw error;
        }
    }

    function hashEmail(email) {
        return CryptoJS.SHA256(email);
    }

    function urlJoin(baseURL, path) {
        const url = new URL(path, baseURL);
        return url.toString();
    }

    function recoverPwd(email, secretKey) {
        const key = hashEmail(email).toString().slice(0, 32);
        const decrypted = CryptoJS.AES.decrypt(secretKey, key).toString(CryptoJS.enc.Utf8);
        return decrypted;
    }

    const currentPath = window.location.pathname;
    let publicKey = currentPath;
    let pdfUrl = integrimarkRoutes[publicKey]; // Use the routes object to get the corresponding PDF URL
    if(!pdfUrl) {
        publicKey = removeFirstFolder(currentPath);
        pdfUrl = integrimarkRoutes[publicKey];
        // check public key is at least one character long
        if(!pdfUrl && publicKey.length > 1) {
            publicKey = publicKey.substring(1);
            pdfUrl = integrimarkRoutes[publicKey];
        }
    }
    if(integrimarkDebug) {
        console.log("currentPath: " + currentPath);
        console.log("publicKey: " + publicKey);
        console.log("pdfUrl: " + pdfUrl);
        console.log("integrimarkBaseURL: " + integrimarkBaseURL);
    }
    
    // Make the path absolute if it is not already (this is to avoid being confused by the
    // paths introduced by the routing, that do not apply to files).
    if(pdfUrl) {
        pdfUrl = urlJoin(integrimarkBaseURL, pdfUrl);
    }

    if (!pdfUrl) {
        document.getElementById('errorMessage').textContent = 'Invalid URL.';
        document.getElementById('errorMessage').style.display = 'block';
        return;
    }

    // Set the file URL
    document.getElementById('fileUrl').value = pdfUrl;

    const urlParams = new URLSearchParams(window.location.search);
    const email = urlParams.get('email');
    const key = urlParams.get('key');

    if (!email || !key) {
        document.getElementById('errorMessage').textContent = 'Malformed URL.';
        document.getElementById('errorMessage').style.display = 'block';
        return;
    }

    const password = recoverPwd(email, key);

    // Fetch the PDF using the value from the fileUrl hidden field
    const response = await fetch(document.getElementById('fileUrl').value);
    const pdfBuffer = await response.arrayBuffer();
    const pdfBytes = new Uint8Array(pdfBuffer);
    const originalFilename = pdfUrl.split('/').pop();
    //const targetFilename = originalFilename;
    const targetFilename = publicKey;

    // Update the filename display in the frame
    document.getElementById('filenameDisplay').textContent = targetFilename;

    // Process the PDF without error catching
    //processPDF(pdfBytes, password, email, targetFilename);

    // Process the PDF with error catching
    try {
        await processPDF(pdfBytes, password, email, targetFilename);
    } catch (error) {
        console.error("Error processing PDF:", error);
        document.getElementById('errorMessage').textContent = 'Error processing the PDF. Please try again later or with new URL.';
        document.getElementById('errorMessage').style.display = 'block';
    }
}

main();