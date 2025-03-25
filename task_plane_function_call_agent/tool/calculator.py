import operator
import re


def calculator(math_arithmetic_expression):
    # 定义运算符的优先级、结合性和对应的函数
    ops = {
        '^': {'prec': 4, 'assoc': 'right', 'func': operator.pow},
        '*': {'prec': 3, 'assoc': 'left', 'func': operator.mul},
        '/': {'prec': 3, 'assoc': 'left', 'func': operator.truediv},
        '+': {'prec': 2, 'assoc': 'left', 'func': operator.add},
        '-': {'prec': 2, 'assoc': 'left', 'func': operator.sub},
    }

    # 预处理表达式并拆分为token列表
    expr = math_arithmetic_expression.replace(' ', '').replace('×', '*').replace('−', '-').replace('÷', '/')
    tokens = re.findall(r"(\d+\.?\d*|[-+*/^()])", expr)

    # 将中缀表达式转换为后缀表达式
    output = []
    stack = []
    for token in tokens:
        if token in ops:
            while stack and stack[-1] != '(' and (
                    ops[stack[-1]]['prec'] > ops[token]['prec'] or
                    (ops[stack[-1]]['prec'] == ops[token]['prec'] and ops[token]['assoc'] == 'left')
            ):
                output.append(stack.pop())
            stack.append(token)
        elif token == '(':
            stack.append(token)
        elif token == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            if not stack:
                raise ValueError("Mismatched parentheses")
            stack.pop()  # 弹出左括号
        else:
            output.append(token)

    # 处理栈中剩余的运算符
    while stack:
        token = stack.pop()
        if token == '(':
            raise ValueError("Mismatched parentheses")
        output.append(token)

    # 计算后缀表达式
    stack = []
    for token in output:
        if token in ops:
            if len(stack) < 2:
                raise ValueError("Invalid expression: insufficient operands for operator {}".format(token))
            b = stack.pop()
            a = stack.pop()
            try:
                result = ops[token]['func'](a, b)
            except ZeroDivisionError:
                raise ValueError("Division by zero")
            stack.append(result)
        else:
            # 转换为数值类型
            if '.' in token:
                num = float(token)
            else:
                num = int(token)
            stack.append(num)

    if len(stack) != 1:
        raise ValueError("Invalid expression: malformed expression")
    return stack[0]


if __name__ == "__main__":
    # 示例用法
    expression = "(25+32)×(45−28)÷7+3 ^ 4"
    expression = "4 * 6+2^ 5/ 3-1"
    result = calculator(expression)
    print(f"计算结果: {result}")  # 计算结果: 219.42857142857142