from requests import get
from vecto.corpus.tokenization import word_tokenize_txt


# TODO: move this to corpus module
def normalize_text(text):
    return text.strip().lower()


def read_first_col_is_label_format(path, char_based=False):
    dataset = []
    with open(path, encoding='utf-8', errors='ignore') as f:
        for i, l in enumerate(f):
            if len(l.strip()) < 3:
                continue
            label, text = l.strip().split(None, 1)
            # TODO: make lower-casing optional
            text = normalize_text(text)
            label = int(label)
            if char_based:
                tokens = list(text)
            else:
                tokens = word_tokenize_txt(text)
            dataset.append((tokens, label))
    return dataset


def fetch_file(url, path, chunk_size=512):
    myfile = get(url, allow_redirects=True)
    open(path, 'wb').write(myfile.content)
#response = get(url, stream=True)
    #handle = open(path, 'wb')
    #for chunk in response.iter_content(chunk_size=chunk_size):
    #    if chunk:
    #        handle.write(chunk)
    #handle.close()