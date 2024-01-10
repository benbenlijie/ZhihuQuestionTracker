# 知乎问题追踪器

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 简介

这是一个利用ChatGPT来辅助开发完成的，用于追踪知乎上潜力问题的程序。

## 功能特性

- 定时从知乎的网站中抓取具有潜力的问题
- 分析问题的数据变化，问题察看值的变化，回答数量的变化
- 可以通过GUI的交互从列表中选择出感兴趣的问题，加入到特别关注列表
- 通过GUI显示关注列表中问题的数据

## 安装指南

```bash
pip install -r requirements.txt
```

1. 下载[geckodriver](https://github.com/mozilla/geckodriver/releases)，然后解压缩到driver目录下。
2. 从浏览器中拷贝知乎网站的登录cookies，保存到cookies文件。


## 快速开始

```bash
python gui.py
```

## 许可证

此项目在 MIT 许可证下授权 - 详见 LICENSE.md 文件。
