import nbformat
import ast
import os
import glob
import re
import builtins

class VariableRenamer(ast.NodeTransformer):
    def __init__(self):
        self.mapping = {}
        # Builtins and common library names to avoid renaming
        self.ignored = set(dir(builtins)) | {'np', 'pd', 'plt', 'sns', 'math', 'os', 'sys'}

    def get_simple_name(self, old_name):
        if old_name in self.ignored:
            return old_name
        
        if old_name in self.mapping:
            return self.mapping[old_name]
        
        new_name = old_name
        
        # Remove underscores
        if '_' in new_name:
            new_name = new_name.replace('_', '')
        
        # Check for 'ai'
        if new_name.lower() == 'ai':
            new_name = 'x'
            
        # If it changed, store in mapping
        if new_name != old_name:
            self.mapping[old_name] = new_name
            return new_name
            
        return old_name

    def visit_Name(self, node):
        node.id = self.get_simple_name(node.id)
        return node

    def visit_arg(self, node):
        node.arg = self.get_simple_name(node.arg)
        return node

    def visit_FunctionDef(self, node):
        node.name = self.get_simple_name(node.name)
        self.generic_visit(node)
        return node
    
    def visit_Attribute(self, node):
        # We generally don't want to rename attributes (like math.sqrt)
        # unless it's our own object. For simple labs, it's safer to only rename the base name.
        node.value = self.visit(node.value)
        return node

def clean_code(code):
    if not code.strip():
        return ""
    try:
        # Check if it's a magics cell (IPython)
        if code.startswith('%') or code.startswith('!'):
            lines = code.split('\n')
            cleaned_lines = []
            for line in lines:
                line = re.sub(r'#.*$', '', line).rstrip()
                if line:
                    cleaned_lines.append(line)
            return '\n'.join(cleaned_lines)

        tree = ast.parse(code)
        renamer = VariableRenamer()
        tree = renamer.visit(tree)
        cleaned_code = ast.unparse(tree)
        return cleaned_code
    except Exception as e:
        # If parsing fails (e.g. invalid syntax or IPython specific syntax), fallback to regex
        lines = code.split('\n')
        cleaned_lines = []
        for line in lines:
            # Strip comments
            line = re.sub(r'#.*$', '', line).rstrip()
            if line:
                # Simple underscore removal for variables (very naive)
                # This part is risky, so maybe just strip comments and handle 'ai'
                line = re.sub(r'\bai\b', 'x', line)
                cleaned_lines.append(line)
        return '\n'.join(cleaned_lines)

def process_notebook(filepath):
    print(f"Processing {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)

        for cell in nb.cells:
            if cell.cell_type == 'code':
                source = cell.source
                cleaned = clean_code(source)
                cell.source = cleaned
                # Clear outputs
                cell.outputs = []
                cell.execution_count = None
            elif cell.cell_type == 'markdown':
                # Remove comments from markdown? User said "dont amke any comemt in any block"
                # usually refers to code comments. But let's check.
                pass

        with open(filepath, 'w', encoding='utf-8') as f:
            nbformat.write(nb, f)
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

if __name__ == "__main__":
    files = glob.glob("*.ipynb")
    for f in files:
        process_notebook(os.path.abspath(f))
    print("Done!")
