# Git 提交分析工具

## 📋 功能介绍

这是一个强大的 Git 仓库分析工具，可以生成详细的提交报告，特别适合分析 Maven 项目的变更情况。

### 主要功能

- 📊 提交统计分析
  - 支持按时间范围、作者、分支筛选
  - 提供多种时间快捷方式（今天、本周、本月等）
  - 详细的代码变更统计

- 📦 Maven 项目分析
  - 模块依赖分析
  - 文件类型分类统计
  - 模块影响范围分析

- 📈 丰富的报告内容
  - 生成总结报告和详细报告
  - 支持 Markdown 格式输出
  - 自动生成报告索引

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本用法

1. 生成基本报告：
```bash
python git_report.py /path/to/repo
```

2. 分析指定时间范围：
```bash
python git_report.py /path/to/repo --start-date 2024-01-01 --end-date 2024-01-31
```

3. 使用时间快捷方式：
```bash
python git_report.py /path/to/repo --date today
python git_report.py /path/to/repo --date thisweek
python git_report.py /path/to/repo --date thismonth
```

4. 分析特定作者的提交：
```bash
python git_report.py /path/to/repo --authors "张三" "李四"
```

5. 分析特定分支：
```bash
python git_report.py /path/to/repo --branch develop
```

6. Maven 项目分析：
```bash
python git_report.py /path/to/repo --maven
```

### 📅 支持的时间快捷方式

- `today`: 今天的变更
- `yesterday`: 昨天的变更
- `thisweek`: 本周的变更
- `lastweek`: 上周的变更
- `thismonth`: 本月的变更
- `lastmonth`: 上个月的变更

### 📊 报告内容

生成的报告包含以下内容：

1. 总结报告 (summary-*.md)
   - 仓库基本信息
   - 变更概览统计
   - 开发者贡献统计
   - 文件类型分布
   - 模块影响分析（Maven项目）

2. 详细报告 (detail-*.md)
   - 完整的提交记录
   - 文件变更详情
   - Maven 项目详细分析

3. 索引文件 (index.md)
   - 报告导航
   - 内容概览

### 🎯 Maven 项目分析

对于 Maven 项目，工具会额外生成以下分析：

1. 模块影响分析
   - POM 文件变更
   - SQL 文件变更
   - Java 源码变更
   - 配置文件变更
   - 测试代码变更
   - 资源文件变更

2. 变更分类统计
   - 按模块统计变更
   - 按文件类型统计
   - 详细的文件清单

## 📝 命令行参数

```
参数说明：
  repo_path              Git 仓库的本地路径
  --start-date           开始日期 (YYYY-MM-DD格式)
  --end-date             结束日期 (YYYY-MM-DD格式)
  --date, -dt            日期快捷方式
  --output, -o           输出文件路径
  --output-dir, -d       输出目录
  --branch, -b           指定分析的分支
  --authors, -a          指定分析的作者列表
  --list-branches, -l    列出所有可用的分支
  --list-authors, -la    列出所有提交过的作者
  --maven, -m            生成Maven项目详细分析
```

## 📂 输出目录结构

默认的输出目录结构如下：

```
reports/
└── {repo_name}/
    └── {YYYYMM}/
        └── {branch}/
            └── {date_range}/
                ├── index.md
                ├── summary-*.md
                └── detail-*.md
```

## 🔧 配置建议

1. 对于大型仓库：
   - 建议指定时间范围，避免分析过多历史记录
   - 可以按作者或分支进行筛选

2. 对于 Maven 项目：
   - 建议使用 --maven 参数获取更详细的分析
   - 关注模块间的依赖关系

3. 报告管理：
   - 建议使用默认的目录结构
   - 定期清理旧的报告文件

## 📚 最佳实践

1. 日常代码审查
```bash
python git_report.py /path/to/repo --date today --maven
```

2. 周报生成
```bash
python git_report.py /path/to/repo --date thisweek --maven
```

3. 项目里程碑总结
```bash
python git_report.py /path/to/repo --start-date 2024-01-01 --end-date 2024-01-31 --maven
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进这个工具！

## 📄 许可证