# coding: utf-8
"""
CDP浏览器控制模块（纯接口，可复用）
@Time :    3/14/2025 11:05
@Author:  fff
@File: browser_cdp.py
@Software: PyCharm

功能说明：
1. 通过 Playwright 连接 Chrome CDP 端口
2. 控制浏览器 Tab 进行页面访问
3. 获取页面 title、截图、html、url 等信息
4. 不依赖数据库，可作为独立接口使用
"""

from re import T
from socket import timeout
from playwright.async_api import async_playwright
import asyncio
import random
import os
import subprocess
import socket
import psutil
from service.Class_Core_Function import Class_Core_Function


class BrowserCDP:
    """
    CDP浏览器控制器
    提供纯浏览器操作接口，不涉及数据库操作
    """
    
    def __init__(self, cdp_port=None, browser_thread=10):
        """
        初始化CDP浏览器控制器
        :param cdp_port: Chrome CDP 端口，默认从配置文件读取
        :param browser_thread: 并发 Tab 数量
        """
        self.Core_Function = Class_Core_Function()
        self.browser = None
        self.cdp_port = cdp_port or self._get_cdp_port()
        self.browser_thread = browser_thread
        
        # 爬取结果
        self.list_url = []          # 提取的URL列表
        self.page_result_list = []  # 页面结果列表
        self.html_list = []         # HTML数据列表

    def _get_cdp_port(self):
        """从配置文件获取 Chrome CDP 端口"""
        try:
            config = self.Core_Function.callback_config()
            if config and 'chrome_cdp_port' in config:
                return config['chrome_cdp_port']
        except:
            pass
        return 19227  # 默认端口

    def _get_chrome_path(self):
        """从配置文件获取 Chrome 路径"""
        try:
            config = self.Core_Function.callback_config()
            if config and 'chrome_path' in config:
                return config['chrome_path']
        except:
            pass
        return r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # 默认路径

    def _check_port_in_use(self, port):
        """检查端口是否被占用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', port)) == 0
        except:
            return False

    def _kill_chrome_on_port(self, port):
        """杀掉占用指定端口的Chrome进程"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        cmdline = proc.info['cmdline']
                        if cmdline and any(f'--remote-debugging-port={port}' in arg for arg in cmdline):
                            self.Core_Function.callback_logging().info(f"杀掉Chrome进程: PID={proc.info['pid']}")
                            proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.Core_Function.callback_logging().error(f"清理Chrome进程失败: {e}")

    def _start_chrome_headless(self):
        """
        启动Chrome无头模式（参考service_manager.py）
        :return: bool - 是否成功
        """
        try:
            chrome_path = self._get_chrome_path()
            cdp_port = self.cdp_port
            
            # 获取代理端口
            config = self.Core_Function.callback_config()
            proxy_port = config.get('burp_port', 8080) if config else 8080
            
            # 获取项目名和UA
            project_name = 'default'
            user_agent = None
            try:
                project_config = self.Core_Function.callback_project_config()
                if project_config:
                    project_name = project_config.get('Project', 'default')
                    user_agent = project_config.get('user_agent', '')
            except:
                pass
            
            # Chrome数据目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            user_data_dir = os.path.join(project_root, 'project_data', project_name, 'chrome_data', 'headless')
            os.makedirs(user_data_dir, exist_ok=True)
            
            # 如果端口已被占用，先尝试清理
            if self._check_port_in_use(cdp_port):
                self._kill_chrome_on_port(cdp_port)
                import time
                time.sleep(2)
            
            # 构建启动命令
            cmd_parts = [
                f'"{chrome_path}"',
                f'--remote-debugging-port={cdp_port}',
                f'--proxy-server=127.0.0.1:{proxy_port}',
                f'--user-data-dir="{user_data_dir}"',
                '--headless',
                '--disable-gpu',
                '--no-sandbox',
                '--window-size=1280,1080',
                '--remote-allow-origins=*',
            ]
            
            if user_agent:
                cmd_parts.append(f'--user-agent="{user_agent}"')
            
            cmd = ' '.join(cmd_parts)
            self.Core_Function.callback_logging().info(f"启动Chrome headless: CDP={cdp_port}, Proxy=127.0.0.1:{proxy_port}")
            
            subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 等待启动
            import time
            time.sleep(3)
            
            if self._check_port_in_use(cdp_port):
                self.Core_Function.callback_logging().info(f"Chrome headless 启动成功，端口: {cdp_port}")
                return True
            else:
                self.Core_Function.callback_logging().error("Chrome headless 启动失败，端口未监听")
                return False
                
        except Exception as e:
            self.Core_Function.callback_logging().error(f"启动Chrome headless失败: {e}")
            return False

    def _screenshot_cmd(self, url, output_path):
        """
        使用命令行截图（更快）
        :param url: 目标URL
        :param output_path: 截图保存路径
        :return: bool - 是否成功
        """
        try:
            chrome_path = self._get_chrome_path()
            cmd = [
                chrome_path,
                '--headless',
                f'--screenshot={output_path}',
                '--window-size=1280,1080',
                '--disable-gpu',
                '--hide-scrollbars',
                url
            ]
            # 执行命令，超时10秒
            result = subprocess.run(
                cmd,
                timeout=10,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            # 检查截图文件是否存在
            return os.path.exists(output_path)
        except subprocess.TimeoutExpired:
            self.Core_Function.callback_logging().error(f"命令行截图超时: {url}")
            return False
        except Exception as e:
            self.Core_Function.callback_logging().error(f"命令行截图失败: {url}, 错误: {e}")
            return False

    # ==================== 页面事件处理 ====================
    
    async def _handle_popup(self, page):
        """关闭click打开的新窗口"""
        try:
            self.list_url.append(page.url)
            await page.close()
        except Exception as e:
            self.Core_Function.callback_logging().error(e)

    async def _handle_dialog(self, dialog):
        """处理alert之类"""
        await dialog.dismiss()

    # ==================== 页面操作 ====================
    
    async def _scroll_to_bottom(self, page, max_scrolls=3):
        """滚动到页面底部（带超时保护）"""
        try:
            previous_height = await asyncio.wait_for(
                page.evaluate("document.body.scrollHeight"), 
                timeout=2
            )

            for _ in range(max_scrolls):
                try:
                    await asyncio.wait_for(page.mouse.wheel(0, 1000), timeout=1)
                    await asyncio.sleep(0.3)
                    new_height = await asyncio.wait_for(
                        page.evaluate("document.body.scrollHeight"), 
                        timeout=2
                    )
                    if new_height == previous_height:
                        break
                    previous_height = new_height
                except asyncio.TimeoutError:
                    break
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            self.Core_Function.callback_logging().error(f"滚动页面失败: {e}")

    async def _extract_links(self, page):
        """提取页面中的链接"""
        try:
            await page.evaluate('''
                var list_href=[];
                for(i=0;i<document.getElementsByTagName("a").length;i++){
                    list_href.push(document.getElementsByTagName("a")[i].href);
                };
                for(i=0;i<document.getElementsByTagName("form").length;i++){
                    list_href.push(document.getElementsByTagName("form")[i].action);
                }
            ''')
            links = list(set(await page.evaluate('list_href')))
            self.list_url.extend(links)
        except Exception as error:
            pass

    async def _get_page_data(self, page, url):
        """
        获取页面数据
        :param page: Playwright page 对象
        :param url: 目标URL
        :return: 页面数据字典
        """
        try:
            # 获取HTML
            html = await page.content()
            html_md5 = self.Core_Function.md5_convert(html)
            html_len = len(html)
            
            # HTML数据
            html_data = {
                'html': html,
                'html_md5': html_md5,
                'html_len': html_len,
                'time': self.Core_Function.callback_time(0),
                'status': 0
            }
            self.html_list.append(html_data)
            
            # 页面结果
            target_request = {
                'url': url,
                'status': 1,
                'html_browser_md5': html_md5,
                'html_len': html_len,
                'title': await page.title(),
                'current_url': page.url,
                'time': self.Core_Function.callback_time(0)
            }
            # 提取链接
            try:
                await self._extract_links(page)
            except:
                pass
            
            self.page_result_list.append(target_request)
            

            
            return target_request
        except Exception as e:
            return None

    async def _setup_page(self, page):
        """设置页面的反检测脚本和事件处理"""
        try:
            # 设置事件处理
            page.on("dialog", self._handle_dialog)
            page.on("popup", self._handle_popup)
            
            # 注入反检测脚本
            js = """
                Object.defineProperties(navigator, {webdriver:{get:()=>false}});
                Object.defineProperties(navigator, {platform:{get:()=>'Win32'}});
                list_href=[]
                window.open = function(url) { location.href=url; };
                window.close = function () { return false; };
            """
            await page.add_init_script(js)
        except Exception as e:
            pass

    async def _goto_page(self, page, url):
        """阶段1：仅打开页面，等待domcontentloaded"""
        try:
            await self._setup_page(page)
            await page.goto(url, wait_until="domcontentloaded", timeout=10000)
            return True
        except Exception as error:
            self.Core_Function.callback_logging().error(f"访问页面失败: {url}, 错误: {error}")
            return False

    async def _process_page(self, page, url):
        """阶段2：获取页面数据和提取链接（带超时保护）"""
        try:
            # 先停止页面加载，避免持续渲染卡住
            try:
                await asyncio.wait_for(
                    page.evaluate("window.stop()"),
                    timeout=2
                )
            except:
                pass
            
            # 滚动页面（带超时）
            try:
                await asyncio.wait_for(self._scroll_to_bottom(page), timeout=10)
            except asyncio.TimeoutError:
                pass
            
            # 获取页面数据（带超时）
            result = await asyncio.wait_for(
                self._get_page_data(page, url), 
                timeout=15
            )
            
            if result:
                self.Core_Function.callback_logging().info(f"动态爬取: {url} | Title: {result.get('title', 'N/A')}")
            
            return result
        except asyncio.TimeoutError:
            self.Core_Function.callback_logging().error(f"处理页面超时: {url}")
            return None
        except Exception as error:
            self.Core_Function.callback_logging().error(f"处理页面失败: {url}, 错误: {error}")
            return None

    # ==================== 主要接口 ====================
    
    async def crawl_async(self, url_list):
        """
        异步爬取入口（优化版：两阶段处理）
        阶段1：并行打开所有页面（等待domcontentloaded）
        阶段2：循环获取页面数据
        
        :param url_list: URL列表
        :return: 页面结果列表
        """
        self.list_url = []
        self.page_result_list = []
        self.html_list = []

        if not url_list:
            return []

        async with async_playwright() as p:
            # 连接到 Chrome CDP 端口（带重启机制）
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    self.browser = await asyncio.wait_for(
                        p.chromium.connect_over_cdp(
                            endpoint_url=f"http://127.0.0.1:{self.cdp_port}",
                            timeout=10000
                        ),
                        timeout=15
                    )
                    break
                except asyncio.TimeoutError:
                    retry_count += 1
                    self.Core_Function.callback_logging().error(f"连接CDP超时，尝试重启Chrome headless ({retry_count}/{max_retries})")
                    if retry_count >= max_retries:
                        raise Exception(f"连接CDP失败，已重试{max_retries}次")
                    # 重启Chrome headless
                    if self._start_chrome_headless():
                        await asyncio.sleep(3)
                    else:
                        self.Core_Function.callback_logging().error("Chrome headless 重启失败")
                except Exception as e:
                    retry_count += 1
                    self.Core_Function.callback_logging().error(f"连接CDP失败: {e}，尝试重启Chrome headless ({retry_count}/{max_retries})")
                    if retry_count >= max_retries:
                        raise
                    # 重启Chrome headless
                    if self._start_chrome_headless():
                        await asyncio.sleep(3)
                    else:
                        self.Core_Function.callback_logging().error("Chrome headless 重启失败")
            
            # 检查连接是否成功
            if not self.browser:
                raise Exception("连接CDP失败：browser对象为None")
            
            # ===== 清理：关闭所有现有tab，只保留一个 =====
            try:
                pages = self.browser.contexts[0].pages
                # 关闭前N-1个tab，只保留最后一个
                for page in pages[:-1]:
                    try:
                        await asyncio.wait_for(page.close(), timeout=3)
                    except:
                        pass
            except Exception as e:
                self.Core_Function.callback_logging().error(f"清理初始tab失败: {e}")
            
            # 计算需要的Tab数量：比URL列表多1个，防止关闭浏览器
            needed_tabs = min(len(url_list), self.browser_thread) + 1
            
            # 补齐不足的 Tab（连接后只剩1个，需要补齐）
            pages = self.browser.contexts[0].pages
            tab_count = len(pages)
            if tab_count < needed_tabs:
                for _ in range(needed_tabs - tab_count):
                    await self.browser.contexts[0].new_page()

            # 获取调整后的页面列表（前N个用于访问，最后1个保持空白）
            pages = self.browser.contexts[0].pages
            
            # ===== 阶段1：并行打开所有页面 =====
            url_page_map = {}  # 记录URL与Page的对应关系
            tasks = []
            
            for i, url in enumerate(url_list[:self.browser_thread]):
                page = pages[i]
                url_page_map[url] = page
                tasks.append(self._goto_page(page, url))
            
            # 并行执行所有 goto（带异常捕获，避免单个URL卡住影响整体）
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=20
                )
                # 记录失败的URL
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        url = url_list[i] if i < len(url_list) else "unknown"
                        self.Core_Function.callback_logging().error(f"goto失败: {url}, 错误: {result}")
            except asyncio.TimeoutError:
                self.Core_Function.callback_logging().error(f"阶段1总体超时(20秒)，跳过剩余任务")
            except Exception as e:
                self.Core_Function.callback_logging().error(f"阶段1异常: {e}")
            await asyncio.sleep(3)
            # ===== 阶段2：倒序循环获取页面数据（带超时控制） =====
            # 倒序处理：先打开的页面等待时间更长，让它多加载一会儿
            # 最后打开的页面刚加载完，先处理它，效率更高
            items = list(url_page_map.items())[::-1]  # 倒序
            
            for url, page in items:
                try:
                    # 单个页面处理超时8秒
                    await asyncio.wait_for(
                        self._process_page(page, url),
                        timeout=8
                    )
                except asyncio.TimeoutError:
                    self.Core_Function.callback_logging().error(f"处理页面超时(20秒): {url}")
                except Exception as e:
                    self.Core_Function.callback_logging().error(f"处理页面失败: {url}, 错误: {e}")
            
            # ===== 阶段3：批量截图 =====
            image_dir = self.Core_Function.create_image_path()
            for page_data in self.page_result_list:
                try:
                    url = page_data.get('url', '')
                    if not url:
                        continue
                    
                    random_name = ''.join(random.sample('ABCDEFGHIJKLMNOPQRSTUVWXYZ012345678zyxwvutsrqponmlkjihgfedcba', 15))
                    filename_img = "%s/%s.png" % (image_dir, random_name)
                    
                    # 使用异步方式调用同步截图方法
                    success = await asyncio.get_event_loop().run_in_executor(
                        None, 
                        self._screenshot_cmd, 
                        url, 
                        filename_img
                    )
                    
                    if success:
                        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                        relative_path = os.path.relpath(filename_img, project_root).replace('\\', '/')
                        page_data['screenshot'] = relative_path
                    else:
                        page_data['screenshot'] = ''
                except Exception as e:
                    self.Core_Function.callback_logging().error(f"截图失败: {url}, 错误: {e}")
                    page_data['screenshot'] = ''

        print('爬取完成')
        return self.page_result_list

    def crawl(self, url_list):
        """
        同步爬取入口
        :param url_list: URL列表
        :return: dict - 爬取结果
        """
        try:
            if not url_list:
                return {
                    'success': False,
                    'message': 'URL列表为空',
                    'pages': [],
                    'urls': [],
                    'htmls': []
                }
            
            asyncio.run(self.crawl_async(url_list))
            
            return {
                'success': True,
                'message': '爬取完成',
                'pages': self.page_result_list,
                'urls': list(set(self.list_url)),
                'htmls': self.html_list
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'爬取失败: {str(e)}',
                'pages': [],
                'urls': [],
                'htmls': []
            }

    def get_results(self):
        """获取爬取结果"""
        return {
            'pages': self.page_result_list,
            'urls': list(set(self.list_url)),
            'htmls': self.html_list
        }


if __name__ == "__main__":
    # 测试代码
    browser = BrowserCDP(cdp_port=19227, browser_thread=5)
    result = browser.crawl(['https://www.baidu.com', 'https://www.molun.com'])
    print(result)
