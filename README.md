# FitGirl Repack Automator

A robust, Windows 7-styled desktop application to automate downloading games from **FitGirl Repacks** (specifically using the **FuckingFast** mirror).

![Screenshot 2026-01-12 105713](https://github.com/user-attachments/assets/6d6e1e40-9b6c-47b4-aa86-de1f8c7a25f6)
![Screenshot 2026-01-12 105834](https://github.com/user-attachments/assets/25738dc6-4fe6-4975-8763-c597cb33e279)




## Features

-   **Automated Downloader**: Bypasses ads and countdowns on FuckingFast.co automatically.
-   **Sequential Downloading**: Downloads files one by one to maximize stability.
-   **Selective Download**: Automatically groups "Selective" files (like Language Packs) and enforces selection rules.
-   **Smart Resume**: Remembers your progress. If a download is interrupted, just restart the app to resume.
-   **Windows 7 Aesthetic**: A nostalgic, clean interface inspired by the original installers.

## Prerequisites

-   **Windows 10/11**
-   **Internet Connection** (stable enough for large downloads)

## How to Run

### Option 1: Standalone EXE (Recommended)
1.  Download the latest `FitGirlAutomator.exe` from Releases.
2.  Run it.
3.  *Note*: On first run, it may take a moment to initialize the browser engine required for automation.

### Option 2: Run from Source
1.  Install Python 3.8+.
2.  Clone this repository.
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```
4.  Run the app:
    ```bash
    python gui.py
    ```

## Usage

1.  **Copy URL**: Go to a game page on `fitgirl-repacks.site`.
2.  **Paste URL**: Paste it into the Automator.
3.  **Select Files**: Choose your destination and which optional components you want.
4.  **Download**: Sit back and watch the green bar go!

## Disclaimer

This tool is for educational purposes and automation convenience only. It is not affiliated with FitGirl Repacks. Please support the original repackers and seed torrents when possible.
