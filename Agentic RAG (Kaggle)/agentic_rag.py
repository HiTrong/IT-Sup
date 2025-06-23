# === Import Libs ===
from models import LLM, Qwen, Gemini, ChatConfig
from prompting import PromptManager
from utils import TextParser
from hybrid_search import HybridSearchSystem, BM25DB, check_similar_keywords

from abc import ABC, abstractmethod
import logging, re
from rich.console import Console
import random
        
# === LOGGING Class ===
class Logging:
    def __init__(self, filename="/kaggle/working/agentic_rag.txt", format="%(message)s"):
        # Log to file
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.file_handler = logging.FileHandler(filename)
        self.file_handler.setLevel(logging.INFO)
        self.formatter = logging.Formatter(format)
        self.file_handler.setFormatter(self.formatter)
        self.logger.addHandler(self.file_handler)
        
        # Log to console
        self.console = Console()

    def master_agent(self, message: str):
        message_lst = message.split("\n")
        for i in range(0, len(message_lst)):
            if i == 0:
                self.console.print(f"[bold gold3]   [Master Agent]:[/bold gold3] {message_lst[i]}")
            else:
                self.console.print(f"                   {message_lst[i]}")
        self.logger.info(f"[Master Agent]: {message}")

    def doc_agent(self, message: str):
        message_lst = message.split("\n")
        for i in range(0, len(message_lst)):
            if i == 0:
                self.console.print(f"[bold sky_blue1][Documents Agent]:[/bold sky_blue1] {message_lst[i]}")
            else:
                self.console.print(f"                   {message_lst[i]}")
        self.logger.info(f"[Documents Agent]: {message}")

    def user(self, message: str):
        message_lst = message.split("\n")
        for i in range(0, len(message_lst)):
            if i == 0:
                self.console.print(f"[bold green3]           [User]:[/bold green3] {message_lst[i]}")
            else:
                self.console.print(f"                   {message_lst[i]}")
        self.logger.info(f"[User]: {message}")
        
    def info(self, message):
        self.logger.info(f"[{message}]")


# === Agent Class ===
# LLMAgent Abtract class
class LLMAgent(ABC):
    @abstractmethod
    def __init__(self, model:LLM, text_parser:TextParser):
        self.model = model
        self.text_parser = text_parser
        
    @abstractmethod
    def BinaryGenerate(self, messages, true_keywords=['đúng', 'true', 'có', 'chính xác', 'xác nhận', 'cần ngữ cảnh', 'có cần tài liệu']):
        binary_config = ChatConfig(
            top_k=5, 
            top_p=1.0, 
            temperature=0.0, 
            repetition_penalty=1.0, 
            max_tokens=3, 
            use_tqdm=False
        )
        response = self.model.chat(messages=messages, config=binary_config)
        binary_result = self.text_parser.Binary(response, true_keywords=true_keywords)
        return binary_result
    
    @abstractmethod
    def NumberGenerate(self, messages):
        number_config = ChatConfig(
            top_k=5, 
            top_p=1.0, 
            temperature=0.0, 
            repetition_penalty=1.0, 
            max_tokens=3, 
            use_tqdm=False
        )
        response = self.model.chat(messages=messages, config=number_config)
        number = self.text_parser.Number(response)
        return number
    
    @abstractmethod
    def ChatGenerate(self, messages, max_tokens=1024):
        chat_config = ChatConfig(
            top_k=5, 
            top_p=1.0, 
            temperature=0.0, 
            repetition_penalty=1.0, 
            max_tokens=max_tokens, 
            use_tqdm=False
        )
        response = self.model.chat(messages=messages, config=chat_config)
        return response
    
    
# DocAgent Class
class DocAgent(LLMAgent):
    def __init__(self, model, text_parser, logger:Logging, hybrid_search:HybridSearchSystem, expert_db:BM25DB):
        super().__init__(model, text_parser)
        self.logger = logger
        self.prompt_manager = PromptManager()
        self.hybrid_search = hybrid_search
        self.expert_db = expert_db
    
    def BinaryGenerate(self, messages, true_keywords=['đúng', 'true', 'có', 'chính xác', 'xác nhận', 'cần ngữ cảnh', 'có cần tài liệu']):
        return super().BinaryGenerate(messages, true_keywords)
    
    def ChatGenerate(self, messages, max_tokens=1024):
        return super().ChatGenerate(messages, max_tokens)
    
    def NumberGenerate(self, messages):
        return super().NumberGenerate(messages)
    
    
    # reWrite: to rewrite query
    # Return new query (str)
    def reWrite(self, role, query):
        messages = self.prompt_manager.get_rewrite_messages(role=role, query=query)
        return self.ChatGenerate(messages=messages, max_tokens=50)
    
    
    # find_pdf_docs: Find pdf documents
    # Return bool,str, list, list
    def find_pdf_docs(self, id, query, top_k):
        query_state, query_result = self.hybrid_search.query(id=id, text=query, top_k=top_k)
        if query_state:
            docs_str = "### Tài liệu PDF\n"
            docs = query_result["docs"]
            pdfs = query_result["pdfs"]
            metadatas = query_result["metadatas"]
        
            self.logger.doc_agent(f"Found {len(docs)} docs in {pdfs}")
        
            for doc in docs[::-1]:
                docs_str += doc + "\n\n"
            source_lst = []
            url_lst = []
            for i in range(0,len(metadatas)):
                source_lst.append(metadatas[i]["description"])
                url_lst.append(metadatas[i]["source"])
                
            return True, docs_str.strip(), source_lst, url_lst
        self.logger.doc_agent(f"No related documents found")
        return False, "", [], []
    
    
    # find_expert_docs: Find expert QA
    # Return str 
    def find_expert_docs(self, query, top_k=15):
        expert_docs_lst = self.expert_db.query(text=query, top_k=top_k)
        if expert_docs_lst[0][1] > 10:
            expert_docs_str = "### Tài liệu tư vấn viên\n"
            self.logger.doc_agent(f"Found {len(expert_docs_lst)} docs in Expert Docs")
            if len(expert_docs_lst) > 0:
                for doc in expert_docs_lst[::-1]:
                    expert_docs_str += doc[0] + "\n\n"
                return expert_docs_str.strip()
        return ""
    
    # Return: state(bool), docs_str(str), source_lst(list), url_lst(list)
    def pdf_task(self, id, question, top_k=7, max_rewrite=2):
        agent_name, agent_role = self.hybrid_search.get_agent_info(id)
        self.logger.doc_agent(f"Assigned documents task to Agent {agent_name}")
        query = question
        docs_str, source_lst, url_lst = "", [], []
        while max_rewrite > 0:
            query_state, docs_str, source_lst, url_lst = self.find_pdf_docs(id=id, query=query, top_k=top_k)
            if query_state:
                return True, docs_str, source_lst, url_lst
            else:
                max_rewrite -= 1
                if max_rewrite > 0:
                    new_query = self.reWrite(role=agent_role, query=query)
                    self.logger.doc_agent(f"Rewrite query\nFrom: {query}\nTo: {new_query}")
                    query = new_query
            
        self.logger.doc_agent(f"Task was FAILED")
        return False, "", [], []

        
    # Return: state(bool), expert_docs(str)
    def expert_task(self, question, top_k=15):
        expert_docs = self.find_expert_docs(query=question, top_k=top_k)
        if expert_docs == "":
            return False, ""
        return True, expert_docs
    
# Master Agent class
class MasterAgent(LLMAgent):
    def __init__(self, model, text_parser:TextParser, logger:Logging, doc_agent:DocAgent):
        super().__init__(model, text_parser)
        self.prompt_manager = PromptManager()
        self.logger = logger
        self.unknown_questions = {}
        self.doc_agent = doc_agent
        
    def BinaryGenerate(self, messages, true_keywords=['đúng', 'true', 'có', 'chính xác', 'xác nhận', 'cần ngữ cảnh', 'có cần tài liệu']):
        return super().BinaryGenerate(messages, true_keywords)
    
    def NumberGenerate(self, messages):
        return super().NumberGenerate(messages)
    
    def ChatGenerate(self, messages, max_tokens=1024):
        return super().ChatGenerate(messages, max_tokens)
    
    def needContext(self, question):
        messages = self.prompt_manager.get_needcontext_messages(question=question)
        return self.BinaryGenerate(messages=messages)
    
    def router(self, question, description):
        messages = self.prompt_manager.get_router_messages(question=question, description=description)
        return self.NumberGenerate(messages=messages)
    
    def confirm(self, question):
        messages = self.prompt_manager.get_confirm_messages(question=question)
        return self.BinaryGenerate(messages=messages)
    
    def require_state(self, input_dict):
        phone_number = input_dict['phone_number']
        text = input_dict['question']
        check, phone_number = self.text_parser.contains_valid_vietnam_phone_number(text)
        if check: # Có số điện thoại mới và cần xác nhận (confirm)
            self.logger.master_agent("User provided phone number")
            self.logger.master_agent("Confirm phone number with user")
            confirm_responses = ["Chúng tôi đã nhận được số điện thoại {phone_number}. Vui lòng xác nhận lại số này có chính xác không?","Bạn vừa nhập số {phone_number}. Đây có phải là số điện thoại của bạn không?","Số điện thoại của bạn là {phone_number}, đúng không? Vui lòng xác nhận để tiếp tục.","Vui lòng kiểm tra lại số điện thoại {phone_number} và xác nhận nếu chính xác.","Chúng tôi sẽ liên hệ với bạn qua số {phone_number}. Nếu số này đúng, vui lòng xác nhận.","Bạn có muốn sử dụng số {phone_number} để nhận phản hồi từ chúng tôi không?","Để đảm bảo bạn nhận được thông tin kịp thời, hãy xác nhận số {phone_number} mà bạn vừa nhập.","Số {phone_number} có phải là số điện thoại bạn muốn dùng để liên hệ không?","Chúng tôi thấy bạn đã nhập số {phone_number}. Vui lòng xác nhận lại để tránh sai sót.","Bạn có thể kiểm tra lại số {phone_number} không? Nếu đúng, hãy xác nhận giúp chúng tôi nhé!"]
            input_dict['phone_number'] = phone_number
            input_dict['state'] = 'confirm'
            input_dict['response'] = random.choice(confirm_responses).format(phone_number=phone_number)
        elif len(phone_number) > 6: # Người dùng có nhập sđt nhưng không hợp lệ do lỗi gì đó
            self.logger.master_agent("User provided the wrong phone number")
            self.logger.master_agent("Require again")
            retry_phone_number_templates = ["Hình như số điện thoại bạn nhập chưa đầy đủ hoặc có lỗi, bạn có thể kiểm tra lại giúp mình không?","Mình thấy số điện thoại bạn nhập có vẻ chưa chính xác, bạn nhập lại giúp mình nhé!","Có vẻ như số bạn nhập bị thiếu hoặc sai định dạng, bạn kiểm tra lại và nhập lại giúp mình nha!","Số điện thoại của bạn có thể chưa đúng, bạn có thể nhập lại không?","Mình không chắc số bạn nhập có chính xác không, bạn kiểm tra lại thử nhé!","Oops! Có vẻ như số điện thoại bạn nhập chưa đầy đủ hoặc sai, bạn vui lòng nhập lại nhé!","Hình như bạn nhập nhầm số rồi, bạn nhập lại giúp mình được không?","Có vẻ như số điện thoại bị thiếu hoặc sai, bạn có thể kiểm tra và nhập lại không?","Mình không chắc số bạn nhập có đúng không, bạn kiểm tra lại thử nha!","Số điện thoại bạn cung cấp có vẻ chưa đầy đủ, bạn có thể nhập lại giúp mình không?"]
            input_dict['phone_number'] = ''
            input_dict['state'] = 'require_phone_number'
            input_dict['response'] = random.choice(retry_phone_number_templates)
        else: # Người dùng không cung cấp sđt mà hỏi câu hỏi khác
            input_dict['phone_number'] = ''
            input_dict['state'] = 'normal'
        return input_dict
    
    def confirm_state(self, input_dict):
        question = input_dict['question']
        confirm = self.confirm(question=question)
        if confirm:
            self.logger.master_agent("User confirmed the phone number")
            question_forwarded_templates = ["Câu hỏi của bạn đã được gửi đến chuyên gia. Bạn sẽ nhận được phản hồi sớm nhất có thể!","Chúng tôi đã chuyển câu hỏi của bạn đến chuyên gia. Hãy chờ một chút nhé!","Câu hỏi đã được gửi đi! Chuyên gia sẽ phản hồi bạn trong thời gian sớm nhất.","Câu hỏi của bạn đã được chuyển đến chuyên gia để xem xét. Bạn vui lòng đợi phản hồi!","Chúng tôi đã gửi câu hỏi đến chuyên gia. Bạn sẽ sớm nhận được câu trả lời!","Câu hỏi của bạn đã được chuyển đến bộ phận chuyên gia. Hãy chờ phản hồi nhé!","Chúng tôi đang xử lý câu hỏi của bạn. Chuyên gia sẽ liên hệ với bạn sớm!","Câu hỏi đã được gửi đến chuyên gia. Bạn hãy kiểm tra tin nhắn sau nhé!","Chúng tôi đã tiếp nhận câu hỏi của bạn. Hãy đợi chuyên gia phản hồi trong thời gian ngắn!","Câu hỏi của bạn đã được gửi đi thành công! Hãy chờ chuyên gia giải đáp nhé!"]
            input_dict['response'] = random.choice(question_forwarded_templates)
            input_dict['state'] = 'normal'
            return True, input_dict
        else: # Người dùng không xác nhận số điện thoại
            self.logger.master_agent("User did not confirm the phone number")
            self.logger.master_agent("Require again")
            request_new_phone_number_templates = ["Bạn có thể nhập lại một số điện thoại khác giúp mình không?", "Có vẻ như bạn chưa xác nhận số điện thoại, bạn vui lòng cung cấp một số khác nhé!", "Mình chưa thể tiếp nhận số điện thoại này, bạn có thể thử nhập số khác không?", "Bạn vui lòng nhập lại một số điện thoại khác để mình có thể hỗ trợ tốt hơn nhé!", "Số điện thoại này có vẻ chưa đúng, bạn có thể cung cấp một số khác được không?","Bạn vui lòng nhập lại số điện thoại khác giúp mình nhé!","Hình như bạn chưa xác nhận số điện thoại, bạn có thể nhập lại một số khác không?","Nếu số điện thoại chưa đúng, bạn có thể nhập một số khác để tiếp tục nhé!","Số điện thoại này chưa được chấp nhận, bạn có thể thử nhập số khác không?","Bạn có thể nhập lại một số điện thoại khác để mình có thể hỗ trợ tốt hơn không?"]
            input_dict['phone_number'] = ''
            input_dict['state'] = 'require_phone_number'
            input_dict['response'] = random.choice(request_new_phone_number_templates)
            return False, input_dict
    
    def answer_without_context(self, question, max_tokens):
        messages = self.prompt_manager.get_chat_messages(question=question)
        return self.ChatGenerate(messages=messages, max_tokens=max_tokens)
    
    def answer_with_context(self, question, documents, max_tokens):
        messages = self.prompt_manager.get_ragchat_messages(question=question, docs_str=documents)
        return self.ChatGenerate(messages=messages, max_tokens=max_tokens)
        
    def format_output(self, input_dict):
        if "url" not in input_dict:
            input_dict["url"] = []
        if "source" not in input_dict:
            input_dict["source"] = []
            
        new_sources = []
        new_urls = []
            
        for i in range(len(input_dict["source"])):
            if check_similar_keywords(input_dict["response"], input_dict["source"][i]):
                new_sources.append(input_dict["source"][i])
                new_urls.append(input_dict["url"][i])
        input_dict["source"] = new_sources
        input_dict["url"] = new_urls
        input_dict["response"] = input_dict["response"].replace("TRUE","").replace("FALSE", "").replace("Trả lời:", "").strip()
        input_dict['response_speak'] = self.text_parser.Acronym(input_dict['response'].lower()).replace("@gmail.", " A còng gờ meo chấm ").replace("@email.", " A còng i meo chấm ")
        return input_dict
        
    def get_unknown_questions(self):
        return self.unknown_questions
    
    def save_question(self, question, phone_number):
        if question not in self.unknown_questions:
            self.unknown_questions[question] = {
                "solve": False,
                "phone_number": [phone_number]
            }
        else:
            if phone_number not in self.unknown_questions[question]["phone_number"]:
                self.unknown_questions[question]["phone_number"].append(phone_number)
                
    def solve_question(self, question, answer):
        if question not in self.unknown_questions:
            return False 
        if self.unknown_questions[question]['solve'] == True:
            return False
        self.unknown_questions[question]['solve'] = True
        self.doc_agent.expert_db.load([f"Câu hỏi: {question}\nTrả lời: {answer}"])
        return True
    
    def cannot_answer(self, input_dict):
        system_cannot_answer_templates = ["Có vẻ hệ thống chưa thể trả lời câu hỏi này. Bạn vui lòng để lại số điện thoại để chuyên gia của chúng tôi liên hệ giải đáp nhé!","Chúng tôi chưa có câu trả lời phù hợp cho câu hỏi của bạn. Vui lòng nhập số điện thoại để chuyên gia hỗ trợ bạn sớm nhất!","Rất tiếc, hệ thống chưa xử lý được câu hỏi này. Bạn có thể để lại số điện thoại để nhận hỗ trợ từ chuyên gia.","Hiện tại chúng tôi chưa thể trả lời chính xác câu hỏi của bạn. Vui lòng cung cấp số điện thoại để chuyên gia tư vấn trực tiếp!","Câu hỏi của bạn hơi đặc biệt! Bạn vui lòng để lại số điện thoại để chuyên gia liên hệ giải đáp nhé!","Xin lỗi, hệ thống chưa thể phản hồi câu hỏi này. Vui lòng nhập số điện thoại để nhận hỗ trợ từ chuyên gia.","Câu hỏi của bạn cần được chuyên gia xem xét kỹ hơn. Hãy để lại số điện thoại để chúng tôi hỗ trợ bạn tốt hơn!","Chúng tôi gặp khó khăn khi xử lý câu hỏi này. Vui lòng để lại số điện thoại để được chuyên gia tư vấn trực tiếp.","Hệ thống chưa thể trả lời câu hỏi của bạn vào lúc này. Bạn có thể nhập số điện thoại để nhận tư vấn từ chuyên gia.","Câu hỏi này cần sự hỗ trợ từ chuyên gia. Vui lòng cung cấp số điện thoại để chúng tôi kết nối bạn với người phù hợp!"]
        stored_phone_responses = ["Chúng tôi đã ghi nhận số điện thoại {phone_number} từ trước. Bạn có muốn sử dụng lại số này không?","Hệ thống đã lưu số {phone_number} của bạn. Vui lòng xác nhận nếu bạn vẫn muốn dùng số này.","Bạn từng cung cấp số {phone_number}. Đây có phải là số bạn muốn tiếp tục sử dụng không?","Số điện thoại {phone_number} đã được lưu trước đó. Bạn có muốn xác nhận sử dụng số này không?","Chúng tôi nhận thấy bạn đã từng nhập số {phone_number}. Vui lòng xác nhận lại số này.","Trước đó bạn đã nhập số {phone_number}. Bạn có muốn tiếp tục dùng số này để liên hệ không?","Hệ thống hiện có số {phone_number} cho bạn. Hãy xác nhận nếu bạn muốn dùng số này.","Bạn muốn tiếp tục sử dụng số {phone_number} mà bạn đã nhập trước đó chứ?","Số {phone_number} đã có trong hệ thống của chúng tôi. Vui lòng xác nhận để sử dụng tiếp.","Bạn đã cung cấp số {phone_number} trước đây. Nếu số này còn đúng, vui lòng xác nhận nhé!"]
        question = input_dict['question']
        phone_number = input_dict['phone_number']
        input_dict['source'] = []
        input_dict['url'] = []
        if phone_number != "":
            input_dict['state'] = "confirm"
            if question not in input_dict['unknown_question']:
                input_dict['unknown_question'].append(question)
            input_dict['response'] = random.choice(system_cannot_answer_templates) + "\n" + random.choice(stored_phone_responses).format(phone_number=phone_number)
        else:
            input_dict['state'] = "require_phone_number"
            if question not in input_dict['unknown_question']:
                input_dict['unknown_question'].append(question)
            input_dict['response'] = random.choice(system_cannot_answer_templates)
        return input_dict
    
    def check_response(self, response):
        # check chinese
        return bool(re.search(r'[\u4e00-\u9fff]', response))
    
    def forward(self, input_dict, max_tokens=1024, max_router=3, max_rewrite=2, pdf_top_k=7, expert_top_k=15):
        self.logger.info("START")
        self.logger.user(f"{input_dict['question']}")
        state = input_dict['state']
        if state == "require_phone_number":
            input_dict = self.require_state(input_dict)
        elif state == "confirm":
            check, input_dict = self.confirm_state(input_dict)
            if check:
                # store question
                self.logger.master_agent("Storing the unknown question with phone number")
                phone_number = input_dict['phone_number']
                unknown_question = input_dict['unknown_question']
                for q in unknown_question:
                    self.save_question(q, phone_number)
                input_dict['unknown_question'] = []
            self.logger.info("END")
            return self.format_output(input_dict)
        
        if state == "normal":
            self.logger.master_agent("Received question from user!")
            question = self.text_parser.Acronym(input_dict["question"])
            needContext = self.needContext(question=question)
            if needContext:
                self.logger.master_agent("This question needs context")
                # Router to find pdf documents
                mistakes = []
                pdf_docs, source_lst, url_lst = "", [], []
                have_pdf = False
                while True:
                    if max_router <= 0:
                        break
                    id = self.router(question=question, description=self.doc_agent.hybrid_search.get_agent_description(mistakes=mistakes))
                    self.logger.master_agent(f"Routing to {id}")
                    check, pdf_docs, source_lst, url_lst = self.doc_agent.pdf_task(id=id, question=question, top_k=pdf_top_k, max_rewrite=max_rewrite)
                    if check:
                        have_pdf = True
                        break
                    mistakes.append(id)
                    max_router -= 1
                
                self.logger.master_agent(f"Find Expert Documents")
                have_expert, expert_docs = self.doc_agent.expert_task(question=question, top_k=expert_top_k)
                documents = ""
                if not have_pdf and not have_expert:
                    self.logger.master_agent(f"Failed to answer! Need the expert's help")
                    self.logger.master_agent(f"Require phone number")
                    input_dict = self.cannot_answer(input_dict)
                else:
                    if have_pdf:
                        documents += pdf_docs + "\n\n"
                        input_dict['source'] = source_lst
                        input_dict['url'] = url_lst
                    if have_expert:
                        documents += expert_docs
                    self.logger.master_agent(f"Generate with context")
                    response = self.answer_with_context(question=question, documents=documents, max_tokens=max_tokens)
                    if self.check_response(response=response):
                        self.logger.master_agent(f"Answer has unsupported language! Failed to answer!")
                        self.logger.master_agent(f"Require phone number! Need the expert's help")
                        input_dict = self.cannot_answer(input_dict)
                    else:
                        input_dict['response'] = response
            else:
                self.logger.master_agent("This question DOES NOT need context")
                self.logger.master_agent("Generate WITHOUT context")
                response = self.answer_without_context(question=question, max_tokens=max_tokens)
                input_dict['response'] = response
                input_dict['source'] = []
                input_dict['url'] = []
            
        self.logger.info("END")
        return self.format_output(input_dict)
                    