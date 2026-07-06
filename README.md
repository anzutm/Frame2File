# Frame2File

Frame2File is a local Python desktop application for converting image files into a single PDF through a modern PySide6 / Qt for Python interface.

## Main Features

- Select a folder and automatically load supported image files.
- Add individual image files manually.
- Preview images as thumbnails before conversion.
- Reorder images by dragging thumbnails.
- Move the selected image up or down.
- Remove selected images from the conversion list.
- Convert images into one PDF file.
- Show conversion progress and status messages.
- Scan thumbnails and export PDF without freezing the UI.
- Runs locally on your computer.

## Supported Image Formats

- JPG
- JPEG
- PNG
- WEBP
- BMP

## Requirements

- Python 3.10 or newer
- Pillow
- PySide6

Frame2File requires PySide6 and Pillow.

The `run_frame2file.vbs` launcher is intended for Windows and uses `pyw.exe` to start the PySide6 app without showing a console window.

## Installation

1. Clone this project.

```powershell
git clone https://github.com/anzutm/Frame2File.git
cd Frame2File
```

2. Open a terminal in the project folder.

3. Optional but recommended: create and activate a virtual environment.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

4. Install dependencies.

```powershell
py -m pip install -r requirements.txt
```

## Running the Application

Run the new PySide6 application from the project folder:

```powershell
python -m frame2file.app
```

On Windows, you can also use:

```powershell
py -m frame2file.app
```

## Running with the VBS Launcher

The `run_frame2file.vbs` file works as a Windows launcher. It starts the new PySide6 app using `pyw.exe`, hides the console window, and opens the Frame2File GUI.

You can run it by double-clicking:

```text
run_frame2file.vbs
```

This requires Python to be installed with the `pyw.exe` launcher available on your system.

## Basic Usage

1. Open Frame2File.
2. Click **Pilih Folder** to choose a folder containing images.
3. Review the loaded image thumbnails.
4. Drag thumbnails to change their order, or use **Naik**, **Turun**, and **Hapus** for the selected image.
5. Use **Tambah** to add more image files if needed.
6. Click **Buat PDF** to create the PDF.

The generated PDF is saved in the selected folder and named after that folder. For example, selecting a folder named `Images` creates:

```text
Images/Images.pdf
```

## Project Structure

```text
Frame2File/
+-- frame2file/
|   +-- app.py
|   +-- core/
|   |   +-- image_loader.py
|   |   +-- pdf_exporter.py
|   |   `-- sorting.py
|   `-- gui/
|       +-- main_window.py
|       +-- resources/
|       +-- services/
|       `-- widgets/
+-- requirements.txt
+-- run_frame2file.vbs
+-- .gitignore
`-- README.md
```

- `frame2file/app.py` is the new PySide6 entry point.
- `frame2file/core/` contains reusable image loading, natural sorting, and PDF export logic.
- `frame2file/gui/` contains the Qt widgets, window, styling, and worker threads.
- `run_frame2file.vbs` launches the PySide6 app on Windows through `pyw.exe`.
- `.gitignore` excludes Python cache files and `desktop.ini`.
- `README.md` provides project documentation.

## Local-Only Note

Frame2File runs locally on your computer. Image files are loaded from local folders, processed locally with Pillow, and saved as a local PDF file.

## License

This project is provided without a specified license. Add a license file if you plan to publish, share, or distribute it.
