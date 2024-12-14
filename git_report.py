import os
from git import Repo
from datetime import datetime, timedelta
import pytz
import sys
from git.exc import InvalidGitRepositoryError, GitCommandError
import argparse
from collections import defaultdict

def get_date_range(date_shortcut):
    """根据快捷方式获取日期范围"""
    today = datetime.now(pytz.utc)
    
    if date_shortcut == 'today':
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today
    elif date_shortcut == 'yesterday':
        start_date = (today - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(hour=23, minute=59, second=59)
    elif date_shortcut == 'thisweek':
        start_date = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today
    elif date_shortcut == 'lastweek':
        this_week_start = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = this_week_start - timedelta(days=7)
        end_date = this_week_start - timedelta(seconds=1)
    elif date_shortcut == 'thismonth':
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = today
    elif date_shortcut == 'lastmonth':
        this_month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month = this_month_start - timedelta(days=1)
        start_date = last_month.replace(day=1)
        end_date = this_month_start - timedelta(seconds=1)
    else:
        return None, None
    
    return start_date, end_date

class GitReportGenerator:
    def __init__(self, repo_path, branch=None):
        self.repo_path = os.path.abspath(repo_path)
        try:
            self.repo = Repo(repo_path)
            # 获取仓库名称
            self.repo_name = os.path.basename(self.repo_path)
            if self.repo_name == '':  # 处理路径以斜杠结尾的情况
                self.repo_name = os.path.basename(os.path.dirname(self.repo_path))
            
            # 设置分支
            if branch:
                try:
                    self.repo.git.checkout(branch)
                    print(f"已切换到分支: {branch}")
                except GitCommandError as e:
                    print(f"错误: 切换到分支 '{branch}' 失败: {str(e)}")
                    sys.exit(1)
            
            # 获取当前分支
            self.current_branch = self.repo.active_branch.name
            
        except InvalidGitRepositoryError:
            print(f"错误: '{repo_path}' 不是一个有效的 Git 仓库")
            print("请确保指定的路径是一个 Git 仓库")
            sys.exit(1)
    
    def get_branches(self):
        """获取仓库的所有分支"""
        try:
            branches = []
            for branch in self.repo.heads:
                branches.append({
                    'name': branch.name,
                    'is_current': branch.name == self.current_branch
                })
            return branches
        except Exception as e:
            print(f"获取分支列表时出错: {str(e)}")
            return []
    
    def get_commits_in_range(self, start_date=None, end_date=None, authors=None):
        """获取指定日期范围内的提交"""
        if not start_date:
            start_date = datetime.now(pytz.utc) - timedelta(days=7)
        if not end_date:
            end_date = datetime.now(pytz.utc)
            
        commits = []
        try:
            # 如果指定了作者，先获取完整的作者信息
            author_info = set()
            if authors:
                all_authors = self.get_authors()
                print("\n调试信息:")
                print(f"搜索的作者: {authors}")
                print("仓库中的所有作者:")
                for author in all_authors:
                    print(f"  {author}")
                
                for full_author in all_authors:
                    name_email = full_author.lower()
                    for search_author in authors:
                        if search_author.lower() in name_email:
                            author_name = full_author.split(' <')[0]
                            author_info.add(author_name)
                            print(f"找到匹配: {search_author} -> {author_name}")
                
                print(f"最终匹配到的作者: {author_info}")
            
            # 获取所有提交
            all_commits = self.repo.iter_commits()
            commit_count = 0
            matched_count = 0
            
            for commit in all_commits:
                commit_count += 1
                commit_date = datetime.fromtimestamp(commit.committed_date, pytz.utc)
                # 检查日期范围
                if start_date <= commit_date <= end_date:
                    # 如果指定了作者，检查作者是否匹配
                    if authors:
                        if commit.author.name not in author_info:
                            continue
                    matched_count += 1
                    commits.append({
                        'hash': commit.hexsha,
                        'author': commit.author.name,
                        'email': commit.author.email,
                        'date': commit_date,
                        'message': commit.message.strip(),
                        'stats': commit.stats.total,
                        'files': commit.stats.files
                    })
            
            print(f"\n处理的提交总数: {commit_count}")
            print(f"时间范围内的匹配提交数: {matched_count}")
            
        except Exception as e:
            print(f"获取提交记录时出错: {str(e)}")
            sys.exit(1)
        return commits
    
    def generate_markdown_report(self, commits, start_date=None, end_date=None):
        """生成Markdown格式的报告"""
        # 报告标题和概述
        report = "# 📊 Git 提交报告\n\n"
        report += "## 📌 仓库信息\n\n"
        report += f"- **仓库名称**: `{self.repo_name}`\n"
        report += f"- **仓库路径**: `{self.repo_path}`\n"
        report += f"- **当前分支**: `{self.current_branch}`\n"
        report += f"- **分析时间范围**: {self._format_date_range(start_date, end_date)}\n"
        report += f"- **报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 获取所有分支信息
        branches = self.get_branches()
        if branches:
            report += "### 🌿 分支列表\n\n"
            for branch in branches:
                current_marker = "👉 " if branch['is_current'] else "　 "
                report += f"{current_marker}`{branch['name']}`\n"
            report += "\n"
        
        # 统计摘要
        report += "## 📈 统计摘要\n\n"
        total_insertions = sum(commit['stats']['insertions'] for commit in commits)
        total_deletions = sum(commit['stats']['deletions'] for commit in commits)
        report += f"- **总提交次数**: {len(commits)} 次\n"
        report += f"- **代码变更**: +{total_insertions} 行, -{total_deletions} 行\n"
        
        # 作者贡献统计
        authors_stats = defaultdict(lambda: {'commits': 0, 'insertions': 0, 'deletions': 0, 'email': ''})
        for commit in commits:
            author = commit['author']
            authors_stats[author]['commits'] += 1
            authors_stats[author]['insertions'] += commit['stats']['insertions']
            authors_stats[author]['deletions'] += commit['stats']['deletions']
            authors_stats[author]['email'] = commit['email']  # 保存作者邮箱
        
        report += "\n## 👥 作者贡献\n\n"
        report += "| 作者 | 邮箱 | 提交次数 | 添加行数 | 删除行数 |\n"
        report += "|------|------|----------|----------|----------|\n"
        for author, stats in authors_stats.items():
            report += f"| {author} | {stats['email']} | {stats['commits']} | +{stats['insertions']} | -{stats['deletions']} |\n"
        
        # 文件变更统计
        files_stats = defaultdict(lambda: {'changes': 0, 'insertions': 0, 'deletions': 0})
        for commit in commits:
            for file_path, stats in commit['files'].items():
                files_stats[file_path]['changes'] += 1
                files_stats[file_path]['insertions'] += stats.get('insertions', 0)
                files_stats[file_path]['deletions'] += stats.get('deletions', 0)
        
        report += "\n## 📁 文件变更统计\n\n"
        report += "| 文件 | 变更次数 | 添加行数 | 删除行数 |\n"
        report += "|------|----------|----------|----------|\n"
        # 按变更次数排序
        sorted_files = sorted(files_stats.items(), key=lambda x: x[1]['changes'], reverse=True)
        for file_path, stats in sorted_files[:10]:  # 只显示变更最多的10个文件
            report += f"| `{file_path}` | {stats['changes']} | +{stats['insertions']} | -{stats['deletions']} |\n"
        
        # 详细提交记录
        report += "\n## 📝 详细提交记录\n\n"
        # 按日期分组显示提交
        commits_by_date = defaultdict(list)
        for commit in commits:
            date_str = commit['date'].strftime('%Y-%m-%d')
            commits_by_date[date_str].append(commit)
        
        for date_str, day_commits in sorted(commits_by_date.items(), reverse=True):
            report += f"### 📅 {date_str}\n\n"
            for commit in day_commits:
                report += f"#### ⚡ 提交 `{commit['hash'][:8]}`\n\n"
                report += f"- **作者**: {commit['author']} <{commit['email']}>\n"
                report += f"- **时间**: {commit['date'].strftime('%H:%M:%S')}\n"
                report += f"- **变更**: +{commit['stats']['insertions']} 行, -{commit['stats']['deletions']} 行\n"
                report += f"- **说明**: {commit['message']}\n\n"
                # 显示文件变更详情
                if commit['files']:
                    report += "**变更文件**:\n"
                    for file_path, stats in commit['files'].items():
                        report += f"- `{file_path}`: +{stats.get('insertions', 0)} -{stats.get('deletions', 0)}\n"
                report += "\n---\n\n"
        
        return report
    
    def _format_date_range(self, start_date, end_date):
        """格式化日期范围显示"""
        if start_date and end_date:
            return f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
        elif start_date:
            return f"{start_date.strftime('%Y-%m-%d')} 至今"
        elif end_date:
            return f"直到 {end_date.strftime('%Y-%m-%d')}"
        else:
            return "最近7天"
    
    def save_report(self, report, output_dir, output_file):
        """保存报告到指定目录"""
        try:
            # 确定报告类型和对应的子目录
            if output_file.startswith('summary-'):
                sub_dir = 'summary'
            elif output_file.startswith('detail-'):
                sub_dir = 'details'
            elif output_file.startswith('maven-'):
                sub_dir = 'maven'
            else:
                sub_dir = ''
            
            # 构建完整的输出路径
            if sub_dir:
                output_path = os.path.join(output_dir, sub_dir, output_file)
            else:
                output_path = os.path.join(output_dir, output_file)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 写入报告文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            return output_path
        except Exception as e:
            print(f"保存报告时出错: {str(e)}")
            sys.exit(1)
    
    def get_authors(self):
        """获取仓库中所有的提交作者"""
        try:
            authors = set()
            for commit in self.repo.iter_commits():
                authors.add(f"{commit.author.name} <{commit.author.email}>")
            return sorted(list(authors))
        except Exception as e:
            print(f"获取作者列表出错: {str(e)}")
            return []

def parse_date(date_str):
    """解析日期字符串，格式: YYYY-MM-DD"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=pytz.utc)
    except ValueError:
        print(f"错误: 日期格式不正确，请使用 YYYY-MM-DD 格式")
        sys.exit(1)

def generate_output_filename(repo_name, branch=None, authors=None, start_date=None, end_date=None, date_shortcut=None):
    """生成规范的输出文件名"""
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 清理仓库名称（移除特殊字符）
    repo_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in repo_name)
    
    # 构建文件名各部分
    parts = ['git_report', repo_name]
    
    # 添加分支信息
    if branch:
        parts.append(f"branch_{branch}")
    
    # 添加作者信息
    if authors:
        # 处理多个作者
        if isinstance(authors, list):
            author_names = []
            for author in authors:
                # 清理作者名称中的特殊字符
                clean_author = ''.join(c if c.isalnum() or c in '-_' else '_' for c in author)
                author_names.append(clean_author)
            parts.append(f"authors_{'-'.join(author_names)}")
        else:
            # 单个作者的情况
            clean_author = ''.join(c if c.isalnum() or c in '-_' else '_' for c in authors)
            parts.append(f"author_{clean_author}")
    
    # 添加日期范围
    if date_shortcut:
        parts.append(date_shortcut)
    elif start_date and end_date:
        parts.append(f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}")
    elif start_date:
        parts.append(f"from_{start_date.strftime('%Y%m%d')}")
    elif end_date:
        parts.append(f"until_{end_date.strftime('%Y%m%d')}")
    else:
        parts.append("last_7_days")
    
    # 添加时间戳
    parts.append(current_time)
    
    # 生成文件名
    return f"{'-'.join(parts)}.md"

def format_search_conditions(branch=None, authors=None, start_date=None, end_date=None, date_shortcut=None):
    """格式化显示查找条件"""
    conditions = []
    
    if branch:
        conditions.append(f"分支: {branch}")
    
    if authors:
        if isinstance(authors, list):
            conditions.append(f"作者: {', '.join(authors)}")
        else:
            conditions.append(f"作者: {authors}")
    
    if date_shortcut:
        date_map = {
            'today': '今天',
            'yesterday': '昨天',
            'thisweek': '本周',
            'lastweek': '上周',
            'thismonth': '本月',
            'lastmonth': '上个月'
        }
        conditions.append(f"时间范围: {date_map.get(date_shortcut, date_shortcut)}")
    elif start_date and end_date:
        conditions.append(f"时间范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    elif start_date:
        conditions.append(f"时间范围: {start_date.strftime('%Y-%m-%d')} 至今")
    elif end_date:
        conditions.append(f"时间范围: 直到 {end_date.strftime('%Y-%m-%d')}")
    else:
        conditions.append("时间范围: 最近7天")
    
    return " | ".join(conditions)

def generate_report_directory(repo_name, branch=None, date_shortcut=None, start_date=None, end_date=None, maven_info=None):
    """生成规范的报告目录结构"""
    # 基础目录结构：reports/{repo_name}/{year}/{month}/{branch}/{date_range}
    current_date = datetime.now()
    year = current_date.strftime('%Y')
    month = current_date.strftime('%m')
    
    # 清理仓库名称中的特殊字符
    clean_repo_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in repo_name)
    
    # 构建基础路径
    parts = ['reports', clean_repo_name, year, month]
    
    # 添加分支目录
    if branch:
        clean_branch = ''.join(c if c.isalnum() or c in '-_' else '_' for c in branch)
        parts.append(clean_branch)
    else:
        parts.append('default_branch')
    
    # 生成日期子目录
    if date_shortcut:
        date_dir = date_shortcut
    elif start_date and end_date:
        date_dir = f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"
    elif start_date:
        date_dir = f"from_{start_date.strftime('%Y%m%d')}"
    elif end_date:
        date_dir = f"until_{end_date.strftime('%Y%m%d')}"
    else:
        date_dir = 'last_7_days'
    
    parts.append(date_dir)
    
    # 生成完整路径
    report_dir = os.path.join(*parts)
    
    # 创建目录结构
    try:
        os.makedirs(report_dir, exist_ok=True)
        
        # 创建子目录
        os.makedirs(os.path.join(report_dir, 'summary'), exist_ok=True)
        os.makedirs(os.path.join(report_dir, 'details'), exist_ok=True)
        if maven_info and maven_info.get('modules'):
            os.makedirs(os.path.join(report_dir, 'maven'), exist_ok=True)
        
        # 创建 assets 目录（用于存放图表等资源）
        os.makedirs(os.path.join(report_dir, 'assets'), exist_ok=True)
        
    except Exception as e:
        print(f"创建目录结构时出错: {str(e)}")
        sys.exit(1)
    
    return report_dir

def analyze_maven_project(repo_path):
    """分析Maven项目的结构和依赖"""
    maven_info = {
        'modules': [],
        'dependencies': defaultdict(list),
        'module_paths': {}  # 用于存储路径到模块的映射
    }
    
    try:
        # 查找所有的pom.xml文件
        for root, _, files in os.walk(repo_path):
            if 'pom.xml' in files:
                relative_path = os.path.relpath(root, repo_path)
                module_name = os.path.basename(root)
                
                pom_path = os.path.join(root, 'pom.xml')
                with open(pom_path, 'r', encoding='utf-8') as f:
                    pom_content = f.read()
                
                module_info = {
                    'name': module_name,
                    'path': relative_path,
                    'pom_path': pom_path,
                    'base_dir': root
                }
                maven_info['modules'].append(module_info)
                
                # 添加路径映射
                maven_info['module_paths'][relative_path] = module_info
                # 如果是根路径，也添加映射
                if relative_path == '.':
                    maven_info['module_paths'][''] = module_info
    except Exception as e:
        print(f"分析Maven项目时出错: {str(e)}")
    
    return maven_info

def find_module_for_file(file_path, maven_info):
    """找到文件所属的模块"""
    file_dir = os.path.dirname(file_path)
    
    # 从文件所在目录开始，逐级向上查找，直到找到包含它的模块
    while file_dir:
        if file_dir in maven_info['module_paths']:
            return maven_info['module_paths'][file_dir]
        file_dir = os.path.dirname(file_dir)
    
    # 如果没找到，检查是否在根目录
    if '' in maven_info['module_paths']:
        return maven_info['module_paths']['']
    
    return None

def categorize_maven_changes(file_path):
    """对Maven项目的文件变更进行分类"""
    ext = os.path.splitext(file_path)[1].lower()
    basename = os.path.basename(file_path).lower()
    
    # Maven 特定文件
    if basename == 'pom.xml':
        return 'Maven配置'
    
    # 源代码和资源文件
    if file_path.startswith('src/main/java/'):
        return 'Java源码'
    elif file_path.startswith('src/test/java/'):
        return 'Java测试'
    elif file_path.startswith('src/main/resources/'):
        if ext in ['.properties', '.yml', '.yaml', '.xml']:
            return '应用配置'
        return '资源文件'
    elif file_path.startswith('src/test/resources/'):
        return '测���资源'
    
    # 其他常见目录
    if 'webapp' in file_path:
        return 'Web资源'
    elif 'docker' in file_path:
        return 'Docker配置'
    elif 'scripts' in file_path:
        return '脚本文件'
    
    return '其他文件'

def generate_maven_report(maven_info, commits):
    """生成Maven项目的变更报告"""
    report = "# Maven项目分析报告\n\n"
    
    # 模块列表
    report += "## 项目结构\n\n"
    for module in maven_info['modules']:
        report += f"- {module['name']} (`{module['path']}`)\n"
    
    # 按模块和文件类型统计变更
    module_changes = defaultdict(lambda: {
        'total_files': set(),
        'changes_by_type': defaultdict(lambda: {
            'files': set(),
            'insertions': 0,
            'deletions': 0
        })
    })
    
    # 分析每个提交的文件变更
    for commit in commits:
        for file_path, stats in commit['files'].items():
            # 找到文件所属的模块
            module = find_module_for_file(file_path, maven_info)
            if module:
                module_name = module['name']
                change_type = categorize_maven_changes(file_path)
                
                # 更新统计信息
                module_changes[module_name]['total_files'].add(file_path)
                module_changes[module_name]['changes_by_type'][change_type]['files'].add(file_path)
                module_changes[module_name]['changes_by_type'][change_type]['insertions'] += stats.get('insertions', 0)
                module_changes[module_name]['changes_by_type'][change_type]['deletions'] += stats.get('deletions', 0)
    
    # 生成模块变更报告
    report += "\n## 模块变更分析\n\n"
    
    for module_name, stats in sorted(module_changes.items()):
        report += f"### 📦 {module_name}\n\n"
        
        # 模块总体统计
        total_insertions = sum(type_stats['insertions'] for type_stats in stats['changes_by_type'].values())
        total_deletions = sum(type_stats['deletions'] for type_stats in stats['changes_by_type'].values())
        
        report += f"- 变更文件总数: {len(stats['total_files'])} 个\n"
        report += f"- 总体变更: +{total_insertions} 行, -{total_deletions} 行\n\n"
        
        # 按文件类型统计
        report += "#### 文件类型分布\n\n"
        report += "| 类型 | 文件数 | 添加行数 | 删除行数 |\n"
        report += "|------|---------|----------|----------|\n"
        
        for change_type, type_stats in sorted(stats['changes_by_type'].items()):
            report += f"| {change_type} | {len(type_stats['files'])} | +{type_stats['insertions']} | -{type_stats['deletions']} |\n"
        
        # 变更文件列表
        report += "\n#### 变更文件列表\n\n"
        for change_type, type_stats in sorted(stats['changes_by_type'].items()):
            if type_stats['files']:
                report += f"**{change_type}**:\n"
                for file_path in sorted(type_stats['files']):
                    report += f"- `{file_path}`\n"
                report += "\n"
        
        report += "---\n\n"
    
    return report

def categorize_file_type(file_path):
    """对文件类型进行分类"""
    ext = os.path.splitext(file_path)[1].lower()
    basename = os.path.basename(file_path).lower()
    
    # Maven 特定文件
    if basename == 'pom.xml':
        return 'Maven POM'
    
    # 配置文件
    if ext in ['.properties', '.yml', '.yaml', '.xml', '.json', '.conf', '.config']:
        return f'配置文件 ({ext})'
    
    # 源代码文件
    if ext == '.java':
        return 'Java 源码'
    elif ext in ['.js', '.ts', '.jsx', '.tsx']:
        return 'JavaScript/TypeScript'
    elif ext in ['.py']:
        return 'Python 源码'
    elif ext in ['.go']:
        return 'Go 源码'
    elif ext in ['.cpp', '.hpp', '.c', '.h']:
        return 'C/C++ 源码'
    
    # 资源文件
    if ext in ['.css', '.scss', '.less']:
        return 'CSS 样式'
    elif ext in ['.html', '.htm', '.jsp', '.ftl']:
        return '网页模板'
    elif ext in ['.sql']:
        return 'SQL 脚本'
    elif ext in ['.md', '.txt', '.doc', '.docx']:
        return '文档'
    elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg']:
        return '图片资源'
    
    # 其他类型
    if ext:
        return f'其他 ({ext})'
    return '无扩展名'

def analyze_file_changes(commits):
    """分析文件变更的详细情况"""
    file_types = defaultdict(lambda: {
        'files': set(),
        'changes': 0,
        'insertions': 0,
        'deletions': 0
    })
    
    for commit in commits:
        for file_path, stats in commit['files'].items():
            file_type = categorize_file_type(file_path)
            file_types[file_type]['files'].add(file_path)
            file_types[file_type]['changes'] += 1
            file_types[file_type]['insertions'] += stats.get('insertions', 0)
            file_types[file_type]['deletions'] += stats.get('deletions', 0)
    
    return file_types

def analyze_module_impact(commits, maven_info):
    """分析模块变更的影响范围"""
    module_impacts = defaultdict(lambda: {
        'pom_changes': set(),          # POM文件变更
        'sql_changes': set(),          # SQL文件变更
        'java_changes': set(),         # Java文件变更
        'config_changes': set(),       # 配置文件变更
        'script_changes': set(),       # 脚本文件变更
        'test_changes': set(),         # 测试文件变更
        'resource_changes': set(),     # 资源文件变更
        'affected_modules': set(),     # 受影响的相关模块
        'total_insertions': 0,
        'total_deletions': 0
    })

    # 分析每个提交中的文件变更
    for commit in commits:
        for file_path, stats in commit['files'].items():
            # 找到文件所属的模块
            module = find_module_for_file(file_path, maven_info)
            if not module:
                continue

            module_name = module['name']
            ext = os.path.splitext(file_path)[1].lower()
            basename = os.path.basename(file_path).lower()

            # 更新统计数据
            module_impacts[module_name]['total_insertions'] += stats.get('insertions', 0)
            module_impacts[module_name]['total_deletions'] += stats.get('deletions', 0)

            # 分类文件变更
            if basename == 'pom.xml':
                module_impacts[module_name]['pom_changes'].add(file_path)
            elif ext == '.sql':
                module_impacts[module_name]['sql_changes'].add(file_path)
            elif ext == '.java':
                if 'test' in file_path.lower():
                    module_impacts[module_name]['test_changes'].add(file_path)
                else:
                    module_impacts[module_name]['java_changes'].add(file_path)
            elif ext in ['.properties', '.yml', '.yaml', '.xml', '.json', '.conf']:
                module_impacts[module_name]['config_changes'].add(file_path)
            elif ext in ['.sh', '.bat', '.cmd', '.ps1']:
                module_impacts[module_name]['script_changes'].add(file_path)
            elif file_path.startswith('src/main/resources/'):
                module_impacts[module_name]['resource_changes'].add(file_path)

    return module_impacts

def generate_impact_report(module_impacts):
    """生成模块影响分析报告"""
    report = "# 📊 模块影响分析报告\n\n"

    # 添加总览部分
    report += "## 📋 变更总览\n\n"
    report += "| 模块名称 | POM变更 | SQL变更 | Java变更 | 配置变更 | 脚本变更 | 测试变更 | 资源变更 |\n"
    report += "|----------|----------|----------|-----------|------------|------------|------------|------------|\n"

    # 按照变更文件总数排序
    sorted_modules = sorted(
        module_impacts.items(),
        key=lambda x: (len(x[1]['pom_changes']) + 
                      len(x[1]['sql_changes']) + 
                      len(x[1]['java_changes']) + 
                      len(x[1]['config_changes']) + 
                      len(x[1]['script_changes'])),
        reverse=True
    )

    # 生成总览表格
    for module_name, impact in sorted_modules:
        total_changes = (len(impact['pom_changes']) + 
                        len(impact['sql_changes']) + 
                        len(impact['java_changes']) + 
                        len(impact['config_changes']) + 
                        len(impact['script_changes']) +
                        len(impact['test_changes']) +
                        len(impact['resource_changes']))
        
        if total_changes == 0:
            continue

        report += f"| {module_name} | "
        report += "✓ | " if impact['pom_changes'] else "- | "
        report += "✓ | " if impact['sql_changes'] else "- | "
        report += "✓ | " if impact['java_changes'] else "- | "
        report += "✓ | " if impact['config_changes'] else "- | "
        report += "✓ | " if impact['script_changes'] else "- | "
        report += "✓ | " if impact['test_changes'] else "- | "
        report += "✓ |" if impact['resource_changes'] else "- |"
        report += "\n"

    report += "\n## 📦 模块详细分析\n\n"

    # 生成每个模块的详细报告
    for module_name, impact in sorted_modules:
        total_changes = (len(impact['pom_changes']) + 
                        len(impact['sql_changes']) + 
                        len(impact['java_changes']) + 
                        len(impact['config_changes']) + 
                        len(impact['script_changes']) +
                        len(impact['test_changes']) +
                        len(impact['resource_changes']))
        
        if total_changes == 0:
            continue

        report += f"### {module_name}\n\n"
        report += f"- 总体变更: +{impact['total_insertions']} 行, -{impact['total_deletions']} 行\n\n"

        # 变更类型统计
        report += "#### 变更类型统计\n\n"
        report += "| 变更类型 | 文件数 |\n"
        report += "|----------|--------|\n"
        
        if impact['pom_changes']:
            report += f"| Maven POM | {len(impact['pom_changes'])} |\n"
        if impact['sql_changes']:
            report += f"| SQL 文件 | {len(impact['sql_changes'])} |\n"
        if impact['java_changes']:
            report += f"| Java 源码 | {len(impact['java_changes'])} |\n"
        if impact['test_changes']:
            report += f"| 测试代码 | {len(impact['test_changes'])} |\n"
        if impact['config_changes']:
            report += f"| 配置文件 | {len(impact['config_changes'])} |\n"
        if impact['script_changes']:
            report += f"| 脚本文件 | {len(impact['script_changes'])} |\n"
        if impact['resource_changes']:
            report += f"| 资源文件 | {len(impact['resource_changes'])} |\n"

        # 详细文件列表
        report += "\n#### 详细变更列表\n\n"

        # POM 变更
        if impact['pom_changes']:
            report += "##### Maven POM 变更\n\n"
            for file_path in sorted(impact['pom_changes']):
                report += f"- `{file_path}`\n"
            report += "\n"

        # SQL 变更
        if impact['sql_changes']:
            report += "##### SQL 文件变更\n\n"
            for file_path in sorted(impact['sql_changes']):
                report += f"- `{file_path}`\n"
            report += "\n"

        # Java 源码变更
        if impact['java_changes']:
            report += "##### Java 源码变更\n\n"
            for file_path in sorted(impact['java_changes']):
                report += f"- `{file_path}`\n"
            report += "\n"

        # 测试代码变更
        if impact['test_changes']:
            report += "##### 测试代码变更\n\n"
            for file_path in sorted(impact['test_changes']):
                report += f"- `{file_path}`\n"
            report += "\n"

        # 配置文件变更
        if impact['config_changes']:
            report += "##### 配置文件变更\n\n"
            for file_path in sorted(impact['config_changes']):
                report += f"- `{file_path}`\n"
            report += "\n"

        # 脚本文件变更
        if impact['script_changes']:
            report += "##### 脚本文件变更\n\n"
            for file_path in sorted(impact['script_changes']):
                report += f"- `{file_path}`\n"
            report += "\n"

        # 资源文件变更
        if impact['resource_changes']:
            report += "##### 资源文件变更\n\n"
            for file_path in sorted(impact['resource_changes']):
                report += f"- `{file_path}`\n"
            report += "\n"

        report += "---\n\n"

    return report

def generate_summary_report(commits, maven_info=None, repo_info=None):
    """生成总结报告"""
    summary = "# 📑 Git 提交汇总报告\n\n"
    
    # 仓库基本信息
    summary += "## 📌 仓库信息\n\n"
    summary += f"- **仓库名称**: `{repo_info['name']}`\n"
    summary += f"- **仓库路径**: `{repo_info['path']}`\n"
    summary += f"- **当前分支**: `{repo_info['branch']}`\n"
    summary += f"- **分析时间范围**: {repo_info['date_range']}\n"
    summary += f"- **报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # 基本统计
    total_commits = len(commits)
    total_insertions = sum(commit['stats']['insertions'] for commit in commits)
    total_deletions = sum(commit['stats']['deletions'] for commit in commits)
    authors = {commit['author'] for commit in commits}
    
    # 变更文件统计
    all_files = set()
    file_types = defaultdict(int)
    for commit in commits:
        for file_path in commit['files'].keys():
            all_files.add(file_path)
            ext = os.path.splitext(file_path)[1].lower()
            if ext:
                file_types[ext] += 1
            else:
                file_types['无扩展名'] += 1
    
    # 生成摘要文本
    summary += "## 📊 变更概览\n\n"
    summary += f"- 总提交次数: **{total_commits}** 次\n"
    summary += f"- 参与开发人数: **{len(authors)}** 人\n"
    summary += f"- 变更文件数: **{len(all_files)}** 个\n"
    summary += f"- 代码变更: **+{total_insertions}** 行, **-{total_deletions}** 行\n"
    
    if maven_info and maven_info['modules']:
        summary += f"- Maven模块数: **{len(maven_info['modules'])}** 个\n"
    
    # 作者贡献统计
    authors_stats = defaultdict(lambda: {'commits': 0, 'insertions': 0, 'deletions': 0})
    for commit in commits:
        author = commit['author']
        authors_stats[author]['commits'] += 1
        authors_stats[author]['insertions'] += commit['stats']['insertions']
        authors_stats[author]['deletions'] += commit['stats']['deletions']
    
    summary += "\n## 👥 开发者贡献\n\n"
    summary += "| 开发者 | 提交次数 | 添加行数 | 删除行数 |\n"
    summary += "|--------|----------|----------|----------|\n"
    # 按提交次数排序
    for author, stats in sorted(authors_stats.items(), key=lambda x: x[1]['commits'], reverse=True):
        summary += f"| {author} | {stats['commits']} | +{stats['insertions']} | -{stats['deletions']} |\n"
    
    # 文件类型统计（使用新的分类方法）
    file_types = analyze_file_changes(commits)
    if file_types:
        summary += "\n## 📁 文件类型分布\n\n"
        summary += "| 文件类型 | 文件数量 | 变更次数 | 添加行数 | 删除行数 | 占比 |\n"
        summary += "|----------|----------|----------|----------|----------|------|\n"
        
        total_files = sum(len(stats['files']) for stats in file_types.values())
        
        # 按文件数量排序
        sorted_types = sorted(
            file_types.items(),
            key=lambda x: len(x[1]['files']),
            reverse=True
        )
        
        for file_type, stats in sorted_types:
            file_count = len(stats['files'])
            percentage = (file_count / total_files) * 100
            summary += f"| {file_type} | {file_count} | {stats['changes']} | +{stats['insertions']} | -{stats['deletions']} | {percentage:.1f}% |\n"
        
        # 添加文件列表
        summary += "\n### 文件清单\n\n"
        for file_type, stats in sorted_types:
            if stats['files']:
                summary += f"#### {file_type}\n\n"
                for file_path in sorted(stats['files']):
                    summary += f"- `{file_path}`\n"
                summary += "\n"
    
    # 主要变更内容
    summary += "\n## 💡 主要变更内容\n\n"
    
    # 按日期分组统计提交信息
    date_commits = defaultdict(list)
    for commit in commits:
        date = commit['date'].strftime('%Y-%m-%d')
        date_commits[date].append(commit['message'].split('\n')[0])  # 只取第一行
    
    # 生成每日变更摘要
    for date in sorted(date_commits.keys(), reverse=True):
        summary += f"### 📅 {date}\n\n"
        for msg in date_commits[date]:
            summary += f"- {msg}\n"
        summary += "\n"
    
    # 如果是Maven项目，添加模块影响分析
    if maven_info and maven_info['modules']:
        # 生成模块影响分析
        module_impacts = analyze_module_impact(commits, maven_info)
        impact_report = generate_impact_report(module_impacts)
        summary += "\n" + impact_report

    return summary

def generate_index_file(output_dir, summary_file, detail_file, maven_file=None, repo_info=None):
    """生成美观的索引文件"""
    index_content = f"""# 🔍 Git 提交分析报告

## 📌 基本信息

- **仓库名称**: `{repo_info['name']}`
- **分析分支**: `{repo_info['branch']}`
- **时间范围**: {repo_info['date_range']}
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📑 报告导航

### 1️⃣ [总结报告](./summary/{summary_file})

总结报告包含以下内容：
- 变更概览统计
- 开发者贡献分析
- 文件类型分布
- 主要变更内容

### 2️⃣ [详细报告](./details/{detail_file})

详细报告包含以下内容：
- 完整的提交记录
- 文件变更详情
- 代码行变化统计
"""

    if maven_file:
        index_content += f"""
### 3️⃣ [Maven 项目分析](./maven/{maven_file})

Maven 项目分析包含：
- 模块依赖分析
- 模块影响范围
- 文件类型分类
- 详细变更清单
"""

    index_content += """
## 📊 报告说明

1. **总结报告**：适合快速了解项目变更概况
2. **详细报告**：适合深入查看具体变更内容
3. **Maven分析**：适合了解模块级别的变更影响

## 🔍 快速链接

- [返回上级目录](../)
- [查看资源文件](./assets/)

---
*报告由 Git 提交分析工具自动生成*
"""

    return index_content

def main():
    parser = argparse.ArgumentParser(description='生成Git仓库的提交报告')
    parser.add_argument('repo_path', help='Git仓库的本地路径')
    parser.add_argument('--start-date', help='开始日期 (YYYY-MM-DD格式)')
    parser.add_argument('--end-date', help='结束日期 (YYYY-MM-DD格式)')
    parser.add_argument('--date', '-dt', choices=['today', 'yesterday', 'thisweek', 'lastweek', 'thismonth', 'lastmonth'],
                      help='日期快捷方式')
    parser.add_argument('--output', '-o', help='输出文件路径（可选，默认根据仓库名和日期自动生成）')
    parser.add_argument('--output-dir', '-d', help='输出目录（可选，默认为 ./git_reports/仓库名）')
    parser.add_argument('--branch', '-b', help='指定要分析的分支（可选，默认为当前分支）')
    parser.add_argument('--authors', '-a', nargs='+', help='指定要分析的作者列表（可选，支持多个作者）')
    parser.add_argument('--list-branches', '-l', action='store_true', help='列出所有可用的分支')
    parser.add_argument('--list-authors', '-la', action='store_true', help='列出所有提交过的作者')
    parser.add_argument('--maven', '-m', action='store_true', help='生成Maven项目详细分析报告')
    
    args = parser.parse_args()
    
    # 检查路径是否存在
    if not os.path.exists(args.repo_path):
        print(f"错误: 路径 '{args.repo_path}' 不存在")
        sys.exit(1)
    
    # 处理日期范围
    if args.date:
        start_date, end_date = get_date_range(args.date)
    else:
        start_date = parse_date(args.start_date) if args.start_date else None
        end_date = parse_date(args.end_date) if args.end_date else None
    
    # 创建报告生成器实例（带有指定的分支）
    generator = GitReportGenerator(args.repo_path, args.branch)
    
    # 显示分析信息
    print(f"\n正在分析仓库: {args.repo_path}")
    print(f"当前分支: {generator.current_branch}")
    print(f"查找条件: {format_search_conditions(args.branch, args.authors, start_date, end_date, args.date)}")
    
    # 如果是列出分支，则显示分支列表后退出
    if args.list_branches:
        print("\n可用的分支:")
        branches = generator.get_branches()
        for branch in branches:
            current_marker = "* " if branch['is_current'] else "  "
            print(f"{current_marker}{branch['name']}")
        sys.exit(0)
    
    # 如果只是列出作者，则显示作者列表后退出
    if args.list_authors:
        print("\n仓库的所有提交作者:")
        authors = generator.get_authors()
        for author in authors:
            print(f"  {author}")
        sys.exit(0)
    
    # 获取提交记录
    commits = generator.get_commits_in_range(start_date, end_date, args.authors)
    
    if not commits:
        print("警告: 在指定时间范围内没有找到任何提交记录")
        sys.exit(0)
    
    # 获取Maven项目信息（如果需要）
    maven_info = None
    maven_report = None
    if args.maven:
        maven_info = analyze_maven_project(args.repo_path)
        if maven_info['modules']:
            maven_report = generate_maven_report(maven_info, commits)
    
    # 确定输出目录（移到获取maven_info之后）
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = generate_report_directory(
            generator.repo_name,
            args.branch,
            args.date,
            start_date,
            end_date,
            maven_info
        )
    
    # 准备仓库信息
    repo_info = {
        'name': generator.repo_name,
        'path': generator.repo_path,
        'branch': generator.current_branch,
        'date_range': generator._format_date_range(start_date, end_date)
    }
    
    # 生成总结报告
    summary_report = generate_summary_report(commits, maven_info, repo_info)
    
    # 生成详细报告
    detail_report = generator.generate_markdown_report(commits, start_date, end_date)
    if maven_report:
        detail_report += "\n---\n\n" + maven_report
    
    # 确定输出文件名
    output_file = args.output if args.output else generate_output_filename(
        generator.repo_name,
        args.branch,
        args.authors,
        start_date,
        end_date,
        args.date
    )
    
    # 生成报告文件名
    summary_file = f"summary-{output_file}"
    detail_file = f"detail-{output_file}"
    maven_file = f"maven-{output_file}" if maven_report else None
    
    # 保存报告
    summary_path = generator.save_report(summary_report, output_dir, summary_file)
    detail_path = generator.save_report(detail_report, output_dir, detail_file)
    
    if maven_report:
        maven_path = generator.save_report(maven_report, output_dir, maven_file)
    
    # 生成索引文件
    index_content = generate_index_file(
        output_dir,
        summary_file,
        detail_file,
        maven_file,
        repo_info
    )
    
    index_path = generator.save_report(index_content, output_dir, "index.md")
    
    # 输出结果
    print("\n📊 报告生成完成！")
    print(f"\n📂 报告目录: {output_dir}")
    print("\n📑 生成的文件:")
    print(f"- 索引文件: {index_path}")
    print(f"- 总结报告: {summary_path}")
    print(f"- 详细报告: {detail_path}")
    if maven_report:
        print(f"- Maven分析: {maven_path}")
    print("\n✨ 完成！")

if __name__ == "__main__":
    main() 