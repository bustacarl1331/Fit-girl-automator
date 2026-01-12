# FitGirl Repack Automator

A robust, Windows 7-styled desktop application to automate downloading games from **FitGirl Repacks** (specifically using the **FuckingFast** mirror).

![Screenshot 2026-01-12 112459](https://github.com/user-attachments/assets/607ea825-4066-4e6c-965f-b714b6e5ce51)
![Screenshot 2026-01-12 105834](https://github.com/user-attachments/assets/9c879743-47a1-46ac-9665-bae28ad2690c)
![Screenshot 2026-01-12 105713](https://github.com/user-attachments/assets/6bc294c2-081f-475c-a3d5-e6f55ee2ab60)



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

1.  **Install Python**: Ensure you have Python 3.8+ installed.
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```
3.  **Run the App**:
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

