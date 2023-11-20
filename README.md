# IntegriMark

IntegriMark is a sophisticated command-line tool designed for the secure and traceable distribution of digital PDF documents. It focuses on watermarking PDF files with unique, user-specific details, enhancing their traceability and deterring unauthorized sharing.

## Features

- **Encryption of PDF Files:** Securely encrypts PDF files, storing them in a `_bundle` directory.
- **Unique Password Generation:** Each file is encrypted with a unique, automatically generated password for robust security.
- **Customized URL Generation:** Creates customized URLs for each encrypted file, tailored to specific email addresses, enabling controlled distribution and tracking of document access.
- **Hosting on Specified Base URL:** Allows hosting of the watermarked documents on a specified base URL, ideal for distributing sensitive or proprietary information securely.

## Installation

IntegriMark can be installed using pip:

```bash
pip install integrimark
```

## Usage

### Creating an Encrypted Bundle

To encrypt PDF files and save them in the `_bundle` directory:

```bash
integrimark create [OPTIONS] FILES...
```

Options:
- `-o`, `--output_directory`: Directory where `_bundle` folder will be created. Defaults to the current working directory.
- `-u`, `--base_url`: Base URL at which the IntegriMark vault will be hosted.

### Generating Customized URLs

To generate URLs for a given email address and file names:

```bash
integrimark url [OPTIONS] BUNDLE_PATH EMAIL_ADDRESS
```

Options:
- `-f`, `--file_name`: Name of the file (e.g., 'HW1-SOLUTIONS'). Can be used multiple times for multiple files.

## Example

```bash
integrimark create --output_directory ./mydocs --base_url https://example.com mydoc.pdf
integrimark url ./mydocs/_bundle someone@example.com
```

## Bundle Structure

The `_bundle` directory is produced by IntegriMark based on the provided files to be watermarked, and is intended to be hosted on GitHub Pages.

Here is an example of a `_bundle` directory:
```bash
_bundle
├── 404.html
├── _16bd60bcd372880e018303072d605d6e.enc.pdf
├── _266f48d5d164ef7b50095f37e9a0238e.enc.pdf
├── _584b8e2a64c6999c46b6ebf40fd2db6a.enc.pdf
├── _9b8638292a13aac15f090cdffdcf49db.enc.pdf
├── _a3d730435ea820bec63441d81d552116.enc.pdf
├── _a6024a44d566030763e4f5469e82ab77.enc.pdf
├── _fc0a90e636a4b5ccdd046f6b826b4258.enc.pdf
├── passwords.json
└── routing.js
```

The `_bundle` directory contains the following files:
- `404.html`: The is the page that Google Pages uses when a file is not found. We use it to redirect to the correct download file according to the `routing.js`.
- `routing.js`: This is the file that contains the routing information for the files. It is a JavaScript file that contains a dictionary mapping email addresses to file names. For example, the following is the content of `routing.js`:
    ```javascript
    var integrimarkRoutes = {
    "Exam1-Solutions.pdf": "_266f48d5d164ef7b50095f37e9a0238e.enc.pdf",
    "HW2-Solutions.pdf": "_584b8e2a64c6999c46b6ebf40fd2db6a.enc.pdf",
    "HW3-Solutions.pdf": "_9b8638292a13aac15f090cdffdcf49db.enc.pdf",
    "HW4-Solutions.pdf": "_fc0a90e636a4b5ccdd046f6b826b4258.enc.pdf",
    "HW5-Solutions.pdf": "_a6024a44d566030763e4f5469e82ab77.enc.pdf",
    "HW6-Solutions.pdf": "_16bd60bcd372880e018303072d605d6e.enc.pdf",
    "HW7-Solutions.pdf": "_a3d730435ea820bec63441d81d552116.enc.pdf"
    };

    var integrimarkBaseURL = 'https://cit-5920.github.io/vault/';
    ```
- `passwords.json`: This is the file that contains the passwords for the encrypted files. It is a JSON file that contains a dictionary mapping file names to passwords. For example, the following is the content of `passwords.json`:
    ```json
    {
        "manifestVersion": 1,
        "passwords": {
            "_266f48d5d164ef7b50095f37e9a0238e.enc.pdf": "cadillac ...",
            "_584b8e2a64c6999c46b6ebf40fd2db6a.enc.pdf": "rarity ...",
            "_9b8638292a13aac15f090cdffdcf49db.enc.pdf": "appointee ...",
            "_fc0a90e636a4b5ccdd046f6b826b4258.enc.pdf": "playhouse ...",
            "_a6024a44d566030763e4f5469e82ab77.enc.pdf": "dipping ...",
            "_16bd60bcd372880e018303072d605d6e.enc.pdf": "glorified ...",
            "_a3d730435ea820bec63441d81d552116.enc.pdf": "gawk ..."
        },
        "base_url": "https://cit-5920.github.io/vault/",
        "routing": {
            "Exam1-Solutions.pdf": "_266f48d5d164ef7b50095f37e9a0238e.enc.pdf",
            "HW2-Solutions.pdf": "_584b8e2a64c6999c46b6ebf40fd2db6a.enc.pdf",
            "HW3-Solutions.pdf": "_9b8638292a13aac15f090cdffdcf49db.enc.pdf",
            "HW4-Solutions.pdf": "_fc0a90e636a4b5ccdd046f6b826b4258.enc.pdf",
            "HW5-Solutions.pdf": "_a6024a44d566030763e4f5469e82ab77.enc.pdf",
            "HW6-Solutions.pdf": "_16bd60bcd372880e018303072d605d6e.enc.pdf",
            "HW7-Solutions.pdf": "_a3d730435ea820bec63441d81d552116.enc.pdf"
        }
    }
    ```
- the other files are the encrypted files, with the name of the encrypted file being the hash of the password used to encrypt the file.

## Contributing

Contributions to IntegriMark are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for more information.

## License

IntegriMark is released under the LGPLv3 License. See [LICENSE](LICENSE.md) for more information. Essentially, this means you can use this software for free, even for commercial purposes, as long as you include a copy of the license in any copies or substantial portions of the software. If you make any changes to this library, you must also release them under the LGPLv3. However you may include this library in your own projects without releasing the source code for those projects.

## Acknowledgments

Built with love by Jérémie Lumbroso <lumbroso@seas.upenn.edu>. Feedback and contributions are welcome.

For more information, visit [IntegriMark on GitHub](https://github.com/jlumbroso/integrimark).