import requests, bs4, curses, pyfiglet, time, sys
import re, string, numpy as np, pandas as pd
from curses.textpad import Textbox, rectangle
from sklearn.feature_extraction.text import TfidfVectorizer

if len(sys.argv) > 1:
    OUTPUT_DIR = sys.argv[1]
else:
    OUTPUT_DIR = ""

def main():
    curses.wrapper(curses_main)

def curses_main(window):
    # TODO: implement view rom info (console, collection, size, checksums)
    # redump.org checksum verification after download?
    # implement playlist creation within rom_options()?

    r"""Main program entry point. Presents a main menu and diverts program flow accoring to user selection.

    :param window: curses window object (`stdscr`)
    :return: None
    """
    curses.curs_set(0)

    consoles = []
    collections = {}

    load_collections(collections, consoles)

    title_screen(window)

    while True:
        sel_cursor = main_menu(window)

        if sel_cursor == 0:
            search_all(window, collections, [k[0] for k in consoles])
        elif sel_cursor == 1:
            console_key = select_console(window, consoles)
            if console_key != None:
                search_console(window, collections[console_key], console_key)
        elif sel_cursor == 2:
            url = select_collection(window, collections, [k[0] for k in consoles])
            browse_collection(window, url)
        elif sel_cursor == 3:
            browse_favorites(window)
        elif sel_cursor == -1:
            break

        title_screen(window)

def main_menu(window):
    r"""Main UI menu

    :param window: curses window object (`stdscr`)
    :return: `int` of user selection
    """
    sel_cursor = 0

    disp_text = window.subpad(5, curses.COLS - 9, curses.LINES - 5 - 8, 5)

    disp_text.addstr(0, 0, "Select search method:", curses.A_UNDERLINE)
    disp_text.addstr(1, 1, "Search All")
    disp_text.addstr(2, 1, "Search Specific Console")
    disp_text.addstr(3, 1, "Browse Collection(s)")
    disp_text.addstr(4, 1, "Browse Favorites")

    cursor_pad = window.subpad(4, 2, curses.LINES - 5 - 7, 4)
    cursor_pad.addstr(0, 0, ">")

    msg_pad = window.subpad(1, len("Press ESC to exit") + 1, curses.LINES - 2, curses.COLS // 2 - len("Press ESC to exit") // 2)
    msg_pad.addstr(0, 0, "Press ESC to exit")

    disp_text.refresh()
    cursor_pad.refresh()
    msg_pad.refresh()

    while True:
        key = window.getch()
        if key == curses.KEY_UP:
            cursor_pad.clear()
            if sel_cursor > 0:
                sel_cursor -= 1
            elif sel_cursor == 0:
                sel_cursor = 3
            cursor_pad.addstr(sel_cursor, 0, ">")
        elif key == curses.KEY_DOWN:
            cursor_pad.clear()
            if sel_cursor < 3:
                sel_cursor += 1
            elif sel_cursor == 3:
                sel_cursor = 0
            cursor_pad.addstr(sel_cursor, 0, ">")
        elif key == curses.KEY_ENTER or key == 10:
            break
        elif key == curses.ascii.ESC:
            return -1
        cursor_pad.refresh()

    cursor_pad.clear()
    disp_text.clear()

    return sel_cursor
        
def get_query(window):
    r"""Simple UI for displaying search prompt and collecting user-input search query
    
    :param window: curses window object (`stdscr`)
    :return: `String` obtained from curses Textpad object containing user-input query
    """
    disp_text = window.subwin(1, len("Search: ") + 1, curses.LINES - 2, curses.COLS // 2 - 2 * len("Search: "))
    disp_text.addstr(0, 0, "Search: ")
    disp_text.refresh()

    search_win = window.subwin(1, curses.COLS // 2 - len("Search: "), curses.LINES - 2, curses.COLS // 2 - len("Search: "))
    search_box = Textbox(search_win)
    search_win.clear()
    search_box.edit()

    return search_box.gather()

def batch_search(parsed_entries: list[list[str]], query: str, res_per_batch: int):
    r"""Performs a specialized search of provided entries retaining only the n-most similar results of each search.
    Main helper function which helps optimize the searching of ALL collections for ALL consoles.

    :param parsed_entries: `List` of string lists used to assign each search result to its corresponding ROM name and URL
    :param query: `String` of user-supplied search term(s)
    :param res_per_batch: Specifies the n-most similar search results to retain from each batch
    :return: `List` of string lists containing the names of each ROM, its download link, and its similarity value to be sorted later
    """
    roms = []

    batch_search_results = search(parsed_entries, query, True)

    for i in range(0, res_per_batch):
        if batch_search_results[i][1] > 0.01:
            roms.append([parsed_entries[batch_search_results[i][0]][0], 
                        parsed_entries[batch_search_results[i][0]][1], batch_search_results[i][1]])
    
    return roms

def search(entries: list[list[str]], query: str, batch: bool):
    r"""TF-IDF weighted search engine to find best match(es) for a query against supplied entries.

    :param entries: `List` of strings containing every valid search candidate
    :param query: `String` of user-supplied search term(s)
    :param batch: `Boolean` switch used to supply `batch_search()` with relevant results
    :return: If `batch == True` returns raw `Tuple` of entry indices paired with similarity values.
    Else If `batch == False` returns `List` of string lists containing ROM names and ROM URLs each 
    corresponding to search results with similarity >0.01
    """
    entries_set = [k[0] for k in entries]

    # cleans/prunes each entry
    for e in entries_set:
        e = re.sub(r'[^\w\s\d]', ' ', e)
        e = re.sub(r'[%s]' % re.escape(string.punctuation), ' ', e)
        e = e.lower()
        

    v = TfidfVectorizer(stop_words='english')
    
    X = v.fit_transform(entries_set)
    X = X.T.toarray()

    dataFrame = pd.DataFrame(X, index=v.get_feature_names_out())

    query = query.lower()

    # retrieves sorted list of (entry_index, sim_val) pairs
    results = get_similar_entries(entries_set, query, dataFrame, v)

    # formats final string list with entry strings with >0.01 similarity
    search_results = []
    for i in range(len(results)):
        if results[i][1] > 0.01:
            search_results.append(entries[results[i][0]])

    if batch:
        return results
    else:
        return search_results

def get_similar_entries(entries: list[str], query: str, dataFrame: pd.DataFrame, v: TfidfVectorizer):
    r"""Vectorizes supplied search query and calculates cosine similarity values for each entry in TF-IDF matrix.
    Sorts compiled entries based on similarity.

    :param entries: `List` of strings containing every search candidate used as looping bound
    :param query: `String` query used in similarity calculations
    :param dataFrame: `pd.DataFrame` containing vectorized entries for similarity calculations
    :param v: `TfidfVectorizer` used to vectorize query
    :return: `Tuple` containing entry indices and similarity values
    """
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

def search_all(window, collections: dict[str, list[str]], consoles: list[str]):
    r"""Search UI for obtaining a search query and compiling similarity-sorted search results
    for all consoles and all collections, results navigation, and basic interactions. 

    :param window: curses window object (`stdscr`)
    :param collections: `Dictionary` of all ROM collections keyed by abbrev. console names
    :param consoles: `List` of strings containing abbrev. console names
    :return: None
    """
    title_screen(window)

    key = ''

    batch_results = []
    roms = []
    
    status_pad = window.subpad(1, 18, curses.LINES // 2 + 1, curses.COLS // 2 - 9)

    msg_splash(window, "ALL")
    
    query = get_query(window)

    while True:
        msg_splash(window, "ALL")

        loading_screen(window, "Searching All Collections...", True)

        for console in consoles:
            status_pad.addstr(0, 0, "Searching %s..." % console)
            status_pad.refresh()
            for collection in collections[console]:
                entries = parse_collection(collection.strip())
                roms.extend(batch_search(entries, query, 5))

        sorted_results = sorted(roms, key=lambda x: x[2], reverse=True)

        for i in range(len(sorted_results)):
            batch_results.append([sorted_results[i][0], sorted_results[i][1]])

        loading_screen(window, "", False)

        while True:
            rom_sel = nav_results(window, batch_results, False)

            if rom_sel != None:
                rom_options(window, rom_sel)
            msg = "Press ESC to return | Press S to search | Press any other key to keep browsing"
            msg_pad = window.subpad(1, len(msg) + 1, curses.LINES - 2, curses.COLS // 2 - len(msg) // 2)
            msg_pad.addstr(0, 0, msg)
            msg_pad.refresh()

            key = window.getch()

            msg_pad.clear()
            msg_pad.refresh()

            if key == ord('s') or key == ord('S') or key == curses.ascii.ESC:
                break
        if key == curses.ascii.ESC:
            break
        else:
            batch_results.clear()
            query = get_query(window)

def search_console(window, collections: list[str], console: str):
    r"""Search UI for obtaining a search query and processing per-console searches, result
    navigation, and basic interactions.

    :param window: curses window object (`stdscr`)
    :param collections: `List` of strings containing all archive.org/ URLs for a particular console
    :param console: `String` of abbrev. console name used for splash message
    :return: None
    """
    key = ''

    loading_screen(window, "Parsing %s Collection(s)..." % console, True)

    entries = []
    for c in collections:
        entries.extend(parse_collection(c.strip()))

    loading_screen(window, "", False)

    msg_splash(window, console)

    query = get_query(window)

    while True:
        msg_splash(window, console)
        search_results = search(entries, query, False)

        while True:
            rom_sel = nav_results(window, search_results, False)

            if rom_sel != None:
                rom_options(window, rom_sel)
            msg = "Press ESC to return | Press S to search | Press any other key to keep browsing"
            msg_pad = window.subpad(1, len(msg) + 1, curses.LINES - 2, curses.COLS // 2 - len(msg) // 2)
            msg_pad.addstr(0, 0, msg)
            msg_pad.refresh()
            
            key = window.getch()

            msg_pad.clear()
            msg_pad.refresh()

            if key == ord('s') or key == ord('S') or key == curses.ascii.ESC:
                break
        if key == curses.ascii.ESC:
            break
        else:
            query = get_query(window)
    
def select_console(window, keys: list[list[str]]):
    # returns key to dict of selected console
    r"""Selection UI for choosing a console to search.

    :param window: curses window object (`stdscr`)
    :param keys: `List` of string lists containing abbrev. and full console names
    :return: Abbreviated console name `string`
    """
    title_screen(window)

    console_list = []
    for i in range(len(keys)):
        console_list.append([keys[i][1], keys[i][0]])

    ret = nav_results(window, console_list, True)

    if ret != None:
        return ret[1]
    else:
        return None

def select_collection(window, collections: dict[str, list[str]], consoles: list[str]):
    r"""Selection UI for choosing a ROM collection to browse.

    :param window: curses window object (`stdscr`)
    :param collections: `Dictionary` of collections keyed by console name abbrev.
    :param consoles: `List` of abbrev. console name strings used to access collection dictionary
    :return: `String` of nav_results() output denoting selected collection URL
    """
    title_screen(window)

    collection_list = []

    for c in consoles:
        for collection in collections[c]:
            collection_list.append([collection, c])

    msg_splash(window, "COLX")

    url = nav_results(window, collection_list, False)[0]

    return url

def browse_collection(window, url: str):
    r"""Browse UI for individual ROM collection specified by provided URL string.

    :param window: curses window object (`stdscr`)
    :param url: `String` denoting the URL of collection to browse
    :return: None
    """
    title_screen(window)

    loading_screen(window, "Parsing Collection...", True)

    entries = parse_collection(url)

    loading_screen(window, "", False)

    while True:
        msg_splash(window, "BRWS")

        rom_sel = nav_results(window, entries, False)

        if rom_sel != None:
            rom_options(window, rom_sel)
        else:
            break

def browse_favorites(window):
    r"""Browse ROMs located within `favorites.txt`.
    
    :param window: curses window object (`stdscr`)
    :return: None
    """
    title_screen(window)

    entries = parse_favorites()

    while True:
        msg_splash(window, "F A V")

        rom_sel = nav_results(window, [k[0] for k in entries], False)

        if rom_sel != None:
            rom_options(window, entries, rom_sel)
        else:
            break
        


def rom_options(window, rom: list[list[str]]):
    r"""Displays simple option menu and processes corresponding input. Options
    include downloading, favoriting, viewing ROM info, and returning.

    :param window: curses window object (`stdscr`)
    :param entries: `List` of string lists containing ROM name and download link
    :param sel: `String` denoting the name of the ROM in subject
    :return: None
    """

    msg_splash(window, "ROM")

    msg = "Download (D) | Favorite (F) | View Info (I) | Back (B)"
    msg_pad = window.subpad(1, len(msg) + 1, curses.LINES - 2, curses.COLS // 2 - len(msg) // 2)
    msg_pad.addstr(0, 0, msg, curses.A_BOLD)
    msg_pad.refresh()

    key = window.getch()

    if key == ord("d") or key == ord("D"):
        download_rom(window, rom)
    elif key == ord("f") or key == ord("F"):
        favorite_rom(window, rom)
    elif key == ord("i") or key == ord("I"):
        # view_info(window, rom)
        pass

    msg_pad.clear()
    msg_pad.refresh()

def download_rom(window, rom: list[str]):
    r"""Issues a GET request for ROM file through its download link.

    :param window: curses window object (`stdscr`)
    :param rom: `List` of string lists containing ROM name and download link
    :return: None
    """
    
    title_screen(window)
    msg_splash(window, "DL")

    loading_screen(window, "Downloading %s..." % rom[0], True)

    res = requests.get(rom[1].strip(), stream=True)
    rom_byte_size = int(res.headers["Content-Length"], 10)
    cur_dl_size = 0

    p = str(rom_byte_size) + " / " + str(rom_byte_size) + " | 100.00%"

    progress_pad = window.subpad(2, len(p) + 1, (curses.LINES // 2) + 1, curses.COLS // 2 - len(p) // 2)

    with open(OUTPUT_DIR + rom[0], "wb") as f:
        for chunk in res.iter_content(chunk_size=1024):
            progress_pad.addstr(0, 0, "%s / %s | %.2f%%" % (str(cur_dl_size), str(rom_byte_size), (cur_dl_size / rom_byte_size) * 100))
            if chunk:
                f.write(chunk)
                cur_dl_size += len(chunk)
                progress_pad.refresh()
    
    msg_pad = window.subpad(1, curses.COLS // 2, (curses.LINES // 2) + 2, curses.COLS // 2 - len("Download Complete.") // 2)
    msg_pad.addstr(0, 0, "Download Complete.")
    msg_pad.refresh()
    window.getch()

    loading_screen(window, "", False)

def favorite_rom(window, rom: list[list[str]]):
    r"""Appends `favorites.txt` file with specified ROM name and download link.

    :param window: curses window object (`stdscr`)
    :param rom: `List` of string lists containing ROM name and download link
    :return: None
    """
    title_screen(window)

    loading_screen(window, "Added to Favorites", True)
    open("favorites.txt", "a").write(rom[0] + " ; " + rom[1] + "\n")
    time.sleep(0.75)
    loading_screen(window, "", False)

def title_screen(window):
    r"""Cleanly clears and preps window to display a pyfiglet title splash.

    :param window: curses window object (`stdscr`)
    :return: None
    """
    window.clear()
    window.border(0)
    dispText = window.subpad(8, int(curses.COLS * 0.6), 1, 2)
    title = pyfiglet.figlet_format("ROMScraper")
    dispText.addstr(0, 0, title)
    dispText.refresh()
    window.refresh()

def loading_screen(window, message: str, in_progress: bool):
    r"""Clears and formats terminal for clean display of loading message(s).

    :param window: curses window object (`stdscr`)
    :param message: String message to be displayed
    :param in_progress: `Bool` which allows for clean init'ing and cleaning up
    before/during and after loading message display
    :return: None
    """
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

def nav_results(window, search_results: list[list[str]], splash: bool):
    r"""Navigates list of results in a scrollable fashion.

    :param window: curses window object (`stdscr`)
    :param search_results: `String` list containing results to navigate
    :param splash: `Boolean` var. which will add splashes based on cursor. Needs splash messages to be paired alongside navigable results.
    :return: Upon `ENTER` keypress returns selected entry string. Otherwise returns `None`.
    """

    pruned_results = [k[0] for k in search_results]
    splash_list = []

    if splash:
        splash_list = [k[1] for k in search_results]

    cursor_pad_pos = 0
    cursor_offset = 0
    
    cursor_pad = window.subpad(curses.LINES - 9, 1, 8, 2)
    cursor_pad.addstr(cursor_pad_pos, 0, ">")
    cursor_pad.refresh()
    disp_text = window.subpad(1, curses.COLS - 4, curses.LINES - 2, 3)
    disp_text.addstr(0, 0, "%d results found" % len(search_results), curses.A_BOLD)
    disp_text.refresh()

    show_results(window, pruned_results, cursor_offset)

    if len(search_results) > 0:
        while True:
            if splash:
                msg_splash(window, splash_list[cursor_pad_pos + cursor_offset])
            key = window.getch()
            if key == curses.KEY_UP:
                cursor_pad.clear()
                if cursor_pad_pos > 0:
                    cursor_pad_pos -= 1
                elif cursor_offset > 0:
                    cursor_offset -= 1
                cursor_pad.addstr(cursor_pad_pos, 0, ">")
                show_results(window, pruned_results, cursor_offset)
            elif key == curses.KEY_DOWN:
                cursor_pad.clear()
                if cursor_pad_pos + 10 < curses.LINES - 1 and cursor_pad_pos < len(search_results) - 1:
                    cursor_pad_pos += 1
                elif cursor_offset + (curses.LINES - 10) < len(search_results):
                    cursor_offset += 1
                cursor_pad.addstr(cursor_pad_pos, 0, ">")
                show_results(window, pruned_results, cursor_offset)
            elif key == curses.KEY_ENTER or key == 10:
                return search_results[cursor_pad_pos + cursor_offset]
            elif key == curses.ascii.ESC:
                break
            cursor_pad.refresh()
    else:
        cursor_pad.clear()
        cursor_pad.refresh()
    
    cursor_pad.clear()
    cursor_pad.refresh()
    disp_text.clear()
    disp_text.refresh()

    return None

def show_results(window, search_results: list[str], cur_offset: int):
    r"""Displays navigable results to the terminal.

    :param window: curses window object (`stdscr`)
    :param search_results: `List` of strings containing results to display
    :param cur_offset: Results offset relative to the 1st result displayed used
    for displaying results outside viewable window. Meant to be used in tandem with
    `nav_results()`
    :return: None
    """
    rom_nav = window.subpad(curses.LINES - 10, curses.COLS - 5, 8, 4)
    rom_nav.refresh()

    if len(search_results) > 0:
        rom_nav.clear()
        rom_nav.refresh()
        for i in range(cur_offset, len(search_results)):
            if i - cur_offset < curses.LINES - 10:
                if len(search_results[i]) > curses.COLS - 8:
                    rom_nav.addstr(i - cur_offset, 0, search_results[i][:curses.COLS - 10])
                    pass
                else:
                    rom_nav.addstr(i - cur_offset, 0, search_results[i])
            rom_nav.refresh()
    else:
        rom_nav.clear()
        rom_nav.addstr(0, 0, "No results found")
        rom_nav.refresh()
        msg = "Press any key to return..."
        msg_pad = window.subpad(1, len(msg) + 1, curses.LINES - 2, curses.COLS // 2 - len(msg) // 2 - 3)
        msg_pad.addstr(0, 0, msg, curses.A_BOLD)
        msg_pad.refresh()
        msg_splash(window, ": (")
        window.getch()
        rom_nav.clear()
        rom_nav.refresh()

def msg_splash(window, msg: str):
    r"""Displays short `pyfiglet` splash message of 5 characters or less to top-right of terminal.
    
    :param window: curses window object (`stdscr`)
    :param msg: `String` containing the message to display
    :return: None
    """
    if len(msg) < 6:
        splash = window.subpad(12, 24, 3, curses.COLS - 26)
        splash.addstr(0, 0, pyfiglet.figlet_format(msg, font="small"))
        splash.refresh()
    else:
        splash = window.subpad(12, 24, 3, curses.COLS - 26)
        splash.addstr(0, 0, pyfiglet.figlet_format("N/A", font="small"))
        splash.refresh()

def load_collections(collections: dict[str, list[str]], consoles: list[list[str]]):
    # load collections from file into dictionary and parse consoles into string list
    r"""Loads all archive.org collections from `collections.txt` into a dictionary
    with ROM name values keyed with their respective consoles.

    :param collections: `Dictionary` to store parsed data
    :param consoles: `List` of string lists containing abbrev. and full console names
    :return: None    
    """    
    file = open("collections.txt", "r")
    lines = file.readlines()

    for i in range(0, len(lines)):
        if lines[i].startswith("+"):
            console = lines[i][1:].strip().split(" : ")
            collection_list = []
            i += 1
            while lines[i].startswith('https://archive.org/download/'):
                collection_list.append(lines[i].strip())
                i += 1
                if i >= len(lines) - 1:
                    break
            collections[console[0]] = collection_list
            consoles.append(console)
    file.close()

def parse_favorites():
    r"""Parses `favorites.txt` file similarly to `parse_collection()`.
    
    :return: :list[list[str]]: `List` of every favorite ROM paired with its download link
    """

    file = open("favorites.txt", "r")
    lines = file.readlines()

    entries = []

    for line in lines:
        entries.append(line.split(" ; "))
    file.close()

    return entries

def parse_collection(url):
    r"""Parses archive.org collections.

    :param url: URL string of collection to parse
    :return: :list[list[str]]: `List` of every ROM entry paired with its download link
    """
    # TODO: need to be parsing hrefs alongside every entry in the collection
    # this will alter how every other function uses the entries (indexing mostly)
    # should be somewhat of a priority to minimize refactoring
    res = requests.get(url)
    res.raise_for_status()
    bs = bs4.BeautifulSoup(res.text, 'html.parser')
    table = bs.find('table', class_='directory-listing-table')
    rows = table.find_all('tr')

    strs = []
    hrefs = []
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
                or s.endswith('.32x') or s.endswith('.gg')  \
                or s.endswith('.bin') or s.endswith('.md')  \
                or s.endswith('.xci') or s.endswith('.rvz'):
                strs.append(str(s))
        h = entry.find('a').get('href')
        if h.endswith('.zip') or h.endswith('.7z') \
            or h.endswith('.rar') or h.endswith('.iso') \
            or h.endswith('.nes') or h.endswith('.smc') \
            or h.endswith('.sfc') or h.endswith('.smd') \
            or h.endswith('.gba') or h.endswith('.z64') \
            or h.endswith('.32x') or h.endswith('.gg')  \
            or h.endswith('.bin') or h.endswith('.md')  \
            or h.endswith('.xci') or h.endswith('.rvz'):
            hrefs.append(url + h)

    entries = []
    for i in range(len(strs)):
        entries.append([strs[i], hrefs[i]])

    return entries

main()