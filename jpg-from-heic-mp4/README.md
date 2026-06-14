# JPG from HEIC & MP4 Converter

!Version

A professional PowerShell automation script that converts Apple's HEIC image format to standard JPG and extracts the very first frame of MP4 video files into a JPG image. 

The script is designed for bulk processing across multiple directories. It utilizes **FFmpeg** as the backend media processing engine.

## Prerequisites

- **Windows PowerShell** (or PowerShell Core).
- **FFmpeg** installed and accessible via the system PATH variable.
  - *Note: You can easily install FFmpeg via Winget by running `winget install ffmpeg` in your console.*

## Author Information

- **Author**: Roman Pindela
- **Email**: roman.pindela@gmail.com
- **GitHub**: https://github.com/romanpindela

---

## Usage

Run the script via PowerShell, passing the folders you want to process as a parameter. The script features input validation and will skip invalid paths or halt if FFmpeg is missing.

### Example 1: Basic execution with a single directory
```powershell
.\jpg-from-heic-mp4.ps -Folders "C:\Users\rpindela\Downloads\March"
```

### Example 2: Bulk processing multiple directories
You can pass an array of directories separated by commas.
```powershell
.\jpg-from-heic-mp4.ps -Folders "C:\Downloads\January", "C:\Downloads\February", "C:\Downloads\March"
```

### Example 3: Pipeline Input
You can pass directory paths directly into the script via the pipeline.
```powershell
"C:\Downloads\April", "C:\Downloads\May" | .\jpg-from-heic-mp4.ps
```

### Example 4: View Help Menu
To view the built-in PowerShell help, execute the script without parameters or use the `-Help` (or `-h`) switch.
```powershell
.\jpg-from-heic-mp4.ps -Help
```