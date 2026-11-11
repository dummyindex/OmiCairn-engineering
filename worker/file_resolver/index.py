#!/usr/bin/env python3
"""
File Resolver Script - Quick file inspection tool
Supports: text files, h5ad files, RDS files, and binary files
"""

import os
import sys
import argparse
from pathlib import Path
import mimetypes


def get_file_info(filepath):
    """Get basic file information"""
    stat = os.stat(filepath)
    return {
        'size': stat.st_size,
        'size_mb': stat.st_size / (1024 * 1024),
        'modified': stat.st_mtime,
    }


def is_text_file(filepath):
    """Check if file is a text file"""
    mime_type, _ = mimetypes.guess_type(filepath)
    if mime_type and mime_type.startswith('text'):
        return True
    
    # Check common text extensions
    text_extensions = {'.txt', '.csv', '.tsv', '.json', '.xml', '.html', '.md', 
                      '.py', '.r', '.R', '.sh', '.yml', '.yaml', '.log'}
    if Path(filepath).suffix.lower() in text_extensions:
        return True
    
    # Try to read first few bytes
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(1024)
            # Check if it's mostly ASCII/UTF-8
            try:
                chunk.decode('utf-8')
                return True
            except UnicodeDecodeError:
                return False
    except:
        return False


def print_text_file(filepath, max_lines=100):
    """Print text file content"""
    print(f"\n{'='*60}")
    print(f"TEXT FILE: {filepath}")
    print(f"{'='*60}")
    
    info = get_file_info(filepath)
    print(f"Size: {info['size_mb']:.2f} MB ({info['size']} bytes)")
    
    print(f"\n--- Content (first {max_lines} lines) ---\n")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if i > max_lines:
                    print(f"\n... (truncated, showing first {max_lines} lines)")
                    break
                print(line.rstrip())
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                for i, line in enumerate(f, 1):
                    if i > max_lines:
                        print(f"\n... (truncated, showing first {max_lines} lines)")
                        break
                    print(line.rstrip())
        except Exception as e:
            print(f"Error reading file: {e}")


def print_h5ad_structure(filepath):
    """Print h5ad file structure without loading full data into memory"""
    print(f"\n{'='*60}")
    print(f"H5AD FILE: {filepath}")
    print(f"{'='*60}")
    
    try:
        import h5py
        import numpy as np
        
        info = get_file_info(filepath)
        print(f"Size: {info['size_mb']:.2f} MB ({info['size']} bytes)")
        
        with h5py.File(filepath, 'r') as f:
            print(f"\n--- H5AD Structure ---")
            
            # Main matrix
            if 'X' in f:
                X = f['X']
                print(f"\nX (Main Expression Matrix):")
                if isinstance(X, h5py.Group):
                    # Sparse matrix
                    if 'data' in X:
                        print(f"  Type: Sparse (CSR/CSC)")
                        print(f"  Shape: {X.attrs.get('shape', 'N/A')}")
                        print(f"  Data dtype: {X['data'].dtype}")
                        print(f"  Number of non-zero elements: {len(X['data'])}")
                else:
                    # Dense matrix
                    print(f"  Type: Dense")
                    print(f"  Shape: {X.shape}")
                    print(f"  Dtype: {X.dtype}")
            
            # Observations (obs_names)
            if 'obs' in f:
                obs = f['obs']
                if '_index' in obs:
                    obs_names = obs['_index']
                    print(f"\nobs_names (Cell/Sample IDs):")
                    print(f"  Count: {len(obs_names)}")
                    print(f"  Dtype: {obs_names.dtype}")
                    # Show first few
                    sample = obs_names[:5] if len(obs_names) >= 5 else obs_names[:]
                    decoded = [x.decode() if isinstance(x, bytes) else x for x in sample]
                    print(f"  First few: {decoded}")
                
                # obs columns
                print(f"\nobs.keys() (Observation metadata):")
                for key in obs.keys():
                    if key != '_index':
                        item = obs[key]
                        if hasattr(item, 'dtype'):
                            print(f"  - {key}: dtype={item.dtype}, shape={item.shape}")
                        elif hasattr(item, 'keys'):
                            print(f"  - {key}: (categorical with {len(item)} items)")
            
            # Variables (var_names)
            if 'var' in f:
                var = f['var']
                if '_index' in var:
                    var_names = var['_index']
                    print(f"\nvar_names (Gene/Feature IDs):")
                    print(f"  Count: {len(var_names)}")
                    print(f"  Dtype: {var_names.dtype}")
                    # Show first few
                    sample = var_names[:5] if len(var_names) >= 5 else var_names[:]
                    decoded = [x.decode() if isinstance(x, bytes) else x for x in sample]
                    print(f"  First few: {decoded}")
                
                # var columns
                print(f"\nvar.keys() (Feature metadata):")
                for key in var.keys():
                    if key != '_index':
                        item = var[key]
                        if hasattr(item, 'dtype'):
                            print(f"  - {key}: dtype={item.dtype}, shape={item.shape}")
                        elif hasattr(item, 'keys'):
                            print(f"  - {key}: (categorical with {len(item)} items)")
            
            # Layers
            if 'layers' in f:
                layers = f['layers']
                print(f"\nlayers.keys():")
                for key in layers.keys():
                    layer = layers[key]
                    if isinstance(layer, h5py.Group):
                        print(f"  - {key}: Sparse, shape={layer.attrs.get('shape', 'N/A')}")
                    else:
                        print(f"  - {key}: dtype={layer.dtype}, shape={layer.shape}")
            
            # obsm (multi-dimensional obs annotations)
            if 'obsm' in f:
                obsm = f['obsm']
                print(f"\nobsm.keys() (Observation matrices, e.g., PCA, UMAP):")
                for key in obsm.keys():
                    item = obsm[key]
                    if hasattr(item, 'dtype'):
                        print(f"  - {key}: dtype={item.dtype}, shape={item.shape}")
            
            # varm (multi-dimensional var annotations)
            if 'varm' in f:
                varm = f['varm']
                print(f"\nvarm.keys() (Feature matrices):")
                for key in varm.keys():
                    item = varm[key]
                    if hasattr(item, 'dtype'):
                        print(f"  - {key}: dtype={item.dtype}, shape={item.shape}")
            
            # obsp (pairwise obs annotations)
            if 'obsp' in f:
                obsp = f['obsp']
                print(f"\nobsp.keys() (Observation pairwise matrices):")
                for key in obsp.keys():
                    item = obsp[key]
                    if isinstance(item, h5py.Group):
                        print(f"  - {key}: Sparse, shape={item.attrs.get('shape', 'N/A')}")
                    else:
                        print(f"  - {key}: dtype={item.dtype}, shape={item.shape}")
            
            # varp (pairwise var annotations)
            if 'varp' in f:
                varp = f['varp']
                print(f"\nvarp.keys() (Feature pairwise matrices):")
                for key in varp.keys():
                    item = varp[key]
                    if isinstance(item, h5py.Group):
                        print(f"  - {key}: Sparse, shape={item.attrs.get('shape', 'N/A')}")
                    else:
                        print(f"  - {key}: dtype={item.dtype}, shape={item.shape}")
            
            # uns (unstructured annotations)
            if 'uns' in f:
                uns = f['uns']
                print(f"\nuns.keys() (Unstructured annotations):")
                def print_uns_recursive(group, prefix=""):
                    for key in group.keys():
                        item = group[key]
                        if isinstance(item, h5py.Group):
                            print(f"  {prefix}- {key}: (group)")
                            print_uns_recursive(item, prefix + "  ")
                        elif isinstance(item, h5py.Dataset):
                            print(f"  {prefix}- {key}: dtype={item.dtype}, shape={item.shape}")
                        else:
                            print(f"  {prefix}- {key}: {type(item)}")
                
                print_uns_recursive(uns)
        
        print(f"\n{'='*60}")
        
    except ImportError:
        print("Error: h5py is not installed. Install with: pip install h5py")
        print("Falling back to anndata (slower)...")
        try:
            import anndata as ad
            adata = ad.read_h5ad(filepath, backed='r')
            print(f"\n--- AnnData Object (backed mode) ---")
            print(adata)
        except ImportError:
            print("Error: anndata is also not installed. Install with: pip install anndata")
    except Exception as e:
        print(f"Error reading h5ad file: {e}")


def print_rds_structure(filepath):
    """Print RDS file structure"""
    print(f"\n{'='*60}")
    print(f"RDS FILE: {filepath}")
    print(f"{'='*60}")
    
    info = get_file_info(filepath)
    print(f"Size: {info['size_mb']:.2f} MB ({info['size']} bytes)")
    
    try:
        import subprocess
        import json
        
        # Method 1: Try using rpy2
        try:
            from rpy2 import robjects
            from rpy2.robjects import r
            
            print("\n--- RDS Structure (using rpy2) ---")
            
            # Load the RDS file
            r_script = f'''
            obj <- readRDS("{filepath}")
            
            # Get structure info
            list(
                class = class(obj),
                type = typeof(obj),
                length = length(obj),
                names = if(is.null(names(obj))) NA else head(names(obj), 10),
                dim = dim(obj),
                str = capture.output(str(obj, max.level = 2, vec.len = 3))
            )
            '''
            
            result = r(r_script)
            
            print(f"\nClass: {result[0]}")
            print(f"Type: {result[1]}")
            print(f"Length: {result[2][0] if len(result[2]) > 0 else 'N/A'}")
            
            if not (len(result[3]) == 1 and str(result[3][0]) == 'NA'):
                print(f"Names (first 10): {list(result[3])}")
            
            if result[4] is not None and len(result[4]) > 0:
                print(f"Dimensions: {tuple(result[4])}")
            
            print(f"\nStructure:")
            for line in result[5]:
                print(f"  {line}")
            
        except ImportError:
            print("\nrpy2 not installed, trying R command line...")
            
            # Method 2: Use R command line
            r_script = f'''
            obj <- readRDS("{filepath.replace(chr(92), '/')}")
            cat("Class:", class(obj), "\\n")
            cat("Type:", typeof(obj), "\\n")
            cat("Length:", length(obj), "\\n")
            if(!is.null(names(obj))) {{
                cat("Names (first 10):", head(names(obj), 10), "\\n")
            }}
            if(!is.null(dim(obj))) {{
                cat("Dimensions:", dim(obj), "\\n")
            }}
            cat("\\nStructure:\\n")
            str(obj, max.level = 2, vec.len = 3)
            '''
            
            result = subprocess.run(
                ['Rscript', '-e', r_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"\n{result.stdout}")
            else:
                print(f"Error running R: {result.stderr}")
                
    except ImportError:
        print("Error: rpy2 is not installed and R is not available")
        print("Install rpy2 with: pip install rpy2")
        print("Or install R from: https://www.r-project.org/")
    except FileNotFoundError:
        print("Error: R is not installed or not in PATH")
        print("Install R from: https://www.r-project.org/")
    except Exception as e:
        print(f"Error reading RDS file: {e}")


def print_binary_file_info(filepath):
    """Print binary file information"""
    print(f"\n{'='*60}")
    print(f"BINARY FILE: {filepath}")
    print(f"{'='*60}")
    
    info = get_file_info(filepath)
    print(f"Size: {info['size_mb']:.2f} MB ({info['size']} bytes)")
    
    # Get file extension and mime type
    ext = Path(filepath).suffix
    mime_type, _ = mimetypes.guess_type(filepath)
    
    print(f"Extension: {ext}")
    print(f"MIME Type: {mime_type or 'Unknown'}")
    
    # Show first few bytes (hex dump)
    print(f"\n--- First 256 bytes (hex) ---")
    try:
        with open(filepath, 'rb') as f:
            data = f.read(256)
            # Print hex dump
            for i in range(0, len(data), 16):
                hex_part = ' '.join(f'{b:02x}' for b in data[i:i+16])
                ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
                print(f"{i:08x}  {hex_part:<48}  {ascii_part}")
    except Exception as e:
        print(f"Error reading binary file: {e}")


def resolve_file(filepath, max_lines=100):
    """Main function to resolve and print file information"""
    filepath = os.path.abspath(filepath)
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return
    
    if not os.path.isfile(filepath):
        print(f"Error: Not a file: {filepath}")
        return
    
    # Get file extension
    ext = Path(filepath).suffix.lower()
    
    # Route to appropriate handler
    if ext == '.h5ad':
        print_h5ad_structure(filepath)
    elif ext == '.rds':
        print_rds_structure(filepath)
    elif is_text_file(filepath):
        print_text_file(filepath, max_lines)
    else:
        print_binary_file_info(filepath)


def main():
    parser = argparse.ArgumentParser(
        description='Quick file inspection tool for text, h5ad, RDS, and binary files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python index.py data.txt
  python index.py data.h5ad
  python index.py data.rds
  python index.py --max-lines 50 large_file.csv
        '''
    )
    
    parser.add_argument('filepath', help='Path to the file to inspect')
    parser.add_argument('--max-lines', type=int, default=200,
                       help='Maximum number of lines to display for text files (default: 200)')
    
    args = parser.parse_args()
    
    resolve_file(args.filepath, args.max_lines)


if __name__ == '__main__':
    main()
