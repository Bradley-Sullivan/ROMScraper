# ROMScraper
## Description
ROMScraper is a tool used to scrape game console ROMs (and other files) from `archive.org` collections that can then be searched and downloaded. 

Search options include searching all provided collections, searching by specific consoles, browsing specific collecitons, and browsing favorited ROMs/other files.

![ROMScraper_Main_menu](https://user-images.githubusercontent.com/77858921/183275665-9f096d00-1a5c-4010-8cb5-9c1b938263ba.png)

![ROM_Console_Selection](https://user-images.githubusercontent.com/77858921/185808735-87641dd9-a103-4b4a-8986-1bdfa4749ce9.png)

![ROM_Search_Results](https://user-images.githubusercontent.com/77858921/185809758-e021b3e9-91c3-4e1a-82ce-44ad12eccd19.png)

## Tested Development Environments
- Ubuntu 22.04
  - Python v3.10.4
  
## Configuration and Usage
- Configuration
  - `collections.txt`

    - This program relies on `archive.org/download/` collections that are placed in the text file `collections.txt`. This is where it pulls the archives that it will scrape, parse, and download from.

    - If you wish to organize each collection by console, or some other designation, each URL will need to be placed on its own line after a header in the format `+<Abbrev. Title> : <Full title>`. Abbreviated titles are used internally and as decorative UI splashes, where full titles are used for menu selections.
  
 - Usage
 
    - Navigate to program directory and execute `python3 scraper.py [output_dir]`

      - NOTE: Before running the program, make sure that the terminal window is sized large enough (roughly 35 lines by 135 columns) or fullscreen

    - If no output directory is specified all downloaded files will be stored alongside `scraper.py`
