import json
import re
import sys
import os
from typing import Dict, List, Any, Optional
from openai import OpenAI

# 添加 backend 目录到 Python 路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from config import settings
from database import get_db
from models import APICallLog
import time

class MBTIEvaluator:
    """MBTI评估引擎 - 双层LLM架构"""

    def __init__(self, api_enabled=None, api_key=None, base_url=None, model=None, cost_per_call=None):
        """
        初始化评估引擎
        参数优先从传入值获取，其次从settings获取
        """
        self.api_enabled = api_enabled if api_enabled is not None else settings.API_ENABLED
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.base_url = base_url or settings.DEEPSEEK_BASE_URL
        self.model = model or settings.DEEPSEEK_MODEL
        self.cost_per_call = cost_per_call or settings.COST_PER_CALL

        # 只在启用且有API key时初始化客户端
        if self.api_enabled and self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        else:
            self.client = None

    def evaluate_single_question(self, question: Dict, answer: str, session_id: str) -> Dict:
        """
        第一层：评估单道题目
        返回：score(0-10), confidence(0-1), reasoning, key_quotes
        """
        if not self.api_enabled:
            return {
                "question_id": question["id"],
                "dimension": question["dimension"],
                "score": 5,
                "confidence": 0.5,
                "reasoning": "API已禁用，返回默认值",
                "key_quotes": []
            }

        if not self.client:
            return {
                "question_id": question["id"],
                "dimension": question["dimension"],
                "score": 5,
                "confidence": 0.3,
                "reasoning": "API客户端未初始化（缺少API Key）",
                "key_quotes": []
            }

        prompt = self._build_first_layer_prompt(question, answer)
        start_time = time.time()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位专业的MBTI评估分析师。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            elapsed = time.time() - start_time
            result = json.loads(response.choices[0].message.content)

            # 记录API调用
            self._log_api_call(
                session_id=session_id,
                call_type="evaluate_single",
                question_id=question["id"],
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                cost=self.cost_per_call * response.usage.total_tokens / 1000,
                success=True
            )

            # 确保返回结构正确
            return {
                "question_id": question["id"],
                "dimension": question["dimension"],
                "score": max(0, min(10, int(result.get("score", 5)))),
                "confidence": max(0, min(1, float(result.get("confidence", 0.5)))),
                "reasoning": result.get("reasoning", "")[:100],
                "key_quotes": result.get("key_quotes", [])[:3]
            }

        except Exception as e:
            # 记录失败
            self._log_api_call(
                session_id=session_id,
                call_type="evaluate_single",
                question_id=question["id"],
                success=False,
                error=str(e)
            )
            return {
                "question_id": question["id"],
                "dimension": question["dimension"],
                "score": 5,
                "confidence": 0.3,
                "reasoning": f"评估失败: {str(e)[:50]}",
                "key_quotes": []
            }

    def generate_final_report(self, assessments: List[Dict], dimension_scores: Dict[str, float]) -> Dict:
        """
        第二层：生成最终报告
        """
        if not self.api_enabled:
            return {
                "personality_summary": "API已禁用，无法生成报告",
                "dimension_analysis": {d: "无数据" for d in ["EI", "SN", "TF", "JP"]},
                "caveats": "系统未启用",
                "recommendations": "请启用API后重新评估"
            }

        if not self.client:
            return {
                "personality_summary": "API客户端未初始化（缺少API Key）",
                "dimension_analysis": {d: "无法生成" for d in ["EI", "SN", "TF", "JP"]},
                "caveats": "请配置API Key",
                "recommendations": "请联系管理员配置系统"
            }

        summary = self._build_summary(dimension_scores, assessments)

        prompt = f"""你是一位MBTI认证分析师。根据用户的93道论述题评估结果，生成一份综合分析报告。

{summary}

请输出JSON格式：
{{
 "personality_summary": "整体性格特征描述（100字内）",
 "dimension_analysis": {{
   "EI": "该维度的具体分析（50字内）",
   "SN": "该维度的具体分析（50字内）",
   "TF": "该维度的具体分析（50字内）",
   "JP": "该维度的具体分析（50字内）"
 }},
 "caveats": "需要注意的事项（如低一致性维度、用户表达中的矛盾点等，50字内）",
 "recommendations": "给用户的建议（80字内）
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位经验丰富的MBTI分析师，擅长从评估数据中提炼洞察。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            return {
                "personality_summary": f"报告生成失败: {str(e)[:50]}",
                "dimension_analysis": {d: "生成失败" for d in ["EI", "SN", "TF", "JP"]},
                "caveats": str(e)[:50],
                "recommendations": "请稍后重试"
            }

    def _build_first_layer_prompt(self, question: Dict, answer: str) -> str:
        """构建第一层评估提示词"""
        dimension_desc = {
            "EI": "外向(E) vs 内向(I) - 能量来源、社交偏好、思考方式",
            "SN": "实感(S) vs 直觉(N) - 信息收集、关注点、思维导向",
            "TF": "思考(T) vs 情感(F) - 决策依据、价值判断、人际处理",
            "JP": "判断(J) vs 感知(P) - 生活方式、计划性、开放性"
        }

        anchors = {
            "EI": {"left": "外向(E)", "right": "内向(I)"},
            "SN": {"left": "实感(S)", "right": "直觉(N)"},
            "TF": {"left": "思考(T)", "right": "情感(F)"},
            "JP": {"left": "判断(J)", "right": "感知(P)"}
        }

        dim = question["dimension"]
        anchor = anchors[dim]

        return f"""你是一位MBTI专业评估分析师。请根据用户的论述，评估其在{question['dimension']}维度上的倾向。

## 题目信息
题目ID：{question['id']}
考察维度：{dimension_desc[dim]}
细分面向：{question.get('sub_aspect', '未指定')}
题目：{question['open_ended']}

## 用户论述
{answer}

## 评分标准
请评估用户在该维度上的倾向强度（0-10分）：
- 0-3分：强烈倾向{anchor['left']}
- 4-6分：中间状态或混合倾向
- 7-10分：强烈倾向{anchor['right']}

考虑因素：
- 用户描述的行为模式
- 表达的感受和偏好
- 具体例子中的表现
- 语言中的倾向性词汇

## 输出格式（严格JSON）
{{
  "score": 0-10的整数,
  "confidence": 0-1之间的小数（评估的可信度）,
  "reasoning": "判断依据（20字内，简洁说明）",
  "key_quotes": ["用户论述中的关键句1", "关键句2"]
}}

请评估："""

    def _build_summary(self, dimension_scores: Dict[str, float], assessments: List[Dict]) -> str:
        """构建汇总报告的数据摘要"""
        # 按维度分组
        dimension_data = {d: [] for d in ["EI", "SN", "TF", "JP"]}
        for a in assessments:
            dim = a["dimension"]
            if dim in dimension_data:
                dimension_data[dim].append((a["score"], a["confidence"]))

        summary = "各维度加权平均得分：\n"
        for dim in ["EI", "SN", "TF", "JP"]:
            scores = dimension_data[dim]
            if scores:
                weighted_sum = sum(s[0] * s[1] for s in scores)
                total_weight = sum(s[1] for s in scores)
                avg = weighted_sum / total_weight if total_weight > 0 else 5
                dimension_scores[dim] = avg
                left = "E" if dim == "EI" else "S" if dim == "SN" else "T" if dim == "TF" else "J"
                right = "I" if dim == "EI" else "N" if dim == "SN" else "F" if dim == "TF" else "P"
                summary += f"- {dim}（{left}/{right}）：{avg:.1f}分（0={left}，10={right}）\n"

        summary += "\n各维度有效题目数及一致性：\n"
        for dim in ["EI", "SN", "TF", "JP"]:
            scores = dimension_data[dim]
            count = len(scores)
            if count >= 3:
                values = [s[0] for s in scores]
                std_dev = (sum((x - sum(values)/len(values))**2 for x in values) / len(values))**0.5
                if std_dev < 1.5:
                    consistency = "高度一致"
                elif std_dev < 3:
                    consistency = "中度一致"
                else:
                    consistency = "存在矛盾"
            else:
                consistency = "信息不足"
            summary += f"- {dim}：{count}题，一致性{consistency}\n"

        return summary

    def _log_api_call(self, session_id: str, call_type: str, question_id: Optional[str] = None,
                     prompt_tokens: int = 0, completion_tokens: int = 0, total_tokens: int = 0,
                     cost: float = 0.0, success: bool = True, error: Optional[str] = None):
        """记录API调用"""
        try:
            db = next(get_db())
            log = APICallLog(
                session_id=session_id,
                call_type=call_type,
                question_id=question_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost=cost,
                success=success,
                error=error
            )
            db.add(log)
            db.commit()
        except Exception as e:
            print(f"Failed to log API call: {e}")

    def scores_to_type(self, scores: Dict[str, float]) -> str:
        """将得分转换为MBTI四字母"""
        ei = "E" if scores["EI"] < 5 else "I"
        sn = "S" if scores["SN"] < 5 else "N"
        tf = "T" if scores["TF"] < 5 else "F"
        jp = "J" if scores["JP"] < 5 else "P"
        return f"{ei}{sn}{tf}{jp}"
