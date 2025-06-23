# === Import Libs ===
import vllm
import kagglehub
import google.generativeai as genai
from kaggle_secrets import UserSecretsClient

from abc import ABC, abstractmethod
import re
import random
from datetime import datetime

# === ChatConfig Class ===
# Chat Config class
class ChatConfig:
    def __init__(self, top_k=20, top_p = 0.8, temperature=0.7, repetition_penalty=1.05, max_tokens=512, use_tqdm=False):
        self.top_k = top_k
        self.top_p = top_p
        self.temperature = temperature
        self.repetition_penalty = repetition_penalty
        self.max_tokens = max_tokens
        self.use_tqdm = use_tqdm
        
# === Model Class ===
# Abstract class for LLMs
class LLM(ABC):
    @abstractmethod
    def chat(self, messages, config:ChatConfig):
        pass
    
# Qwen class for VLLM
class Qwen(LLM):
    def __init__(self, model_name="qwen-lm/qwen2.5/Transformers/14b-instruct-awq/1"):
        print("[Models]: Qwen is being initialized")
        self.model_path = kagglehub.model_download(model_name)
        
        self.llm = vllm.LLM(
            self.model_path,
            quantization="awq",
            tensor_parallel_size=2,
            gpu_memory_utilization=0.95,
            trust_remote_code=True,
            dtype="half",
            enforce_eager=True,
            max_model_len=8192,
            disable_log_stats=True
        )
        
        self.tokenizer = self.llm.get_tokenizer()
        
    def clear_markdown(self, response):
        # Thay thế \n\n bằng \n
        response = re.sub(r'\n\n+', '\n', response)
        # Loại bỏ markdown như ** và *
        response = re.sub(r'\*\*|\*', '', response)
        return response
        
    def apply_template(self, messages):
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        return text
    
    def chat(self, messages, config=ChatConfig()):
        # Set sampling parameters
        sampling_params = vllm.SamplingParams(
            n=1,  # Number of output sequences to return for each prompt.
            top_k=config.top_k,  # Float that controls the cumulative probability of the top tokens to consider.
            top_p=config.top_p,
            temperature=config.temperature,  # randomness of the sampling
            repetition_penalty=config.repetition_penalty,
            # seed=777, # Seed for reprodicibility
            skip_special_tokens=False,  # Whether to skip special tokens in the output.
            max_tokens=config.max_tokens,  # Maximum number of tokens to generate per output sequence.
        )
        
        inputs = [self.apply_template(messages)]
        responses = self.llm.generate(inputs, sampling_params, use_tqdm=config.use_tqdm)
        responses = [x.outputs[0].text for x in responses]
        print("[Qwen]:", self.clear_markdown(responses[0]))
        return self.clear_markdown(responses[0])
    
# Gemini class for VLLM
class Gemini(LLM):
    def __init__(self, api_lst:list, model_lst:list):
        print("[Models]: Gemini is being initialized")
        self.api_model_choice = []
        for m in model_lst:
            for a in api_lst:
                self.api_model_choice.append((m, a))

        self.choice_index = 0

    def get_choice(self):
        self.choice_index += 1
        if self.choice_index >= len(self.api_model_choice):
            self.choice_index = 0
        return self.api_model_choice[self.choice_index]
        
    def clear_markdown(self, response):
        # Thay thế \n\n bằng \n
        response = re.sub(r'\n\n+', '\n', response)
        # Loại bỏ markdown như ** và *
        response = re.sub(r'\*\*|\*', '', response)
        return response
    
    def chat(self, messages, config=ChatConfig()):
        instruct = "Bạn là Chatbot AI phục vụ cho sinh viên khoa Công Nghệ Thông Tin của Trường đại học Sư Phạm Kỹ Thuật."
        inputs = ""
        for message in messages:
            if message["role"] == "system":
                instruct = message["content"]
            else:
                inputs += f"{message['role']}: {message['content']}\n"

        for i in range(len(self.api_model_choice)):
            try:
                model_name, api_key = self.get_choice()
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    model_name,
                    system_instruction=instruct,
                    generation_config=genai.GenerationConfig(
                        max_output_tokens=config.max_tokens,
                        top_k=config.top_k,
                        top_p=config.top_p,
                        temperature=config.temperature
                    )
                )
                response = model.generate_content(inputs)
                print("[Gemini]:", self.clear_markdown(response.text))
                return self.clear_markdown(response.text)
            except:
                print(f"WARNING: GEMINI API - Request failed at {datetime.now()}")
        print("[Gemini]: Đã có lỗi xảy ra trong quá trình xử lý yêu cầu. Vui lòng thử lại sau.")
        return "Đã có lỗi xảy ra trong quá trình xử lý yêu cầu. Vui lòng thử lại sau."
    
    
    
# === How to use in Kaggle ===

# qwen = Qwen(model_name="qwen-lm/qwen2.5/Transformers/14b-instruct-awq/1")

# user_secrets = UserSecretsClient()
# gemini = Gemini(api_lst=user_secrets.get_secret("API_GEMINI").split("###"),
#                 model_lst=['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-1.5-pro'])
    
    
    
    
    
    
    
    
    