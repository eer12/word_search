import openpyxl
import xlrd
import os

def convert_excel_to_html(filepath, file_id):
    """
    在后端直接读取Excel文件并生成HTML表格
    """
    # 获取文件名
    filename = os.path.basename(filepath)
    
    # 构建HTML模板
    html_template = '''
    <div style="padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <h2 style="margin-top: 0; margin-bottom: 30px; border-bottom: 2px solid #3498db; padding-bottom: 10px; color: #333;">Excel文件预览 - {filename}</h2>
        {excel_content}
    </div>
    '''
    
    # 读取Excel文件并生成HTML内容
    excel_content = ''
    try:
        if filepath.endswith('.xlsx'):
            # 处理xlsx文件
            workbook = openpyxl.load_workbook(filepath)
            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                # 使用三引号的多行字符串
                excel_content += '''
                <div style="margin-bottom: 40px;">
                    <h3 style="margin-top: 0; margin-bottom: 15px; color: #555;">工作表: ''' + sheet_name + '''</h3>
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                '''
                
                # 获取最大行数和列数
                max_row = sheet.max_row
                max_col = sheet.max_column
                
                if max_row == 0 or max_col == 0:
                    excel_content += '<tr><td style="padding: 40px; text-align: center; color: #999; font-style: italic;">此工作表为空</td></tr>'
                else:
                    # 生成表头
                    excel_content += '<thead><tr>'
                    for col in range(1, max_col + 1):
                        cell = sheet.cell(row=1, column=col)
                        cell_value = cell.value
                        # 转义HTML特殊字符
                        cell_value_str = cell_value if cell_value is not None else ''
                        cell_value_str = str(cell_value_str).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
                        excel_content += '<th style="border: 1px solid #dee2e6; padding: 8px; text-align: left; background-color: #f8f9fa; font-weight: 600;">' + cell_value_str + '</th>'
                    excel_content += '''</tr></thead>
                    <tbody>'''
                    
                    # 生成数据行
                    for row in range(2, max_row + 1):
                        excel_content += '<tr>'
                        for col in range(1, max_col + 1):
                            cell = sheet.cell(row=row, column=col)
                            cell_value = cell.value
                            # 转义HTML特殊字符
                            cell_value_str = cell_value if cell_value is not None else ''
                            cell_value_str = str(cell_value_str).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
                            excel_content += '<td style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">' + cell_value_str + '</td>'
                        excel_content += '</tr>'
                    excel_content += '</tbody>'
                
                excel_content += '</table></div></div>'
        elif filepath.endswith('.xls'):
            # 处理xls文件
            try:
                workbook = xlrd.open_workbook(filepath)
                for sheet_name in workbook.sheet_names():
                    sheet = workbook.sheet_by_name(sheet_name)
                    # 使用三引号的多行字符串
                    excel_content += '''
                    <div style="margin-bottom: 40px;">
                        <h3 style="margin-top: 0; margin-bottom: 15px; color: #555;">工作表: ''' + sheet_name + '''</h3>
                        <div style="overflow-x: auto;">
                            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                    '''
                    
                    nrows = sheet.nrows
                    ncols = sheet.ncols
                    
                    if nrows == 0 or ncols == 0:
                        excel_content += '<tr><td style="padding: 40px; text-align: center; color: #999; font-style: italic;">此工作表为空</td></tr>'
                    else:
                        # 生成表头
                        excel_content += '<thead><tr>'
                        for col in range(ncols):
                            cell_value = sheet.cell_value(0, col)
                            # 转义HTML特殊字符
                            cell_value_str = cell_value if cell_value is not None else ''
                            cell_value_str = str(cell_value_str).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
                            excel_content += '<th style="border: 1px solid #dee2e6; padding: 8px; text-align: left; background-color: #f8f9fa; font-weight: 600;">' + cell_value_str + '</th>'
                        excel_content += '''</tr></thead>
                        <tbody>'''
                        
                        # 生成数据行
                        for row in range(1, nrows):
                            excel_content += '<tr>'
                            for col in range(ncols):
                                cell_value = sheet.cell_value(row, col)
                                # 转义HTML特殊字符
                                cell_value_str = cell_value if cell_value is not None else ''
                                cell_value_str = str(cell_value_str).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
                                excel_content += '<td style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">' + cell_value_str + '</td>'
                            excel_content += '</tr>'
                        excel_content += '</tbody>'
                    
                    excel_content += '</table></div></div>'
            except ImportError:
                # 如果xlrd未安装，尝试使用openpyxl
                workbook = openpyxl.load_workbook(filepath)
                for sheet_name in workbook.sheetnames:
                    sheet = workbook[sheet_name]
                    # 使用三引号的多行字符串
                    excel_content += '''
                    <div style="margin-bottom: 40px;">
                        <h3 style="margin-top: 0; margin-bottom: 15px; color: #555;">工作表: ''' + sheet_name + '''</h3>
                        <div style="overflow-x: auto;">
                            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                    '''
                    
                    # 获取最大行数和列数
                    max_row = sheet.max_row
                    max_col = sheet.max_column
                    
                    if max_row == 0 or max_col == 0:
                        excel_content += '<tr><td style="padding: 40px; text-align: center; color: #999; font-style: italic;">此工作表为空</td></tr>'
                    else:
                        # 生成表头
                        excel_content += '<thead><tr>'
                        for col in range(1, max_col + 1):
                            cell = sheet.cell(row=1, column=col)
                            cell_value = cell.value
                            # 转义HTML特殊字符
                            cell_value_str = cell_value if cell_value is not None else ''
                            cell_value_str = str(cell_value_str).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
                            excel_content += '<th style="border: 1px solid #dee2e6; padding: 8px; text-align: left; background-color: #f8f9fa; font-weight: 600;">' + cell_value_str + '</th>'
                        excel_content += '''</tr></thead>
                        <tbody>'''
                        
                        # 生成数据行
                        for row in range(2, max_row + 1):
                            excel_content += '<tr>'
                            for col in range(1, max_col + 1):
                                cell = sheet.cell(row=row, column=col)
                                cell_value = cell.value
                                # 转义HTML特殊字符
                                cell_value_str = cell_value if cell_value is not None else ''
                                cell_value_str = str(cell_value_str).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
                                excel_content += '<td style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">' + cell_value_str + '</td>'
                            excel_content += '</tr>'
                        excel_content += '</tbody>'
                    
                    excel_content += '</table></div></div>'
        print(f"Excel文件预览生成成功: {filename}")
    except Exception as e:
        # 使用三引号的多行字符串
        excel_content = '''
        <div style="padding: 20px; background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; border-radius: 4px; text-align: center;">
            <h3>预览失败</h3>
            <p>错误信息: ''' + str(e) + '''</p>
            <p>请尝试下载文件后本地打开</p>
        </div>
        '''
        print(f"Excel文件预览生成失败: {e}")
        # 打印详细的错误信息
        import traceback
        traceback.print_exc()
    
    # 替换模板中的变量
    html = html_template.replace('{filename}', filename)
    html = html.replace('{excel_content}', excel_content)
    
    return html

if __name__ == '__main__':
    # 测试函数
    test_file = 'test.xlsx'
    if os.path.exists(test_file):
        html = convert_excel_to_html(test_file, 1)
        with open('excel_preview.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'预览文件已生成: excel_preview.html')
    else:
        print(f'测试文件不存在: {test_file}')
