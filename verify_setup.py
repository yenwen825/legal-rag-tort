"""
驗證專案設置是否正確
"""

import os
import sys

def check_file(path, name):
    """檢查檔案是否存在"""
    if os.path.exists(path):
        print(f"✅ {name}")
        return True
    else:
        print(f"❌ {name} - 找不到檔案")
        return False

def check_directory(path, name):
    """檢查資料夾是否存在"""
    if os.path.isdir(path):
        print(f"✅ {name}")
        return True
    else:
        print(f"❌ {name} - 找不到資料夾")
        return False

def check_env():
    """檢查 .env 檔案"""
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and api_key != 'your_openai_api_key_here':
            print(f"✅ .env 檔案已設定 (API Key 長度: {len(api_key)} 字元)")
            return True
        else:
            print("⚠️  .env 檔案存在，但 OPENAI_API_KEY 尚未設定")
            return False
    else:
        print("❌ .env 檔案不存在 - 請手動建立並填入 OPENAI_API_KEY")
        return False

def check_packages():
    """檢查必要套件是否安裝"""
    required_packages = [
        'flask',
        'openai',
        'numpy',
        'dotenv',
        'tenacity',
        'pydantic',
        'tqdm',
        'requests'
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            if package == 'dotenv':
                __import__('dotenv')
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - 尚未安裝")
            all_installed = False
    
    return all_installed

def main():
    print("=" * 60)
    print("Legal RAG Tort - 專案設置驗證")
    print("=" * 60)
    
    print("\n【檢查資料夾結構】")
    dirs_ok = all([
        check_directory('templates', 'templates/'),
        check_directory('data', 'data/'),
        check_directory('data/raw', 'data/raw/'),
        check_directory('etl', 'etl/')
    ])
    
    print("\n【檢查核心檔案】")
    files_ok = all([
        check_file('app.py', 'app.py'),
        check_file('requirements.txt', 'requirements.txt'),
        check_file('README.md', 'README.md'),
        check_file('templates/index.html', 'templates/index.html'),
        check_file('etl/fetch_data.py', 'etl/fetch_data.py'),
        check_file('etl/pipeline.py', 'etl/pipeline.py'),
        check_file('.gitignore', '.gitignore')
    ])
    
    print("\n【檢查環境變數】")
    env_ok = check_env()
    
    print("\n【檢查 Python 套件】")
    packages_ok = check_packages()
    
    print("\n" + "=" * 60)
    if dirs_ok and files_ok and env_ok and packages_ok:
        print("🎉 專案設置完成！可以開始使用")
        print("\n下一步:")
        print("  1. python etl/fetch_data.py  # 下載判決資料")
        print("  2. python etl/pipeline.py    # 清洗與向量化")
        print("  3. python app.py               # 啟動 Web 應用")
        return 0
    else:
        print("⚠️  專案設置未完成，請修正上述問題")
        print("\n常見問題:")
        if not env_ok:
            print("  - 請建立 .env 檔案並填入 OPENAI_API_KEY")
        if not packages_ok:
            print("  - 請執行: pip install -r requirements.txt")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n中斷檢查")
        sys.exit(1)
