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

## Contributing

Contributions to IntegriMark are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for more information.

## License

IntegriMark is released under the LGPLv3 License. See [LICENSE](LICENSE.md) for more information. Essentially, this means you can use this software for free, even for commercial purposes, as long as you include a copy of the license in any copies or substantial portions of the software. If you make any changes to this library, you must also release them under the LGPLv3. However you may include this library in your own projects without releasing the source code for those projects.

## Acknowledgments

Built with love by Jérémie Lumbroso <lumbroso@seas.upenn.edu>. Feedback and contributions are welcome.

For more information, visit [IntegriMark on GitHub](https://github.com/jlumbroso/integrimark).