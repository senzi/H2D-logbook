#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from ruamel.yaml import YAML
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

def generate_id(title='', model_name=''):
    """生成记录 ID，格式为 YYYYMMDD-keyword"""
    date_str = datetime.now().strftime('%Y%m%d')
    
    # 提取关键词
    keyword = ''
    if title:
        keyword = title.strip()[:20]
    elif model_name:
        keyword = model_name.strip()[:20]
    else:
        keyword = 'record'
    
    # 清理关键词，只保留字母数字和中文
    import re
    keyword = re.sub(r'[^\w\u4e00-\u9fff-]', '', keyword)
    if not keyword:
        keyword = 'record'
    
    return f"{date_str}-{keyword}"

class YAMLLoader:
    """YAML 文件加载器和管理器"""
    
    def __init__(self, data_path):
        self.data_path = Path(data_path)
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.width = 4096
        self.yaml.indent(mapping=2, sequence=4, offset=2)
        
        # 加载 schemas
        self.schemas = {}
        self._load_schemas()
    
    def _load_schemas(self):
        """加载所有 JSON Schema"""
        schema_dir = Path(__file__).parent.parent / 'schemas'
        if not schema_dir.exists():
            logger.warning(f"Schema directory not found: {schema_dir}")
            return
        
        for schema_file in schema_dir.glob('*.json'):
            try:
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema_name = schema_file.stem
                    self.schemas[schema_name] = json.load(f)
                    logger.info(f"Loaded schema: {schema_name}")
            except Exception as e:
                logger.error(f"Error loading schema {schema_file}: {e}")
    
    def load_schema(self, record_type):
        """获取指定类型的 schema"""
        return self.schemas.get(record_type, {})
    
    def load_records_by_type(self, record_type):
        """加载指定类型的所有记录"""
        records = {}
        type_dir = self.data_path / record_type
        
        if not type_dir.exists():
            logger.info(f"Directory not found: {type_dir}")
            return records
        
        for yaml_file in type_dir.glob('*.yml'):
            try:
                record_id = yaml_file.stem
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    record_data = self.yaml.load(f)
                    if record_data:
                        records[record_id] = record_data
            except Exception as e:
                logger.error(f"Error loading {yaml_file}: {e}")
        
        return records
    
    def load_record(self, record_type, record_id):
        """加载单个记录"""
        yaml_file = self.data_path / record_type / f"{record_id}.yml"
        
        if not yaml_file.exists():
            return None
        
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                return self.yaml.load(f)
        except Exception as e:
            logger.error(f"Error loading record {record_id}: {e}")
            return None
    
    def save_record(self, record_type, record_id, record_data):
        """保存记录到 YAML 文件"""
        try:
            # 确保目录存在
            type_dir = self.data_path / record_type
            type_dir.mkdir(parents=True, exist_ok=True)
            
            yaml_file = type_dir / f"{record_id}.yml"
            
            with open(yaml_file, 'w', encoding='utf-8') as f:
                self.yaml.dump(record_data, f)
            
            logger.info(f"Record saved: {yaml_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving record {record_id}: {e}")
            return False
    
    def delete_record(self, record_type, record_id):
        """删除记录"""
        try:
            yaml_file = self.data_path / record_type / f"{record_id}.yml"
            
            if yaml_file.exists():
                yaml_file.unlink()
                logger.info(f"Record deleted: {yaml_file}")
                return True
            else:
                logger.warning(f"Record not found for deletion: {yaml_file}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting record {record_id}: {e}")
            return False
    
    def validate_record(self, record_type, record_data):
        """验证记录数据"""
        schema = self.schemas.get(record_type)
        
        if not schema:
            logger.warning(f"No schema found for type: {record_type}")
            return {'valid': True, 'error': None}
        
        try:
            validate(instance=record_data, schema=schema)
            return {'valid': True, 'error': None}
        except ValidationError as e:
            return {'valid': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return {'valid': False, 'error': str(e)}
