from mcp.server.fastmcp import FastMCP
from datetime import datetime
import math

mcp = FastMCP("MathTimeServer")

@mcp.tool()
def get_current_time(timezone: str = "UTC") -> str:
    """获取指定时区的当前时间（时区格式如'Asia/Shanghai'）"""
    try:
        now = datetime.now().astimezone()
        return f"{now:%Y-%m-%d %H:%M:%S} {now.tzname()}"
    except Exception as e:
        return f"错误：{str(e)}"

# @mcp.tool()
# def calculate_expression(expression: str) -> float:
#     """计算数学表达式（支持+-*/^和math库函数）"""
#     try:
#         # 安全过滤（可根据需求扩展）
#         allowed_chars = set("0123456789+-*/.^()eπ ")
#         if not all(c in allowed_chars for c in expression):
#             raise ValueError("包含非法字符")
            
#         # 替换常见数学符号
#         expr = expression.replace('^', '​**​').replace('π', 'math.pi')
#         return eval(f"math.{expr}" if 'math.' not in expr else expr)
#     except Exception as e:
#         return f"计算错误：{str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")