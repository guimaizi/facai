# coding: utf-8
from flask import Flask, render_template, jsonify, request, send_from_directory
import json
import os

app = Flask(__name__, static_folder='static')

CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

# 导入并注册project_api蓝图
from api.project_api import project_api
app.register_blueprint(project_api)

# 导入并注册traffic_api蓝图
from api.traffic_api import traffic_api
app.register_blueprint(traffic_api)

# 导入并注册assets_config_api蓝图
from api.assets_config_api import assets_config_bp
app.register_blueprint(assets_config_bp)

# 导入并注册import_traffic_api蓝图
from api.import_traffic_api import import_traffic_api
app.register_blueprint(import_traffic_api)

# 导入并注册tools_api蓝图
from api.tools_api import tools_api
app.register_blueprint(tools_api)

# 导入并注册subdomain_api蓝图
from api.subdomain_api import subdomain_api
app.register_blueprint(subdomain_api)

# 导入并注册website_api蓝图
from api.website_api import website_api
app.register_blueprint(website_api)

# 导入并注册html_api蓝图
from api.html_api import html_api
app.register_blueprint(html_api)

# 导入并注册http_api蓝图
from api.http_api import http_api
app.register_blueprint(http_api)

# 导入并注册highlight_api蓝图
from api.highlight_api import highlight_api
app.register_blueprint(highlight_api)

# 导入并注册overview_api蓝图
from api.overview_api import overview_api
app.register_blueprint(overview_api)

# 导入并注册service_api蓝图
from api.service_api import service_api
app.register_blueprint(service_api)

# 导入并注册agent_api蓝图
from api.agent_api import agent_bp
app.register_blueprint(agent_bp)

# 导入并注册mcp_api蓝图
from api.mcp_api import mcp_bp
app.register_blueprint(mcp_bp)

# 导入并注册scaner_api蓝图
from api.scaner_api import scaner_api
app.register_blueprint(scaner_api)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/project_data/<path:filename>')
def serve_project_data(filename):
    """提供project_data目录下的静态文件（截图等）"""
    return send_from_directory('project_data', filename)

@app.route('/api/traffic/list', methods=['GET'])
def traffic_list():
    return jsonify({'traffic': []})

@app.route('/api/traffic/detail/<id>', methods=['GET'])
def traffic_detail(id):
    return jsonify({})

@app.route('/api/traffic/clear', methods=['POST'])
def traffic_clear():
    return jsonify({'message': '流量清空成功'})

@app.route('/api/assets/overview', methods=['GET'])
def assets_overview():
    return jsonify({
        'subdomains': 0,
        'websites': 0,
        'http': 0,
        'ip': 0,
        'highlights': 0
    })

@app.route('/api/assets/config', methods=['GET'])
def assets_config_get():
    return jsonify({'config': {}})

@app.route('/api/assets/config', methods=['POST'])
def assets_config_post():
    return jsonify({'message': '配置保存成功'})

@app.route('/api/assets/subdomains', methods=['GET'])
def assets_subdomains_list():
    return jsonify({'subdomains': []})

@app.route('/api/assets/subdomains', methods=['POST'])
def assets_subdomains_add():
    return jsonify({'message': '子域名添加成功'})

@app.route('/api/assets/subdomains/<id>', methods=['DELETE'])
def assets_subdomains_delete(id):
    return jsonify({'message': '子域名删除成功'})

@app.route('/api/assets/websites', methods=['GET'])
def assets_websites_list():
    return jsonify({'websites': []})

@app.route('/api/assets/websites/<id>', methods=['GET'])
def assets_websites_detail(id):
    return jsonify({})

@app.route('/api/assets/websites/<id>', methods=['DELETE'])
def assets_websites_delete(id):
    return jsonify({'message': '网站删除成功'})

@app.route('/api/assets/html', methods=['GET'])
def assets_html_list():
    return jsonify({'html': []})

@app.route('/api/assets/html/<md5>', methods=['GET'])
def assets_html_detail(md5):
    return jsonify({})

@app.route('/api/assets/html/<md5>', methods=['DELETE'])
def assets_html_delete(md5):
    return jsonify({'message': 'HTML删除成功'})

@app.route('/api/assets/ip-cidr', methods=['GET'])
def assets_ipcidr_list():
    return jsonify({'ipc': []})

@app.route('/api/assets/ip-cidr', methods=['POST'])
def assets_ipcidr_add():
    return jsonify({'message': 'IP C段添加成功'})

@app.route('/api/assets/ip-cidr/<id>', methods=['DELETE'])
def assets_ipcidr_delete(id):
    return jsonify({'message': 'IP C段删除成功'})

@app.route('/api/assets/ip', methods=['GET'])
def assets_ip_list():
    return jsonify({'ip': []})

@app.route('/api/assets/ip', methods=['POST'])
def assets_ip_add():
    return jsonify({'message': 'IP添加成功'})

@app.route('/api/assets/ip/<id>', methods=['DELETE'])
def assets_ip_delete(id):
    return jsonify({'message': 'IP删除成功'})

@app.route('/api/assets/highlights', methods=['GET'])
def assets_highlights_list():
    return jsonify({'data': []})

@app.route('/api/assets/highlights', methods=['POST'])
def assets_highlights_add():
    return jsonify({'message': '重点资产添加成功'})

@app.route('/api/assets/highlights/<id>', methods=['POST'])
def assets_highlights_update(id):
    return jsonify({'message': '重点资产更新成功'})

@app.route('/api/assets/highlights/<id>', methods=['DELETE'])
def assets_highlights_delete(id):
    return jsonify({'message': '重点资产删除成功'})



@app.route('/api/tools/encode/base64', methods=['POST'])
def tools_encode_base64():
    return jsonify({})

@app.route('/api/tools/encode/url', methods=['POST'])
def tools_encode_url():
    return jsonify({})

@app.route('/api/tools/decode/base64', methods=['POST'])
def tools_decode_base64():
    return jsonify({})

@app.route('/api/tools/decode/url', methods=['POST'])
def tools_decode_url():
    return jsonify({})

@app.route('/api/tools/clipboard', methods=['GET'])
def tools_clipboard_list():
    return jsonify({'clipboard': []})

@app.route('/api/tools/clipboard', methods=['POST'])
def tools_clipboard_add():
    return jsonify({'message': '剪贴板添加成功'})

@app.route('/api/tools/clipboard/<index>', methods=['DELETE'])
def tools_clipboard_delete(index):
    return jsonify({'message': '剪贴板删除成功'})

@app.route('/api/system/config', methods=['GET'])
def system_config_get():
    config = load_config()
    return jsonify({'config': config})

@app.route('/api/system/config', methods=['POST'])
def system_config_post():
    data = request.get_json()
    save_config(data)
    return jsonify({'message': '配置保存成功'})

@app.route('/api/system/status', methods=['GET'])
def system_status():
    return jsonify({})

if __name__ == '__main__':
    config = load_config()
    port = config.get('flask_port', 5000)
    app.run(debug=False, host='0.0.0.0', port=port)