from flask import Flask, render_template, request, jsonify
import json
from collections import Counter
import os
import re
import hashlib
import subprocess
import sys

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
# 测试结果文件目录和统一JSON文件
TESTS_DIR = 'tests'
TESTS_FILE = os.path.join(TESTS_DIR, 'tests.json')



@app.after_request
def set_response_headers(response):
    """确保所有HTML响应都有正确的Content-Type"""
    if response.headers.get('Content-Type', '').startswith('text/html'):
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

def generate_test_id(test_name):
    """根据测试名称生成test_id（MD5前6位）"""
    return hashlib.md5(test_name.encode('utf-8')).hexdigest()[:6]

def load_all_tests_data():
    """加载所有测试数据"""
    if not os.path.exists(TESTS_FILE):
        return []
    
    try:
        with open(TESTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_all_tests_data(tests_data):
    """保存所有测试数据"""
    os.makedirs(TESTS_DIR, exist_ok=True)
    with open(TESTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tests_data, f, ensure_ascii=False, indent=2)

def load_test_data_by_id(test_id):
    """根据测试ID加载测试数据"""
    tests_data = load_all_tests_data()
    for test in tests_data:
        if test.get('test_id') == test_id:
            # 验证test_id是否与test_name的MD5前6位一致
            test_name = test.get('test_name', '')
            expected_test_id = generate_test_id(test_name)
            actual_test_id = test.get('test_id', '')
            
            if actual_test_id == expected_test_id:
                return test
    return None

def get_all_tests():
    """获取所有测试列表"""
    tests_data = load_all_tests_data()
    return [{
        'test_id': test.get('test_id', ''),
        'test_name': test.get('test_name', '')
    } for test in tests_data]

def save_test_data(test_name, test_id, results):
    """保存/更新测试数据"""
    tests_data = load_all_tests_data()
    
    # 查找是否已存在相同test_id的测试
    test_index = -1
    for i, test in enumerate(tests_data):
        if test.get('test_id') == test_id:
            test_index = i
            break
    
    # 构建新的测试项
    new_test = {
        'test_id': test_id,
        'test_name': test_name,
        'results': results
    }
    
    if test_index >= 0:
        # 更新现有测试
        tests_data[test_index] = new_test
    else:
        # 添加新测试
        tests_data.append(new_test)
    
    # 保存所有测试数据
    save_all_tests_data(tests_data)

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/tests', methods=['GET'])
def api_tests():
    """获取所有测试列表的API"""
    tests = get_all_tests()
    return jsonify({'tests': tests})

@app.route('/manage')
def manage():
    """管理页面"""
    return render_template('manage.html')

@app.route('/api/generate_test_id', methods=['GET'])
def api_generate_test_id():
    """生成test_id的API"""
    test_name = request.args.get('test_name', '').strip()
    if not test_name:
        return jsonify({'error': '测试名称不能为空'}), 400
    
    test_id = generate_test_id(test_name)
    return jsonify({'test_id': test_id})

@app.route('/api/save_test', methods=['POST'])
def api_save_test():
    """保存/更新测试的API"""
    try:
        data = request.get_json()
        test_name = data.get('test_name', '').strip()
        results = data.get('results', {})
        
        # 验证输入
        if not test_name:
            return jsonify({'error': '测试名称不能为空'}), 400
        
        if not results:
            return jsonify({'error': '至少需要填写一个选项的测试结果'}), 400
        
        # 自动生成test_id
        test_id = generate_test_id(test_name)
        
        # 保存测试数据
        save_test_data(test_name, test_id, results)
        
        return jsonify({
            'success': True,
            'test_id': test_id,
            'test_name': test_name,
            'message': '测试保存成功'
        })
    
    except Exception as e:
        return jsonify({'error': f'保存失败: {str(e)}'}), 500

@app.route('/test', methods=['POST'])
def process_test():
    """处理心理测试请求"""
    try:
        # 获取表单数据
        test_id = request.form.get('test_id', '').strip()
        options = request.form.get('options', '').strip().upper()
        
        # 验证输入：test_id是必填的
        if not test_id:
            return jsonify({'error': '请输入测试编号'}), 400
        
        if not options:
            return jsonify({'error': '请输入选项'}), 400
        
        # 统计选项出现次数
        option_counter = Counter(options)
        
        # 找出最多的选项
        if not option_counter:
            return jsonify({'error': '选项不能为空'}), 400
        
        most_common = option_counter.most_common(1)[0]
        most_option = most_common[0]
        
        # 加载测试数据
        test_data = load_test_data_by_id(test_id)
        if not test_data:
            return jsonify({'error': f'未找到测试编号"{test_id}"的配置文件'}), 404
        
        # 获取对应选项的结果
        results = test_data.get('results', {})
        if most_option in results:
            result_text = results[most_option]
        else:
            return jsonify({'error': f'选项 {most_option} 的测试结果尚未配置'}), 400
        
        # 返回结果
        return jsonify({
            'success': True,
            'test_id': test_data.get('test_id', ''),
            'test_name': test_data.get('test_name', ''),
            'most_option': most_option,
            'result': result_text
        })
    
    except Exception as e:
        return jsonify({'error': f'处理错误: {str(e)}'}), 500


@app.route('/api/bazi_pillars', methods=['POST'])
def api_bazi_pillars():
    """通过 bazi.py 计算四柱（优先用真实排盘脚本）"""
    try:
        data = request.get_json(silent=True) or {}
        year = int(data.get('year'))
        month = int(data.get('month'))
        day = int(data.get('day'))
        hour = int(data.get('hour'))
    except Exception:
        return jsonify({'error': '参数错误：year/month/day/hour 必须为整数'}), 400

    if not (1 <= month <= 12 and 1 <= day <= 31 and 0 <= hour <= 23):
        return jsonify({'error': '参数范围错误：month(1-12) day(1-31) hour(0-23)'}), 400

    script_path = os.path.join(os.path.dirname(__file__), 'bazi.py')
    if not os.path.exists(script_path):
        return jsonify({'error': '未找到 bazi.py'}), 500

    try:
        cmd = [sys.executable, script_path, '-g', str(year), str(month), str(day), str(hour)]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=20
        )
        output = (proc.stdout or '') + '\n' + (proc.stderr or '')

        # 从输出中提取: "四柱：甲子 乙丑 丙寅 丁卯"
        m = re.search(r'四柱：\s*([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s+[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s+[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s+[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])', output)
        if not m:
            # 兼容多空格或 ANSI 干扰
            clean = re.sub(r'\x1b\[[0-9;]*m', '', output)
            m = re.search(r'四柱：\s*([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s+[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s+[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s+[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])', clean)

        if not m:
            return jsonify({'error': 'bazi.py 输出中未找到四柱结果'}), 500

        pillars = m.group(1).split()
        if len(pillars) != 4:
            return jsonify({'error': '四柱解析失败'}), 500

        return jsonify({
            'success': True,
            'yearGZ': pillars[0],
            'monthGZ': pillars[1],
            'dayGZ': pillars[2],
            'hourGZ': pillars[3],
            'source': 'bazi.py'
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'bazi.py 计算超时'}), 504
    except Exception as e:
        return jsonify({'error': f'bazi.py 计算失败: {str(e)}'}), 500

def migrate_old_tests():
    """迁移旧的单个JSON文件到统一的tests.json"""
    if os.path.exists(TESTS_FILE):
        return  # 已经迁移过了
    
    tests_data = []
    if os.path.exists(TESTS_DIR):
        for filename in os.listdir(TESTS_DIR):
            if filename.endswith('.json') and filename != 'tests.json':
                filepath = os.path.join(TESTS_DIR, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        test_data = json.load(f)
                        # 验证test_id是否与test_name的MD5前6位一致
                        test_name = test_data.get('test_name', '')
                        expected_test_id = generate_test_id(test_name)
                        actual_test_id = test_data.get('test_id', '')
                        
                        if actual_test_id == expected_test_id:
                            tests_data.append(test_data)
                except:
                    continue
    
    if tests_data:
        save_all_tests_data(tests_data)


@app.route('/debug/fs')
def debug_filesystem():
    """调试文件系统"""
    import os
    
    result = []
    result.append(f"<h2>文件系统调试</h2>")
    
    # 当前目录
    cwd = os.getcwd()
    result.append(f"<h3>当前目录: {cwd}</h3>")
    result.append(f"<p>内容: {os.listdir(cwd)}</p>")
    
    # 递归查找templates
    for root, dirs, files in os.walk(cwd):
        if 'templates' in dirs or 'templates' in root:
            result.append(f"<h3>找到templates: {root}</h3>")
            result.append(f"<p>子目录: {dirs}</p>")
            result.append(f"<p>文件: {files}</p>")
    
    return "<br>".join(result)


if __name__ == '__main__':
    # 确保tests目录存在
    os.makedirs(TESTS_DIR, exist_ok=True)
    
    # 迁移旧的JSON文件
    migrate_old_tests()
    
    app.run(debug=False, host='0.0.0.0', port=9000)

