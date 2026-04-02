from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import os
import sqlite3
from datetime import datetime
from docx import Document

# 导入配置
from config import Config

# 禁用 OneDNN 加速，避免算子冲突
os.environ['FLAGS_use_mkldnn'] = '0'
# 禁用 PIR 新架构，回退到稳定版执行器
os.environ['FLAGS_enable_pir_api'] = '0'

# 导入处理doc文件所需的模块
try:
    import pythoncom
    import win32com.client
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False

try:
    import docx2txt
    DOCX2TXT_AVAILABLE = True
except ImportError:
    DOCX2TXT_AVAILABLE = False

try:
    import olefile
    OLEFILE_AVAILABLE = True
except ImportError:
    OLEFILE_AVAILABLE = False

# 密码验证装饰器
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 如果未启用验证，直接通过
        if not Config.ENABLE_AUTH:
            return f(*args, **kwargs)
        # 检查session中是否有登录状态
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 管理员权限装饰器
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 如果未启用验证，直接通过
        if not Config.ENABLE_AUTH:
            return f(*args, **kwargs)
        # 检查session中是否有登录状态
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        # 检查用户角色是否为管理员
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function



try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

app = Flask(__name__)
# 创建Config实例
config_instance = Config()
# 加载配置
app.config['UPLOAD_FOLDER'] = config_instance.UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = Config.ALLOWED_EXTENSIONS
# 添加session配置
app.config['SECRET_KEY'] = 'document_search_system_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'

# 确保目录存在
Config.ensure_directories()

# 数据库类型
DB_TYPE = 'sqlite'  # 默认使用SQLite

# SQLite数据库配置
DB_PATH = config_instance.DB_PATH

# 初始化数据库
def init_db():
    # 延迟初始化数据库，在安装过程中会手动调用
    global DB_TYPE
    
    # 强制使用SQLite数据库
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 创建分类表
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # 创建文档表
    c.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            issuing_unit TEXT DEFAULT '',
            upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_delete INTEGER DEFAULT 0,
            remark TEXT DEFAULT ''
        )
    ''')
    # 创建文档-分类关联表（实现一对多关系）
    c.execute('''
        CREATE TABLE IF NOT EXISTS document_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(id),
            FOREIGN KEY (category_id) REFERENCES categories(id),
            UNIQUE (document_id, category_id)
        )
    ''')
    # 创建SQLite全文检索表
    c.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS file_content_fts USING fts5(
            content,                -- 全文内容
            file_id,                -- 关联的文档ID
            tokenize=unicode61  -- 使用unicode61分词器
        )
    ''')
    # 创建触发器，在文档删除时同时删除全文检索记录
    c.execute('''
        CREATE TRIGGER IF NOT EXISTS documents_delete_trigger
        AFTER DELETE ON documents
        FOR EACH ROW
        BEGIN
            DELETE FROM file_content_fts WHERE file_id = OLD.id;
        END
    ''')
    
    # 插入默认分类
    c.execute('SELECT COUNT(*) FROM categories')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO categories (name, description) VALUES (?, ?)', ('默认分类', '系统默认分类'))
        conn.commit()
        print("成功插入默认分类")
    
    conn.commit()
    conn.close()
    DB_TYPE = 'sqlite'
    print("使用SQLite数据库")
    return True

# 延迟初始化数据库，在安装过程中会手动调用
# init_db()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']



def extract_text_from_docx(filepath):
    text = ''
    try:
        doc = Document(filepath)
        for paragraph in doc.paragraphs:
            text += paragraph.text + '\n'
    except Exception as e:
        print(f"处理DOCX文件失败: {e}")
    return text

def extract_text_from_doc(filepath):
    text = ''
    try:
        # 尝试使用docx2txt库处理doc文件
        if DOCX2TXT_AVAILABLE:
            text = docx2txt.process(filepath)
        else:
            raise ImportError("docx2txt库未安装")
    except Exception as e:
        print(f"使用docx2txt处理DOC文件失败: {e}")
        # 如果docx2txt失败，尝试使用pywin32（仅Windows）
        try:
            if PYWIN32_AVAILABLE:
                # 初始化COM库
                pythoncom.CoInitialize()
                word = win32com.client.Dispatch('Word.Application')
                word.Visible = False
                doc = word.Documents.Open(filepath)
                text = doc.Content.Text
                doc.Close()
                word.Quit()
                # 释放COM资源
                pythoncom.CoUninitialize()
            else:
                raise ImportError("pywin32库未安装")
        except Exception as e2:
            print(f"使用pywin32处理DOC文件失败: {e2}")
            # 如果pywin32也失败，尝试使用olefile作为最后手段
            try:
                if OLEFILE_AVAILABLE:
                    if olefile.isOleFile(filepath):
                        ole = olefile.OleFileIO(filepath)
                        # 尝试从WordDocument流中提取文本
                        if 'WordDocument' in ole.listdir():
                            # 这里只是简单的实现，实际可能需要更复杂的解析
                            text = "[DOC文件内容]"
                            print("使用olefile成功打开DOC文件")
                else:
                    raise ImportError("olefile库未安装")
            except Exception as e3:
                print(f"使用olefile处理DOC文件失败: {e3}")
    return text

# 从wps_extractor模块导入WPS文件文本提取函数
from wps_extractor import extract_text_from_wps

# 导入Excel文件预览模块
from excel_previewer import convert_excel_to_html
# 导入PDF OCR模块
from pdf_ocr import ocr_pdf_file
# 导入PDF处理模块
from pdf_processor import extract_text_from_pdf

def extract_text_from_txt(filepath):
    text = ''
    try:
        # 尝试使用utf-8编码读取
        with open(filepath, 'r', encoding='utf-8') as file:
            text = file.read()
    except UnicodeDecodeError:
        # 如果utf-8失败，尝试使用gbk编码
        try:
            with open(filepath, 'r', encoding='gbk') as file:
                text = file.read()
        except Exception as e:
            print(f"处理TXT文件失败: {e}")
    except Exception as e:
        print(f"处理TXT文件失败: {e}")
    return text

def extract_text_from_excel(filepath):
    text = ''
    try:
        if filepath.endswith('.xlsx'):
            # 处理xlsx文件
            import openpyxl
            workbook = openpyxl.load_workbook(filepath)
            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                text += f"工作表: {sheet_name}\n"
                # 获取工作表的最大行数和列数
                max_row = sheet.max_row
                max_col = sheet.max_column
                for row in range(1, max_row + 1):
                    row_cells = []
                    for col in range(1, max_col + 1):
                        cell = sheet.cell(row=row, column=col)
                        cell_value = cell.value
                        row_cells.append(str(cell_value) if cell_value is not None else '')
                    # 检查是否有非空单元格
                    if any(cell.strip() for cell in row_cells):
                        row_text = '\t'.join(row_cells)
                        text += row_text + '\n'
                text += '\n'
        elif filepath.endswith('.xls'):
            # 处理xls文件
            try:
                import xlrd
                workbook = xlrd.open_workbook(filepath)
                for sheet_name in workbook.sheet_names():
                    sheet = workbook.sheet_by_name(sheet_name)
                    text += f"工作表: {sheet_name}\n"
                    for row in range(sheet.nrows):
                        row_cells = []
                        for col in range(sheet.ncols):
                            cell_value = sheet.cell_value(row, col)
                            row_cells.append(str(cell_value) if cell_value is not None else '')
                        # 检查是否有非空单元格
                        if any(cell.strip() for cell in row_cells):
                            row_text = '\t'.join(row_cells)
                            text += row_text + '\n'
                    text += '\n'
            except ImportError:
                print("xlrd库未安装，无法处理.xls文件")
                # 尝试使用openpyxl作为备选
                import openpyxl
                workbook = openpyxl.load_workbook(filepath)
                for sheet_name in workbook.sheetnames:
                    sheet = workbook[sheet_name]
                    text += f"工作表: {sheet_name}\n"
                    # 获取工作表的最大行数和列数
                    max_row = sheet.max_row
                    max_col = sheet.max_column
                    for row in range(1, max_row + 1):
                        row_cells = []
                        for col in range(1, max_col + 1):
                            cell = sheet.cell(row=row, column=col)
                            cell_value = cell.value
                            row_cells.append(str(cell_value) if cell_value is not None else '')
                        # 检查是否有非空单元格
                        if any(cell.strip() for cell in row_cells):
                            row_text = '\t'.join(row_cells)
                            text += row_text + '\n'
                    text += '\n'
        print(f"Excel文件提取内容长度: {len(text)}")
        print(f"Excel文件提取内容前200字符: {text[:200]}...")
    except ImportError as e:
        print(f"缺少必要的库: {e}")
    except Exception as e:
        print(f"处理Excel文件失败: {e}")
        # 打印详细的错误信息
        import traceback
        traceback.print_exc()
    return text

def extract_context(text, keyword, max_chars=200):
    # 提取关键词前后的上下文，直到逗号或句号为止
    import re
    if not keyword or not text:
        return []
    
    contexts = []
    
    # 尝试直接匹配关键词
    try:
        # 查找所有关键词出现的位置
        matches = re.finditer(re.escape(keyword), text, re.IGNORECASE)
        
        for match in matches:
            start = match.start()
            end = match.end()
            
            # 向左查找，直到逗号或句号
            left_start = start
            while left_start > 0 and text[left_start-1] not in [',', '，', '.', '。', '!', '！', '?', '？']:
                left_start -= 1
            
            # 向右查找，直到逗号或句号
            right_end = end
            while right_end < len(text) and text[right_end] not in [',', '，', '.', '。', '!', '！', '?', '？']:
                right_end += 1
            
            # 提取上下文
            context = text[left_start:right_end].strip()
            if context:
                contexts.append(context)
    except:
        pass
    
    # 如果直接匹配失败，尝试分词后匹配
    if not contexts:
        try:
            import jieba
            # 对关键词进行分词
            seg_keyword = jieba.cut(keyword)
            seg_keyword_list = list(seg_keyword)
            
            # 对文本进行分词
            seg_text = jieba.cut(text)
            seg_text_list = list(seg_text)
            
            # 查找关键词分词后的匹配位置
            for i in range(len(seg_text_list) - len(seg_keyword_list) + 1):
                if seg_text_list[i:i+len(seg_keyword_list)] == seg_keyword_list:
                    # 构建匹配的分词字符串
                    matched_seg = ' '.join(seg_text_list[i:i+len(seg_keyword_list)])
                    # 在文本中查找这个分词字符串
                    seg_matches = re.finditer(re.escape(matched_seg), text, re.IGNORECASE)
                    for seg_match in seg_matches:
                        start = seg_match.start()
                        end = seg_match.end()
                        
                        # 向左查找，直到逗号或句号
                        left_start = start
                        while left_start > 0 and text[left_start-1] not in [',', '，', '.', '。', '!', '！', '?', '？']:
                            left_start -= 1
                        
                        # 向右查找，直到逗号或句号
                        right_end = end
                        while right_end < len(text) and text[right_end] not in [',', '，', '.', '。', '!', '！', '?', '？']:
                            right_end += 1
                        
                        # 提取上下文
                        context = text[left_start:right_end].strip()
                        if context:
                            contexts.append(context)
        except:
            pass
    
    # 限制数量，不进行去重，确保显示所有关键词出现的句子
    return contexts[:10]  # 最多返回10个上下文

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        role = request.form.get('role')
        # 根据角色验证密码
        if role == 'admin' and password == Config.ADMIN_PASSWORD:
            # 管理员登录成功
            session['logged_in'] = True
            session['user_role'] = role
            return redirect(url_for('index'))
        elif role == 'user' and password == Config.USER_PASSWORD:
            # 用户登录成功
            session['logged_in'] = True
            session['user_role'] = role
            return redirect(url_for('index'))
        else:
            # 密码错误
            return render_template('login.html', message='密码错误，请重试', message_type='error')
    # GET请求，显示登录页面
    return render_template('login.html', message=None, message_type=None)

@app.route('/')
@login_required
def index():
    return render_template('index.html', message=None, message_type=None, user_role=session.get('user_role'))

@app.route('/upload')
@login_required
def upload_page():
    # 获取分类列表
    categories_list = []
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name FROM categories ORDER BY id DESC')
    categories_list = c.fetchall()
    conn.close()
    return render_template('upload.html', message=None, message_type=None, categories=categories_list, user_role=session.get('user_role'))

@app.route('/search')
@login_required
def search():
    # 获取搜索参数
    match = request.args.get('match', '')
    like = request.args.get('like', '')
    category_id = request.args.get('category', '')
    file_type = request.args.get('file_type', '')
    file_name = request.args.get('file_name', '')
    
    # 获取分类列表
    categories = []
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name FROM categories')
    categories = c.fetchall()
    conn.close()
    return render_template('search.html', categories=categories, match=match, like=like, category_id=category_id, file_type=file_type, file_name=file_name, user_role=session.get('user_role'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    print(">>> [调试] 函数 upload_file 开始执行")  # <--- 加在这里
    try:
        # 获取分类列表
        categories_list = []
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, name FROM categories ORDER BY id DESC')
        categories_list = c.fetchall()
        conn.close()
        
        if 'document' not in request.files:
            return render_template('upload.html', message='未上传文件', message_type='error', categories=categories_list)
        
        file = request.files['document']
        
        if file.filename == '':
            return render_template('upload.html', message='未选择文件', message_type='error', categories=categories_list)
        
        if file and allowed_file(file.filename):
            # 按文件类型创建子文件夹
            if file.filename.endswith('.pdf'):
                file_type_folder = 'pdf'
            elif file.filename.endswith('.docx') or file.filename.endswith('.doc'):
                file_type_folder = 'docx'
            elif file.filename.endswith('.wps'):
                file_type_folder = 'wps'
            elif file.filename.endswith('.txt'):
                file_type_folder = 'txt'
            elif file.filename.endswith('.xlsx') or file.filename.endswith('.xls'):
                file_type_folder = 'excel'
            else:
                file_type_folder = 'other'
            upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], file_type_folder)
            
            # 确保子文件夹存在
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            filename = f"{datetime.now().timestamp()}_{file.filename}"
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            
            # 提取文件内容
            content = ''
            content_valid = True

            print(f"=== 开始处理文件: {file.filename} ===")
            is_watermark_file = False


            if file.filename.endswith('.pdf'):
                print("处理PDF文件...")
                # 使用PDF处理模块提取文本
                print(f"调用extract_text_from_pdf: {filepath}")
                content, is_watermark_file, content_valid = extract_text_from_pdf(filepath)
                print(f"PDF处理结果 - 内容长度: {len(content) if content else 0}, 水印文件: {is_watermark_file}, 内容有效: {content_valid}")
            elif file.filename.endswith('.docx'):
                content = extract_text_from_docx(filepath)
            elif file.filename.endswith('.doc'):
                content = extract_text_from_doc(filepath)
            elif file.filename.endswith('.wps'):
                content = extract_text_from_wps(filepath)
                print(f"WPS文件提取内容长度: {len(content)}")
                print(f"WPS文件提取内容前100字符: {content[:100]}...")
                print(f"WPS文件提取内容是否为路径: {'WPS文件:' in content}")
            elif file.filename.endswith('.txt'):
                content = extract_text_from_txt(filepath)
            elif file.filename.endswith('.xlsx') or file.filename.endswith('.xls'):
                content = extract_text_from_excel(filepath)
                print(f"Excel文件提取内容长度: {len(content)}")
                print(f"Excel文件提取内容前100字符: {content[:100]}...")
            
            
            if not content_valid:
                # 删除上传的文件
                if os.path.exists(filepath):
                    os.remove(filepath)
                # 根据是否为水印文件显示不同的错误消息
                if is_watermark_file:
                    error_message = '上传失败：不支持郑政钉或带水印pdf文件'
                else:
                    error_message = '上传失败：无法读取文件内容或文件内容无效'
                return render_template('upload.html', message=error_message, message_type='error', categories=categories_list)
            
            # 获取文件大小
            file_size = os.path.getsize(filepath)
            
            # 获取表单字段
            category_ids_str = request.form.get('category_id', '')
            # 解析逗号分隔的分类ID
            if category_ids_str:
                category_ids = category_ids_str.split(',')
            else:
                # 如果没有选择分类，使用默认分类ID 1
                category_ids = ['1']
            issuing_unit = request.form.get('issuing_unit', '')
            remark = request.form.get('remark', '')
            
            # 插入文档信息到数据库
            # 使用SQLite
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                'INSERT INTO documents (file_name, file_path, file_size, issuing_unit, remark) VALUES (?, ?, ?, ?, ?)',
                (file.filename, filepath, file_size, issuing_unit, remark)
            )
            document_id = c.lastrowid
            
            # 插入文档-分类关联
            for category_id in category_ids:
                c.execute(
                    'INSERT INTO document_categories (document_id, category_id) VALUES (?, ?)',
                    (document_id, category_id)
                )
            
            # 使用jieba分词后插入到全文检索表
            try:
                import jieba
                # 使用jieba进行分词
                seg_list = jieba.cut(content)
                # 将分词结果用空格连接
                seg_content = ' '.join(seg_list)
                c.execute(
                    'INSERT INTO file_content_fts (content, file_id) VALUES (?, ?)',
                    (seg_content, document_id)
                )
            except ImportError:
                # 如果jieba未安装，直接使用原内容
                c.execute(
                    'INSERT INTO file_content_fts (content, file_id) VALUES (?, ?)',
                    (content, document_id)
                )
            
            conn.commit()
            conn.close()
            
            return render_template('upload.html', message='文件上传成功', message_type='success', categories=categories_list)
        else:
            return render_template('upload.html', message='无效的文件类型。仅支持.docx、.doc、.pdf、.wps和.txt格式。', message_type='error', categories=categories_list)
    except Exception as e:
        print(f"上传文件失败: {e}")
        return render_template('upload.html', message=f'上传文件失败: {str(e)}', message_type='error', categories=categories_list)

@app.route('/search-results')
@login_required
def search_results():
    match_query = request.args.get('match')
    like_query = request.args.get('like')
    category_id = request.args.getlist('category')
    file_type = request.args.get('file_type', '')
    file_name = request.args.get('file_name', '')
    
    # 确保至少有一个搜索框有输入
    if not match_query and not like_query and not file_name:
        return redirect(url_for('search'))
    
    # 获取分类映射
    category_map = {}
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name FROM categories')
    for row in c.fetchall():
        category_map[row[0]] = row[1]
    conn.close()
    
    # 使用SQLite进行搜索，支持中文
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 构建查询和参数
    if match_query:
        # 使用FTS5 MATCH操作符进行精确匹配
        where_clauses = ['file_content_fts MATCH ?', 'documents.is_delete = 0']
        params = []
        
        # 使用jieba对搜索词进行分词
        try:
            import jieba
            seg_list = jieba.cut(match_query)
            seg_query = ' '.join(seg_list)
            params.append(seg_query)
        except ImportError:
            # 如果jieba未安装，直接使用原内容
            params.append(match_query)
        
        # 构建JOIN子句和WHERE条件
        join_clauses = 'JOIN file_content_fts ON documents.id = file_content_fts.file_id '
        
        # 添加分类过滤
        if category_id and len(category_id) > 0:
            # 过滤掉空字符串
            category_id = [cid for cid in category_id if cid]
            if category_id:
                # 为每个分类添加一个JOIN子句
                for i, cat_id in enumerate(category_id):
                    try:
                        int(cat_id)
                        join_clauses += f'JOIN document_categories dc{i} ON documents.id = dc{i}.document_id '
                        where_clauses.append(f'dc{i}.category_id = ?')
                        params.append(cat_id)
                    except ValueError:
                        pass
        
        # 添加文件类型过滤
        if file_type:
            where_clauses.append('documents.file_name LIKE ?')
            params.append('%' + file_type)
        
        # 添加文件名过滤
        if file_name:
            where_clauses.append('documents.file_name LIKE ?')
            params.append('%' + file_name + '%')
        
        # 构建SQL语句
        sql = '''
            SELECT DISTINCT documents.* 
            FROM documents 
            ''' + join_clauses + '''
            WHERE ''' + ' AND '.join(where_clauses) + ''' 
            ORDER BY documents.upload_time DESC
        '''
        
        c.execute(sql, params)
        query = match_query
    else:
        # 使用LIKE操作符进行模糊匹配
        where_clauses = ['documents.is_delete = 0']
        params = []
        
        # 添加内容搜索
        if like_query:
            where_clauses.append('file_content_fts.content LIKE ?')
            # 对搜索词进行分词处理
            try:
                import jieba
                seg_list = jieba.cut(like_query)
                seg_query = ' '.join(seg_list)
                # 构建LIKE查询参数
                like_param = '%' + seg_query + '%'
            except ImportError:
                # 如果jieba未安装，直接使用原内容
                like_param = '%' + like_query + '%'
            params.append(like_param)
        
        # 构建JOIN子句和WHERE条件
        join_clauses = 'JOIN file_content_fts ON documents.id = file_content_fts.file_id '
        
        # 添加分类过滤
        if category_id and len(category_id) > 0:
            # 过滤掉空字符串
            category_id = [cid for cid in category_id if cid]
            if category_id:
                # 为每个分类添加一个JOIN子句
                for i, cat_id in enumerate(category_id):
                    try:
                        int(cat_id)
                        join_clauses += f'JOIN document_categories dc{i} ON documents.id = dc{i}.document_id '
                        where_clauses.append(f'dc{i}.category_id = ?')
                        params.append(cat_id)
                    except ValueError:
                        pass
        
        # 添加文件类型过滤
        if file_type:
            where_clauses.append('documents.file_name LIKE ?')
            params.append('%' + file_type)
        
        # 添加文件名过滤
        if file_name:
            where_clauses.append('documents.file_name LIKE ?')
            params.append('%' + file_name + '%')
        
        # 构建SQL语句
        sql = '''
            SELECT DISTINCT documents.* 
            FROM documents 
            ''' + join_clauses + '''
            WHERE ''' + ' AND '.join(where_clauses) + ''' 
            ORDER BY documents.upload_time DESC
        '''
        
        c.execute(sql, params)
        query = like_query
    results = c.fetchall()
    conn.close()
    
    # 转换结果为字典列表
    results_list = []
    for result in results:
        # 获取文档的分类
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT category_id FROM document_categories WHERE document_id = ?', (result[0],))
        category_ids = [row[0] for row in c.fetchall()]
        conn.close()
        
        # 获取第一个分类名称
        category_name = '未知分类'
        if category_ids:
            category_name = category_map.get(category_ids[0], '未知分类')
        
        results_list.append({
            'id': result[0],
            'filename': result[1],
            'filepath': result[2],
            'filetype': category_name,
            'upload_date': result[5]
        })
    
    return render_template('search-results.html', query=query, results=results_list, match_query=match_query, like_query=like_query, category_id=category_id, file_type=file_type, file_name=file_name)

# 分类管理路由
@app.route('/categories')
@login_required
def categories():
    # 获取搜索参数
    search = request.args.get('search', '')
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页显示10条记录
    offset = (page - 1) * per_page
    
    # 构建查询条件
    where_clause = ''
    params = []
    
    if search:
        where_clause = 'WHERE name LIKE ?'
        params.append(f'%{search}%')
    
    # 获取总记录数
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    count_sql = f'SELECT COUNT(*) FROM categories {where_clause}'
    c.execute(count_sql, params)
    total = c.fetchone()[0]
    # 获取分页数据
    query_sql = f'SELECT * FROM categories {where_clause} ORDER BY id DESC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])
    c.execute(query_sql, params)
    categories_list = c.fetchall()
    conn.close()
    
    # 计算总页数
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('categories.html', categories=categories_list, page=page, total_pages=total_pages, per_page=per_page, search=search, user_role=session.get('user_role'))

@app.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO categories (name, description) VALUES (?, ?)', (name, description))
        conn.commit()
        conn.close()
        
        return redirect(url_for('categories'))
    
    return render_template('add-category.html')

@app.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE categories SET name = ?, description = ? WHERE id = ?', (name, description, id))
        conn.commit()
        conn.close()
        
        return redirect(url_for('categories'))
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM categories WHERE id = ?', (id,))
    category = c.fetchone()
    conn.close()
    
    return render_template('edit-category.html', category=category)

@app.route('/categories/delete/<int:id>')
@login_required
def delete_category(id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM categories WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('categories'))

@app.route('/files/delete/<int:id>')
@login_required
def delete_file(id):
    # 获取来源页面和搜索参数
    from_page = request.args.get('from', '')
    match_keyword = request.args.get('match', '')
    like_keyword = request.args.get('like', '')
    category_id = request.args.get('category', '')
    
    # 真数据库删除，同时删除相关的关联数据
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 获取文件路径，用于删除物理文件
    c.execute('SELECT file_path FROM documents WHERE id = ?', (id,))
    file_path = c.fetchone()
    
    # 删除关联的分类关系
    c.execute('DELETE FROM document_categories WHERE document_id = ?', (id,))
    # 删除全文检索记录
    c.execute('DELETE FROM file_content_fts WHERE file_id = ?', (id,))
    # 删除文档记录
    c.execute('DELETE FROM documents WHERE id = ?', (id,))
    
    conn.commit()
    conn.close()
    
    # 移动文件到is delete文件夹，而不是删除
    if file_path and file_path[0]:
        try:
            import os
            if os.path.exists(file_path[0]):
                # 获取文件所在的上一级文件夹
                file_dir = os.path.dirname(file_path[0])
                parent_dir = os.path.dirname(file_dir)
                # 构建is delete文件夹路径
                delete_dir = os.path.join(parent_dir, 'is delete')
                # 如果is delete文件夹不存在，创建它
                if not os.path.exists(delete_dir):
                    os.makedirs(delete_dir)
                    print(f"创建is delete文件夹: {delete_dir}")
                # 构建目标文件路径
                file_name = os.path.basename(file_path[0])
                dest_path = os.path.join(delete_dir, file_name)
                # 移动文件
                os.rename(file_path[0], dest_path)
                print(f"已移动文件到: {dest_path}")
        except Exception as e:
            print(f"移动文件失败: {e}")
    
    # 根据来源页面进行不同的重定向
    if from_page == 'search':
        return redirect(url_for('merged_search', match=match_keyword, like=like_keyword, category=category_id))
    else:
        return redirect(url_for('file_list'))

# 文件列表路由
@app.route('/file-list')
@login_required
def file_list():
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页显示10条记录
    offset = (page - 1) * per_page
    
    # 获取总记录数
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM documents WHERE is_delete = 0')
    total = c.fetchone()[0]
    # 获取分页数据，使用JOIN获取文档及其分类
    c.execute('''
        SELECT d.*, c.name as category_name 
        FROM documents d
        LEFT JOIN document_categories dc ON d.id = dc.document_id
        LEFT JOIN categories c ON dc.category_id = c.id
        WHERE d.is_delete = 0 
        ORDER BY d.upload_time DESC 
        LIMIT ? OFFSET ?
    ''', (per_page, offset))
    files = c.fetchall()
    conn.close()
    
    # 计算总页数
    total_pages = (total + per_page - 1) // per_page
    
    # 转换文件大小为友好格式
    def format_file_size(size):
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        else:
            return f"{size / (1024 * 1024):.2f} MB"
    
    # 转换结果为字典列表
    files_list = []
    for file in files:
        # 处理分类名称
        category_name = file[9] if file[9] else '未分类'
        print(f"分类名称: {category_name}")
        # 处理上传时间
        upload_date = file[5]
        if isinstance(upload_date, str):
            # 尝试解析字符串格式的日期
            try:
                upload_date = datetime.strptime(upload_date, '%Y-%m-%d %H:%M:%S')
            except:
                pass
        # 格式化日期
        if hasattr(upload_date, 'strftime'):
            upload_date_str = upload_date.strftime('%Y-%m-%d %H:%M')
        else:
            upload_date_str = str(upload_date)
        # 处理发文单位
        issuing_unit = file[4] if file[4] else ''
        # 处理备注
        remark = file[8] if file[8] else ''
        files_list.append({
            'id': file[0],
            'filename': file[1],
            'filepath': file[2],
            'file_size': format_file_size(file[3]),
            'filetype': category_name,
            'upload_date': upload_date_str,
            'issuing_unit': issuing_unit,
            'remark': remark
        })
    
    return render_template('file-list.html', files=files_list, page=page, total_pages=total_pages, per_page=per_page, user_role=session.get('user_role'))

# 系统设置路由
@app.route('/merged-search')
@login_required
def merged_search():
    # 获取搜索参数
    match_keyword = request.args.get('match', '')
    like_keyword = request.args.get('like', '')
    category_ids = request.args.getlist('category')
    file_type = request.args.get('file_type', '')
    file_name = request.args.get('file_name', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页显示10条记录
    offset = (page - 1) * per_page
    
    # 使用关键词作为搜索词
    search_term = match_keyword if match_keyword else like_keyword
    
    print(f"Search parameters: match_keyword='{match_keyword}', like_keyword='{like_keyword}', category_ids='{category_ids}', file_type='{file_type}', file_name='{file_name}', page={page}")
    
    # 获取分类列表
    categories = []
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name FROM categories')
    categories = c.fetchall()
    conn.close()
    
    # 构建查询语句
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 构建WHERE子句
    where_clause = 'WHERE d.is_delete = 0'
    params = []
    
    if search_term:
        # 根据用户选择的搜索类型执行不同的搜索策略
        if match_keyword:
            # 使用FTS5 MATCH操作符进行精确匹配
            where_clause += ' AND d.id IN (SELECT file_id FROM file_content_fts WHERE file_content_fts MATCH ?)'
            # 使用jieba对搜索词进行分词
            try:
                import jieba
                seg_list = jieba.cut(match_keyword)
                seg_keyword = ' '.join(seg_list)
                params.append(seg_keyword)
            except ImportError:
                # 如果jieba未安装，直接使用原内容
                params.append(match_keyword)
        else:
            # 使用LIKE操作符进行模糊匹配
            where_clause += ' AND d.id IN (SELECT file_id FROM file_content_fts WHERE content LIKE ?)'
            # 对搜索词进行分词处理
            try:
                import jieba
                seg_list = jieba.cut(like_keyword)
                seg_term = ' '.join(seg_list)
                # 构建LIKE查询参数，在分词后的搜索词前后添加%通配符
                like_param = '%' + seg_term + '%'
            except ImportError:
                # 如果jieba未安装，直接使用原内容
                like_param = '%' + like_keyword + '%'
            params.append(like_param)
    
    # 添加文件类型过滤
    if file_type:
        where_clause += ' AND d.file_name LIKE ?'
        params.append('%' + file_type)
    
    # 添加文件名过滤
    if file_name:
        where_clause += ' AND d.file_name LIKE ?'
        params.append('%' + file_name + '%')
    
    if category_ids and len(category_ids) > 0:
        try:
            # 过滤掉空字符串
            category_ids = [cid for cid in category_ids if cid]
            if category_ids:
                # 构建分类AND条件 - 文件必须包含所有选中的分类
                for cid in category_ids:
                    try:
                        cat_id = int(cid)
                        where_clause += ' AND d.id IN (SELECT document_id FROM document_categories WHERE category_id = ?)'
                        params.append(cat_id)
                        print(f"Added category filter: {cat_id}")
                    except ValueError:
                        print(f"Invalid category_id: {cid}")
        except Exception as e:
            # 处理异常，忽略分类过滤
            print(f"处理分类参数时出错: {e}")
            pass
    
    # 获取总记录数
    count_sql = f'''SELECT COUNT(*) FROM documents d
                  {where_clause}'''
    print(f"Count SQL: {count_sql}")
    print(f"Count params: {params}")
    c.execute(count_sql, params)
    total = c.fetchone()[0]
    print(f"Total records: {total}")
    
    # 获取分页数据
    sql = f'''
        SELECT d.*, MAX(c.name) as category_name 
        FROM documents d
        LEFT JOIN document_categories dc ON d.id = dc.document_id
        LEFT JOIN categories c ON dc.category_id = c.id
        {where_clause}
        GROUP BY d.id
        ORDER BY d.upload_time DESC 
        LIMIT ? OFFSET ?
    '''
    params.extend([per_page, offset])
    print(f"Query SQL: {sql}")
    print(f"Query params: {params}")
    c.execute(sql, params)
    files = c.fetchall()
    print(f"Found {len(files)} files")
    
    # 对于关键词搜索(MATCH)，需要在应用层检查是否包含完整的搜索词组
    if match_keyword:
        filtered_files = []
        for file in files:
            # 从file_content_fts表中获取文件内容
            c.execute('SELECT content FROM file_content_fts WHERE file_id = ?', (file[0],))
            content_result = c.fetchone()
            if content_result and content_result[0]:
                # 获取分词后的内容
                seg_content = content_result[0]
                # 将分词后的内容还原为原始内容（去除空格）
                original_content = seg_content.replace(' ', '')
                # 检查搜索词是否作为完整词组存在
                if match_keyword in original_content:
                    filtered_files.append(file)
        files = filtered_files
        print(f"Filtered files: {len(files)}")
    
    conn.close()
    
    # 计算总页数（如果是关键词搜索且有过滤，使用过滤后的数量）
    if match_keyword:
        total = len(files)
    total_pages = (total + per_page - 1) // per_page
    
    # 转换文件大小为友好格式
    def format_file_size(size):
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        else:
            return f"{size / (1024 * 1024):.2f} MB"
    
    # 转换结果为字典列表
    files_list = []
    for file in files:
        # 处理上传时间
        upload_date = file[5]
        if isinstance(upload_date, str):
            # 尝试解析字符串格式的日期
            try:
                upload_date = datetime.strptime(upload_date, '%Y-%m-%d %H:%M:%S')
            except:
                pass
        # 格式化日期
        if hasattr(upload_date, 'strftime'):
            upload_date_str = upload_date.strftime('%Y-%m-%d %H:%M')
        else:
            upload_date_str = str(upload_date)
        # 处理发文单位
        issuing_unit = file[4] if file[4] else ''
        # 处理备注
        remark = file[8] if file[8] else ''
        
        # 获取文档的所有分类
        file_categories = []
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT c.id, c.name FROM document_categories dc JOIN categories c ON dc.category_id = c.id WHERE dc.document_id = ?', (file[0],))
        file_categories = c.fetchall()
        conn.close()
        
        # 提取关键词上下文
        contexts = []
        if search_term:
            # 从file_content_fts表中获取文件内容
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT content FROM file_content_fts WHERE file_id = ?', (file[0],))
            content_result = c.fetchone()
            conn.close()
            
            if content_result and content_result[0]:
                # 获取分词后的内容
                seg_content = content_result[0]
                # 将分词后的内容还原为原始内容（去除空格）
                original_content = seg_content.replace(' ', '')
                
                # 提取上下文
                contexts = extract_context(original_content, search_term)
                
                # 对关键词进行加亮处理
                highlighted_contexts = []
                for context in contexts:
                    # 使用HTML标签对关键词进行加亮
                    highlighted_context = context
                    # 直接匹配原始搜索词
                    try:
                        import re
                        highlighted_context = re.sub(re.escape(search_term), f'<span class="highlight">{search_term}</span>', highlighted_context, flags=re.IGNORECASE)
                    except:
                        pass
                    highlighted_contexts.append(highlighted_context)
                contexts = highlighted_contexts
        
        # 获取文件所在文件夹路径
        import os
        file_folder = os.path.dirname(file[2])
        # 检查文件是否存在
        file_exists = os.path.exists(file[2])
        
        files_list.append({
            'id': file[0],
            'filename': file[1],
            'filepath': file[2],
            'file_folder': file_folder,
            'file_exists': file_exists,
            'file_size': format_file_size(file[3]),
            'categories': file_categories,
            'upload_date': upload_date_str,
            'issuing_unit': issuing_unit,
            'remark': remark,
            'contexts': contexts
        })
    
    return render_template('merged-search.html', files=files_list, page=page, total_pages=total_pages, per_page=per_page, categories=categories, match_keyword=match_keyword, like_keyword=like_keyword, category_ids=category_ids, file_type=file_type, file_name=file_name, user_role=session.get('user_role'))

@app.route('/get-document-categories/<int:file_id>')
@login_required
def get_document_categories(file_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT c.id, c.name FROM document_categories dc JOIN categories c ON dc.category_id = c.id WHERE dc.document_id = ?', (file_id,))
    categories = c.fetchall()
    conn.close()
    
    # 转换为字典列表
    result = []
    for category in categories:
        result.append({'id': category[0], 'name': category[1]})
    
    return jsonify(result)

@app.route('/api/categories')
@login_required
def api_categories():
    """获取所有分类的API"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name FROM categories ORDER BY id')
    categories = c.fetchall()
    conn.close()
    
    # 转换为字典列表
    result = []
    for category in categories:
        result.append({'id': category[0], 'name': category[1]})
    
    return jsonify(result)

@app.route('/update-document-categories', methods=['POST'])
@login_required
def update_document_categories():
    data = request.get_json()
    file_id = data.get('file_id')
    category_ids = data.get('category_ids', [])
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # 删除现有关联
        c.execute('DELETE FROM document_categories WHERE document_id = ?', (file_id,))
        
        # 添加新关联
        for category_id in category_ids:
            c.execute('INSERT INTO document_categories (document_id, category_id) VALUES (?, ?)', (file_id, category_id))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"更新分类失败: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/test-pdf-processing')
@login_required
def test_pdf_processing():
    """
    测试PDF处理功能和日志输出
    """
    test_pdf_path = 'c:\\Users\\ADMIN\\Documents\\trae_projects\\word_wearch\\test.pdf'
    print(f"=== 测试PDF处理: {test_pdf_path} ===")
    
    from pdf_processor import extract_text_from_pdf
    content, is_watermark_file, content_valid = extract_text_from_pdf(test_pdf_path)
    
    print(f"测试结果:")
    print(f"内容长度: {len(content) if content else 0}")
    print(f"是否为水印文件: {is_watermark_file}")
    print(f"内容是否有效: {content_valid}")
    print(f"提取的内容: {content}")
    
    return f"PDF处理测试完成，查看终端日志和日志文件以获取详细信息。"

@app.route('/open-file-location/<int:file_id>')
@admin_required
def open_file_location(file_id):
    # 根据文件ID获取文件路径
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT file_path FROM documents WHERE id = ?', (file_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        file_path = result[0]
        # 确保路径使用反斜杠，符合Windows格式
        file_path = file_path.replace('/', '\\')
        # 在Windows系统中，使用explorer.exe打开文件夹并选定文件
        import subprocess
        try:
            # 使用explorer.exe /select命令打开文件夹并选定文件
            # 正确的命令格式是: explorer.exe /select,"文件路径"
            command = f'explorer.exe /select,"{file_path}"'
            subprocess.run(command, shell=True)
            return '文件位置已打开'
        except Exception as e:
            print(f"打开文件位置失败: {e}")
            return '打开文件位置失败'
    else:
        return '文件不存在'

@app.route('/download-file/<int:file_id>')
@login_required
def download_file(file_id):
    # 根据文件ID获取文件路径和文件名
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT file_path, file_name FROM documents WHERE id = ?', (file_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        file_path, file_name = result
        # 检查文件是否存在
        import os
        if os.path.exists(file_path):
            # 使用Flask的send_file函数发送文件
            from flask import send_file
            try:
                return send_file(file_path, as_attachment=True, download_name=file_name)
            except Exception as e:
                print(f"下载文件失败: {e}")
                return '下载文件失败'
        else:
            return '该文件未存储'
    else:
        return '文件不存在'

@app.route('/download-excel/<int:file_id>')
@login_required
def download_excel(file_id):
    """
    下载Excel文件（用于预览）
    """
    # 根据文件ID获取文件路径和文件名
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT file_path, file_name FROM documents WHERE id = ?', (file_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        file_path, file_name = result
        # 检查文件是否存在
        import os
        if os.path.exists(file_path):
            # 使用Flask的send_file函数发送文件
            from flask import send_file, jsonify
            try:
                return send_file(file_path, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            except Exception as e:
                print(f"下载Excel文件失败: {e}")
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify({'error': '文件不存在'}), 404
    else:
        return jsonify({'error': '文件不存在'}), 404

@app.route('/view-file/<int:file_id>')
@login_required
def view_file(file_id):
    # 根据文件ID获取文件路径、文件名和其他信息
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT file_path, file_name, file_size, upload_time FROM documents WHERE id = ?', (file_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        file_path, file_name, file_size, upload_time = result
        # 检查文件是否存在
        import os
        if os.path.exists(file_path):
            # 确定文件扩展名
            file_ext = os.path.splitext(file_name)[1].lower().lstrip('.')
            
            # 确定MIME类型
            mime_type = 'application/octet-stream'  # 默认MIME类型
            if file_ext == 'pdf':
                mime_type = 'application/pdf'
            elif file_ext in ['doc', 'docx']:
                mime_type = 'application/msword' if file_ext == 'doc' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif file_ext == 'wps':
                mime_type = 'application/vnd.ms-works'
            elif file_ext == 'txt':
                mime_type = 'text/plain'
            
            # 格式化文件大小
            def format_file_size(size):
                if size < 1024:
                    return f"{size} B"
                elif size < 1024 * 1024:
                    return f"{size / 1024:.2f} KB"
                else:
                    return f"{size / (1024 * 1024):.2f} MB"
            
            # 格式化上传时间
            if isinstance(upload_time, str):
                upload_time_str = upload_time
            else:
                upload_time_str = upload_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # 尝试在后端将Word、WPS和Excel文件转换为HTML
            word_html = None
            if file_ext in ['doc', 'docx', 'wps']:
                try:
                    import mammoth
                    with open(file_path, 'rb') as f:
                        result = mammoth.convert_to_html(f)
                        word_html = result.value
                    print(f"{file_ext.upper()}文件转换成功")
                except Exception as e:
                    print(f"{file_ext.upper()}文件转换失败: {e}")
                    # 尝试使用文本提取作为备用
                    try:
                        if file_ext == 'wps':
                            text = extract_text_from_wps(file_path)
                        elif file_ext == 'doc':
                            text = extract_text_from_doc(file_path)
                        elif file_ext == 'docx':
                            text = extract_text_from_docx(file_path)
                        if text:
                            # 将文本转换为简单的HTML
                            word_html = f"<pre>{text}</pre>"
                            print(f"{file_ext.upper()}文件文本提取成功并转换为HTML")
                    except Exception as e2:
                        print(f"{file_ext.upper()}文件文本提取失败: {e2}")
            elif file_ext in ['xlsx', 'xls']:
                # 处理Excel文件
                try:
                    word_html = convert_excel_to_html(file_path, file_id)
                    print(f"{file_ext.upper()}文件转换成功")
                except Exception as e:
                    print(f"{file_ext.upper()}文件转换失败: {e}")
                    # 尝试使用文本提取作为备用
                    try:
                        text = extract_text_from_excel(file_path)
                        if text:
                            # 将文本转换为简单的HTML
                            word_html = f"<pre>{text}</pre>"
                            print(f"{file_ext.upper()}文件文本提取成功并转换为HTML")
                    except Exception as e2:
                        print(f"{file_ext.upper()}文件文本提取失败: {e2}")
            
            # 渲染模板
            return render_template('view-file.html', 
                               file_name=file_name, 
                               file_size=format_file_size(file_size), 
                               upload_time=upload_time_str, 
                               file_id=file_id, 
                               file_ext=file_ext, 
                               mime_type=mime_type,
                               word_html=word_html)
        else:
            return '该文件未存储'
    else:
        return '文件不存在'

@app.route('/get-file/<int:file_id>')
@login_required
def get_file(file_id):
    # 根据文件ID获取文件路径和文件名
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT file_path, file_name FROM documents WHERE id = ?', (file_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        file_path, file_name = result
        # 检查文件是否存在
        import os
        if os.path.exists(file_path):
            # 确定文件扩展名
            file_ext = os.path.splitext(file_name)[1].lower().lstrip('.')
            
            # 确定MIME类型
            mime_type = 'application/octet-stream'  # 默认MIME类型
            if file_ext == 'pdf':
                mime_type = 'application/pdf'
            elif file_ext == 'doc':
                mime_type = 'application/msword'
            elif file_ext == 'docx':
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif file_ext == 'wps':
                mime_type = 'application/vnd.ms-works'
            elif file_ext == 'txt':
                mime_type = 'text/plain'
            
            # 使用Flask的send_file函数发送文件
            from flask import send_file
            try:
                return send_file(file_path, as_attachment=False, mimetype=mime_type)
            except Exception as e:
                print(f"发送文件失败: {e}")
                return '发送文件失败'
        else:
            return '该文件未存储'
    else:
        return '文件不存在'

@app.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    if request.method == 'POST':
        # 打印表单数据
        print('表单数据:', request.form)
        
        upload_folder = request.form.get('upload_folder')
        print('接收到的上传目录:', upload_folder)
        
        # 规范化路径，处理反斜杠问题
        upload_folder = os.path.normpath(upload_folder)
        print('规范化后的上传目录:', upload_folder)
        
        # 确保目录存在
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        # 更新上传目录
        app.config['UPLOAD_FOLDER'] = upload_folder
        print('更新后的上传目录:', app.config['UPLOAD_FOLDER'])
        
        # 保存设置
        print('UPLOAD_FOLDER更新成功:', upload_folder)
        
        return render_template('settings.html', upload_folder=upload_folder, message='设置保存成功', message_type='success')
    
    return render_template('settings.html', upload_folder=app.config['UPLOAD_FOLDER'])

if __name__ == '__main__':
    # 初始化数据库
    init_db()
    app.run(debug=True, port=3000)
