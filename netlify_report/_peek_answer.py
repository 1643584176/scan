# -*- coding: utf-8 -*-
# _peek_answer.py - extract answerAgentRunnerSession + interaction payload format
import re
src = open(r"D:\scan\netlify_report\_js\net_lib.js", encoding="utf-8", errors="replace").read()
i = src.find("answerAgentRunnerSession")
print(src[i-400:i+700])
print("\n\n=== createAgentRunnerSession ===")
j = src.find("createAgentRunnerSession")
print(src[j-100:j+900])
