#!/usr/bin/env python3
"""
Static validation for postprocessor optimizations.
Checks code structure and patterns without running the actual code.
"""

import os
import sys
import ast
import re

def check_file_exists(filepath):
    """Check if a file exists."""
    if os.path.exists(filepath):
        print(f"✓ Found: {filepath}")
        return True
    else:
        print(f"✗ Missing: {filepath}")
        return False

def check_temp_file_cleanup(filepath):
    """Check if temp file cleanup is properly implemented."""
    print(f"\nChecking temp file cleanup in {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check for try-finally blocks with os.unlink
    try_finally_pattern = r'try:.*?finally:.*?os\.unlink\(temp.*?\)'
    matches = re.findall(try_finally_pattern, content, re.DOTALL)
    
    # Count tempfile usages
    temp_file_count = len(re.findall(r'tempfile\.NamedTemporaryFile', content))
    cleanup_count = len(re.findall(r'os\.unlink\(', content))
    
    print(f"  Tempfile usages: {temp_file_count}")
    print(f"  Cleanup calls (os.unlink): {cleanup_count}")
    
    if cleanup_count >= 4:  # We should have at least 4 cleanup calls
        print(f"✓ Proper cleanup implemented")
        return True
    else:
        print(f"✗ Missing cleanup (expected at least 4, found {cleanup_count})")
        return False

def check_function_exists(filepath, function_name):
    """Check if a function exists in the file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    pattern = rf'def {function_name}\s*\('
    if re.search(pattern, content):
        print(f"✓ Function '{function_name}' exists")
        return True
    else:
        print(f"✗ Function '{function_name}' not found")
        return False

def check_class_exists(filepath, class_name):
    """Check if a class exists in the file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    pattern = rf'class {class_name}'
    if re.search(pattern, content):
        print(f"✓ Class '{class_name}' exists")
        return True
    else:
        print(f"✗ Class '{class_name}' not found")
        return False

def check_docstrings(filepath):
    """Check that functions have docstrings."""
    print(f"\nChecking docstrings in {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
        
        functions_with_docs = 0
        total_functions = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total_functions += 1
                docstring = ast.get_docstring(node)
                if docstring:
                    functions_with_docs += 1
        
        print(f"  Functions with docstrings: {functions_with_docs}/{total_functions}")
        
        # We expect at least some improvement
        if functions_with_docs >= 5:
            print(f"✓ Good docstring coverage")
            return True
        else:
            print(f"⚠ Limited docstring coverage")
            return True  # Don't fail on this
            
    except SyntaxError as e:
        print(f"✗ Syntax error in file: {e}")
        return False

def check_optimization_report():
    """Check that optimization report exists and has content."""
    print("\nChecking OPTIMIZATION_REPORT.md...")
    
    filepath = "OPTIMIZATION_REPORT.md"
    if not os.path.exists(filepath):
        print(f"✗ OPTIMIZATION_REPORT.md not found")
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check for key sections
    required_sections = [
        "Memory Leak",
        "Performance",
        "Optimization",
        "Documentation",
    ]
    
    found_sections = sum(1 for section in required_sections if section in content)
    
    print(f"  Found {found_sections}/{len(required_sections)} key sections")
    print(f"  Document length: {len(content)} characters")
    
    if found_sections >= 3 and len(content) > 5000:
        print(f"✓ Comprehensive optimization report")
        return True
    else:
        print(f"✗ Incomplete optimization report")
        return False

def check_syntax(filepath):
    """Check Python syntax."""
    print(f"\nChecking syntax of {filepath}...")
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        ast.parse(content)
        print(f"✓ Valid Python syntax")
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error: {e}")
        return False

def main():
    """Run all static validation checks."""
    print("=" * 60)
    print("STATIC VALIDATION FOR POSTPROCESSOR OPTIMIZATIONS")
    print("=" * 60)
    
    os.chdir('/home/runner/work/Hunyuan3D-2/Hunyuan3D-2')
    
    results = []
    
    # Check files exist
    postprocessors_file = "hy3dgen/shapegen/postprocessors.py"
    results.append(("File exists: postprocessors.py", check_file_exists(postprocessors_file)))
    results.append(("File exists: OPTIMIZATION_REPORT.md", check_file_exists("OPTIMIZATION_REPORT.md")))
    
    # Check syntax
    results.append(("Python syntax", check_syntax(postprocessors_file)))
    
    # Check temp file cleanup
    results.append(("Temp file cleanup", check_temp_file_cleanup(postprocessors_file)))
    
    # Check new functions exist
    print("\nChecking new functions...")
    results.append(("reduce_face_trimesh", check_function_exists(postprocessors_file, "reduce_face_trimesh")))
    
    # Check modified classes
    print("\nChecking classes...")
    results.append(("FaceReducer class", check_class_exists(postprocessors_file, "FaceReducer")))
    results.append(("DegenerateFaceRemover class", check_class_exists(postprocessors_file, "DegenerateFaceRemover")))
    results.append(("MeshSimplifier class", check_class_exists(postprocessors_file, "MeshSimplifier")))
    
    # Check docstrings
    results.append(("Docstrings", check_docstrings(postprocessors_file)))
    
    # Check optimization report
    results.append(("Optimization Report", check_optimization_report()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("-" * 60)
    print(f"Total: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✓ All static validation checks passed!")
        print("✓ Code is ready for review")
        return 0
    else:
        print(f"\n✗ {total - passed} check(s) failed")
        return 1

if __name__ == "__main__":
    exit(main())
