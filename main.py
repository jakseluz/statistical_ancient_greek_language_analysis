import zipfile
import xml.etree.ElementTree as ET

found_words = dict()

with zipfile.ZipFile("./Diorisis.zip") as z:
    for name in z.namelist():
        if not name.endswith(".xml"):
            continue

        with z.open(name) as xml_file:
            for event, elem in ET.iterparse(xml_file, events=("end",)):
                if elem.tag == "word":

                    lemma_elem = elem.find("lemma")
                    if lemma_elem is not None:
                        entry = lemma_elem.get("entry")
                        if entry is not None:
                            if entry in found_words:
                                found_words[entry] += 1
                            else:
                                found_words[entry] = 1
                    elem.clear()

i = 0
for word, count in found_words.items():
    if i >= 50:
        break
    print(f"{word}: {count}")
    i += 1

sorted_by_count = sorted(found_words.items(), key=lambda kv: kv[1], reverse=True)
words_ranking = [(word, count, rank, count * rank) for rank, (word, count) in enumerate(sorted_by_count, start=1)]
print("\n\nSorted by count:\n")
i = 0
for word, count, rank, product in words_ranking:
    if i >= 50:
        break
    print(f"{word}: {count} (rank: {rank}, product: {product})")
    i += 1
