# MetaStrip

MetaStrip is a lightweight, local-first web application designed to help you quickly identify and strip hidden metadata from your files. Whether you're sharing a photo, a resume, or a sensitive document, MetaStrip ensures you aren't accidentally leaking GPS coordinates, author names, or editing history.

## What it does

- **Upload & Analyze**: Drag and drop your files (up to 25MB). MetaStrip instantly parses the file and highlights any sensitive metadata it finds.
- **Support for common formats**: 
  - **Images**: JPEG, PNG, TIFF
  - **Documents**: PDF, DOCX
- **One-Click Cleaning**: Hit "Download Clean File" and MetaStrip will scrub the metadata out of the file and serve you a fresh, anonymized copy.
- **Visual Risk Assessment**: The app provides a sensitivity score and risk breakdown, so you know exactly how much data you were about to expose.

## Under the Hood

The app is split into two parts:

1. **Frontend (Next.js)**: A sleek, responsive React interface styled with Tailwind CSS. It handles file drops, validations (like file size limits), and presents the metadata findings in a clean, readable dashboard.
2. **Backend (Python / Flask)**: A fast, stateless API that processes the files entirely in memory. It uses tools like `pypdf`, `python-docx`, `Pillow`, and `piexif` to extract and strip metadata without corrupting the files. Cleaned files are temporarily cached for 15 minutes before being permanently wiped.

## Getting Started

Since MetaStrip processes sensitive files, the best way to use it is by running it locally on your machine.

### Prerequisites

You'll need to have the following installed:
- Node.js (v18+)
- Python (3.10+)

### 1. Set up the Backend

Navigate to the `backend` folder and set up a virtual environment:

```bash
cd backend
python -m venv venv

# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install the Python dependencies
pip install -r requirements.txt

# Start the Flask server (runs on port 5000 by default)
python wsgi.py
```

*Note: For Windows users, the backend uses `python-magic-bin` to ensure proper MIME detection.*

### 2. Set up the Frontend

Open a new terminal window, navigate to the `frontend` directory, and start the Next.js app:

```bash
cd frontend

# Install the Node dependencies
npm install

# Start the development server
npm run dev
```

The frontend will start up on `http://localhost:3000`. Open that link in your browser, drop a file in, and you're good to go!

## Contributing

Feel free to open an issue or submit a pull request if you want to add support for more file types or improve the UI. 

## License

This project is licensed under the MIT License - see the LICENSE file for details.
