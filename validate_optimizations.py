#!/usr/bin/env python3
"""
Simple validation test for postprocessor optimizations.
Tests that the optimized functions work correctly and don't leak memory.
"""

import tempfile
import os
import sys
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    try:
        from hy3dgen.shapegen.postprocessors import (
            pymeshlab2trimesh,
            trimesh2pymeshlab,
            reduce_face_trimesh,
            FaceReducer,
            DegenerateFaceRemover,
            MeshSimplifier
        )
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_reduce_face_trimesh():
    """Test the optimized trimesh decimation function."""
    print("\nTesting reduce_face_trimesh()...")
    try:
        import trimesh
        from hy3dgen.shapegen.postprocessors import reduce_face_trimesh
        
        # Create a simple test mesh (cube)
        mesh = trimesh.creation.box(extents=[1, 1, 1])
        original_face_count = len(mesh.faces)
        print(f"  Original faces: {original_face_count}")
        
        # Test reduction (should not reduce since it's already small)
        reduced = reduce_face_trimesh(mesh, max_facenum=100)
        reduced_face_count = len(reduced.faces)
        print(f"  After reduction: {reduced_face_count}")
        
        # Create a more complex mesh
        sphere = trimesh.creation.icosphere(subdivisions=4)
        original_faces = len(sphere.faces)
        print(f"  Complex mesh faces: {original_faces}")
        
        # Reduce to 100 faces
        reduced = reduce_face_trimesh(sphere, max_facenum=100)
        reduced_faces = len(reduced.faces)
        print(f"  After reduction: {reduced_faces}")
        
        if reduced_faces <= 100:
            print("✓ Decimation works correctly")
            return True
        else:
            print(f"✗ Decimation failed: {reduced_faces} > 100")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_temp_file_cleanup():
    """Test that temporary files are properly cleaned up."""
    print("\nTesting temporary file cleanup...")
    try:
        import trimesh
        import pymeshlab
        from hy3dgen.shapegen.postprocessors import pymeshlab2trimesh, trimesh2pymeshlab
        
        # Track temporary files before
        temp_dir = tempfile.gettempdir()
        before_files = set(os.listdir(temp_dir))
        
        # Create test mesh
        mesh = trimesh.creation.box(extents=[1, 1, 1])
        
        # Convert trimesh -> pymeshlab -> trimesh
        pymesh = trimesh2pymeshlab(mesh)
        result = pymeshlab2trimesh(pymesh)
        
        # Check if temp files were cleaned up
        after_files = set(os.listdir(temp_dir))
        new_files = after_files - before_files
        
        # Filter to only .ply files (our temp files)
        ply_files = [f for f in new_files if f.endswith('.ply')]
        
        if len(ply_files) == 0:
            print("✓ No temporary files left behind")
            return True
        else:
            print(f"✗ Found {len(ply_files)} uncleaned temporary files: {ply_files}")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_face_reducer_fast_mode():
    """Test FaceReducer with fast mode."""
    print("\nTesting FaceReducer fast mode...")
    try:
        import trimesh
        from hy3dgen.shapegen.postprocessors import FaceReducer
        
        # Create test mesh
        mesh = trimesh.creation.icosphere(subdivisions=4)
        original_faces = len(mesh.faces)
        print(f"  Original faces: {original_faces}")
        
        # Test fast mode
        reducer_fast = FaceReducer(use_fast_method=True)
        reduced_fast = reducer_fast(mesh, max_facenum=100)
        fast_faces = len(reduced_fast.faces)
        print(f"  Fast mode faces: {fast_faces}")
        
        # Test slow mode  
        reducer_slow = FaceReducer(use_fast_method=False)
        reduced_slow = reducer_slow(mesh, max_facenum=100)
        slow_faces = len(reduced_slow.faces)
        print(f"  Slow mode faces: {slow_faces}")
        
        if fast_faces <= 100 and slow_faces <= 100:
            print("✓ Both modes work correctly")
            return True
        else:
            print(f"✗ Reduction failed")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all validation tests."""
    print("=" * 60)
    print("VALIDATION TESTS FOR POSTPROCESSOR OPTIMIZATIONS")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Reduce Face Trimesh", test_reduce_face_trimesh()))
    results.append(("Temp File Cleanup", test_temp_file_cleanup()))
    results.append(("FaceReducer Fast Mode", test_face_reducer_fast_mode()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All validation tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit(main())
