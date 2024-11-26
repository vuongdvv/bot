from flask import Flask, render_template, request, jsonify
from datetime import datetime
from neo4j import GraphDatabase
from flask import session

app = Flask(__name__)

app.secret_key = 'do_an_chuyen_nganh'

# kết nối đến CSDl Neo4j
uri = "bolt://localhost:7687"  # Thay bằng URI của Neo4j
username = "neo4j"  # Tên người dùng của Neo4j
password = "12345678"  # Mật khẩu 

driver = GraphDatabase.driver(uri, auth=(username, password))

# Hàm lấy dữ liệu ngành nghề từ Neo4j
def get_career_data():
    query = """
    MATCH (job:Job)-[:REQUIRES]->(skill:skill)
    RETURN job.name AS job_name, 
           collect(skill.name) AS skills, 
           job.salary AS salary, 
           job.schools AS schools, 
           job.admission_combinations AS admission_combinations, 
           job.tuition_fee AS tuition_fee, 
           job.benchmark AS benchmark, 
           job.tuition_fee_free AS tuition_fee_free
    """
    with driver.session() as session:
        result = session.run(query)
        return [record.data() for record in result]

# Đọc dữ liệu ngành nghề từ Neo4j
career_data = get_career_data()

# Rule-based chatbot logic
def chatbot_response(user_input):
    response = "Xin lỗi, tôi chưa hiểu câu hỏi của bạn. Vui lòng thử lại!"

    greetings = ["chào", "hi", "hello", "xin chào", "chào bạn", "hey"]
    for greeting in greetings:
        if greeting in user_input.lower():
            response = "Chào bạn! Tôi có thể giúp gì cho bạn hôm nay?"
            break

    farewells = ["tạm biệt", "good bye", "bye", "chào tạm biệt", "hẹn gặp lại", "farewell"]
    for farewell in farewells:
        if farewell in user_input.lower():
            response = "Tạm biệt!"
            break

    thanks = ["ok", "cảm ơn", "thank you", "thanks", "thanks a lot", "rất cảm ơn", "cảm ơn bạn"]
    for thank in thanks:
        if thank in user_input.lower():
            response = "Rất vui được giúp bạn!"
            break

    # Kiểm tra nếu người dùng đang hỏi về ngành nghề cụ thể
    if 'ngành' in user_input.lower() or any(career["job_name"].lower() in user_input.lower() for career in career_data):
        # Tìm ngành nghề trong câu hỏi
        for career in career_data:
            if career["job_name"].lower() in user_input.lower():
                session['current_career'] = career["job_name"]  # Lưu ngành nghề vào session
                keyword_responses = {
                    "học trường nào": lambda: f"Ngành {career['job_name']} nên học ở: {', '.join(career['schools'])}.",
                    "kỹ năng": lambda: f"Kỹ năng cần thiết cho ngành {career['job_name']} bao gồm: {', '.join(career['skills'])}.",
                    "mức lương": lambda: f"Mức lương trung bình của ngành {career['job_name']} là {career['salary']}.",
                    "học phí": lambda: f"Học phí trung bình của ngành {career['job_name']} là {career['tuition_fee']}.",
                    "tổ hợp xét tuyển": lambda: f"Tổ hợp xét tuyển của ngành {career['job_name']} gồm {', '.join(career['admission_combinations'])}.",
                    "điểm chuẩn": lambda: f"Điểm chuẩn các năm gần đây của ngành {career['job_name']} như sau: {', '.join(career['benchmark'])}" 
                    if "benchmark" in career and career["benchmark"] else "Tôi không có dữ liệu về điểm chuẩn của ngành này."
                }
                for keyword, reply_func in keyword_responses.items():
                    if keyword in user_input.lower():
                        response = reply_func()
                        break
                else:
                    response = f"""
                        Ngành: {career['job_name']}<br>
                        Kỹ năng cần thiết: {', '.join(career['skills'])}<br>
                        Mức lương: {career['salary']}<br>
                        Trường đào tạo: {', '.join(career['schools'])}<br>
                        Tổ hợp xét tuyển: {', '.join(career['admission_combinations'])}<br>
                        Điểm chuẩn các năm gần đây: {', '.join(career['benchmark']) if "benchmark" in career and career["benchmark"] else 'Không có dữ liệu'}<br>
                        Học phí: {career['tuition_fee'] if not career.get('tuition_fee_free', False) else 'Miễn học phí'}
                    """
                break

    # Nếu không có ngành nghề được xác định trong câu hỏi và có ngành trước đó trong session
    elif 'ngành' not in user_input.lower() and 'current_career' in session:
        current_career = session['current_career']
        for career in career_data:
            if career["job_name"].lower() == current_career.lower():
                keyword_responses = {
                    "học trường nào": lambda: f"Ngành {career['job_name']} nên học ở: {', '.join(career['schools'])}.",
                    "kỹ năng": lambda: f"Kỹ năng cần thiết cho ngành {career['job_name']} bao gồm: {', '.join(career['skills'])}.",
                    "mức lương": lambda: f"Mức lương trung bình của ngành {career['job_name']} là {career['salary']}.",
                    "học phí": lambda: f"Học phí trung bình của ngành {career['job_name']} là {career['tuition_fee']}.",
                    "tổ hợp xét tuyển": lambda: f"Tổ hợp xét tuyển của ngành {career['job_name']} gồm {', '.join(career['admission_combinations'])}.",
                    "điểm chuẩn": lambda: f"Điểm chuẩn các năm gần đây của ngành {career['job_name']} như sau: {', '.join(career['benchmark'])}" 
                    if "benchmark" in career and career["benchmark"] else "Tôi không có dữ liệu về điểm chuẩn của ngành này."
                }

                for keyword, reply_func in keyword_responses.items():
                    if keyword in user_input.lower():
                        response = reply_func()
                        break
                break

    return response

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get_response", methods=["POST"])
def get_response():
    user_input = request.form.get("user_input")

    

    response = chatbot_response(user_input)
    # Lấy thời gian hiện tại
    current_time = datetime.now().strftime("%H:%M")
    return jsonify({"response": response, "time": current_time})


if __name__ == "__main__":
    app.run(debug=True, port=5002)
