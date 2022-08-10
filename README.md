# ROMScraper
## Description
ROMScraper is a tool used to scrape game console ROMs (and other files) from `archive.org` collections that can then be searched and downloaded. 

The UI was designed using the Python curses module. HTML parsing/scraping was built using the requests and BeautifulSoup Python modules. Search engine was constructed using the Python scikit_learn, panda, and numpy modules.

Search options include searching all provided collections, searching by specific consoles, browsing specific collecitons, and browsing favorited ROMs/other files.

![ROMScraper_Main_menu](https://user-images.githubusercontent.com/77858921/183275665-9f096d00-1a5c-4010-8cb5-9c1b938263ba.png)

![ROMScraper_Console_Selection](https://user-images.githubusercontent.com/77858921/183275682-87a807d8-3ad8-4541-8fe7-9fa2042a637b.png)

![ROMScraper_Favorites](https://user-images.githubusercontent.com/77858921/183275684-70991328-b03e-461d-b106-b7756aa36680.png)

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
 
    - If no output directory is specified all downloaded files will be stored alongside `scraper.py`
