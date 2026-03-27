from flask import Flask, render_template, request, redirect, url_for
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
    
    if MYSQL_AVAILABLE:
        try:
            # 直接使用root用户连接，创建数据库
            try:
                # 使用DB_CONFIG中的配置，但覆盖用户名为root且不指定数据库
                root_config = DB_CONFIG.copy()
                root_config['user'] = 'root'
                # 移除database参数，因为此时数据库可能还不存在
                if 'database' in root_config:
                    del root_config['database']
                root_conn = mysql.connector.connect(**root_config)
                root_c = root_conn.cursor()
                # 创建数据库
                root_c.execute('CREATE DATABASE IF NOT EXISTS document_search')
                root_conn.commit()
                root_conn.close()
                print("成功创建数据库")
            except mysql.connector.Error as root_err:
                print(f"Root用户连接错误: {root_err}")
            
            # 然后使用root用户连接
            conn_config = DB_CONFIG.copy()
            conn_config['user'] = 'root'
            conn = mysql.connector.connect(**conn_config)
            c = conn.cursor()
            # 创建分类表
            c.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL COMMENT '分类名称',
                    description TEXT COMMENT '分类描述',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
                )
            ''')
            # 创建文档表
            c.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '文件ID',
                    file_name VARCHAR(255) NOT NULL COMMENT '文件名称',
                    file_path VARCHAR(255) NOT NULL COMMENT '文件存储路径',
                    file_size INT DEFAULT 0 COMMENT '文件大小（字节）',
                    issuing_unit VARCHAR(255) DEFAULT '' COMMENT '发文单位',
                    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
                    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    is_delete INT DEFAULT 0 COMMENT '是否删除',
                    remark TEXT COMMENT '文件备注'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            # 创建文档-分类关联表（实现一对多关系）
            c.execute('''
                CREATE TABLE IF NOT EXISTS document_categories (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '关联ID',
                    document_id INT NOT NULL COMMENT '文档ID',
                    category_id INT NOT NULL COMMENT '分类ID',
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
                    UNIQUE KEY (document_id, category_id) COMMENT '确保文档和分类的组合唯一'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')

            # 继续执行，不影响其他操作
            # 创建关键词分表（按文档ID范围分表）
            for i in range(10):  # 创建10个分表
                sql = 'CREATE TABLE IF NOT EXISTS keywords_' + str(i) + ' ('
                sql += 'id INT AUTO_INCREMENT PRIMARY KEY, '
                sql += 'document_id INT, '
                sql += 'keyword VARCHAR(100) NOT NULL, '
                sql += 'FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE '
                sql += ')'
                c.execute(sql)
            c.execute('''
                CREATE TABLE IF NOT EXISTS file_content_indexes (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '索引ID',
                    file_id INT NOT NULL COMMENT '关联documents.id',
                    content LONGTEXT NOT NULL COMMENT '提取的文件文本',
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    FOREIGN KEY (file_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            ''')
            # 修改现有表结构，将content列改为LONGTEXT
            try:
                c.execute('ALTER TABLE file_content_indexes MODIFY COLUMN content LONGTEXT')
                conn.commit()
            except Exception as e:
                print(f"修改file_content_indexes表结构失败: {e}")
                # 继续执行，不影响其他操作
            
            # 插入默认分类
            c.execute('SELECT COUNT(*) FROM categories')
            if c.fetchone()[0] == 0:
                c.execute('INSERT INTO categories (name, description) VALUES (%s, %s)', ('默认分类', '系统默认分类'))
                conn.commit()
                print("成功插入默认分类")
            
            conn.commit()
            conn.close()
            DB_TYPE = 'mysql'
            print("成功连接到MySQL数据库")
            return True
        except mysql.connector.Error as err:
            print(f"MySQL连接错误: {err}")
            print("回退到SQLite数据库")
    
    # 回退到SQLite
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
    # 创建关键词分表（按文档ID范围分表）
    for i in range(10):  # 创建10个分表
        sql = 'CREATE TABLE IF NOT EXISTS keywords_' + str(i) + ' ('
        sql += 'id INTEGER PRIMARY KEY AUTOINCREMENT, '
        sql += 'document_id INTEGER, '
        sql += 'keyword TEXT NOT NULL, '
        sql += 'FOREIGN KEY (document_id) REFERENCES documents(id) '
        sql += ')'
        c.execute(sql)
    c.execute('''
        CREATE TABLE IF NOT EXISTS file_content_indexes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES documents(id)
        )
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

def extract_keywords(text):
    # 改进的关键词提取，支持中文
    import re
    # 移除特殊字符，保留中文、英文和数字
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', '', text)
    
    # 尝试使用jieba进行中文分词
    try:
        import jieba
        words = jieba.cut(text)
        words = [word for word in words if len(word) >= 2]
    except ImportError:
        # 如果没有安装jieba，使用简单的方法
        # 对于中文，按字符分割，然后组合成可能的词语
        chinese_chars = re.findall(r'[\u4e00-\u9fa5]+', text)
        # 对于英文和数字，按空格分割
        english_parts = re.findall(r'[a-zA-Z0-9]+', text)
        words = chinese_chars + english_parts
        words = [word for word in words if len(word) >= 2]
    
    # 限制关键词长度为100字符
    words = [word[:100] for word in words]
    # 去重
    return list(set(words))

def extract_context(text, keyword, max_chars=200):
    # 提取关键词前后的上下文，直到逗号或句号为止
    import re
    if not keyword or not text:
        return []
    
    contexts = []
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
    
    # 限制数量，不进行去重，确保显示所有关键词出现的句子
    return contexts[:10]  # 最多返回10个上下文

@app.route('/')
def index():
    return render_template('index.html', message=None, message_type=None)

@app.route('/upload')
def upload_page():
    # 获取分类列表
    categories_list = []
    if DB_TYPE == 'mysql':
        conn = mysql.connector.connect(**DB_CONFIG)
        c = conn.cursor()
        c.execute('SELECT id, name FROM categories ORDER BY id DESC')
        categories_list = c.fetchall()
        conn.close()
    else:
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
        if DB_TYPE == 'mysql':
            conn = mysql.connector.connect(**DB_CONFIG)
            c = conn.cursor()
            c.execute(
                'INSERT INTO documents (file_name, file_path, file_size, issuing_unit, remark) VALUES (%s, %s, %s, %s, %s)',
                (file.filename, filepath, file_size, issuing_unit, remark)
            )
            document_id = c.lastrowid
            
            # 插入文档-分类关联
            for category_id in category_ids:
                c.execute(
                    'INSERT INTO document_categories (document_id, category_id) VALUES (%s, %s)',
                    (document_id, category_id)
                )
            
            # 提取关键词并存储到分表
            if content:
                keywords = extract_keywords(content)
                # 根据document_id选择分表
                table_index = document_id % 10
                table_name = 'keywords_' + str(table_index)
                for keyword in keywords:
                    sql = 'INSERT INTO ' + table_name + ' (document_id, keyword) VALUES (%s, %s)'
                    c.execute(sql, (document_id, keyword))
                # 插入文件内容索引
                c.execute(
                    'INSERT INTO file_content_indexes (file_id, content) VALUES (%s, %s)',
                    (document_id, content)
                )
            
            conn.commit()
            conn.close()
        else:
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
            
            # 提取关键词并存储到分表
            if content:
                keywords = extract_keywords(content)
                # 根据document_id选择分表
                table_index = document_id % 10
                table_name = 'keywords_' + str(table_index)
                for keyword in keywords:
                    sql = 'INSERT INTO ' + table_name + ' (document_id, keyword) VALUES (?, ?)'
                    c.execute(sql, (document_id, keyword))
                # 插入文件内容索引
                c.execute(
                    'INSERT INTO file_content_indexes (file_id, content) VALUES (?, ?)',
                    (document_id, content)
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
    if DB_TYPE == 'mysql':
        conn = mysql.connector.connect(**DB_CONFIG)
        c = conn.cursor()
        c.execute('SELECT id, name FROM categories')
        for row in c.fetchall():
            category_map[row[0]] = row[1]
        conn.close()
    else:
        conn = sqlite3.connect('documents.db')
        c = conn.cursor()
        c.execute('SELECT id, name FROM categories')
        for row in c.fetchall():
            category_map[row[0]] = row[1]
        conn.close()
    
    if DB_TYPE == 'mysql':
        conn = mysql.connector.connect(**DB_CONFIG)
        c = conn.cursor()
        # 构建分表查询语句
        keyword_tables_query = ''
        for i in range(10):
            if i > 0:
                keyword_tables_query += ' UNION ALL '
            keyword_tables_query += 'SELECT document_id FROM keywords_' + str(i) + ' WHERE keyword LIKE %s'
        
        # 构建完整的查询语句
        sql = 'SELECT DISTINCT documents.* FROM documents LEFT JOIN (' + keyword_tables_query + ') AS keywords ON documents.id = keywords.document_id LEFT JOIN file_content_indexes ON documents.id = file_content_indexes.file_id WHERE (keywords.document_id IS NOT NULL OR file_content_indexes.content LIKE %s) AND documents.is_delete = 0 ORDER BY documents.upload_time DESC'
        params = (f'%{query}%',) * 11
        c.execute(sql, params)
        results = c.fetchall()
        conn.close()
    else:
        # 使用SQLite
        conn = sqlite3.connect('documents.db')
        c = conn.cursor()
        # 构建分表查询语句
        keyword_tables_query = ''
        for i in range(10):
            if i > 0:
                keyword_tables_query += ' UNION ALL '
            keyword_tables_query += 'SELECT document_id FROM keywords_' + str(i) + ' WHERE keyword LIKE ?'
        
        # 构建完整的查询语句
        sql = 'SELECT DISTINCT documents.* FROM documents LEFT JOIN (' + keyword_tables_query + ') AS keywords ON documents.id = keywords.document_id LEFT JOIN file_content_indexes ON documents.id = file_content_indexes.file_id WHERE (keywords.document_id IS NOT NULL OR file_content_indexes.content LIKE ?) AND documents.is_delete = 0 ORDER BY documents.upload_time DESC'
        params = (f'%{query}%',) * 11
        c.execute(sql, params)
        results = c.fetchall()
        conn.close()
    
    # 转换结果为字典列表
    results_list = []
    for result in results:
        category_id = result[4]
        category_name = category_map.get(category_id, '未知分类')
        results_list.append({
            'id': result[0],
            'filename': result[1],
            'filepath': result[2],
            'filetype': category_name,
            'upload_date': result[6]
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
        where_clause = 'WHERE name LIKE %s'
        params.append(f'%{search}%')
    
    # 获取总记录数
    if DB_TYPE == 'mysql':
        conn = mysql.connector.connect(**DB_CONFIG)
        c = conn.cursor()
        count_sql = f'SELECT COUNT(*) FROM categories {where_clause}'
        c.execute(count_sql, params)
        total = c.fetchone()[0]
        # 获取分页数据
        query_sql = f'SELECT * FROM categories {where_clause} ORDER BY id DESC LIMIT %s OFFSET %s'
        params.extend([per_page, offset])
        c.execute(query_sql, params)
        categories_list = c.fetchall()
        conn.close()
    else:
        conn = sqlite3.connect('documents.db')
        c = conn.cursor()
        count_sql = f'SELECT COUNT(*) FROM categories {where_clause.replace("%s", "?")}'
        c.execute(count_sql, params)
        total = c.fetchone()[0]
        # 获取分页数据
        query_sql = f'SELECT * FROM categories {where_clause.replace("%s", "?")} ORDER BY id DESC LIMIT ? OFFSET ?'
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
        
        if DB_TYPE == 'mysql':
            conn = mysql.connector.connect(**DB_CONFIG)
            c = conn.cursor()
            c.execute('INSERT INTO categories (name, description) VALUES (%s, %s)', (name, description))
            conn.commit()
            conn.close()
        else:
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
        
        if DB_TYPE == 'mysql':
            conn = mysql.connector.connect(**DB_CONFIG)
            c = conn.cursor()
            c.execute('UPDATE categories SET name = %s, description = %s WHERE id = %s', (name, description, id))
            conn.commit()
            conn.close()
        else:
            conn = sqlite3.connect('documents.db')
            c = conn.cursor()
            c.execute('UPDATE categories SET name = ?, description = ? WHERE id = ?', (name, description, id))
            conn.commit()
            conn.close()
        
        return redirect(url_for('categories'))
    
    if DB_TYPE == 'mysql':
        conn = mysql.connector.connect(**DB_CONFIG)
        c = conn.cursor()
        c.execute('SELECT * FROM categories WHERE id = %s', (id,))
        category = c.fetchone()
        conn.close()
    else:
        conn = sqlite3.connect('documents.db')
        c = conn.cursor()
        c.execute('SELECT * FROM categories WHERE id = ?', (id,))
        category = c.fetchone()
        conn.close()
    
    return render_template('edit-category.html', category=category)

@app.route('/categories/delete/<int:id>')
def delete_category(id):
    if DB_TYPE == 'mysql':
        conn = mysql.connector.connect(**DB_CONFIG)
        c = conn.cursor()
        c.execute('DELETE FROM categories WHERE id = %s', (id,))
        conn.commit()
        conn.close()
    else:
        conn = sqlite3.connect('documents.db')
        c = conn.cursor()
        c.execute('DELETE FROM categories WHERE id = ?', (id,))
        conn.commit()
        conn.close()
    
    return redirect(url_for('categories'))

# 文件列表路由
@app.route('/file-list')
def file_list():
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页显示10条记录
    offset = (page - 1) * per_page
    
    # 获取总记录数
    if DB_TYPE == 'mysql':
        conn = mysql.connector.connect(**DB_CONFIG)
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
            LIMIT %s OFFSET %s
        ''', (per_page, offset))
        files = c.fetchall()
        conn.close()
    else:
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
    
    print(f"Search parameters: keyword='{keyword}', category_id='{category_id}', page={page}")
    
    # 获取分类列表
    categories = []
    if DB_TYPE == 'mysql':
        conn = mysql.connector.connect(**DB_CONFIG)
        c = conn.cursor()
        c.execute('SELECT id, name FROM categories')
        categories = c.fetchall()
        conn.close()
    else:
        conn = sqlite3.connect('documents.db')
        c = conn.cursor()
        c.execute('SELECT id, name FROM categories')
        categories = c.fetchall()
        conn.close()
    
    # 构建查询语句
    if DB_TYPE == 'mysql':
        conn = mysql.connector.connect(**DB_CONFIG)
        c = conn.cursor()
        
        # 构建WHERE子句
        where_clause = 'WHERE d.is_delete = 0'
        params = []
        
        if keyword:
            # 由于使用了分表，需要查询所有关键词表
            keyword_tables_query = ''
            for i in range(10):
                if i > 0:
                    keyword_tables_query += ' UNION ALL '
                keyword_tables_query += f'SELECT document_id, keyword FROM keywords_{i}'
            
            where_clause += f' AND (EXISTS (SELECT 1 FROM ({keyword_tables_query}) k WHERE k.document_id = d.id AND k.keyword LIKE %s) OR EXISTS (SELECT 1 FROM file_content_indexes f WHERE f.file_id = d.id AND f.content LIKE %s))'
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        
        if category_id and category_id != '':
            try:
                cat_id = int(category_id)
                where_clause += ' AND d.id IN (SELECT document_id FROM document_categories WHERE category_id = %s)'
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
            LIMIT %s OFFSET %s
        '''
        params.extend([per_page, offset])
        print(f"Query SQL: {sql}")
        print(f"Query params: {params}")
        c.execute(sql, params)
        files = c.fetchall()
        print(f"Found {len(files)} files")
        conn.close()
    else:
        conn = sqlite3.connect('documents.db')
        c = conn.cursor()
        
        # 构建WHERE子句
        where_clause = 'WHERE d.is_delete = 0'
        params = []
        
        if keyword:
            # 由于使用了分表，需要查询所有关键词表
            keyword_tables_query = ''
            for i in range(10):
                if i > 0:
                    keyword_tables_query += ' UNION ALL '
                keyword_tables_query += f'SELECT document_id, keyword FROM keywords_{i}'
            
            where_clause += f' AND (EXISTS (SELECT 1 FROM ({keyword_tables_query}) k WHERE k.document_id = d.id AND k.keyword LIKE ?) OR EXISTS (SELECT 1 FROM file_content_indexes f WHERE f.file_id = d.id AND f.content LIKE ?))'
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        
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
        if keyword:
            # 从file_content_indexes表中获取文件内容
            if DB_TYPE == 'mysql':
                conn = mysql.connector.connect(**DB_CONFIG)
                c = conn.cursor()
                c.execute('SELECT content FROM file_content_indexes WHERE file_id = %s', (file[0],))
                content_result = c.fetchone()
                conn.close()
            else:
                conn = sqlite3.connect('documents.db')
                c = conn.cursor()
                c.execute('SELECT content FROM file_content_indexes WHERE file_id = ?', (file[0],))
                content_result = c.fetchone()
                conn.close()
            
            if content_result and content_result[0]:
                contexts = extract_context(content_result[0], keyword)
                # 对关键词进行加亮处理
                highlighted_contexts = []
                for context in contexts:
                    # 使用HTML标签对关键词进行加亮
                    highlighted_context = context.replace(keyword, f'<span class="highlight">{keyword}</span>')
                    # 处理大小写不敏感的情况
                    import re
                    highlighted_context = re.sub(re.escape(keyword), f'<span class="highlight">{keyword}</span>', highlighted_context, flags=re.IGNORECASE)
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

@app.route('/open-file-location/<int:file_id>')
def open_file_location(file_id):
    # 根据文件ID获取文件路径
    if DB_TYPE == 'mysql':
        conn = mysql.connector.connect(**DB_CONFIG)
        c = conn.cursor()
        c.execute('SELECT file_path FROM documents WHERE id = %s', (file_id,))
        result = c.fetchone()
        conn.close()
    else:
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
    if DB_TYPE == 'mysql':
        conn = mysql.connector.connect(**DB_CONFIG)
        c = conn.cursor()
        c.execute('SELECT file_path, file_name FROM documents WHERE id = %s', (file_id,))
        result = c.fetchone()
        conn.close()
    else:
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
    if DB_TYPE == 'mysql':
        conn = mysql.connector.connect(**DB_CONFIG)
        c = conn.cursor()
        c.execute('SELECT file_path, file_name, file_size, upload_time FROM documents WHERE id = %s', (file_id,))
        result = c.fetchone()
        conn.close()
    else:
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
    if DB_TYPE == 'mysql':
        conn = mysql.connector.connect(**DB_CONFIG)
        c = conn.cursor()
        c.execute('SELECT file_path, file_name FROM documents WHERE id = %s', (file_id,))
        result = c.fetchone()
        conn.close()
    else:
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
