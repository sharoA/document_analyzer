#!/usr/bin/env python3
"""
配置pip使用国内镜像源 - 支持阿里云、清华大学、腾讯云
"""

import os
import sys
import subprocess
import time
import urllib.request
from pathlib import Path

# 支持的镜像源配置
MIRROR_SOURCES = {
    "aliyun": {
        "name": "阿里云",
        "url": "https://mirrors.aliyun.com/pypi/simple/",
        "host": "mirrors.aliyun.com"
    },
    "tsinghua": {
        "name": "清华大学",
        "url": "https://pypi.tuna.tsinghua.edu.cn/simple/",
        "host": "pypi.tuna.tsinghua.edu.cn"
    },
    "tencent": {
        "name": "腾讯云",
        "url": "https://mirrors.cloud.tencent.com/pypi/simple/",
        "host": "mirrors.cloud.tencent.com"
    },
    "ustc": {
        "name": "中科大",
        "url": "https://pypi.mirrors.ustc.edu.cn/simple/",
        "host": "pypi.mirrors.ustc.edu.cn"
    },
    "douban": {
        "name": "豆瓣",
        "url": "https://pypi.douban.com/simple/",
        "host": "pypi.douban.com"
    }
}

def test_mirror_speed(mirror_key):
    """测试镜像源的响应速度"""
    mirror = MIRROR_SOURCES[mirror_key]
    try:
        start_time = time.time()
        response = urllib.request.urlopen(mirror["url"], timeout=5)
        end_time = time.time()
        return end_time - start_time
    except:
        return float('inf')

def find_fastest_mirror():
    """自动选择最快的镜像源"""
    print("🔍 正在测试镜像源速度...")
    
    # 优先测试默认的三个镜像源
    priority_mirrors = ["aliyun", "tsinghua", "tencent"]
    speeds = {}
    
    for mirror_key in priority_mirrors:
        mirror = MIRROR_SOURCES[mirror_key]
        print(f"  测试 {mirror['name']}...", end="")
        speed = test_mirror_speed(mirror_key)
        speeds[mirror_key] = speed
        if speed == float('inf'):
            print(" ❌ 超时")
        else:
            print(f" ✅ {speed:.2f}秒")
    
    # 选择最快的镜像
    fastest = min(speeds.items(), key=lambda x: x[1])
    if fastest[1] == float('inf'):
        print("⚠️ 所有镜像源都无法访问，使用阿里云作为默认")
        return "aliyun"
    
    fastest_mirror = MIRROR_SOURCES[fastest[0]]
    print(f"🚀 选择最快镜像源: {fastest_mirror['name']} ({fastest[1]:.2f}秒)")
    return fastest[0]

def setup_pip_config(mirror_key="auto"):
    """设置pip配置文件使用指定镜像"""
    if mirror_key == "auto":
        mirror_key = find_fastest_mirror()
    
    mirror = MIRROR_SOURCES[mirror_key]
    print(f"🔧 配置pip使用{mirror['name']}镜像源...")
    
    # 确定pip配置目录
    if sys.platform == "win32":
        pip_config_dir = Path.home() / "pip"
        config_file = pip_config_dir / "pip.ini"
    else:
        pip_config_dir = Path.home() / ".pip"
        config_file = pip_config_dir / "pip.conf"
    
    # 创建配置目录
    pip_config_dir.mkdir(exist_ok=True)
    
    # pip配置内容
    config_content = f"""[global]
index-url = {mirror['url']}
trusted-host = {mirror['host']}

[install]
trusted-host = {mirror['host']}
"""
    
    # 写入配置文件
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✅ pip配置文件已创建: {config_file}")
    print(f"📍 当前使用镜像源: {mirror['name']} - {mirror['url']}")
    return True

def install_requirements_with_mirror(mirror_key="auto"):
    """使用指定镜像安装requirements.txt中的包"""
    if mirror_key == "auto":
        mirror_key = find_fastest_mirror()
    
    mirror = MIRROR_SOURCES[mirror_key]
    print(f"📦 使用{mirror['name']}镜像安装依赖包...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt 文件不存在")
        return False
    
    try:
        # 使用指定镜像安装
        cmd = [
            sys.executable, "-m", "pip", "install", 
            "-r", "requirements.txt",
            "-i", mirror['url'],
            "--trusted-host", mirror['host']
        ]
        
        print("执行命令:", " ".join(cmd))
        result = subprocess.run(cmd, check=True)
        print("✅ 依赖包安装完成")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装失败: {e}")
        return False

def upgrade_pip_with_mirror(mirror_key="auto"):
    """使用指定镜像升级pip"""
    if mirror_key == "auto":
        mirror_key = find_fastest_mirror()
    
    mirror = MIRROR_SOURCES[mirror_key]
    print(f"🔄 使用{mirror['name']}镜像升级pip...")
    
    try:
        cmd = [
            sys.executable, "-m", "pip", "install", "--upgrade", "pip",
            "-i", mirror['url'],
            "--trusted-host", mirror['host']
        ]
        
        subprocess.run(cmd, check=True)
        print("✅ pip升级完成")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ pip升级失败: {e}")
        return False

def show_mirror_info():
    """显示镜像源信息"""
    print("\n📋 支持的镜像源:")
    for key, mirror in MIRROR_SOURCES.items():
        status = "🌟" if key in ["aliyun", "tsinghua", "tencent"] else "📍"
        print(f"  {status} {mirror['name']}: {mirror['url']}")
    
    print("\n💡 临时使用镜像源的命令:")
    print("pip install package_name -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com")

def main():
    """主函数"""
    print("🚀 pip国内镜像配置工具")
    print("支持阿里云、清华大学、腾讯云等镜像源")
    print("=" * 60)
    
    # 显示镜像源信息
    show_mirror_info()
    
    print("\n选择操作:")
    print("1. 自动选择最快镜像源并配置")
    print("2. 手动选择镜像源")
    print("3. 升级pip")
    print("4. 安装项目依赖包")
    print("5. 全部执行（推荐）")
    
    choice = input("\n请输入选择 (1-5): ").strip()
    
    if choice == "1":
        setup_pip_config("auto")
    elif choice == "2":
        print("\n选择镜像源:")
        for i, (key, mirror) in enumerate(MIRROR_SOURCES.items(), 1):
            status = "🌟" if key in ["aliyun", "tsinghua", "tencent"] else "📍"
            print(f"  {i}. {status} {mirror['name']}")
        
        try:
            mirror_choice = int(input("请输入镜像源编号: ")) - 1
            mirror_keys = list(MIRROR_SOURCES.keys())
            if 0 <= mirror_choice < len(mirror_keys):
                setup_pip_config(mirror_keys[mirror_choice])
            else:
                print("❌ 无效选择")
        except ValueError:
            print("❌ 请输入有效数字")
    elif choice == "3":
        upgrade_pip_with_mirror("auto")
    elif choice == "4":
        install_requirements_with_mirror("auto")
    elif choice == "5":
        print("\n🔄 执行全部操作...")
        mirror_key = find_fastest_mirror()
        setup_pip_config(mirror_key)
        upgrade_pip_with_mirror(mirror_key)
        install_requirements_with_mirror(mirror_key)
    else:
        print("❌ 无效选择")
        return
    
    print("\n✅ 操作完成!")
    print("💡 现在可以正常使用pip安装包，将自动使用配置的镜像源")

if __name__ == "__main__":
    main() 