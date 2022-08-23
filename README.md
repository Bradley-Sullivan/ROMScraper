# ROMScraper
## Description
ROMScraper is a tool used to scrape game console ROMs (and other files) from `archive.org` collections that can then be searched and downloaded. 

Search options include searching all provided collections, searching by specific consoles, browsing specific collecitons, and browsing favorited ROMs/other files.

![ROM_Main_Menu](https://user-images.githubusercontent.com/77858921/185810410-f0c4a896-6ff9-4080-8a8d-ecda72327ace.png)

![ROM_Console_Selection](https://user-images.githubusercontent.com/77858921/185808735-87641dd9-a103-4b4a-8986-1bdfa4749ce9.png)

![ROM_Search_Results](https://user-images.githubusercontent.com/77858921/185809758-e021b3e9-91c3-4e1a-82ce-44ad12eccd19.png)

## Tested Usage/Development Environments
- Ubuntu 22.04
  - Python v3.10.4
  
- Windows 10.0.19044
  - Python v3.9.1
  
## Configuration and Usage
- Configuration

    - This Python program requires Python version >= v3.9

    - Program also relies on several Python modules, outside of the standard library, that must be installed to function correctly:

        - requests, beautifulsoup4, pyfiglet, numpy, pandas, and sklearn

        - These modules can be installed using the Python `pip` module, or installed directly from the module's website

    - `collections.txt`

        - This program relies on `archive.org/download/` collections that are placed in the text file `collections.txt`. This is where it pulls the archives that it will scrape, parse, and download from.

        - If you wish to organize each collection by console, or some other designation, each URL will need to be placed on its own line after a header in the format `+<Abbrev. Title> : <Full title>`. Abbreviated titles are used internally and as decorative UI splashes, where full titles are used for menu selections.
  
 - Usage

    - Navigate to program directory and execute `python3.X scraper.py [output_dir]`

      - NOTE: Before running the program, make sure that the terminal window is sized large enough (roughly 35 lines by 135 columns) or fullscreen

    - If no output directory is specified all downloaded files will be stored alongside `scraper.py`

    - Menus are navigated using the arrow-keys and the ENTER key. The ESC key is a useful key when exiting menus.
