const express = require('express');
const multer = require('multer');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();
const { promisify } = require('util');

const app = express();
const port = 3000;

// 配置模板引擎
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// 配置静态文件目录
app.use(express.static(path.join(__dirname, 'public')));

// 配置文件上传
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, 'uploads/');
  },
  filename: function (req, file, cb) {
    cb(null, Date.now() + '-' + file.originalname);
  }
});

const upload = multer({ storage: storage });

// 确保上传目录存在
const fs = require('fs');
if (!fs.existsSync('uploads')) {
  fs.mkdirSync('uploads');
}

// 初始化数据库
const db = new sqlite3.Database('documents.db');
db.serialize(() => {
  db.run(`
    CREATE TABLE IF NOT EXISTS documents (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      filename TEXT NOT NULL,
      filepath TEXT NOT NULL,
      filetype TEXT NOT NULL,
      upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
      content TEXT
    )
  `);
  
  db.run(`
    CREATE TABLE IF NOT EXISTS keywords (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      document_id INTEGER,
      keyword TEXT NOT NULL,
      FOREIGN KEY (document_id) REFERENCES documents(id)
    )
  `);
});

// 转换数据库操作为Promise
const dbRun = promisify(db.run.bind(db));
const dbAll = promisify(db.all.bind(db));
const dbGet = promisify(db.get.bind(db));

// 导入路由
app.get('/', (req, res) => {
  res.render('index', { message: null, messageType: null });
});

app.get('/search', (req, res) => {
  res.render('search');
});

// 处理文件上传
app.post('/upload', upload.single('document'), async (req, res) => {
  if (!req.file) {
    return res.status(400).send('No file uploaded.');
  }
  
  try {
    // 提取文件内容
    let content = '';
    if (req.file.mimetype === 'application/pdf') {
      const pdfParse = require('pdf-parse');
      const dataBuffer = fs.readFileSync(req.file.path);
      const pdfData = await pdfParse(dataBuffer);
      content = pdfData.text;
    } else if (req.file.mimetype === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
      const fs = require('fs');
      const docxParser = require('docx-parser');
      const data = fs.readFileSync(req.file.path);
      const docxData = docxParser(data);
      content = docxData.text;
    }
    
    // 插入文档信息到数据库
    const result = await dbRun(
      'INSERT INTO documents (filename, filepath, filetype, content) VALUES (?, ?, ?, ?)',
      [req.file.originalname, req.file.path, req.file.mimetype, content]
    );
    
    // 提取关键词并存储
    if (content) {
      const keywords = extractKeywords(content);
      for (const keyword of keywords) {
        await dbRun(
          'INSERT INTO keywords (document_id, keyword) VALUES (?, ?)',
          [result.lastID, keyword]
        );
      }
    }
    
    res.redirect('/');
  } catch (error) {
    console.error('Error processing file:', error);
    res.status(500).send('Error processing file.');
  }
});

// 处理搜索请求
app.get('/search-results', async (req, res) => {
  const query = req.query.q;
  if (!query) {
    return res.redirect('/search');
  }
  
  try {
    // 搜索包含关键词的文档
    const results = await dbAll(`
      SELECT DISTINCT documents.* FROM documents
      JOIN keywords ON documents.id = keywords.document_id
      WHERE keywords.keyword LIKE ?
      ORDER BY documents.upload_date DESC
    `, [`%${query}%`]);
    
    res.render('search-results', { query, results });
  } catch (error) {
    console.error('Error searching:', error);
    res.status(500).send('Error searching.');
  }
});

// 提取关键词的函数
function extractKeywords(text) {
  // 简单的关键词提取，实际应用中可以使用更复杂的算法
  const words = text.toLowerCase()
    .replace(/[^\w\s]/g, '')
    .split(/\s+/)
    .filter(word => word.length > 2);
  
  // 去重
  return [...new Set(words)];
}

// 启动服务器
app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
