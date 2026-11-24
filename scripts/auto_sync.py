import subprocess
import shutil
import os
import sys

def main():
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(repo_dir)

    print("[ETF Auto-Sync] 正在执行每日分钟累计成交额同步更新...")
    script_path = os.path.join(repo_dir, "scripts", "daily_cumdays_update.py")
    res = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("[Warn]", res.stderr)

    desktop_dest = r"C:\Users\31345\Desktop\重点ETF资金看板.html"
    src_html = os.path.join(repo_dir, "index.html")
    if os.path.exists(src_html):
        shutil.copy2(src_html, desktop_dest)
        print(f"[ETF Auto-Sync] 已成功同步镜像至桌面: {desktop_dest}")

    try:
        subprocess.run(["git", "add", "cumdays.json", "index.html"], check=True)
        diff = subprocess.run(["git", "diff", "--cached", "--quiet"])
        if diff.returncode != 0:
            subprocess.run(["git", "commit", "-m", "chore(data): auto-update daily cumdays"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("[ETF Auto-Sync] 已成功自动推送到 GitHub 远程仓库")
    except Exception as e:
        print(f"[ETF Auto-Sync] Git 同步提示: {e}")

if __name__ == "__main__":
    main()
