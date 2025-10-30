#!/usr/bin/env python3
"""
验证合并后的HTML文件质量
"""

import re
from collections import Counter

def validate_html(filename='deepseek-merged.html'):
    """验证HTML文件的完整性和正确性"""
    
    print("🔍 开始验证合并后的HTML文件...\n")
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    warnings = []
    
    # 1. 检查基本HTML结构
    print("📋 检查基本HTML结构...")
    if not content.startswith('<!DOCTYPE html>'):
        issues.append("缺少 DOCTYPE 声明")
    if content.count('<html') != content.count('</html>'):
        issues.append("HTML标签不匹配")
    if content.count('<head>') != content.count('</head>'):
        issues.append("head标签不匹配")
    if content.count('<body>') != content.count('</body>'):
        issues.append("body标签不匹配")
    print("   ✅ HTML基本结构完整\n")
    
    # 2. 检查幻灯片数量
    print("📊 检查幻灯片...")
    slide_count = content.count('<section class="slide"')
    print(f"   ✅ 找到 {slide_count} 个幻灯片\n")
    
    # 3. 检查模态框
    print("🪟 检查模态框...")
    modal_ids = re.findall(r'<div id="(ch\d+-modal-[^"]+)" class="modal">', content)
    modal_count = len(modal_ids)
    print(f"   ✅ 找到 {modal_count} 个模态框")
    
    # 检查模态框ID是否唯一
    modal_id_counts = Counter(modal_ids)
    duplicates = [mid for mid, count in modal_id_counts.items() if count > 1]
    if duplicates:
        issues.append(f"发现重复的模态框ID: {', '.join(duplicates)}")
    else:
        print("   ✅ 所有模态框ID唯一\n")
    
    # 4. 检查openModal引用
    print("🔗 检查模态框引用...")
    open_modal_calls = re.findall(r"openModal\(['\"]([^'\"]+)['\"]", content)
    close_modal_calls = re.findall(r"closeModal\(['\"]([^'\"]+)['\"]", content)
    
    # 检查是否所有openModal调用都有对应的模态框
    for modal_id in set(open_modal_calls):
        if modal_id not in modal_ids:
            issues.append(f"openModal引用了不存在的模态框: {modal_id}")
    
    # 检查是否所有closeModal调用都有对应的模态框
    for modal_id in set(close_modal_calls):
        if modal_id not in modal_ids:
            issues.append(f"closeModal引用了不存在的模态框: {modal_id}")
    
    print(f"   ✅ 找到 {len(open_modal_calls)} 个 openModal 调用")
    print(f"   ✅ 找到 {len(close_modal_calls)} 个 closeModal 调用\n")
    
    # 5. 检查图表
    print("📈 检查图表...")
    canvas_ids = re.findall(r'<canvas id="([^"]+)"', content)
    chart_refs = re.findall(r"getElementById\(['\"]([^'\"]+Chart[^'\"]*)['\"]", content)
    
    print(f"   ✅ 找到 {len(canvas_ids)} 个画布元素")
    print(f"   ✅ 找到 {len(chart_refs)} 个图表引用")
    
    # 检查图表引用是否匹配
    for chart_id in chart_refs:
        if chart_id not in canvas_ids:
            issues.append(f"图表引用了不存在的canvas: {chart_id}")
    
    if not issues:
        print("   ✅ 所有图表引用正确\n")
    
    # 6. 检查外部依赖
    print("📦 检查外部依赖...")
    script_srcs = re.findall(r'<script[^>]*src="([^"]+)"', content)
    link_hrefs = re.findall(r'<link[^>]*href="([^"]+)"', content)
    
    print(f"   ✅ 外部脚本: {len(script_srcs)} 个")
    for src in script_srcs:
        print(f"      - {src}")
    
    print(f"   ✅ 外部样式: {len(link_hrefs)} 个")
    for href in link_hrefs:
        print(f"      - {href}")
    print()
    
    # 7. 检查JavaScript函数定义
    print("⚙️  检查JavaScript函数...")
    
    # 检查核心函数是否定义
    required_functions = [
        'openModal',
        'closeModal',
        'toggleNavigation',
        'jumpToSlide',
        'updateSlideCounter'
    ]
    
    for func in required_functions:
        pattern = f'function\\s+{func}\\s*\\('
        if not re.search(pattern, content):
            issues.append(f"缺少函数定义: {func}")
        else:
            print(f"   ✅ {func} 函数已定义")
    print()
    
    # 8. 检查导航菜单
    print("🧭 检查导航菜单...")
    if 'class="navigation-menu"' in content:
        print("   ✅ 导航菜单存在")
    else:
        warnings.append("缺少导航菜单")
    
    if 'class="slide-counter"' in content:
        print("   ✅ 幻灯片计数器存在")
    else:
        warnings.append("缺少幻灯片计数器")
    print()
    
    # 9. 文件大小检查
    print("📏 检查文件大小...")
    file_size = len(content)
    file_size_mb = file_size / (1024 * 1024)
    print(f"   ✅ 文件大小: {file_size:,} 字符 ({file_size_mb:.2f} MB)")
    
    if file_size_mb > 2:
        warnings.append(f"文件较大 ({file_size_mb:.2f} MB)，可能影响加载速度")
    print()
    
    # 10. 代码质量检查
    print("🔍 检查代码质量...")
    
    # 检查是否有未闭合的标签
    common_tags = ['div', 'section', 'script', 'style', 'button', 'canvas']
    for tag in common_tags:
        open_count = len(re.findall(f'<{tag}[\\s>]', content))
        close_count = content.count(f'</{tag}>')
        if open_count != close_count:
            warnings.append(f"标签不匹配: <{tag}> 开始标签 {open_count} 个，结束标签 {close_count} 个")
    
    if not warnings:
        print("   ✅ 未发现明显的代码质量问题\n")
    
    # 输出总结
    print("\n" + "="*60)
    print("📊 验证总结")
    print("="*60)
    print(f"✅ 幻灯片总数: {slide_count}")
    print(f"✅ 模态框总数: {modal_count}")
    print(f"✅ 图表数量: {len(canvas_ids)}")
    print(f"✅ 外部依赖: {len(script_srcs) + len(link_hrefs)} 个")
    print(f"✅ 文件大小: {file_size:,} 字符")
    
    if issues:
        print(f"\n❌ 发现 {len(issues)} 个严重问题:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    else:
        print("\n✅ 未发现严重问题")
    
    if warnings:
        print(f"\n⚠️  发现 {len(warnings)} 个警告:")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")
    else:
        print("✅ 未发现警告")
    
    if not issues and not warnings:
        print("\n🎉 恭喜！HTML文件验证完全通过！")
        return True
    elif not issues:
        print("\n✅ HTML文件基本正常，仅有少量警告")
        return True
    else:
        print("\n❌ 请修复上述问题后重新验证")
        return False

def main():
    result = validate_html()
    exit(0 if result else 1)

if __name__ == "__main__":
    main()
