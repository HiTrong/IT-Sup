# ==== Import Libs ====
# _tagging
import py_vncorenlp

# Search System
import faiss
from rank_bm25 import BM25Plus
from underthesea import word_tokenize
from sentence_transformers import SentenceTransformer, models
from transformers import AutoTokenizer

# Working with PDF
from unstructured.partition.pdf import partition_pdf

# Necessary
from tqdm.auto import tqdm
import re, os, json
from abc import ABC, abstractmethod
from collections import defaultdict


rdrsegmenter = py_vncorenlp.VnCoreNLP(annotators=["wseg"], save_dir='/kaggle/input/it-sup-stopwords/vncore')

# === Preprocessing function ===
def remove_stopwords(text, stopwords_path="/kaggle/input/it-sup-stopwords/vietnamese-stopwords.txt"):
    with open(stopwords_path, 'r', encoding='utf-8') as f:
        stopwords = set(line.strip().lower() for line in f if line.strip())
    words = re.findall(r'\b\w+\b', text.lower())
    filtered_words = [word for word in words if word not in stopwords]
    return ' '.join(filtered_words)

def _tagging(text):
    return ' '.join(rdrsegmenter.word_segment(text))

def embedding(model, text, show_progress_bar=False, batch_size=128):
    embeddings = model.encode(text, 
                              show_progress_bar=show_progress_bar, 
                              batch_size=batch_size)
    return embeddings

# === Read PDF function ===
def read_pdf(pdf_path):
    elements = partition_pdf(filename=pdf_path)
    texts = []
    for element in elements:
        texts.append(element.text)
    return "\n".join(texts)


# === check similar keywords===
def check_similar_keywords(text_a, text_b):
    processed_text_a = remove_stopwords(_tagging(text_a)).split(" ")
    processed_text_b = remove_stopwords(_tagging(text_b)).split(" ")

    keywords_a = [keyword for keyword in processed_text_a if "_" in keyword]
    keywords_b = [keyword for keyword in processed_text_b if "_" in keyword]

    # Kiểm tra giao giữa hai tập hợp
    return bool(set(keywords_a) & set(keywords_b))

# === DB Class ===
# Abstract class for DB
class Database(ABC):
    @abstractmethod
    def query(self, text, top_k):
        pass
    
    @abstractmethod
    def load(self, data):
        pass

# BM25DB class
class BM25DB(Database):
    def __init__(self):
        self.corpus = []
        self.mapping_dict = {}
        self.bm25 = None
        
    def load(self, data:list):
        preprocessing_data = [remove_stopwords(_tagging(str(s))) for s in data]
        for i in range(0, len(preprocessing_data)):
            tokenized_doc = word_tokenize(preprocessing_data[i], format="text").split()
            self.corpus.append(tokenized_doc)
            self.mapping_dict[len(self.mapping_dict)] = data[i]
        if len(self.corpus) > 1:
            self.bm25 = BM25Plus(self.corpus)
    
    def query(self, text, top_k=5):
        if len(self.corpus) == 0:
            return []
        if len(self.corpus) == 1:
            si = check_similar_keywords(text, self.mapping_dict[0])
            if si: score=2
            else: score=0
            return [(self.mapping_dict[0], score)]
        
        bm25_scores = self.bm25.get_scores(word_tokenize(remove_stopwords(_tagging(text)), format="text").split())
        filtered = [(i, score) for i, score in enumerate(bm25_scores)]
        filtered = sorted(filtered, key=lambda x: x[1], reverse=True)
        top_results = filtered[:top_k]
        return [(self.mapping_dict[idx], score) for idx, score in top_results]

# FaissDB class
class FaissDB(Database):
    def __init__(self, 
                 model, 
                 vector_size=768, 
                 batch_size=128):
        
        # self.model = SentenceTransformer(model_name)
        self.model = model
        self.index = faiss.IndexFlatL2(vector_size)
        self.mapping_dict = {}
        self.batch_size = batch_size
        
    def load(self, data):
        preprocessing_data = [_tagging(str(s)) for s in data]
        embeddings = embedding(self.model, text=preprocessing_data, batch_size=self.batch_size)
        for i in range(0, len(preprocessing_data)):
            self.mapping_dict[len(self.mapping_dict)] = data[i]
            self.index.add(embeddings[i].reshape(1, -1))
        
    def query(self, text, top_k=5):
        result = []
        text = _tagging(text)
        embedding_query = embedding(self.model, text=text, batch_size=self.batch_size)
        D, I = self.index.search(embedding_query.reshape(1, -1), top_k)
        for i in range(top_k):
            idx = I[0][i]
            if idx in self.mapping_dict:
                result.append(self.mapping_dict[idx])
        return result
    
# === Hybrid Search System Class ===
class HybridSearchSystem:
    def __init__(
        self,
        data_path="/kaggle/input/it-sup-all-pdf/Data", 
        model_name="Cloyne/vietnamese-sbert-v3", 
        vector_size=768,
        batch_size=128):

        print("[HybridSearchSystem]: Initialize")

        self.data_path = data_path
        self.model_name = model_name
        self.vector_size = vector_size
        self.batch_size = batch_size
        self.categories_DB = {}

        # Load model
        print(f"[HybridSearchSystem]: Load model {model_name}")
        self.model = SentenceTransformer(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Load all folder names
        self.categories = [name for name in os.listdir(self.data_path)
           if os.path.isdir(os.path.join(self.data_path, name))]

        # Load metadata (folder)
        with open(os.path.join(self.data_path, "metadata.json"), 'r', encoding='utf-8') as f:
            self.categories_metadata = json.load(f)

    def load(self, max_tokens=250, overlap=50):
        print("[HybridSearchSystem]: Load data")
        for category in tqdm(self.categories, desc="Loading data"):
            category_path = os.path.join(self.data_path, category)
            with open(os.path.join(category_path, "metadata.json"), 'r', encoding='utf-8') as f:
                file2infor = json.load(f)
            
            text2id, id2file = {}, {}
            count = 0
            bm25db = BM25DB()
            faissdb = FaissDB(self.model, self.vector_size, self.batch_size)
            if os.path.isdir(category_path):
                print(f"Processing {category}: ", end="")
                for file_name in os.listdir(category_path):
                    if file_name.lower().endswith('.pdf'):
                        id2file[count] = file_name
                        pdf_path = os.path.join(category_path, file_name)
                        pdf_content = read_pdf(pdf_path)
                        tokens = self.tokenizer.encode(pdf_content, add_special_tokens=False)
                        chunks = []
                        start = 0
                        while start < len(tokens):
                            end = start + max_tokens
                            chunk_tokens = tokens[start:end]
                            chunk_text = self.tokenizer.decode(chunk_tokens, skip_special_tokens=True)
                            text2id[chunk_text] = count
                            chunks.append(chunk_text)
                            if end >= len(tokens):
                                break
                            start += max_tokens - overlap
                        bm25db.load(chunks)
                        faissdb.load(chunks)
                        count += 1
                self.categories_DB[category] = {
                    "faissdb": faissdb,
                    "bm25db": bm25db,
                    "text2id": text2id,
                    "id2file": id2file,
                    "file2infor": file2infor
                }
                print("done!")

    def query(self, id, text, top_k=5, bm25_adjust=10, faiss_adjust=10):
        category = self.categories[id]
        
        # Check the similar keywords between text and description of category
        if not check_similar_keywords(text, self.categories_metadata[category]["description"]):
            return False, {}
        
        faissdb = self.categories_DB[category]["faissdb"]
        bm25db = self.categories_DB[category]["bm25db"]
        text2id = self.categories_DB[category]["text2id"]
        id2file = self.categories_DB[category]["id2file"]
        file2infor = self.categories_DB[category]["file2infor"]

        faiss_query = faissdb.query(text, top_k)
        bm25_query = bm25db.query(text, top_k)
        
        # BM25 Threshold
        if bm25_query[0][1] <= 1:
            return False, {}
        
        scores = defaultdict(float)
        for rank, doc in enumerate(bm25_query):
            scores[doc[0]] += 1 / (bm25_adjust + rank + 1)
        for rank, doc in enumerate(faiss_query):
            scores[doc] += 1 / (faiss_adjust + rank + 1) 

        ranked_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        docs = []
        metadatas = []
        pdfs = []
        for doc, _ in ranked_results:
            docs.append(doc)
            file = id2file[text2id[doc]]
            metadata = file2infor[file]
            if file not in pdfs:
                pdfs.append(file)
            if metadata not in metadatas:
                metadatas.append(metadata) 
        return True, {
            "pdfs": pdfs,
            "docs": docs,
            "metadatas": metadatas
        }

    def get_agent_description(self, mistakes=[]):
        agent_description = ""
        for i in range(len(self.categories)):
            if i not in mistakes:
                c = self.categories[i]
                agent_description += f"ID: {i}\n{self.categories_metadata[c]}\n\n"
        return agent_description.strip()

    def get_agent_info(self, id):
        c = self.categories[id]
        return c, self.categories_metadata[c]['description']
