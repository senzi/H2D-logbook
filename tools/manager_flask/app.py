#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from utils.loader import YAMLLoader, generate_id
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'h2d-logbook-local-manager-secret-key'

# 配置数据根目录
DATA_ROOT = os.environ.get('DATA_ROOT', '../../data')
DATA_PATH = Path(DATA_ROOT).resolve()

# 初始化 YAML 加载器
yaml_loader = YAMLLoader(DATA_PATH)

# 支持的记录类型
RECORD_TYPES = {
    'record': '打印记录',
    'plan': '打印计划',
    'consumable_purchase': '耗材采购记录',
    'consumable_retirement': '耗材退役记录',
    'maintenance': '维护记录'
}

@app.route('/')
def index():
    """主页 - 显示所有记录类型的列表"""
    try:
        records_by_type = {}
        for record_type in RECORD_TYPES.keys():
            records = yaml_loader.load_records_by_type(record_type)
            records_by_type[record_type] = records
        
        return render_template('list.html', 
                             records_by_type=records_by_type, 
                             record_types=RECORD_TYPES)
    except Exception as e:
        logger.error(f"Error loading records: {e}")
        flash(f'加载记录时出错: {e}', 'error')
        return render_template('list.html', 
                             records_by_type={}, 
                             record_types=RECORD_TYPES)

@app.route('/edit/<record_type>')
@app.route('/edit/<record_type>/<record_id>')
def edit_record(record_type, record_id=None):
    """编辑记录页面"""
    if record_type not in RECORD_TYPES:
        flash('不支持的记录类型', 'error')
        return redirect(url_for('index'))
    
    record_data = {}
    if record_id:
        try:
            record_data = yaml_loader.load_record(record_type, record_id)
            if not record_data:
                flash('记录不存在', 'error')
                return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Error loading record {record_id}: {e}")
            flash(f'加载记录时出错: {e}', 'error')
            return redirect(url_for('index'))
    
    # 加载对应的 schema
    schema = yaml_loader.load_schema(record_type)
    
    return render_template('edit.html', 
                         record_type=record_type,
                         record_type_name=RECORD_TYPES[record_type],
                         record_id=record_id,
                         record_data=record_data,
                         schema=schema)

@app.route('/save/<record_type>', methods=['POST'])
@app.route('/save/<record_type>/<record_id>', methods=['POST'])
def save_record(record_type, record_id=None):
    """保存记录"""
    if record_type not in RECORD_TYPES:
        flash('不支持的记录类型', 'error')
        return redirect(url_for('index'))
    
    try:
        # 获取表单数据
        form_data = request.form.to_dict()
        
        # 处理特殊字段类型
        processed_data = process_form_data(form_data, record_type)
        
        # 验证数据
        validation_result = yaml_loader.validate_record(record_type, processed_data)
        if not validation_result['valid']:
            flash(f'数据验证失败: {validation_result["error"]}', 'error')
            # 保留表单数据，重新渲染编辑页面
            schema = yaml_loader.load_schema(record_type)
            return render_template('edit.html', 
                                 record_type=record_type,
                                 record_type_name=RECORD_TYPES[record_type],
                                 record_id=record_id,
                                 record_data=form_data,  # 使用原始表单数据
                                 schema=schema)
        
        # 生成或使用现有 ID
        if not record_id:
            record_id = generate_id(processed_data.get('title', ''), processed_data.get('model_name', ''))
        
        # 添加时间戳
        now = datetime.now().isoformat()
        if 'created_at' not in processed_data:
            processed_data['created_at'] = now
        processed_data['updated_at'] = now
        
        # 保存记录
        success = yaml_loader.save_record(record_type, record_id, processed_data)
        
        if success:
            flash('记录保存成功', 'success')
            logger.info(f"Record saved: {record_type}/{record_id}")
            return redirect(url_for('index'))
        else:
            flash('保存记录时出错', 'error')
            # 保存失败时也保留表单数据
            schema = yaml_loader.load_schema(record_type)
            return render_template('edit.html', 
                                 record_type=record_type,
                                 record_type_name=RECORD_TYPES[record_type],
                                 record_id=record_id,
                                 record_data=form_data,
                                 schema=schema)
            
    except Exception as e:
        logger.error(f"Error saving record: {e}")
        flash(f'保存记录时出错: {e}', 'error')
        # 异常时也保留表单数据
        schema = yaml_loader.load_schema(record_type)
        return render_template('edit.html', 
                             record_type=record_type,
                             record_type_name=RECORD_TYPES[record_type],
                             record_id=record_id,
                             record_data=request.form.to_dict(),
                             schema=schema)

@app.route('/delete/<record_type>/<record_id>', methods=['POST'])
def delete_record(record_type, record_id):
    """删除记录"""
    if record_type not in RECORD_TYPES:
        flash('不支持的记录类型', 'error')
        return redirect(url_for('index'))
    
    try:
        success = yaml_loader.delete_record(record_type, record_id)
        if success:
            flash('记录删除成功', 'success')
            logger.info(f"Record deleted: {record_type}/{record_id}")
        else:
            flash('删除记录时出错', 'error')
    except Exception as e:
        logger.error(f"Error deleting record: {e}")
        flash(f'删除记录时出错: {e}', 'error')
    
    return redirect(url_for('index'))

@app.route('/publish', methods=['POST'])
def publish_to_git():
    """发布到 Git"""
    try:
        # 切换到项目根目录
        project_root = Path(__file__).parent.parent.parent
        os.chdir(project_root)
        
        # 执行 Git 命令
        commands = [
            ['git', 'add', '.'],
            ['git', 'commit', '-m', f'Update records - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'],
            ['git', 'push']
        ]
        
        output = []
        for cmd in commands:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            output.append(f"$ {' '.join(cmd)}")
            output.append(result.stdout)
            if result.stderr:
                output.append(f"Error: {result.stderr}")
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
        
        flash('发布成功', 'success')
        logger.info("Git publish successful")
        return jsonify({'success': True, 'output': '\n'.join(output)})
        
    except subprocess.TimeoutExpired:
        error_msg = 'Git 操作超时'
        flash(error_msg, 'error')
        logger.error(error_msg)
        return jsonify({'success': False, 'error': error_msg})
    except subprocess.CalledProcessError as e:
        error_msg = f'Git 操作失败: {e.stderr}'
        flash(error_msg, 'error')
        logger.error(error_msg)
        return jsonify({'success': False, 'error': error_msg})
    except Exception as e:
        error_msg = f'发布时出错: {e}'
        flash(error_msg, 'error')
        logger.error(error_msg)
        return jsonify({'success': False, 'error': error_msg})

@app.route('/view')
def view_records():
    """记录浏览页面"""
    try:
        # 获取筛选参数
        record_type = request.args.get('type', '')
        search_query = request.args.get('search', '')
        
        # 加载所有记录
        all_records = []
        for rtype in RECORD_TYPES.keys():
            records = yaml_loader.load_records_by_type(rtype)
            for record_id, record_data in records.items():
                record_data['id'] = record_id
                record_data['type'] = rtype
                record_data['type_name'] = RECORD_TYPES[rtype]
                all_records.append(record_data)
        
        # 按创建时间排序（最新的在前）
        all_records.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # 应用筛选
        filtered_records = all_records
        if record_type and record_type in RECORD_TYPES:
            filtered_records = [r for r in filtered_records if r['type'] == record_type]
        
        if search_query:
            search_query = search_query.lower()
            filtered_records = [r for r in filtered_records if 
                              search_query in r.get('title', '').lower() or
                              search_query in r.get('model_name', '').lower() or
                              search_query in r.get('model_url', '').lower() or
                              search_query in r.get('notes', '').lower()]
        
        return render_template('view.html', 
                             records=filtered_records,
                             record_types=RECORD_TYPES,
                             current_type=record_type,
                             search_query=search_query)
    except Exception as e:
        logger.error(f"Error loading view: {e}")
        flash(f'加载浏览页面时出错: {e}', 'error')
        return render_template('view.html', 
                             records=[],
                             record_types=RECORD_TYPES,
                             current_type='',
                             search_query='')

def process_form_data(form_data, record_type):
    """处理表单数据，转换特殊字段类型"""
    processed = {}
    
    for key, value in form_data.items():
        if not value.strip():
            continue
            
        # 处理数字字段
        if key in ['rating', 'print_time_hours', 'print_time_minutes', 'layer_height', 'infill_percentage']:
            try:
                if key in ['print_time_hours', 'print_time_minutes', 'infill_percentage']:
                    processed[key] = int(value)
                elif key == 'layer_height':
                    processed[key] = float(value)
                elif key == 'rating':
                    rating = int(value)
                    if 1 <= rating <= 5:
                        processed[key] = rating
                    else:
                        raise ValueError(f"Rating must be between 1 and 5, got {rating}")
            except ValueError as e:
                logger.warning(f"Invalid value for {key}: {value}, error: {e}")
                continue
        
        # 处理布尔字段
        elif key in ['supports_used', 'success']:
            processed[key] = value.lower() in ['true', '1', 'on', 'yes']
        
        # 处理列表字段（逗号分隔）
        elif key in ['tags', 'materials']:
            if value.strip():
                processed[key] = [tag.strip() for tag in value.split(',') if tag.strip()]
        
        # 普通字符串字段
        else:
            processed[key] = value.strip()
    
    return processed

if __name__ == '__main__':
    # 确保数据目录存在
    DATA_PATH.mkdir(parents=True, exist_ok=True)
    for record_type in RECORD_TYPES.keys():
        (DATA_PATH / record_type).mkdir(exist_ok=True)
    
    # 确保日志目录存在
    Path('logs').mkdir(exist_ok=True)
    
    logger.info(f"Starting H2D Logbook Local Manager")
    logger.info(f"Data path: {DATA_PATH}")
    
    app.run(host='127.0.0.1', port=5000, debug=True)
