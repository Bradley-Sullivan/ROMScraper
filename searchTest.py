import re, string, requests, numpy as np, pandas as pd, bs4
from sklearn.feature_extraction.text import TfidfVectorizer

def main():
    collections = {}
    consoles = []
    load_collections(collections, consoles)

    entries = parse_collection("https://archive.org/download/SNES-Arquivista")

    for entry in entries:
        entry = entry.lower()

    v = TfidfVectorizer()
    print(type(v))
    X = v.fit_transform(entries)
    X = X.T.toarray()
    df = pd.DataFrame(X, index=v.get_feature_names_out())
    query = input("Enter query: ")
    query = query.lower()
    get_similar_entries(query, entries, df, v)

def get_similar_entries(query, entries, df, vectorizer):
    query = [query]
    q_vector = vectorizer.transform(query).toarray().reshape(df.shape[0])
    similar_entries = {}

    for i in range(len(entries)):
        similar_entries[i] = np.dot(df.loc[:,i].values, q_vector) / (np.linalg.norm(df.loc[:,i]) * np.linalg.norm(q_vector))
    sorted_entries = sorted(similar_entries.items(), key=lambda x: x[1], reverse=True)

    for i in range(len(sorted_entries)):
        if i < 15:
            print("Similarity: ", sorted_entries[i][1])
            print("Index: ", sorted_entries[i][0])
            print(entries[sorted_entries[i][0]])
            print("\n")

def load_collections(collections: dict[str, list[str]], consoles: list[str]):
    file = open("collections.txt", "r")
    lines = file.readlines()

    for i in range(0, len(lines) - 1):
        if lines[i].startswith("+"):
            str = lines[i][1:].strip()
            collection_list = []
            i += 1
            while lines[i].startswith('https') and i < len(lines) - 1:
                collection_list.append(lines[i])
                i += 1
            collections[str] = collection_list
            consoles.append(str)
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
            if s.endswith('.zip') or s.endswith('.7z') \
                or s.endswith('.rar') or s.endswith('.iso') \
                or s.endswith('.nes') or s.endswith('.smc') \
                or s.endswith('.sfc') or s.endswith('.smd') \
                or s.endswith('.gba') or s.endswith('.z64') \
                or s.endswith('.32x') or s.endswith('.gg'):
                strs.append(str(s))

    return strs

main()