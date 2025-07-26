"""
Code Modifier - Module for self-modification capabilities
Allows Ranger AI to modify its own code based on learning and improvements
"""

import asyncio
import ast
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import shutil
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)

class CodeModifier:
    def __init__(self):
        self.backup_dir = "backups"
        self.modification_history = []
        self.max_modifications_per_session = 10
        self.modification_count = 0
        
        # Create backup directory
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Files that can be modified
        self.modifiable_files = [
            'main.py',
            'modules/learning_engine.py',
            'modules/web_verifier.py',
            'modules/knowledge_base.py',
            'modules/conversation_analyzer.py',
            'modules/self_improvement.py'
        ]
        
        # Safety patterns - code that should not be modified
        self.safety_patterns = [
            r'import\s+os\s*$',  # Prevent os import removal
            r'import\s+subprocess\s*$',  # Prevent subprocess import
            r'__import__\s*\(',  # Prevent dynamic imports
            r'eval\s*\(',  # Prevent eval usage
            r'exec\s*\(',  # Prevent exec usage
            r'open\s*\(.*,\s*[\'"]w[\'"]',  # Prevent file writing
            r'file\s*\(.*,\s*[\'"]w[\'"]',  # Prevent file writing
        ]
    
    async def apply_modification(self, modification: Dict[str, Any]) -> bool:
        """Apply a code modification safely"""
        try:
            # Check modification limit
            if self.modification_count >= self.max_modifications_per_session:
                logger.warning("Modification limit reached for this session")
                return False
            
            # Validate modification
            if not self._validate_modification(modification):
                logger.error("Invalid modification request")
                return False
            
            # Create backup before modification
            backup_path = await self._create_backup(modification.get('file_path'))
            if not backup_path:
                logger.error("Failed to create backup")
                return False
            
            # Apply the modification
            success = await self._apply_safe_modification(modification)
            
            if success:
                self.modification_count += 1
                self.modification_history.append({
                    'modification': modification,
                    'timestamp': datetime.now().isoformat(),
                    'backup_path': backup_path
                })
                
                logger.info(f"Successfully applied modification: {modification.get('description', 'Unknown')}")
                return True
            else:
                # Restore from backup
                await self._restore_from_backup(backup_path, modification.get('file_path'))
                logger.error("Modification failed, restored from backup")
                return False
                
        except Exception as e:
            logger.error(f"Error applying modification: {e}")
            return False
    
    def _validate_modification(self, modification: Dict[str, Any]) -> bool:
        """Validate a modification request"""
        try:
            required_fields = ['file_path', 'modification_type', 'content']
            for field in required_fields:
                if field not in modification:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Check if file is modifiable
            file_path = modification['file_path']
            if file_path not in self.modifiable_files:
                logger.error(f"File {file_path} is not modifiable")
                return False
            
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"File {file_path} does not exist")
                return False
            
            # Validate modification type
            valid_types = ['add_function', 'modify_function', 'add_import', 'add_class', 'modify_class']
            if modification['modification_type'] not in valid_types:
                logger.error(f"Invalid modification type: {modification['modification_type']}")
                return False
            
            # Check for safety violations
            content = modification['content']
            for pattern in self.safety_patterns:
                if re.search(pattern, content, re.MULTILINE):
                    logger.error(f"Safety violation detected: {pattern}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating modification: {e}")
            return False
    
    async def _create_backup(self, file_path: str) -> Optional[str]:
        """Create a backup of the file before modification"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{Path(file_path).stem}_{timestamp}.bak"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            shutil.copy2(file_path, backup_path)
            
            logger.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    async def _restore_from_backup(self, backup_path: str, file_path: str):
        """Restore file from backup"""
        try:
            shutil.copy2(backup_path, file_path)
            logger.info(f"Restored {file_path} from backup")
        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
    
    async def _apply_safe_modification(self, modification: Dict[str, Any]) -> bool:
        """Apply a modification safely"""
        try:
            file_path = modification['file_path']
            modification_type = modification['modification_type']
            content = modification['content']
            
            # Read current file
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            # Apply modification based on type
            if modification_type == 'add_function':
                new_content = await self._add_function(current_content, content)
            elif modification_type == 'modify_function':
                new_content = await self._modify_function(current_content, content)
            elif modification_type == 'add_import':
                new_content = await self._add_import(current_content, content)
            elif modification_type == 'add_class':
                new_content = await self._add_class(current_content, content)
            elif modification_type == 'modify_class':
                new_content = await self._modify_class(current_content, content)
            else:
                logger.error(f"Unknown modification type: {modification_type}")
                return False
            
            # Validate new content
            if not self._validate_python_syntax(new_content):
                logger.error("Modified content has syntax errors")
                return False
            
            # Write modified content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying modification: {e}")
            return False
    
    async def _add_function(self, current_content: str, function_code: str) -> str:
        """Add a new function to the file"""
        try:
            # Find the end of the file (before any trailing whitespace)
            lines = current_content.split('\n')
            
            # Find the last non-empty line
            last_non_empty = len(lines) - 1
            while last_non_empty >= 0 and not lines[last_non_empty].strip():
                last_non_empty -= 1
            
            # Add function at the end
            if last_non_empty >= 0:
                lines.insert(last_non_empty + 1, '\n' + function_code)
            else:
                lines.append(function_code)
            
            return '\n'.join(lines)
            
        except Exception as e:
            logger.error(f"Error adding function: {e}")
            return current_content
    
    async def _modify_function(self, current_content: str, modification: str) -> str:
        """Modify an existing function"""
        try:
            # Parse the modification (should contain function name and new content)
            lines = modification.split('\n')
            function_name = lines[0].strip()
            
            # Find the function in the current content
            pattern = rf'def\s+{function_name}\s*\([^)]*\):'
            match = re.search(pattern, current_content)
            
            if not match:
                logger.error(f"Function {function_name} not found")
                return current_content
            
            # Replace the function
            start_pos = match.start()
            
            # Find the end of the function
            lines = current_content.split('\n')
            start_line = current_content[:start_pos].count('\n')
            
            # Find the end of the function (indentation-based)
            end_line = start_line
            for i in range(start_line + 1, len(lines)):
                if lines[i].strip() and not lines[i].startswith(' ' * 4):
                    break
                end_line = i
            
            # Replace the function
            new_lines = lines[:start_line] + [modification] + lines[end_line + 1:]
            return '\n'.join(new_lines)
            
        except Exception as e:
            logger.error(f"Error modifying function: {e}")
            return current_content
    
    async def _add_import(self, current_content: str, import_statement: str) -> str:
        """Add a new import statement"""
        try:
            lines = current_content.split('\n')
            
            # Find the last import statement
            last_import = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    last_import = i
            
            # Add import after the last import or at the beginning
            if last_import >= 0:
                lines.insert(last_import + 1, import_statement)
            else:
                # Find the first non-comment, non-docstring line
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped and not stripped.startswith('#') and not stripped.startswith('"""'):
                        lines.insert(i, import_statement)
                        break
            
            return '\n'.join(lines)
            
        except Exception as e:
            logger.error(f"Error adding import: {e}")
            return current_content
    
    async def _add_class(self, current_content: str, class_code: str) -> str:
        """Add a new class to the file"""
        try:
            # Similar to adding function
            lines = current_content.split('\n')
            
            # Find the last non-empty line
            last_non_empty = len(lines) - 1
            while last_non_empty >= 0 and not lines[last_non_empty].strip():
                last_non_empty -= 1
            
            # Add class at the end
            if last_non_empty >= 0:
                lines.insert(last_non_empty + 1, '\n' + class_code)
            else:
                lines.append(class_code)
            
            return '\n'.join(lines)
            
        except Exception as e:
            logger.error(f"Error adding class: {e}")
            return current_content
    
    async def _modify_class(self, current_content: str, modification: str) -> str:
        """Modify an existing class"""
        try:
            # Parse the modification (should contain class name and new content)
            lines = modification.split('\n')
            class_name = lines[0].strip()
            
            # Find the class in the current content
            pattern = rf'class\s+{class_name}\s*[:\(]'
            match = re.search(pattern, current_content)
            
            if not match:
                logger.error(f"Class {class_name} not found")
                return current_content
            
            # Replace the class (similar to function modification)
            start_pos = match.start()
            lines = current_content.split('\n')
            start_line = current_content[:start_pos].count('\n')
            
            # Find the end of the class
            end_line = start_line
            for i in range(start_line + 1, len(lines)):
                if lines[i].strip() and not lines[i].startswith(' ' * 4):
                    break
                end_line = i
            
            # Replace the class
            new_lines = lines[:start_line] + [modification] + lines[end_line + 1:]
            return '\n'.join(new_lines)
            
        except Exception as e:
            logger.error(f"Error modifying class: {e}")
            return current_content
    
    def _validate_python_syntax(self, content: str) -> bool:
        """Validate Python syntax of modified content"""
        try:
            ast.parse(content)
            return True
        except SyntaxError as e:
            logger.error(f"Syntax error in modified content: {e}")
            return False
    
    async def get_modification_history(self) -> List[Dict[str, Any]]:
        """Get history of modifications"""
        return self.modification_history
    
    async def reset_modification_count(self):
        """Reset the modification count for a new session"""
        self.modification_count = 0
        logger.info("Modification count reset")
    
    async def update_modifiable_files(self, files: List[str]):
        """Update the list of modifiable files"""
        self.modifiable_files = files
        logger.info(f"Updated modifiable files: {files}")
    
    async def add_safety_pattern(self, pattern: str):
        """Add a new safety pattern"""
        self.safety_patterns.append(pattern)
        logger.info(f"Added safety pattern: {pattern}")
    
    async def create_restore_point(self, description: str = None):
        """Create a restore point for the entire project"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            restore_dir = os.path.join(self.backup_dir, f"restore_point_{timestamp}")
            
            os.makedirs(restore_dir, exist_ok=True)
            
            # Copy all modifiable files
            for file_path in self.modifiable_files:
                if os.path.exists(file_path):
                    dest_path = os.path.join(restore_dir, file_path)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.copy2(file_path, dest_path)
            
            # Save metadata
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'description': description or 'Auto-generated restore point',
                'files': self.modifiable_files,
                'modification_count': self.modification_count
            }
            
            with open(os.path.join(restore_dir, 'metadata.json'), 'w') as f:
                import json
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Created restore point: {restore_dir}")
            return restore_dir
            
        except Exception as e:
            logger.error(f"Error creating restore point: {e}")
            return None 