from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import sqlite3
from datetime import datetime
import PyPDF2
from docx import Document
import pytesseract
from PIL import Image
import pdf2image
import tempfile

# 导入配置
from config import Config

try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

app = Flask(__name__)
# 加载配置
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = Config.ALLOWED_EXTENSIONS

# 确保上传目录存在
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 数据库类型
DB_TYPE = 'sqlite'  # 默认使用SQLite

# MySQL数据库配置
DB_CONFIG = Config.DB_CONFIG

# 初始化数据库
def init_db():
    global DB_TYPE
    
    # 强制使用SQLite数据库
    conn = sqlite3.connect('documents.db')
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

init_db()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_text_from_pdf(filepath):
    text = ''
    # 尝试使用PyPDF2提取文本
    with open(filepath, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page_text = page.extract_text()
            if page_text:
                text += page_text
    
    # 如果没有提取到文本，尝试使用OCR
    if not text.strip():
        try:
            # 检查tesseract是否可用
            import subprocess
            subprocess.run(['tesseract', '--version'], capture_output=True, check=True)
            # 检查poppler是否可用
            subprocess.run(['pdfinfo', '--version'], capture_output=True, check=True)
            
            # 将PDF转换为图像
            images = pdf2image.convert_from_path(filepath)
            for image in images:
                # 使用OCR提取文本
                ocr_text = pytesseract.image_to_string(image, lang='chi_sim')
                text += ocr_text
            print("OCR处理成功")
        except subprocess.CalledProcessError:
            print("OCR依赖未安装: tesseract或poppler不在系统PATH中")
        except Exception as e:
            print(f"OCR处理失败: {e}")
    
    return text

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
        # 使用antiword或其他工具处理doc文件
        # 这里使用一个简单的方法，实际生产环境可能需要更复杂的处理
        import subprocess
        result = subprocess.run(['antiword', filepath], capture_output=True, text=True)
        text = result.stdout
    except Exception as e:
        print(f"处理DOC文件失败: {e}")
        # 如果antiword不可用，尝试使用python-docx的扩展
        try:
            from docx import Document
            doc = Document(filepath)
            for paragraph in doc.paragraphs:
                text += paragraph.text + '\n'
        except Exception as e2:
            print(f"尝试使用python-docx处理DOC文件失败: {e2}")
    return text

def extract_text_from_wps(filepath):
    text = ''
    try:
        # 使用pywpsrpc库处理wps文件
        from pywpsrpc import WpsRpcClient
        from pywpsrpc.app import wps
        
        client = WpsRpcClient()
        app = client.getWpsApplication()
        doc = app.Documents.Open(filepath)
        text = doc.Content.Text
        doc.Close()
        app.Quit()
    except Exception as e:
        print(f"处理WPS文件失败: {e}")
    return text

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

@app.route('/')
def index():
    return render_template('index.html', message=None, message_type=None)

@app.route('/upload')
def upload_page():
    # 获取分类列表
    categories_list = []
    conn = sqlite3.connect('documents.db')
    c = conn.cursor()
    c.execute('SELECT id, name FROM categories ORDER BY id DESC')
    categories_list = c.fetchall()
    conn.close()
    return render_template('upload.html', message=None, message_type=None, categories=categories_list)

@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'document' not in request.files:
        return render_template('index.html', message='No file uploaded', message_type='error')
    
    file = request.files['document']
    
    if file.filename == '':
        return render_template('upload.html', message='No file selected', message_type='error')
    
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
        if file.filename.endswith('.pdf'):
            content = extract_text_from_pdf(filepath)
        elif file.filename.endswith('.docx'):
            content = extract_text_from_docx(filepath)
        elif file.filename.endswith('.doc'):
            content = extract_text_from_doc(filepath)
        elif file.filename.endswith('.wps'):
            content = extract_text_from_wps(filepath)
        elif file.filename.endswith('.txt'):
            content = extract_text_from_txt(filepath)
        
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
        conn = sqlite3.connect('documents.db')
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
        if content:
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
        
        return render_template('upload.html', message='File uploaded successfully', message_type='success')
    else:
        return render_template('upload.html', message='Invalid file type. Only .docx and .pdf are allowed.', message_type='error')

@app.route('/search-results')
def search_results():
    query = request.args.get('q')
    if not query:
        return redirect(url_for('search'))
    
    # 获取分类映射
    category_map = {}
    conn = sqlite3.connect('documents.db')
    c = conn.cursor()
    c.execute('SELECT id, name FROM categories')
    for row in c.fetchall():
        category_map[row[0]] = row[1]
    conn.close()
    
    # 使用SQLite进行搜索，支持中文
    conn = sqlite3.connect('documents.db')
    c = conn.cursor()
    
    # 根据搜索词长度和是否包含标点符号选择不同的搜索策略
    has_punctuation = any(p in query for p in [',', '，', '.', '。', '!', '！', '?', '？', '；', ':', '：'])
    is_long_sentence = len(query) > 20
    
    if has_punctuation or is_long_sentence:
        # 对于长句子或包含标点符号的搜索词，使用LIKE操作符
        sql = '''
            SELECT DISTINCT documents.* 
            FROM documents 
            JOIN file_content_fts ON documents.id = file_content_fts.file_id 
            WHERE file_content_fts.content LIKE ? AND documents.is_delete = 0 
            ORDER BY documents.upload_time DESC
        '''
        # 对搜索词进行分词处理
        try:
            import jieba
            seg_list = jieba.cut(query)
            seg_query = ' '.join(seg_list)
            # 构建LIKE查询参数
            like_param = '%' + seg_query + '%'
        except ImportError:
            # 如果jieba未安装，直接使用原内容
            like_param = '%' + query + '%'
        c.execute(sql, (like_param,))
    else:
        # 对于短关键词，使用FTS5 MATCH操作符（性能更好）
        sql = '''
            SELECT DISTINCT documents.* 
            FROM documents 
            JOIN file_content_fts ON documents.id = file_content_fts.file_id 
            WHERE file_content_fts MATCH ? AND documents.is_delete = 0 
            ORDER BY documents.upload_time DESC
        '''
        # 使用jieba对搜索词进行分词
        try:
            import jieba
            seg_list = jieba.cut(query)
            seg_query = ' '.join(seg_list)
            c.execute(sql, (seg_query,))
        except ImportError:
            # 如果jieba未安装，直接使用原内容
            c.execute(sql, (query,))
    results = c.fetchall()
    conn.close()
    
    # 转换结果为字典列表
    results_list = []
    for result in results:
        # 获取文档的分类
        conn = sqlite3.connect('documents.db')
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
    
    return render_template('search-results.html', query=query, results=results_list)

# 分类管理路由
@app.route('/categories')
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
    conn = sqlite3.connect('documents.db')
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
    
    return render_template('categories.html', categories=categories_list, page=page, total_pages=total_pages, per_page=per_page, search=search)

@app.route('/categories/add', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        
        conn = sqlite3.connect('documents.db')
        c = conn.cursor()
        c.execute('INSERT INTO categories (name, description) VALUES (?, ?)', (name, description))
        conn.commit()
        conn.close()
        
        return redirect(url_for('categories'))
    
    return render_template('add-category.html')

@app.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
def edit_category(id):
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        
        conn = sqlite3.connect('documents.db')
        c = conn.cursor()
        c.execute('UPDATE categories SET name = ?, description = ? WHERE id = ?', (name, description, id))
        conn.commit()
        conn.close()
        
        return redirect(url_for('categories'))
    
    conn = sqlite3.connect('documents.db')
    c = conn.cursor()
    c.execute('SELECT * FROM categories WHERE id = ?', (id,))
    category = c.fetchone()
    conn.close()
    
    return render_template('edit-category.html', category=category)

@app.route('/categories/delete/<int:id>')
def delete_category(id):
    conn = sqlite3.connect('documents.db')
    c = conn.cursor()
    c.execute('DELETE FROM categories WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('categories'))

@app.route('/files/delete/<int:id>')
def delete_file(id):
    # 获取来源页面和搜索参数
    from_page = request.args.get('from', '')
    keyword = request.args.get('keyword', '')
    category_id = request.args.get('category', '')
    
    # 真数据库删除，同时删除相关的关联数据
    conn = sqlite3.connect('documents.db')
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
        return redirect(url_for('merged_search', keyword=keyword, category=category_id))
    else:
        return redirect(url_for('file_list'))

# 文件列表路由
@app.route('/file-list')
def file_list():
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页显示10条记录
    offset = (page - 1) * per_page
    
    # 获取总记录数
    conn = sqlite3.connect('documents.db')
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
    
    return render_template('file-list.html', files=files_list, page=page, total_pages=total_pages, per_page=per_page)

# 系统设置路由
@app.route('/merged-search')
def merged_search():
    # 获取搜索参数
    keyword = request.args.get('keyword', '')
    category_id = request.args.get('category', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页显示10条记录
    offset = (page - 1) * per_page
    
    # 使用关键词作为搜索词
    search_term = keyword
    
    print(f"Search parameters: search_term='{search_term}', category_id='{category_id}', page={page}")
    
    # 获取分类列表
    categories = []
    conn = sqlite3.connect('documents.db')
    c = conn.cursor()
    c.execute('SELECT id, name FROM categories')
    categories = c.fetchall()
    conn.close()
    
    # 构建查询语句
    conn = sqlite3.connect('documents.db')
    c = conn.cursor()
    
    # 构建WHERE子句
    where_clause = 'WHERE d.is_delete = 0'
    params = []
    
    if search_term:
        # 根据搜索词长度和是否包含标点符号选择不同的搜索策略
        # 短关键词使用MATCH操作符（性能更好）
        # 长句子或包含标点符号的搜索词使用LIKE操作符（更灵活）
        has_punctuation = any(p in search_term for p in [',', '，', '.', '。', '!', '！', '?', '？', '；', ':', '：'])
        is_long_sentence = len(search_term) > 20
        
        if has_punctuation or is_long_sentence:
            # 对于长句子或包含标点符号的搜索词，使用LIKE操作符
            where_clause += ' AND d.id IN (SELECT file_id FROM file_content_fts WHERE content LIKE ?)'
            # 对搜索词进行分词处理
            try:
                import jieba
                seg_list = jieba.cut(search_term)
                seg_term = ' '.join(seg_list)
                # 构建LIKE查询参数，在分词后的搜索词前后添加%通配符
                like_param = '%' + seg_term + '%'
            except ImportError:
                # 如果jieba未安装，直接使用原内容
                like_param = '%' + search_term + '%'
            params.append(like_param)
        else:
            # 对于短关键词，使用FTS5 MATCH操作符（性能更好）
            where_clause += ' AND d.id IN (SELECT file_id FROM file_content_fts WHERE file_content_fts MATCH ?)'
            # 使用jieba对搜索词进行分词
            try:
                import jieba
                seg_list = jieba.cut(search_term)
                seg_keyword = ' '.join(seg_list)
                params.append(seg_keyword)
            except ImportError:
                # 如果jieba未安装，直接使用原内容
                params.append(search_term)
    
    if category_id and category_id != '':
        try:
            cat_id = int(category_id)
            where_clause += ' AND d.id IN (SELECT document_id FROM document_categories WHERE category_id = ?)'
            params.append(cat_id)
            print(f"Added category filter: {cat_id}")
        except ValueError:
            print(f"Invalid category_id: {category_id}")
    
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
        categories = []
        if DB_TYPE == 'mysql':
            conn = mysql.connector.connect(**DB_CONFIG)
            c = conn.cursor()
            c.execute('SELECT c.id, c.name FROM document_categories dc JOIN categories c ON dc.category_id = c.id WHERE dc.document_id = %s', (file[0],))
            categories = c.fetchall()
            conn.close()
        else:
            conn = sqlite3.connect('documents.db')
            c = conn.cursor()
            c.execute('SELECT c.id, c.name FROM document_categories dc JOIN categories c ON dc.category_id = c.id WHERE dc.document_id = ?', (file[0],))
            categories = c.fetchall()
            conn.close()
        
        # 提取关键词上下文
        contexts = []
        if search_term:
            # 从file_content_fts表中获取文件内容
            conn = sqlite3.connect('documents.db')
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
            'categories': categories,
            'upload_date': upload_date_str,
            'issuing_unit': issuing_unit,
            'remark': remark,
            'contexts': contexts
        })
    
    return render_template('merged-search.html', files=files_list, page=page, total_pages=total_pages, per_page=per_page, categories=categories, keyword=keyword, category_id=category_id)

@app.route('/get-document-categories/<int:file_id>')
def get_document_categories(file_id):
    conn = sqlite3.connect('documents.db')
    c = conn.cursor()
    c.execute('SELECT c.id, c.name FROM document_categories dc JOIN categories c ON dc.category_id = c.id WHERE dc.document_id = ?', (file_id,))
    categories = c.fetchall()
    conn.close()
    
    # 转换为字典列表
    result = []
    for category in categories:
        result.append({'id': category[0], 'name': category[1]})
    
    return jsonify(result)

@app.route('/update-document-categories', methods=['POST'])
def update_document_categories():
    data = request.get_json()
    file_id = data.get('file_id')
    category_ids = data.get('category_ids', [])
    
    conn = sqlite3.connect('documents.db')
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

@app.route('/open-file-location/<int:file_id>')
def open_file_location(file_id):
    # 根据文件ID获取文件路径
    conn = sqlite3.connect('documents.db')
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
def download_file(file_id):
    # 根据文件ID获取文件路径和文件名
    conn = sqlite3.connect('documents.db')
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

@app.route('/view-file/<int:file_id>')
def view_file(file_id):
    # 根据文件ID获取文件路径、文件名和其他信息
    conn = sqlite3.connect('documents.db')
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
            
            # 尝试在后端将Word文件转换为HTML
            word_html = None
            if file_ext in ['doc', 'docx']:
                try:
                    import mammoth
                    with open(file_path, 'rb') as f:
                        result = mammoth.convert_to_html(f)
                        word_html = result.value
                    print("Word文件转换成功")
                except Exception as e:
                    print(f"Word文件转换失败: {e}")
            
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
def get_file(file_id):
    # 根据文件ID获取文件路径和文件名
    conn = sqlite3.connect('documents.db')
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
        
        # 更新配置文件
        config_path = os.path.join(os.path.dirname(__file__), 'config.py')
        print('配置文件路径:', config_path)
        
        with open(config_path, 'r', encoding=Config.FILE_ENCODING) as f:
            config_content = f.read()
        
        # 替换UPLOAD_FOLDER的值（使用正则表达式匹配任意格式的UPLOAD_FOLDER设置）
        import re
        # 将路径中的反斜杠替换为双反斜杠，避免在字符串中被解释为转义字符
        escaped_path = upload_folder.replace('\\', '\\\\')
        new_config_content = re.sub(
            r"UPLOAD_FOLDER = .*",
            f"UPLOAD_FOLDER = r'{escaped_path}'",
            config_content
        )
        
        with open(config_path, 'w', encoding=Config.FILE_ENCODING) as f:
            f.write(new_config_content)
        print('配置文件更新成功')
        
        # 更新Config类的UPLOAD_FOLDER属性
        Config.UPLOAD_FOLDER = upload_folder
        print('Config.UPLOAD_FOLDER更新成功:', Config.UPLOAD_FOLDER)
        
        return render_template('settings.html', upload_folder=upload_folder, message='设置保存成功', message_type='success')
    
    return render_template('settings.html', upload_folder=app.config['UPLOAD_FOLDER'])

if __name__ == '__main__':
    app.run(debug=True, port=3000)
