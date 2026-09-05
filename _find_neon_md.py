# -*- coding: utf-8 -*-
"""Find and print migration-related neon reports"""
import os
import sys

base = r"F:\scan\neon_report"
for f in sorted(os.listdir(base)):
    if not f.lower().endswith(".md"):
        continue
    if any(k in f for k in ["数据", "迁移", "Anonym", "repack", "内置", "横切", "平台库"]):
        print("FOUND:", f)
