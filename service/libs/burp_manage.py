"""
Burp Suite 管理模块
负责 Burp Suite 的启动、停止和状态检查
"""

import subprocess
import psutil
import time


class BurpManager:
    """Burp Suite 管理器"""

    def __init__(self):
        self.process = None
        self.is_running = False

    def start(self, project, burp_path):
        """
        启动 Burp Suite

        Args:
            project: 项目名称
            burp_path: Burp Suite 安装路径

        Returns:
            tuple: (success: bool, message: dict or str)
        """
        if not burp_path:
            return False, "未配置 Burp Suite 路径"

        if self.is_running:
            return False, "Burp Suite 已在运行中"

        # 构建 Burp 启动命令
        burp_command = f'java --add-opens=java.desktop/javax.swing=ALL-UNNAMED --add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED --add-opens=java.base/jdk.internal.org.objectweb.asm.tree=ALL-UNNAMED --add-opens=java.base/jdk.internal.org.objectweb.asm.Opcodes=ALL-UNNAMED -javaagent:{burp_path}\\BurpLoaderKeygen.jar -noverify -jar {burp_path}\\burpsuite_pro.jar'

        try:
            # 使用 subprocess 启动 Burp Suite
            self.process = subprocess.Popen(
                burp_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # 等待启动
            time.sleep(3)

            if self.process.poll() is None:
                self.is_running = True
                return True, {'process': self.process}
            else:
                return False, 'Burp Suite 启动失败，进程已退出'
        except Exception as e:
            return False, f'Burp Suite 启动失败: {str(e)}'

    def stop(self):
        """
        停止 Burp Suite

        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.is_running:
            return False, "Burp Suite 未运行"

        try:
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # 强制终止
                    self.process.kill()
                    self.process.wait()

            # 查找并终止所有 Burp Suite 相关进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'java' in proc.info['name'].lower():
                        cmdline = proc.info['cmdline']
                        if cmdline and 'burpsuite' in ' '.join(cmdline).lower():
                            proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            self.process = None
            self.is_running = False
            return True, "Burp Suite 已停止"
        except Exception as e:
            return False, f'停止失败: {str(e)}'

    def get_status(self):
        """
        获取 Burp Suite 状态

        Returns:
            dict: {'is_running': bool, 'message': str}
        """
        try:
            # 通过检查进程是否存在来判断
            if self.process and self.process.poll() is None:
                self.is_running = True
            else:
                # 检查是否有 Burp Suite 进程在运行
                found = False
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc.info['name'] and 'java' in proc.info['name'].lower():
                            cmdline = proc.info['cmdline']
                            if cmdline and 'burpsuite' in ' '.join(cmdline).lower():
                                found = True
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                self.is_running = found

            return {
                'is_running': self.is_running,
                'message': '运行中' if self.is_running else '已停止'
            }
        except Exception as e:
            return {
                'is_running': False,
                'message': f'状态检查失败: {str(e)}'
            }

    def restart(self, project, burp_path):
        """
        重启 Burp Suite

        Args:
            project: 项目名称
            burp_path: Burp Suite 安装路径

        Returns:
            tuple: (success: bool, message: dict or str)
        """
        stop_result = self.stop()
        if not stop_result[0]:
            # 如果停止失败但进程不存在，可以继续启动
            if '未运行' not in stop_result[1]:
                return False, f'停止失败: {stop_result[1]}'

        time.sleep(2)
        return self.start(project, burp_path)
