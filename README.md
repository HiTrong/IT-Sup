# IT-Sup (IT Student Support Chatbot)

[![Kaggle](https://img.shields.io/badge/env-grey?style=flat&logo=kaggle&label=Kaggle&labelColor=white)](https://www.kaggle.com/)
[![React Native](https://img.shields.io/badge/0.8-grey?style=flat&logo=React&label=React%20Native&labelColor=black)](https://reactnative.dev/)
[![Flask](https://img.shields.io/badge/web%26api-grey?style=flat&logo=Flask&label=Flask&labelColor=purple)](https://flask.palletsprojects.com/en/stable/)
[![Python](https://img.shields.io/badge/3.10-green?style=flat-square&logo=Python&label=Python&labelColor=green&color=grey)](https://www.python.org/downloads/release/python-3100/)
[![PyTorch](https://img.shields.io/badge/11.8-black?style=flat-square&logo=PyTorch&logoColor=red&label=Torch&labelColor=orange&color=grey)](https://pytorch.org/)
[![HuggingFace](https://img.shields.io/badge/transformers-black?style=flat-square&logo=HuggingFace&logoColor=red&label=HuggingFace&labelColor=yellow&color=grey)](https://pypi.org/project/transformers/)
[![Gemini API](https://img.shields.io/badge/Free_API-black?style=flat-square&logo=Google&logoColor=white&label=Gemini&labelColor=blue&color=grey)](https://ai.google.dev/)

# Introduction

- This is the graduation project of Ho Chi Minh City University of Technology and Education.
- It aims to build a chatbot for IT student using Agentic RAG.
- Using Large Language Models (Qwen and Gemini) with Speech processing technology
- Applying Agentic RAG
- Deploy on Web and Mobile applications
- Survey and Evaluation

# Architecture

![Architecture](./img/architecture.png)

- Agentic RAG is deployed on Kaggle, which offers free GPUs weekly (great for personal projects without any fees). We deploy an API endpoint by Flask and open port by Ngrok Tunnel.
- At local, we have Web Application (HTML/CSS, JS with Flask) and Mobile Application (React Native)
- Users can use keyboard or voice to interact the application 

# Agentic RAG flow

![Agentic RAG flow](./img/agenticrag.png)

This system utilizes a Master Agent to route user questions to the most appropriate agents for processing:

1. User submits a question → The Master Agent analyzes and routes it to a suitable DocAgent.
2. DocAgents (A, B, C, ...):

- Generate vector embeddings for the query.
- Perform Hybrid Search (FAISS + BM25) over document chunks.
- If relevant documents are found, fallback to a Large Language Model (LLM) to generate a response.
- If not, attempt to rewrite the query and search again.
- Stop if verification is successful or no useful result is found.

3. If no agent can answer:

- The Master Agent activates Helpful Tools (e.g., request/confirm phone number, store the question, or escalate to a human expert).

4. Final answer is returned to the user.

# Interfaces

- Mobile Application:

![mobile1](./img/mobile1.png)

![mobile2](./img/mobile2.png)

- Web Application:

![web1](./img/web1.png)

![web2](./img/web2.png)


# Evaluation

- Comparing Qwen and Gemini (API)

![eval1](./img/eval1.png)

- Practical implementation with 30 students at HCMUTE

![eval2](./img/eval2.png)



