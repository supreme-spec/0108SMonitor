#!/usr/bin/env python3
"""
GPU Support Checker
Проверяет доступность GPU для onnxruntime и faiss перед установкой.
"""

import sys

def check_cuda():
    """Проверяет наличие CUDA Toolkit"""
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ NVIDIA GPU найден:")
            print(result.stdout.split('\n')[0:3])
            return True
        else:
            print("❌ NVIDIA GPU не найден или nvidia-smi недоступен")
            return False
    except Exception as e:
        print(f"❌ Ошибка проверки NVIDIA GPU: {e}")
        return False

def check_onnxruntime_gpu():
    """Проверяет доступность onnxruntime-gpu"""
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        print(f"✅ ONNX Runtime доступен. Провайдеры: {providers}")
        
        if 'CUDAExecutionProvider' in providers:
            print("✅ CUDAExecutionProvider доступен для ONNX Runtime")
            return True
        else:
            print("⚠️ CUDAExecutionProvider недоступен, будет использован CPU")
            return False
    except ImportError:
        print("⚠️ onnxruntime не установлен. Установите его:")
        print("   pip install onnxruntime-gpu  # для GPU")
        print("   pip install onnxruntime      # для CPU")
        return None
    except Exception as e:
        print(f"❌ Ошибка проверки ONNX Runtime: {e}")
        return False

def check_faiss_gpu():
    """Проверяет доступность faiss-gpu"""
    try:
        import faiss
        print("✅ FAISS установлен")
        
        try:
            res = faiss.StandardGpuResources()
            print("✅ FAISS GPU поддерживается")
            return True
        except Exception as e:
            print(f"⚠️ FAISS GPU недоступен: {e}")
            print("   Будет использована CPU-версия FAISS")
            return False
    except ImportError:
        print("⚠️ faiss не установлен. Установите его:")
        print("   pip install faiss-gpu  # для GPU")
        print("   pip install faiss-cpu  # для CPU")
        return None
    except Exception as e:
        print(f"❌ Ошибка проверки FAISS: {e}")
        return False

def main():
    print("=" * 60)
    print("GPU Support Checker для Smart Security Monitor")
    print("=" * 60)
    print()
    
    print("1. Проверка NVIDIA GPU...")
    cuda_available = check_cuda()
    print()
    
    print("2. Проверка ONNX Runtime...")
    onnx_gpu = check_onnxruntime_gpu()
    print()
    
    print("3. Проверка FAISS...")
    faiss_gpu = check_faiss_gpu()
    print()
    
    print("=" * 60)
    print("РЕКОМЕНДАЦИИ:")
    print("=" * 60)
    
    if cuda_available:
        if onnx_gpu and faiss_gpu:
            print("✅ Все компоненты GPU доступны!")
            print("   Используйте requirements.txt с GPU-версиями.")
        else:
            print("⚠️ GPU доступен, но не все компоненты поддерживают GPU:")
            if not onnx_gpu:
                print("   - Установите: pip install onnxruntime-gpu")
            if not faiss_gpu:
                print("   - Установите: pip install faiss-gpu")
    else:
        print("❌ NVIDIA GPU недоступен.")
        print("   Используйте CPU-версии:")
        print("   pip install onnxruntime faiss-cpu")
    
    print()
    print("Для подробной установки см. GPU_SETUP.md")

if __name__ == "__main__":
    main()
