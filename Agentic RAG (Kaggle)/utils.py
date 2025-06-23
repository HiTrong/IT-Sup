# Import Libs
import re

# text Parser class
class TextParser:
    def __init__(self):
        print("[Text Parser]: Initialize")
    
    def Binary(self, text, true_keywords=['đúng', 'true']):
        for keyword in true_keywords:
            if keyword in text.lower():
                return True
        return False

    def Number(self, text):
        digits = re.findall(r'\d+', text)
        if digits:
            return int(''.join(digits))
        else:
            return -1
    
    def Acronym(self, text):
        # acronym2words = {"t": "Tôi","KLTN": "Khóa luận tốt nghiệp","TLCN": "Tiểu luận chuyên ngành","CTĐT": "Chương trình đào tạo","AV": "Anh văn","NN": "Ngoại ngữ","b": "Bạn","ĐRL": "Điểm rèn luyện","CTXH": "Công tác xã hội","BHYT": "Bảo hiểm y tế","GVHD": "Giảng viên hướng dẫn","HK": "Học kỳ","SV": "Sinh viên","CNTT": "Công nghệ Thông tin","GV": "Giảng viên","TC": "Tín chỉ","NCKH": "Nghiên cứu khoa học","QLKH-QHQT": "Quản lý khoa học và quan hệ quốc tế","TN": "Tốt nghiệp","TS": "Tiến sĩ","PGS.TS.": "Phó giáo sư tiến sĩ","ThS": "Thạc sĩ","HV": "Học viên","NCS": "Nghiên cứu sinh","KHTC": "Kế hoạch tài chính","HSSV": "Học sinh sinh viên","CTSV": "Công tác sinh viên","NV": "Nguyện vọng","CLC": "Chất lượng cao","ĐH": "Đại học","ATTT": "An toàn thông tin","KTDL": "Kỹ thuật dữ liệu","CNPM": "Công nghệ Phần mềm","TTNT": "Trí tuệ nhân tạo","HTTT": "Hệ thống thông tin","BTC": "Ban tổ chức","CCCD": "Căn cước công dân","CĐ": "Cao đẳng","HCMUTE": "Trường Đại học Sư phạm Kỹ thuật thành phố Hồ Chí Minh","IT": "Công nghệ Thông tin","AI": "Trí tuệ nhân tạo","đk": "Đăng ký","xl": "xin lỗi","k": "không","cx": "cũng","hong": "không","a": "anh","e": "em","c": "chị","hk bt": "không biết","hb": "không biết","trang onl": "trang online hcmute","đ": "không","khong": "không","hc": "học","rep": "trả lời","đkmh": "Đăng ký môn học","ib": "nhắn tin","cmt": "bình luận","ad": "admin","pk": "phải không","ko": "không","dc": "được","đc": "được","z": "vậy","ms": "mới","tk": "tài khoản","nh": "ngân hàng","mk": "mật khẩu","bt": "bình thường","kp": "không phải","kb": "kết bạn","qt": "quan trọng","nt": "nhắn tin","r": "rồi","bn": "bao nhiêu","ck": "chuyển khoản","sdt": "số điện thoại","sđt": "số điện thoại","tn": "tin nhắn","mn": "mọi người","gg": "google","lm": "làm","pp": "tạm biệt","kbh": "không bao giờ","bh": "bao giờ","lq": "liên quan","trc": "trước","stt": "trạng thái","qtv": "quản trị viên","chx": "chưa","pt": "phát triển","plz": "làm ơn","bt": "bài tập","cv": "công việc","ppt": "PowerPoint","cty": "công ty","hs": "học sinh","tks": "cảm ơn","h": "giờ","s": "sao","gđ": "gia đình","ph": "phụ huynh","bm": "bố mẹ","ac": "anh chị","lp": "lớp","hp": "học phần","cs": "có","ch": "chưa","dk": "đăng ký"}
        # acronym2words = {'tp.hcm': "thành phố hồ chí minh", 'tphcm': "thành phố hồ chí minh",'tp':"thành phố", 'hcm': "hồ chí minh" ,"t": "tôi","kltn": "khóa luận tốt nghiệp","tlcn": "tiểu luận chuyên ngành","ctđt": "chương trình đào tạo","av": "anh văn","nn": "ngoại ngữ","b": "bạn","đrl": "điểm rèn luyện","ctxh": "công tác xã hội","bhyt": "bảo hiểm y tế","gvhd": "giảng viên hướng dẫn","hk": "học kỳ","sv": "sinh viên","cntt": "công nghệ thông tin","gv": "giảng viên","gv.": "giảng viên","tc": "tín chỉ","nckh": "nghiên cứu khoa học","qlkh-qhqt": "quản lý khoa học và quan hệ quốc tế","tn": "tốt nghiệp","ts.": "tiến sĩ","pgs.": "phó giáo sư","ths.": "thạc sĩ","ks.": "kỹ sư","cn.": "cử nhân","hv": "học viên","ncs": "nghiên cứu sinh","khtc": "kế hoạch tài chính","hssv": "học sinh sinh viên","ctsv": "công tác sinh viên","nv": "nguyện vọng","clc": "chất lượng cao","đh": "đại học","attt": "an toàn thông tin","ktdl": "kỹ thuật dữ liệu","cnpm": "công nghệ phần mềm","ttnt": "trí tuệ nhân tạo","httt": "hệ thống thông tin","btc": "ban tổ chức","cccd": "căn cước công dân","cđ": "cao đẳng","hcmute": "trường đại học sư phạm kỹ thuật thành phố hồ chí minh","it": "công nghệ thông tin","ai": "trí tuệ nhân tạo","đk": "đăng ký","xl": "xin lỗi","k": "không","cx": "cũng","hong": "không","a": "anh","e": "em","c": "chị","hk bt": "không biết","hb": "không biết","trang onl": "trang online hcmute","đ": "không","khong": "không","hc": "học","rep": "trả lời","đkmh": "đăng ký môn học","ib": "nhắn tin","cmt": "bình luận","ad": "admin","pk": "phải không","ko": "không","dc": "được","đc": "được","z": "vậy","ms": "mới","tk": "tài khoản","nh": "ngân hàng","mk": "mật khẩu","bt": "bình thường","kp": "không phải","kb": "kết bạn","qt": "quan trọng","nt": "nhắn tin","r": "rồi","bn": "bao nhiêu","ck": "chuyển khoản","sdt": "số điện thoại","sđt": "số điện thoại","tn": "tin nhắn","mn": "mọi người","gg": "google","lm": "làm","pp": "tạm biệt","kbh": "không bao giờ","bh": "bao giờ","lq": "liên quan","trc": "trước","stt": "số thứ tự","qtv": "quản trị viên","chx": "chưa","pt": "phát triển","plz": "làm ơn","bt": "bài tập","cv": "công việc","ppt": "powerpoint","cty": "công ty","hs": "học sinh","tks": "cảm ơn","h": "giờ","s": "sao","gđ": "gia đình","ph": "phụ huynh","bm": "bố mẹ","ac": "anh chị","lp": "lớp","hp": "học phần","cs": "có","ch": "chưa","dk": "đăng ký","sv": "sinh viên","mhx": "mùa hè xanh","xtn": "xuân tình nguyện","tsmt": "tiếp sức mùa thi","avđr": "anh văn đầu ra","clb": "câu lạc bộ","mit": "mastering it"}
        acronym2words = {'qlkh-qhqt': "quản lý khoa học và quan hệ quốc tế","onl": "trang online hcmute","hcmute": "trường đại học sư phạm kỹ thuật thành phố hồ chí minh",'tp.hcm': "thành phố hồ chí minh","khong": "không",'tphcm': "thành phố hồ chí minh","hk bt": "không biết","kltn": "khóa luận tốt nghiệp","tlcn": "tiểu luận chuyên ngành","ktlt":"kỹ thuật lập trình","csdl":"cơ sở dữ liệu","ctđt": "chương trình đào tạo","ctxh": "công tác xã hội","bhyt": "bảo hiểm y tế","pgs.": "phó giáo sư","ths.": "thạc sĩ","dtcb": "điện tử căn bản","nckh": "nghiên cứu khoa học","gvhd": "giảng viên hướng dẫn","khtc": "kế hoạch tài chính","hssv": "học sinh sinh viên","ctsv": "công tác sinh viên","hong": "không","đkmh": "đăng ký môn học","cccd": "căn cước công dân","tsmt": "tiếp sức mùa thi","avđr": "anh văn đầu ra","attt": "an toàn thông tin","ktdl": "kỹ thuật dữ liệu","cnpm": "công nghệ phần mềm","ttnt": "trí tuệ nhân tạo","httt": "hệ thống thông tin","cntt": "công nghệ thông tin","gv.": "giảng viên","kbh": "không bao giờ","ts.": "tiến sĩ","ncs": "nghiên cứu sinh","clc": "chất lượng cao","sdt": "số điện thoại","sđt": "số điện thoại","btc": "ban tổ chức","anm":"an ninh mạng","mhx": "mùa hè xanh","xtn": "xuân tình nguyện","cmt": "bình luận","tks": "cảm ơn","clb": "câu lạc bộ","mit": "mastering it","plz": "làm ơn",'hcm': "hồ chí minh","ks.": "kỹ sư","rep": "trả lời","cn.": "cử nhân","trc": "trước","stt": "số thứ tự","qtv": "quản trị viên","chx": "chưa","ppt": "powerpoint","cty": "công ty","đrl": "điểm rèn luyện",'tp':"thành phố","hv": "học viên","tn": "tốt nghiệp","nv": "nguyện vọng","đh": "đại học","av": "anh văn","gv": "giảng viên","cđ": "cao đẳng","bn": "bao nhiêu","ck": "chuyển khoản","ib": "nhắn tin","hb": "không biết","đk": "đăng ký","hc": "học","hs": "học sinh","xl": "xin lỗi","tc": "tín chỉ","cx": "cũng","nn": "ngoại ngữ","hk": "học kỳ","mn": "mọi người","gg": "google","gđ": "gia đình","ph": "phụ huynh","bm": "bố mẹ","ac": "anh chị","lp": "lớp","hp": "học phần","cs": "có","ch": "chưa","dk": "đăng ký","sv": "sinh viên","lm": "làm","pp": "tạm biệt","ad": "admin","pk": "phải không","cn":"cử nhân","ko": "không","bt": "bài tập","cv": "công việc","bh": "bao giờ","dc": "được","đc": "được","sv": "sinh viên","ms": "mới","tk": "tài khoản","nh": "ngân hàng","mk": "mật khẩu","pt": "phát triển","bt": "bình thường","kp": "không phải","kb": "kết bạn","lq": "liên quan","qt": "quan trọng","nt": "nhắn tin","t": "tôi","b": "bạn","k": "không","a": "anh","e": "em","c": "chị","đ": "không","z": "vậy","r": "rồi","h": "giờ","s": "sao"}
        words = text.split()
        expanded_text = " ".join([acronym2words.get(word.lower(), word) for word in words])
        text = re.sub(r"[^\w\s]", "", expanded_text)
        words = text.split()
        expanded_text = " ".join([acronym2words.get(word, word) for word in words])
        return expanded_text
    
    def text_to_number(self, text):
        NUMBER_MAP = {
            "một": "1", "hai": "2", "ba": "3", "bốn": "4", "năm": "5", "sáu": "6", 
            "bảy": "7", "tám": "8", "chín": "9", "không": "0"
        }
        for word, num in NUMBER_MAP.items():
            # Chỉ thay thế nếu là từ đứng riêng biệt (dùng \b để tránh trùng lặp với từ khác)
            text = re.sub(rf"\b{word}\b", num, text, flags=re.IGNORECASE)
        return text
    
    def normalize_phone_number(self, text):
        text = self.text_to_number(text)

        # **Thay thế +84 thành 0 trước khi loại dấu câu**
        text = re.sub(r"\+84", "0", text)

        # Loại bỏ dấu câu, giữ lại số
        text = re.sub(r"[^\d]", "", text)

        # Nếu chuỗi bị dư "00" ở đầu (do lỗi "không"), sửa lại thành "0"
        if text.startswith("00"):
            text = text[1:]

        return text 
    
    def contains_valid_vietnam_phone_number(self, text):
        phone = self.normalize_phone_number(text)
        if len(phone) > 10:
            phone = phone[-10:]
        # Regex kiểm tra số điện thoại hợp lệ
        phone_regex = re.compile(r"^(0)(3|5|7|9)\d{8}$")
        return bool(phone_regex.match(phone)), phone
