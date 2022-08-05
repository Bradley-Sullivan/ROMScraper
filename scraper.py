import requests, bs4, curses, pyfiglet, time
import re, string, numpy as np, pandas as pd
from curses.textpad import Textbox, rectangle
from sklearn.feature_extraction.text import TfidfVectorizer

def main():
    curses.wrapper(curses_main)

def curses_main(window):
    curses.curs_set(0)

    consoles = []
    collections = {}

    load_collections(collections, consoles)

    title_screen(window)

    while True:
        sel_cursor = search_method_sel(window)

        if sel_cursor == 0:
            search_all(window, collections, consoles)
        elif sel_cursor == 1:
            console_key = select_console(window, consoles)
            if console_key != None:
                search_console(window, collections[console_key], console_key)
        elif sel_cursor == 2:
            url = select_collection(window, collections, consoles)
            browse_collection(window, url)
        elif sel_cursor == -1:
            break

        title_screen(window)

def search_method_sel(window):
    sel_cursor = 0
    disp_text = window.subwin(curses.LINES - 4, curses.COLS - 4, 2, 2)

    disp_text.addstr(curses.LINES - 5 - 6, 1, "Select search method:", curses.A_UNDERLINE)
    disp_text.addstr(curses.LINES - 4 - 6, 4, "Search All")
    disp_text.addstr(curses.LINES - 3 - 6, 4, "Search Specific Console")
    disp_text.addstr(curses.LINES - 2 - 6, 4, "Browse Collection(s)")
    disp_text.refresh()

    cursor_win = window.subwin(4, 1, curses.LINES - 8, 4)
    cursor_win.addstr(0, 0, ">")
    cursor_win.refresh()

    msg_pad = window.subpad(1, len("Press ESC to exit") + 1, curses.LINES - 2, curses.COLS // 2 - len("Press ESC to exit") // 2)
    msg_pad.addstr(0, 0, "Press ESC to exit")

    while True:
        key = window.getch()
        if key == curses.KEY_UP:
            cursor_win.clear()
            if sel_cursor > 0:
                sel_cursor -= 1
            elif sel_cursor == 0:
                sel_cursor = 2
            cursor_win.addstr(sel_cursor, 0, ">")
        elif key == curses.KEY_DOWN:
            cursor_win.clear()
            if sel_cursor < 2:
                sel_cursor += 1
            elif sel_cursor == 2:
                sel_cursor = 0
            cursor_win.addstr(sel_cursor, 0, ">")
        elif key == curses.KEY_ENTER or key == 10:
            break
        elif key == curses.ascii.ESC:
            return -1
        cursor_win.refresh()

    cursor_win.clear()
    disp_text.clear()
    cursor_win.refresh()
    disp_text.refresh()

    return sel_cursor
        
def get_query(window):
    # sets up search prompt and text box; returns user-input query
    disp_text = window.subwin(1, len("Search: ") + 1, curses.LINES - 2, curses.COLS // 2 - 2 * len("Search: "))
    disp_text.addstr(0, 0, "Search: ")
    disp_text.refresh()

    search_win = window.subwin(1, curses.COLS // 2 - len("Search: "), curses.LINES - 2, curses.COLS // 2 - len("Search: "))
    search_box = Textbox(search_win)
    search_win.clear()
    search_box.edit()

    return search_box.gather()

def batch_search(raw_results, matched_results, parsed_entries: list[list[str]], query: str, res_per_batch: int):
    cur_valid_batch = 0
    roms = []

    entries = [k[0] for k in parsed_entries]

    batch_search_results = search(entries, query, True)

    for i in range(0, res_per_batch):
        raw_results.append(batch_search_results[i])

    for i in range(len(raw_results) - res_per_batch, len(raw_results)):
        if raw_results[i][1] > 0.01:
            matched_results.append(list(raw_results[i]))
            cur_valid_batch += 1

    for i in range(len(matched_results) - cur_valid_batch, len(matched_results)):
        matched_results[i][0] = entries[matched_results[i][0]]
        for e in parsed_entries:
            if e[0] == matched_results[i][0]:
                roms.append(e)
                break
    
    return roms

def search(entries: list[str], query: str, batch: bool):
    entries_set = []

    # cleans/prunes each entry
    for e in entries:
        e = re.sub(r'[^\w\s\d]', ' ', e)
        e = re.sub(r'[%s]' % re.escape(string.punctuation), ' ', e)
        entries_set.append(e.lower())
        

    v = TfidfVectorizer(stop_words='english')
    
    X = v.fit_transform(entries)
    X = X.T.toarray()

    dataFrame = pd.DataFrame(X, index=v.get_feature_names_out())

    query = query.lower()

    # retrieves sorted list of (entry_index, sim_val) pairs
    results = get_similar_entries(entries, query, dataFrame, v)

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
    title_screen(window)

    batch_results = []
    raw_search_results = []
    matched_results = []
    roms = []
    
    status_pad = window.subpad(1, 18, curses.LINES // 2 + 1, curses.COLS // 2 - 9)

    while True:
        msg_splash(window, "ALL")
        query = get_query(window)

        loading_screen(window, "Searching All Collections...", True)

        for console in consoles:
            status_pad.addstr(0, 0, "Searching %s..." % console)
            status_pad.refresh()
            for collection in collections[console]:
                entries = parse_collection(collection.strip())
                roms.extend(batch_search(raw_search_results, matched_results, entries, query, 5))

        sorted_results = sorted(matched_results, key=lambda x: x[1], reverse=True)

        for i in range(len(sorted_results)):
            batch_results.append(sorted_results[i][0])

        loading_screen(window, "", False)

        rom_sel = nav_results(window, batch_results)

        if rom_sel == None:
            msg_pad = window.subpad(1, curses.COLS // 2, curses.LINES - 2, curses.COLS // 2 - len("Press ESC to return | Press any other key to search") // 2)
            msg_pad.addstr(0, 0, "Press ESC to return | Press any other key to search")
            key = window.getch()
            if key == curses.ascii.ESC:
                return
            else:
                batch_results.clear()
                raw_search_results.clear()
                matched_results.clear()
                msg_pad.clear()
                msg_pad.refresh()
        else:
            for r in roms:
                if r[0] == rom_sel:
                    rom_options(window, roms, rom_sel)
                    break
            pass

def search_console(window, collections: list[str], console: str):
    loading_screen(window, "Parsing %s Collection(s)..." % console, True)

    entries = []
    for c in collections:
        entries.extend(parse_collection(c.strip()))

    loading_screen(window, "", False)

    while True:
        msg_splash(window, console)

        query = get_query(window)

        search_results = search([k[0] for k in entries], query, False)

        rom_sel = nav_results(window, search_results)

        if rom_sel == None:
            msg_pad = window.subpad(1, curses.COLS // 2, curses.LINES - 2, curses.COLS // 2 - len("Press ESC to return | Press any other key to search") // 2)
            msg_pad.addstr(0, 0, "Press ESC to return | Press any other key to search")
            key = window.getch()
            if key == curses.ascii.ESC:
                return
            else:
                msg_pad.clear()
                msg_pad.refresh()
        else:
            # donwload rom/rom options menu
            for e in entries:
                if e[0] == rom_sel:
                    rom_options(window, entries, rom_sel)
                    break
            pass        
    
def select_console(window, keys: list[str]):
    # returns key to dict of selected console
    title_screen(window)

    sel_cursor = 0
    
    disp_text = window.subwin(len(keys), 15, 5, curses.COLS - 25)
    cursor_win = window.subwin(len(keys) + 1, 1, 5, curses.COLS - 26)
    ascii_art = window.subwin(7, 75, 17, 18)
    msg_pad = window.subpad(1, len("Press ESC to return to main menu") + 1, curses.LINES - 2, curses.COLS // 2 - len("Press ESC to return to main menu") // 2)
    
    msg_pad.addstr(0, 0, "Press ESC to return to main menu")
    ascii_art.addstr(0, 0, pyfiglet.figlet_format(keys[sel_cursor]))
    window.addstr(4, curses.COLS - 30, "Select a console", curses.A_UNDERLINE)
    cursor_win.addstr(sel_cursor, 0, ">")
    for i in range(len(keys)):
        disp_text.addstr(i, 2, keys[i], curses.A_BOLD)    
    
    disp_text.refresh()
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
        elif key == curses.ascii.ESC:
            return None
        cursor_win.refresh()
        ascii_art.refresh()

    return keys[sel_cursor]

def select_collection(window, collections: dict[str, list[str]], consoles: list[str]):
    title_screen(window)
    # returns url of selected collection
    collection_list = []

    for c in consoles:
        for collection in collections[c]:
            collection_list.append(collection)

    msg_splash(window, "COL")

    sel = nav_results(window, collection_list)

    return sel

def browse_collection(window, url: str):
    title_screen(window)

    loading_screen(window, "Parsing Collection...", True)

    entries = parse_collection(url.strip())

    loading_screen(window, "", False)

    while True:
        msg_splash(window, "BRWS")

        rom_sel = nav_results(window, [k[0] for k in entries])

        if rom_sel == None:
            msg_pad = window.subpad(1, curses.COLS // 2, curses.LINES - 2, curses.COLS // 2 - len("Press ESC to return | Press any other key to search") // 2)
            msg_pad.addstr(0, 0, "Press ESC to return | Press any other key to search")
            key = window.getch()
            if key == curses.ascii.ESC:
                return
            else:
                msg_pad.clear()
                msg_pad.refresh()
        else:
            rom_options(window, entries, rom_sel)
            pass

def rom_options(window, entries: list[str], sel: str):

    for e in entries:
        if e[0] == sel:
            rom = e
            break

    msg_splash(window, "ROM")

    msg = "Download (D) | Favorite (F) | View Info (I) | Back (B)"
    msg_pad = window.subpad(1, len(msg) + 1, curses.LINES - 2, curses.COLS // 2 - len(msg) // 2)
    msg_pad.addstr(0, 0, msg)

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
    title_screen(window)
    msg_splash(window, "DL")

    loading_screen(window, "Downloading %s..." % rom[0], True)

    res = requests.get(rom[1].strip(), stream=True)
    rom_byte_size = int(res.headers["Content-Length"], 10)
    cur_dl_size = 0

    p = str(rom_byte_size) + " / " + str(rom_byte_size) + " | 100.00%"

    progress_pad = window.subpad(2, len(p) + 1, (curses.LINES // 2) + 1, curses.COLS // 2 - len(p) // 2)

    with open(rom[0], "wb") as f:
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

def favorite_rom(window, rom: list[str]):
    title_screen(window)

    loading_screen(window, "Added to Favorites", True)
    open("favorites.txt", "a").write(rom[0] + " : " + rom[1] + "\n")
    time.sleep(1)
    loading_screen(window, "", False)

def title_screen(window):
    window.clear()
    window.border(0)
    dispText = window.subpad(8, int(curses.COLS * 0.6), 1, 2)
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

def nav_results(window, search_results: list[str]):
    cursor_pad_pos = 0
    cursor_offset = 0
    
    cursor_pad = window.subpad(curses.LINES - 9, 1, 8, 2)
    cursor_pad.addstr(cursor_pad_pos, 0, ">")
    disp_text = window.subpad(1, curses.COLS - 4, curses.LINES - 2, 3)
    disp_text.addstr(0, 0, "%d results found" % len(search_results), curses.A_BOLD)
    disp_text.refresh()

    show_results(window, search_results, cursor_offset)

    if len(search_results) > 0:
        while True:
            key = window.getch()
            if key == curses.KEY_UP:
                cursor_pad.clear()
                if cursor_pad_pos > 0:
                    cursor_pad_pos -= 1
                elif cursor_offset > 0:
                    cursor_offset -= 1
                cursor_pad.addstr(cursor_pad_pos, 0, ">")
                show_results(window, search_results, cursor_offset)
            elif key == curses.KEY_DOWN:
                cursor_pad.clear()
                if cursor_pad_pos + 10 < curses.LINES - 1 and cursor_pad_pos < len(search_results) - 1:
                    cursor_pad_pos += 1
                elif cursor_offset + (curses.LINES - 10) < len(search_results):
                    cursor_offset += 1
                cursor_pad.addstr(cursor_pad_pos, 0, ">")
                show_results(window, search_results, cursor_offset)
            elif key == curses.KEY_ENTER or key == 10:
                return search_results[cursor_pad_pos + cursor_offset]
            elif key == curses.ascii.ESC:
                break
            cursor_pad.refresh()
    else:
        msg_splash(window, ": (")
    
    cursor_pad.clear()
    cursor_pad.refresh()
    disp_text.clear()
    disp_text.refresh()

    return None

def show_results(window, search_results: list[str], cur_offset: int):
    rom_nav = window.subpad(curses.LINES - 10, curses.COLS - 5, 8, 4)

    if len(search_results) > 0:
        rom_nav.clear()
        rom_nav.refresh()
        for i in range(cur_offset, len(search_results)):
            if i - cur_offset < curses.LINES - 10:
                rom_nav.addstr(i - cur_offset, 0, search_results[i])
            rom_nav.refresh()
    else:
        rom_nav.clear()
        rom_nav.addstr(0, 0, "No results found")
        rom_nav.refresh()

def msg_splash(window, msg: str):
    if len(msg) < 5:
        splash = window.subpad(12, 24, 3, curses.COLS - 26)
        splash.addstr(0, 0, pyfiglet.figlet_format(msg, font="small"))
        splash.refresh()
    else:
        splash = window.subpad(12, 24, 3, curses.COLS - 26)
        splash.addstr(0, 0, pyfiglet.figlet_format("N/A", font="small"))
        splash.refresh()

def load_collections(collections: dict[str, list[str]], consoles: list[str]):
    # load collections from file into dictionary and parse consoles into string list
    file = open("collections.txt", "r")
    lines = file.readlines()

    for i in range(0, len(lines)):
        if lines[i].startswith("+"):
            str = lines[i][1:].strip()
            collection_list = []
            i += 1
            while lines[i].startswith('https://archive.org/download/'):
                collection_list.append(lines[i])
                i += 1
                if i >= len(lines) - 1:
                    break
            collections[str] = collection_list
            consoles.append(str)
    file.close()
    
def parse_collection(url):
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
                or s.endswith('.32x') or s.endswith('.gg'):
                strs.append(str(s))
        h = entry.find('a').get('href')
        if h.endswith('.zip') or h.endswith('.7z') \
            or h.endswith('.rar') or h.endswith('.iso') \
            or h.endswith('.nes') or h.endswith('.smc') \
            or h.endswith('.sfc') or h.endswith('.smd') \
            or h.endswith('.gba') or h.endswith('.z64') \
            or h.endswith('.32x') or h.endswith('.gg'):
            hrefs.append(url + h)

    entries = []
    for i in range(len(strs)):
        entries.append([strs[i], hrefs[i]])

    return entries

main()