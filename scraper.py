import requests, bs4, curses, pyfiglet
import re, string, numpy as np, pandas as pd
from curses.textpad import Textbox, rectangle
from sklearn.feature_extraction.text import TfidfVectorizer

def main():
    curses.wrapper(curses_main)

def curses_main(window):
    consoles = []
    collections = {}

    load_collections(collections, consoles)

    title_screen(window)

    sel_cursor = search_method_sel(window)

    if sel_cursor == 0:
        search_all(window, collections)
    elif sel_cursor == 1:
        url = select_collection(window, collections)
        search_collection(window, url)
    elif sel_cursor == 2:
        console_key = select_console(window, consoles)
        search_console(window, collections[console_key], console_key)
    elif sel_cursor == 3:
        url = select_collection(window, collections)
        browse_collection(window, url)
    window.border(0)
    window.getch()

def search_method_sel(window):
    curses.curs_set(0)
    sel_cursor = 0
    dispText = window.subwin(curses.LINES - 4, curses.COLS - 4, 2, 2)

    dispText.addstr(curses.LINES - 5 - 6, 1, "Select search method:", curses.A_UNDERLINE)
    dispText.addstr(curses.LINES - 4 - 6, 4, "Search All")
    dispText.addstr(curses.LINES - 3 - 6, 4, "Search Specific Collection")
    dispText.addstr(curses.LINES - 2 - 6, 4, "Search Specific Console")
    dispText.addstr(curses.LINES - 1 - 6, 4, "Browse Collections")
    dispText.refresh()

    cursor_win = window.subwin(5, 1, curses.LINES - 8, 4)
    cursor_win.addstr(0, 0, ">")

    while True:
        key = window.getch()
        if key == curses.KEY_UP:
            cursor_win.clear()
            if sel_cursor > 0:
                sel_cursor -= 1
            elif sel_cursor == 0:
                sel_cursor = 3
            cursor_win.addstr(sel_cursor, 0, ">")
        elif key == curses.KEY_DOWN:
            cursor_win.clear()
            if sel_cursor < 3:
                sel_cursor += 1
            elif sel_cursor == 3:
                sel_cursor = 0
            cursor_win.addstr(sel_cursor, 0, ">")
        elif key == curses.KEY_ENTER or key == 10:
            break
        cursor_win.refresh()

    cursor_win.clear()
    dispText.clear()
    return sel_cursor
        
def get_query(window):
    # sets up search prompt and text box
    # returns user-input query
    dispText = window.subwin(1, len("Search: ") + 1, curses.LINES - 2, curses.COLS // 2 - 2 * len("Search: "))
    dispText.addstr(0, 0, "Search: ")
    dispText.refresh()

    search_win = window.subwin(1, curses.COLS // 2 - len("Search: "), curses.LINES - 2, curses.COLS // 2 - len("Search: "))
    search_box = Textbox(search_win)
    search_win.clear()
    search_box.edit()

    return search_box.gather()

def search(entries: list[str], query: str):
    entries_set = []

    # cleans/prunes each entry
    for e in entries:
        e = re.sub(r'[^\x00-\x7F]+', ' ', e)
        e = re.sub(r'@\w+', ' ', e)
        e = re.sub(r'[^\w\s\d]', ' ', e)
        e = re.sub(r'[%s]' % re.escape(string.punctuation), ' ', e)
        e = re.sub(r'\s{2,}', ' ', e)
        entries_set.append(e.lower())
        

    v = TfidfVectorizer(stop_words='english')
    
    X = v.fit_transform(entries)
    X = X.T.toarray()

    dataFrame = pd.DataFrame(X, index=v.get_feature_names_out())

    query = query.lower()

    # retrieves sorted list of (entry_index, sim_val) pairs
    results = get_similar_entries(entries, query, dataFrame, v)

    # formats final string list with entry strings with >0.0 similarity
    search_results = []
    for i in range(len(results)):
        if results[i][1] > 0.0:
            search_results.append(entries[results[i][0]])

    return search_results

def get_similar_entries(entries: list[str], query: str, dataFrame: pd.DataFrame, v: TfidfVectorizer):
    # vectorize query
    query = [query]
    q_vec = v.transform(query).toarray().reshape(dataFrame.shape[0])

    similar_entries = {}

    for i in range(len(entries)):
        if (np.linalg.norm(dataFrame.loc[:,i]) * np.linalg.norm(q_vec)) != 0:
            # calculate cosine similarity
            # divides parallel components of dataFrame and q_vec with their distance from each other to get similarity
            similar_entries[i] = np.dot(dataFrame.loc[:,i].values, q_vec) / (np.linalg.norm(dataFrame.loc[:,i]) * np.linalg.norm(q_vec))
        else:
            similar_entries[i] = -1
    
    # sort by similarity value (descending)
    sorted_entries = sorted(similar_entries.items(), key=lambda x: x[1], reverse=True)

    return sorted_entries

def search_all(window, value: dict[str, list[str]]):
    pass

def search_console(window, collections: list[str], console: str):
    loading_screen(window, "Parsing Collections...", True)

    entries = []
    for c in collections:
        entries.extend(parse_collection(c.strip()))

    loading_screen(window, "Parsing Collections...", False)

    console_splash(window, console)

    query = get_query(window)

    search_results = search(entries, query)

    # nicely format search results (want to make tese results scrollable)
    if len(search_results) > 0:
        for i in range(0, len(search_results)):
            if i < curses.LINES - 10:
                window.addstr(i + 8, 2, search_results[i])
    else:
        window.addstr(8, 3, "No results found")

    window.refresh()
    window.getch()
    
def select_console(window, keys: list[str]):
    # returns key to dict of selected console
    title_screen(window)
    # display consoles to the right of the screen
    sel_cursor = 0
    dispText = window.subwin(len(keys), 15, 5, curses.COLS - 25)
    cursor_win = window.subwin(len(keys) + 1, 1, 5, curses.COLS - 26)
    ascii_art = window.subwin(7, 75, 17, 18)

    ascii_art.addstr(0, 0, pyfiglet.figlet_format(keys[sel_cursor]))
    window.addstr(4, curses.COLS - 30, "Select a console", curses.A_UNDERLINE)
    cursor_win.addstr(sel_cursor, 0, ">")
    for i in range(len(keys)):
        dispText.addstr(i, 2, keys[i], curses.A_BOLD)    
    
    dispText.refresh()
    ascii_art.refresh()
    window.refresh()
    

    while True:
        key = window.getch()
        if key == curses.KEY_UP:
            cursor_win.clear()
            if sel_cursor > 0:
                sel_cursor -= 1
            elif sel_cursor == 0:
                sel_cursor = len(keys) - 1
            cursor_win.addstr(sel_cursor, 0, ">")
            ascii_art.addstr(0, 0, pyfiglet.figlet_format(keys[sel_cursor]))
        elif key == curses.KEY_DOWN:
            cursor_win.clear()
            if sel_cursor < len(keys) - 1:
                sel_cursor += 1
            elif sel_cursor == len(keys) - 1:
                sel_cursor = 0
            cursor_win.addstr(sel_cursor, 0, ">")
            ascii_art.addstr(0, 0, pyfiglet.figlet_format(keys[sel_cursor]))
        elif key == curses.KEY_ENTER or key == 10:
            break
        cursor_win.refresh()
        ascii_art.refresh()

    # enumerate #-of-games within each console
    return keys[sel_cursor]

def search_collection(window, url: str):
    pass

def select_collection(window, collections: dict[str, list[str]]):
    # returns url of selected collection
    pass

def browse_collection(window, url: str):
    pass

def title_screen(window):
    window.border(0)
    dispText = window.subpad(8, int(curses.COLS * 0.6), 2, 2)
    title = pyfiglet.figlet_format("ROMScraper")
    dispText.addstr(0, 0, title)
    dispText.refresh()
    window.refresh()

def loading_screen(window, message: str, in_progress: bool):
    if in_progress:
        window.clear()
        window.border(0)
        window.addstr(curses.LINES // 2, curses.COLS // 2 - len(message) // 2, message)
        window.refresh()
    else:
        window.clear()
        window.border(0)
        title_screen(window)
        window.refresh()

def console_splash(window, console: str):
    splash = window.subpad(12, 24, 3, curses.COLS - 26)
    splash.addstr(0, 0, pyfiglet.figlet_format(console, font="small"))
    splash.refresh()

def load_collections(collections: dict[str, list[str]], consoles: list[str]):
    # load collections from file into dictionary and parse consoles into string list
    file = open("collections.txt", "r")
    lines = file.readlines()

    for i in range(0, len(lines)):
        if lines[i].startswith("+"):
            str = lines[i][1:].strip()
            consoles.append(str)
            collection_list = []
            i += 1
            while i < len(lines):
                if lines[i].startswith('https://archive.org/download/'):
                    collection_list.append(lines[i])
                i += 1
            collections[str] = collection_list
    file.close()
    
def parse_collection(url):
    res = requests.get(url)
    res.raise_for_status()
    bs = bs4.BeautifulSoup(res.text, 'html.parser')
    table = bs.find('table', class_='directory-listing-table')
    rows = table.find_all('tr')

    strs = []
    for val in rows:
        entry = val.find('td')
        for subval in entry:
            s = subval.getText()
            # want to narrow parsed values to only those that are most likely game ROMs
            # needs to be updated to include other ROM-formats if needed
            if s.endswith('.zip') or s.endswith('.7z') \
                or s.endswith('.rar') or s.endswith('.iso') \
                or s.endswith('.nes') or s.endswith('.smc') \
                or s.endswith('.sfc') or s.endswith('.smd') \
                or s.endswith('.gba') or s.endswith('.z64') \
                or s.endswith('.32x') or s.endswith('.gg'):
                strs.append(str(s))

    return strs

main()