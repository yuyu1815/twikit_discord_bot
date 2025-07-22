# HTML JavaScript Converter

This tool uses Js2Py to extract and execute JavaScript embedded in HTML files, generating static HTML output with the JavaScript effects applied. It's useful for creating static snapshots of dynamic web pages.

## Features

- Extracts JavaScript code from HTML files
- Executes JavaScript using Js2Py
- Applies JavaScript effects to HTML content
- Generates static HTML with dynamic content rendered
- Supports both local HTML files and URLs
- Includes a sample HTML generator for testing

## Installation

You can install the required dependencies in two ways:

### Option 1: Using requirements.txt

```bash
pip install -r requirements.txt
```

### Option 2: Manual Installation

```bash
pip install js2py beautifulsoup4 requests
```

## Usage

### Basic Usage

```bash
python html_js_converter.py input.html output.html
```

### Process a URL

```bash
python html_js_converter.py https://example.com output.html
```

### Run with Sample Data

If you run the script without arguments, it will create and process a sample HTML file:

```bash
python html_js_converter.py
```

This will create two files:
- `sample.html`: A sample HTML file with embedded JavaScript
- `sample_static.html`: The processed static HTML output

### Using the Test Script

A test script is provided to demonstrate the converter with a more comprehensive example:

```bash
python test_converter.py
```

This will:
1. Take the `example.html` file (which contains various JavaScript features)
2. Process it using the converter
3. Generate `example_static.html` with all JavaScript effects applied statically

## How It Works

1. **Extract JavaScript**: The script extracts all inline JavaScript code from the HTML file.
2. **Execute JavaScript**: It uses Js2Py to execute the JavaScript code in a controlled environment.
3. **Apply Effects**: The script applies the effects of the JavaScript to the HTML content using special data attributes:
   - `data-js-content="variableName"`: Replaces the element's content with the value of the JavaScript variable.
   - `data-js-attr="attributeName:variableName"`: Sets the element's attribute to the value of the JavaScript variable.
4. **Generate Static HTML**: It removes all script tags and outputs a static HTML file with the JavaScript effects applied.

## Limitations

- Only works with JavaScript that manipulates the DOM through the special data attributes
- External JavaScript files are not processed
- Complex DOM manipulations may not be captured correctly
- Browser-specific JavaScript APIs are not fully supported

## Example

The sample HTML file includes:
- A dynamic current time display
- A calculated value
- A dynamic link

After processing, these dynamic elements are converted to static content with their computed values.

## Advanced Usage

For more complex scenarios, you may need to modify the `apply_js_effects` function to handle specific JavaScript behaviors in your HTML files.