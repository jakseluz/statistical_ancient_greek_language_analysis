import zipfile
import xml.etree.ElementTree as ET
import time
from word2word import Word2word

start_time = time.time()

text_words = []  # all words from all documents, to be used for NLP analysis in the occurence order
found_words = dict()  # dictionary to store the count of each word, to be used for statistical analysis and ranking
w2w = Word2word("el", "en")


def translate(word):
    try:
        return w2w(word)
    except Exception as e:
        # print(f"Error translating word '{word}': {e}")
        return None


# Read the XML files from the zip archive and extract the words and count their occurrences
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
                        POS = lemma_elem.get("POS")
                        if entry is not None:
                            if entry in found_words:
                                found_words[entry][1] += 1
                            else:
                                found_words[entry] = [POS, 1, translate(entry)]
                            text_words.append((entry, POS))
                    elem.clear()

part_time = time.time()
print(f"Time to read and process XML files: {part_time - start_time:.2f} seconds")

# Sort the words by their count
sorted_by_count = sorted(found_words.items(), key=lambda kv: kv[1][1], reverse=True)
part_time = time.time()
print(f"Time to sort words by count: {part_time - start_time:.2f} seconds")
# Create a list of tuples with word, count, rank and product of Zipf's law
words_ranking = [
    (word, count, rank, count * rank, POS, translation)
    for rank, (word, (POS, count, translation)) in enumerate(sorted_by_count, start=1)
]
part_time = time.time()
print(f"Time to create words ranking: {part_time - start_time:.2f} seconds")

# Print the top 50 words with their count, rank and product of Zipf's law
print("\n\nSorted by count:\n")
i = 1
for word, count, rank, product, POS, translation in words_ranking:
    if i > 50:
        break
    print(f"{i}. {word}: {count} (rank: {rank}, product: {product}, POS: {POS}, translation: {translation})")
    i += 1
part_time = time.time()
print(f"Time to print top 50 words: {part_time - start_time:.2f} seconds")

import networkx as nx
import matplotlib.pyplot as plt

# create a graph with edges between neighbouring words
first_2000_words = sorted_by_count[:2000]
part_time = time.time()
print(f"\nTime to get first 2000 words: {part_time - start_time:.2f} seconds")
G = nx.Graph()
G.add_nodes_from([(word, POS) for word, (POS, _, _) in first_2000_words])
part_time = time.time()
print(f"Time to add nodes to graph: {part_time - start_time:.2f} seconds")
for i in range(len(text_words) - 1):
    word1 = text_words[i]
    word2 = text_words[i + 1]
    if word1 in G and word2 in G:
        if G.has_edge(word1, word2):
            G[word1][word2]["weight"] += 1
        else:
            G.add_edge(word1, word2, weight=1)
    else:
        continue
part_time = time.time()
print(f"Time to add edges to graph: {part_time - start_time:.2f} seconds")

# position = nx.circular_layout(G)

# draw_start = time.time()
# print("Drawing graph...")
# # plt.figure(figsize=(16, 16))
# # nx.draw_networkx_nodes(G, position, node_size=10, node_color="lightblue")
# part_time = time.time()
# print(f"Time to draw nodes: {part_time - draw_start:.2f} seconds")
# # nx.draw_networkx_edges(G, position, width=0.5, alpha=0.5)
# part_time = time.time()
# print(f"Time to draw edges: {part_time - draw_start:.2f} seconds")
# edge_labels = nx.get_edge_attributes(G, "weight")
# # nx.draw_networkx_edge_labels(G, position, edge_labels=edge_labels, font_size=6)
# # part_time = time.time()
# # print(f"Time to draw edge labels: {part_time - draw_start:.2f} seconds")
# # plt.axis("off")
# # plt.show()

top_words_by_connections = sorted(G.degree(weight="weight"), key=lambda x: x[1], reverse=True)
print("\n\nTop 200 words by number of connections:\n")
i = 1
for (word, POS), degree in top_words_by_connections:
    if i > 200:
        break
    print(f"{i}. {word} (POS: {POS}, translation: {translate(word)}): {degree} connections")
    i += 1

print("\n\nTop 50 nouns by number of connections:\n")
i = 1
while i <= 50 and top_words_by_connections:
    (word, POS), degree = top_words_by_connections.pop(0)
    if POS == "noun":
        print(f"{i}. {word} (POS: {POS}, translation: {translate(word)}): {degree} connections")
        i += 1


end_time = time.time()
print(f"\nExecution time: {end_time - start_time:.2f} seconds")
