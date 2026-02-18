import zipfile
import xml.etree.ElementTree as ET
import time
import requests
from urllib.parse import quote
from word2word import Word2word
import networkx as nx
import matplotlib.pyplot as plt

w2w = Word2word("el", "en")  # initialize the Word2word translator for Greek to English translation
FILENAME = "word_ranking.txt"  # file to write the output to


def translate(word) -> str | None:
    """
    Translate a Greek word to English using the Word2word library. If the translation fails, return None.
    Test, for more adequate translation, the Wiktionary API (translate_wiki function) and compare the results.

    :param word: The Greek word to translate
    :type word: str
    :return: The English translation of the given Greek word, or None if the translation fails
    :rtype: str | None
    """
    try:
        return w2w(word)
    except Exception as e:
        # print(f"Error translating word '{word}': {e}")
        return None


def translate_wiki(word) -> list[str] | None:
    """
    Translate a Greek word using the Wiktionary API and return a list of definitions. If the word is not found, return None.

    :param word: The Greek word to translate
    :type word: str
    :return: A list of definitions for the given word, or None if the word is not found
    :rtype: list[str] | None
    """
    url = f"https://en.wiktionary.org/api/rest_v1/page/definition/{quote(word)}"
    headers = {"User-Agent": "StatisticalGreek/1.0 (https://github.com/jakseluz; contact: labuzjak@gmail.com)"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        return retrieve_definitions(data["other"][0]["definitions"])
    return None


def retrieve_definitions(word_definitions) -> list[str]:
    """
    Retrieve the definitions from the Wiktionary API response and clean them by removing any HTML tags.

    :param word_definitions: The list of definitions from the Wiktionary API response
    :type word_definitions: list[dict]
    :return: A list of cleaned definitions for the given word
    :rtype: list[str]
    """
    definitions = []
    for definition in word_definitions:
        d = definition["definition"]
        while "<" in d and ">" in d:
            start = d.find("<")
            end = d.find(">")
            if start < end:
                d = d[:start] + d[end + 1 :]
            else:
                break
        definitions.append(d.replace("\n", "; ").strip())
    return definitions


def write_output(filename, data):
    """
    Write the given data to a file (by appending) with the specified filename.

    :param filename: The name of the file to write to
    :param data: The data to write to the file
    """
    with open(filename, "a", encoding="utf-8") as f:
        f.write(data)


def parse_xmls() -> tuple[list[tuple[str, str]], dict[str, list]]:
    """
    Parse the XML files from the zip archive and extract the words and count their occurrences. Also, translate the words using the translate function.

    :return: A tuple containing a list of (word, POS) tuples and a dictionary of word counts and translations
    :rtype: tuple[list[tuple[str, str]], dict[str, list]]
    """
    text_words = []  # all words from all documents, to be used for NLP analysis in the occurence order
    found_words = dict()  # dictionary to store the count of each word, to be used for statistical analysis and ranking

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
    return text_words, found_words


def create_word_graph(sorted_words, number_of_words, text_words) -> nx.Graph:
    """
    Create a graph with edges between neighbouring words in the text. Only the top `number_of_words` most frequent words are included as nodes in the graph.

    :param sorted_words: A list of tuples containing words and their lists (POS, count, translation, etc.), sorted by count in descending order
    :type sorted_words: list[tuple[str, list]]
    :param number_of_words: The number of most frequent words to include as nodes in the graph
    :type number_of_words: int
    :param text_words: A list of tuples containing words and their POS tags in the order they appear in the text
    :type text_words: list[tuple[str, str]]
    :return: A graph with edges between neighbouring words in the text, where only the top `number_of_words` most frequent words are included as nodes
    :rtype: nx.Graph
    """
    first_2000_words = sorted_words[:number_of_words]
    G = nx.Graph()
    G.add_nodes_from([(word, POS) for word, (POS, _, _) in first_2000_words])
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
    return G


def main():
    start_time = time.time()

    # Parse the XML files and extract the words and count their occurrences
    text_words, found_words = parse_xmls()
    part_time = time.time()
    print(f"Time to read and process XML files: {part_time - start_time:.2f} seconds")

    # Sort the words by their count
    sorted_by_count = sorted(found_words.items(), key=lambda kv: kv[1][1], reverse=True)
    part_time = time.time()
    print(f"Time to sort words by count: {part_time - start_time:.2f} seconds")

    # Clear the output file before writing
    with open(FILENAME, "w", encoding="utf-8") as f:
        pass  # clear the file before writing

    print(f"\n\nNumber of words used in the research: {len(text_words)}\n")
    write_output(FILENAME, f"\n\nNumber of words used in the research: {len(text_words)}\n")
    part_time = time.time()
    print(f"Time to clear output file and count total number of words: {part_time - start_time:.2f} seconds")

    # Create a list of tuples with word, count, rank and product of Zipf's law
    words_ranking = [
        (word, count, rank, count * rank, POS, translation)
        for rank, (word, (POS, count, translation)) in enumerate(sorted_by_count, start=1)
    ]
    part_time = time.time()
    print(f"Time to create words ranking: {part_time - start_time:.2f} seconds")

    # Print the top 50 words with their count, rank and product of Zipf's law
    print("\n\nSorted by count:\n")
    write_output(FILENAME, "\n\nSorted by count:\n")
    i = 1
    for word, count, rank, product, POS, translation in words_ranking:
        if i > 50:
            break
        print(f"{i}. {word}: {count} (rank: {rank}, product: {product}, POS: {POS}, translation: {translation})")
        write_output(
            FILENAME,
            f"{i}. {word}: {count} (rank: {rank}, product: {product}, POS: {POS}, translation: {translation})\n",
        )
        i += 1
    part_time = time.time()
    print(f"Time to print top 50 words: {part_time - start_time:.2f} seconds")

    # create a graph with edges between neighbouring words
    G = create_word_graph(sorted_by_count, 2000, text_words)
    part_time = time.time()
    print(f"Time to add edges to graph: {part_time - start_time:.2f} seconds")

    # optionally: draw the graph (this can be very slow for large graphs and illegible, so it's commented out by default)

    # position = nx.circular_layout(G) # use circular layout
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

    # Analyze the graph to find the most connected words (by degree) and print the top 200 of them with their English definitions from Wiktionary
    top_words_by_connections = sorted(G.degree(weight="weight"), key=lambda x: x[1], reverse=True)
    print("\n\nTop 200 words by number of connections:\n")
    write_output(FILENAME, "\n\nTop 200 words by number of connections:\n")
    i = 1
    for (word, POS), degree in top_words_by_connections:
        if i > 200:
            break
        print(f"{i}. {word} (POS: {POS}, translation: {translate_wiki(word)}): {degree} connections")
        write_output(
            FILENAME,
            f"{i}. {word} (POS: {POS}, translation: {translate_wiki(word)}): {degree} connections\n",
        )
        i += 1

    # Analyze the graph to find the most connected nouns (by degree) and print the top 50 of them with their English definitions from Wiktionary
    print("\n\nTop 50 nouns by number of connections:\n")
    write_output(FILENAME, "\n\nTop 50 nouns by number of connections:\n")
    i = 1
    while i <= 50 and top_words_by_connections:
        (word, POS), degree = top_words_by_connections.pop(0)
        if POS == "noun":
            print(f"{i}. {word} (POS: {POS}, translation: {translate_wiki(word)}): {degree} connections")
            write_output(
                FILENAME,
                f"{i}. {word} (POS: {POS}, translation: {translate_wiki(word)}): {degree} connections\n",
            )
            i += 1

    end_time = time.time()
    print(f"\nExecution time: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    main()
