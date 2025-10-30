#!/usr/bin/env python3
"""
HTML 文件合并工具
将 deepseek-01.html 到 deepseek-12.html 合并为一个完整的 HTML 文件
"""

import re
from pathlib import Path
from typing import List, Dict, Set

class HTMLMerger:
    def __init__(self):
        self.files = [f"deepseek-{i:02d}.html" for i in range(1, 13)]
        self.all_slides = []
        self.all_modals = []
        self.all_scripts = []
        self.chart_configs = []
        self.common_css = None
        self.external_deps = set()
        
    def read_file(self, filename: str) -> str:
        """读取文件内容"""
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    
    def extract_slides(self, content: str, file_num: int) -> List[str]:
        """从HTML内容中提取所有幻灯片"""
        # 提取所有 <section class="slide"> 标签
        pattern = r'<section class="slide"[^>]*>.*?</section>'
        slides = re.findall(pattern, content, re.DOTALL)
        
        # 为每个幻灯片添加章节标识
        processed_slides = []
        for i, slide in enumerate(slides):
            # 在幻灯片中添加章节和序号信息
            slide_with_chapter = slide.replace(
                '<section class="slide"',
                f'<section class="slide" data-chapter="{file_num}" data-slide="{i+1}"'
            )
            processed_slides.append(slide_with_chapter)
        
        return processed_slides
    
    def extract_modals(self, content: str, file_num: int) -> List[str]:
        """提取所有模态框"""
        # 使用更精确的正则表达式来匹配完整的模态框结构
        # 查找以 <div id="modal- 开始的模态框
        pattern = r'<div id="modal-[^"]+"\s+class="modal">.*?(?=<div id="modal-|<script|</body|$)'
        modals = re.findall(pattern, content, re.DOTALL)
        
        # 为模态框ID添加前缀避免冲突
        processed_modals = []
        for modal in modals:
            # 替换modal的ID，添加章节前缀
            modal_with_prefix = re.sub(
                r'id="(modal-[^"]+)"',
                lambda m: f'id="ch{file_num:02d}-{m.group(1)}"',
                modal
            )
            # 更新closeModal调用中的引用
            modal_with_prefix = re.sub(
                r"closeModal\(['\"]modal-([^'\"]+)['\"]",
                lambda m: f"closeModal('ch{file_num:02d}-modal-{m.group(1)}'",
                modal_with_prefix
            )
            processed_modals.append(modal_with_prefix)
        
        return processed_modals
    
    def extract_scripts(self, content: str, file_num: int) -> str:
        """提取JavaScript代码"""
        # 提取 <script> 标签中的内容（不包括CDN引用）
        pattern = r'<script(?![^>]*src=)[^>]*>(.*?)</script>'
        scripts = re.findall(pattern, content, re.DOTALL)
        
        # 合并所有脚本
        combined = '\n\n'.join(scripts)
        
        # 移除openModal和closeModal函数定义（我们会在合并文件中统一定义）
        combined = re.sub(
            r'function\s+openModal\s*\([^)]*\)\s*\{[^}]*\}',
            '',
            combined,
            flags=re.DOTALL
        )
        combined = re.sub(
            r'function\s+closeModal\s*\([^)]*\)\s*\{[^}]*\}',
            '',
            combined,
            flags=re.DOTALL
        )
        
        # 移除重复的modal事件监听器
        combined = re.sub(
            r'document\.querySelectorAll\([\'"]\.modal[\'"]\)\.forEach\([^}]*\}\s*\)\s*\)\s*;',
            '',
            combined,
            flags=re.DOTALL
        )
        
        # 移除重复的Intersection Observer定义
        combined = re.sub(
            r'const\s+observerOptions\s*=\s*\{[^}]*\};.*?document\.querySelectorAll.*?observer\.observe.*?\);',
            '',
            combined,
            flags=re.DOTALL
        )
        
        # 为chart ID添加前缀
        combined = re.sub(
            r"getElementById\(['\"]([^'\"]+Chart[^'\"]*)['\"]",
            lambda m: f"getElementById('ch{file_num:02d}_{m.group(1)}'",
            combined
        )
        
        return combined
    
    def extract_css(self, content: str) -> str:
        """提取CSS样式"""
        pattern = r'<style>(.*?)</style>'
        matches = re.findall(pattern, content, re.DOTALL)
        return '\n\n'.join(matches) if matches else ""
    
    def extract_external_deps(self, content: str) -> Set[str]:
        """提取外部依赖"""
        deps = set()
        
        # 提取script src
        script_pattern = r'<script[^>]*src="([^"]+)"[^>]*>'
        deps.update(re.findall(script_pattern, content))
        
        # 提取link href
        link_pattern = r'<link[^>]*href="([^"]+)"[^>]*>'
        deps.update(re.findall(link_pattern, content))
        
        return deps
    
    def update_modal_references(self, slide_content: str, file_num: int) -> str:
        """更新幻灯片中的模态框引用"""
        # 更新 onclick="openModal('modal-xxx')"
        updated = re.sub(
            r"openModal\(['\"]modal-([^'\"]+)['\"]",
            lambda m: f"openModal('ch{file_num:02d}-modal-{m.group(1)}'",
            slide_content
        )
        return updated
    
    def update_chart_ids(self, slide_content: str, file_num: int) -> str:
        """更新图表canvas的ID"""
        updated = re.sub(
            r'<canvas id="([^"]+Chart[^"]*)"',
            lambda m: f'<canvas id="ch{file_num:02d}_{m.group(1)}"',
            slide_content
        )
        return updated
    
    def merge_files(self):
        """合并所有HTML文件"""
        print("开始分析和合并HTML文件...")
        
        for i, filename in enumerate(self.files, 1):
            print(f"处理 {filename}...")
            
            content = self.read_file(filename)
            
            # 提取各个部分
            slides = self.extract_slides(content, i)
            modals = self.extract_modals(content, i)
            scripts = self.extract_scripts(content, i)
            
            # 更新引用
            slides = [self.update_modal_references(s, i) for s in slides]
            slides = [self.update_chart_ids(s, i) for s in slides]
            
            self.all_slides.extend(slides)
            self.all_modals.extend(modals)
            
            if scripts:
                self.all_scripts.append(f"// === Chapter {i} Scripts ===\n{scripts}")
            
            # 第一个文件的CSS作为基础
            if i == 1:
                self.common_css = self.extract_css(content)
                self.external_deps = self.extract_external_deps(content)
            
            print(f"  - 提取了 {len(slides)} 个幻灯片")
            print(f"  - 提取了 {len(modals)} 个模态框")
        
        print(f"\n总计：")
        print(f"  - {len(self.all_slides)} 个幻灯片")
        print(f"  - {len(self.all_modals)} 个模态框")
        print(f"  - {len(self.external_deps)} 个外部依赖")
    
    def generate_merged_html(self) -> str:
        """生成合并后的HTML"""
        
        # 生成外部依赖引用
        external_links = []
        for dep in sorted(self.external_deps):
            if dep.endswith('.css'):
                external_links.append(f'    <link rel="stylesheet" href="{dep}">')
            elif dep.endswith('.js') or 'cdn' in dep:
                external_links.append(f'    <script src="{dep}"></script>')
        
        # 生成导航菜单
        nav_html = self.generate_navigation()
        
        # 生成完整HTML
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 技术全面报告 - 完整演示文稿</title>
    
    <!-- 外部依赖 -->
{chr(10).join(external_links)}
    
    <style>
{self.common_css}

        /* 导航菜单样式 */
        .navigation-menu {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 900;
        }}
        
        .nav-toggle {{
            background: var(--brand-color);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 12px 20px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(118, 185, 0, 0.3);
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s ease;
        }}
        
        .nav-toggle:hover {{
            background: #628a00;
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(118, 185, 0, 0.4);
        }}
        
        .nav-panel {{
            position: absolute;
            top: 60px;
            right: 0;
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
            padding: 16px;
            min-width: 300px;
            max-height: 70vh;
            overflow-y: auto;
            display: none;
        }}
        
        .nav-panel.active {{
            display: block;
            animation: slideDown 0.3s ease-out;
        }}
        
        @keyframes slideDown {{
            from {{
                opacity: 0;
                transform: translateY(-10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .nav-chapter {{
            margin-bottom: 12px;
        }}
        
        .nav-chapter-title {{
            font-size: 14px;
            font-weight: 700;
            color: var(--brand-color);
            margin-bottom: 6px;
            padding: 6px 10px;
            background: rgba(118, 185, 0, 0.1);
            border-radius: 6px;
        }}
        
        .nav-slide-link {{
            display: block;
            padding: 8px 12px;
            color: #4b5563;
            text-decoration: none;
            border-radius: 6px;
            font-size: 13px;
            transition: all 0.2s ease;
            margin-left: 10px;
        }}
        
        .nav-slide-link:hover {{
            background: #f3f4f6;
            color: var(--brand-color);
            transform: translateX(4px);
        }}
        
        .slide-counter {{
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255, 255, 255, 0.95);
            padding: 8px 20px;
            border-radius: 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            font-size: 14px;
            font-weight: 600;
            color: #4b5563;
            z-index: 900;
        }}
    </style>
</head>
<body>
    
    <!-- 导航菜单 -->
{nav_html}
    
    <!-- 幻灯片计数器 -->
    <div class="slide-counter">
        <span id="currentSlide">1</span> / <span id="totalSlides">{len(self.all_slides)}</span>
    </div>
    
    <!-- 幻灯片容器 -->
    <div class="slides-container" id="slidesContainer">
        
{chr(10).join('        ' + slide for slide in self.all_slides)}
        
    </div>
    
    <!-- 所有模态框 -->
{chr(10).join('    ' + modal for modal in self.all_modals)}
    
    <!-- JavaScript -->
    <script>
        // === 核心功能函数 ===
        
        // 模态框函数
        function openModal(modalId) {{
            const modal = document.getElementById(modalId);
            if (modal) {{
                modal.classList.add('active');
                document.body.classList.add('modal-open');
            }}
        }}
        
        function closeModal(modalId) {{
            const modal = document.getElementById(modalId);
            if (modal) {{
                modal.classList.remove('active');
                document.body.classList.remove('modal-open');
            }}
        }}
        
        // 关闭模态框（点击背景）
        document.addEventListener('DOMContentLoaded', function() {{
            document.querySelectorAll('.modal').forEach(modal => {{
                modal.addEventListener('click', (e) => {{
                    if (e.target === modal) {{
                        modal.classList.remove('active');
                        document.body.classList.remove('modal-open');
                    }}
                }});
            }});
        }});
        
        // === 各章节的图表和特定功能 ===
{chr(10).join(self.all_scripts)}

        // === 通用功能脚本 ===
        
        // 导航菜单切换
        function toggleNavigation() {{
            const navPanel = document.getElementById('navPanel');
            navPanel.classList.toggle('active');
        }}
        
        // 跳转到指定幻灯片
        function jumpToSlide(index) {{
            const slides = document.querySelectorAll('.slide');
            if (slides[index]) {{
                slides[index].scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                toggleNavigation(); // 关闭导航菜单
            }}
        }}
        
        // 更新幻灯片计数器
        function updateSlideCounter() {{
            const container = document.getElementById('slidesContainer');
            const slides = document.querySelectorAll('.slide');
            const currentSlideEl = document.getElementById('currentSlide');
            
            let currentIndex = 0;
            slides.forEach((slide, index) => {{
                const rect = slide.getBoundingClientRect();
                if (rect.top >= 0 && rect.top < window.innerHeight / 2) {{
                    currentIndex = index + 1;
                }}
            }});
            
            if (currentSlideEl) {{
                currentSlideEl.textContent = currentIndex;
            }}
        }}
        
        // 监听滚动事件
        document.getElementById('slidesContainer')?.addEventListener('scroll', updateSlideCounter);
        
        // 点击导航菜单外部关闭菜单
        document.addEventListener('click', function(e) {{
            const navMenu = document.querySelector('.navigation-menu');
            const navPanel = document.getElementById('navPanel');
            if (navPanel && navPanel.classList.contains('active')) {{
                if (!navMenu.contains(e.target)) {{
                    navPanel.classList.remove('active');
                }}
            }}
        }});
        
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {{
            updateSlideCounter();
            
            // 初始化所有动画元素
            const observerOptions = {{
                threshold: 0.3,
                rootMargin: '0px'
            }};
            
            const observer = new IntersectionObserver((entries) => {{
                entries.forEach(entry => {{
                    if (entry.isIntersecting) {{
                        entry.target.classList.add('visible');
                    }}
                }});
            }}, observerOptions);
            
            document.querySelectorAll('.fade-in-up, .mini-card').forEach(el => {{
                observer.observe(el);
            }});
        }});
        
        // 键盘导航支持
        document.addEventListener('keydown', function(e) {{
            const slides = document.querySelectorAll('.slide');
            const container = document.getElementById('slidesContainer');
            
            if (e.key === 'ArrowDown' || e.key === 'PageDown') {{
                e.preventDefault();
                container.scrollBy({{ top: window.innerHeight, behavior: 'smooth' }});
            }} else if (e.key === 'ArrowUp' || e.key === 'PageUp') {{
                e.preventDefault();
                container.scrollBy({{ top: -window.innerHeight, behavior: 'smooth' }});
            }} else if (e.key === 'Home') {{
                e.preventDefault();
                slides[0]?.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }} else if (e.key === 'End') {{
                e.preventDefault();
                slides[slides.length - 1]?.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }}
        }});
    </script>
    
</body>
</html>"""
        
        return html
    
    def generate_navigation(self) -> str:
        """生成导航菜单HTML"""
        chapters = [
            "AI 技术发展背景与算力基础设施",
            "算力卡底层逻辑详解",
            "英伟达算力卡龙头地位分析",
            "机器学习底层逻辑基础",
            "大模型自注意力学习机制",
            "大模型部署技术体系",
            "大模型训练技术体系",
            "知识蒸馏技术详解",
            "知识库技术体系",
            "智能体开发技术",
            "AI 应用案例分析",
            "结语"
        ]
        
        nav_html = """    <div class="navigation-menu">
        <button class="nav-toggle" onclick="toggleNavigation()">
            <i class="fas fa-bars"></i>
            <span>目录导航</span>
        </button>
        <div class="nav-panel" id="navPanel">"""
        
        slide_index = 0
        for chapter_num, chapter_title in enumerate(chapters, 1):
            # 计算该章节的幻灯片数量
            chapter_slides = [s for s in self.all_slides if f'data-chapter="{chapter_num}"' in s]
            
            nav_html += f"""
            <div class="nav-chapter">
                <div class="nav-chapter-title">第 {chapter_num} 章：{chapter_title}</div>"""
            
            for i, slide in enumerate(chapter_slides, 1):
                nav_html += f"""
                <a href="#" class="nav-slide-link" onclick="jumpToSlide({slide_index}); return false;">
                    <i class="fas fa-file-alt"></i> 幻灯片 {i}
                </a>"""
                slide_index += 1
            
            nav_html += """
            </div>"""
        
        nav_html += """
        </div>
    </div>"""
        
        return nav_html
    
    def save_merged_file(self, output_filename: str = "deepseek-merged.html"):
        """保存合并后的文件"""
        html_content = self.generate_merged_html()
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✅ 成功生成合并文件：{output_filename}")
        print(f"   文件大小：{len(html_content):,} 字符")
        print(f"   总幻灯片数：{len(self.all_slides)}")
        print(f"   总模态框数：{len(self.all_modals)}")

def main():
    merger = HTMLMerger()
    merger.merge_files()
    merger.save_merged_file()
    print("\n✨ 合并完成！")

if __name__ == "__main__":
    main()
