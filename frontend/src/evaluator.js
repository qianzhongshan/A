/**
 * MBTI前端评估引擎 - 双层LLM架构
 * 完全在浏览器中运行，无需后端
 */

class MBTIEvaluator {
  constructor(apiKey = '', baseUrl = 'https://api.deepseek.com', model = 'deepseek-chat') {
    this.apiKey = apiKey
    this.baseUrl = baseUrl
    this.model = model
  }

  /**
   * 评估单道题目（第一层）
   */
  async evaluateSingleQuestion(question, answer) {
    if (!this.apiKey) {
      return {
        question_id: question.id,
        dimension: question.dimension,
        score: 5,
        confidence: 0.5,
        reasoning: '请先配置API密钥',
        key_quotes: []
      }
    }

    const prompt = this.buildFirstLayerPrompt(question, answer)

    try {
      const response = await fetch(`${this.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`
        },
        body: JSON.stringify({
          model: this.model,
          messages: [
            { role: 'system', content: '你是一位专业的MBTI评估分析师。' },
            { role: 'user', content: prompt }
          ],
          temperature: 0.3,
          response_format: { type: 'json_object' }
        })
      })

      if (!response.ok) {
        const error = await response.text()
        throw new Error(`API调用失败: ${response.status} - ${error}`)
      }

      const data = await response.json()
      const result = JSON.parse(data.choices[0].message.content)

      return {
        question_id: question.id,
        dimension: question.dimension,
        score: Math.max(0, Math.min(10, parseInt(result.score) || 5)),
        confidence: Math.max(0, Math.min(1, parseFloat(result.confidence) || 0.5)),
        reasoning: (result.reasoning || '').slice(0, 100),
        key_quotes: (result.key_quotes || []).slice(0, 3)
      }
    } catch (error) {
      console.error('评估题目失败:', error)
      return {
        question_id: question.id,
        dimension: question.dimension,
        score: 5,
        confidence: 0.3,
        reasoning: `评估失败: ${error.message.slice(0, 50)}`,
        key_quotes: []
      }
    }
  }

  /**
   * 生成最终报告（第二层）
   */
  async generateFinalReport(assessments, dimensionScores) {
    if (!this.apiKey) {
      return {
        personality_summary: '请先配置API密钥以生成报告',
        dimension_analysis: {
          EI: '无数据',
          SN: '无数据',
          TF: '无数据',
          JP: '无数据'
        },
        caveats: '系统未启用',
        recommendations: '请在设置中输入有效的OpenAI API密钥'
      }
    }

    const summary = this.buildSummary(dimensionScores, assessments)
    const prompt = `你是一位MBTI认证分析师。根据用户的93道论述题评估结果，生成一份综合分析报告。

${summary}

请输出JSON格式：
{
 "personality_summary": "整体性格特征描述（100字内）",
 "dimension_analysis": {
   "EI": "该维度的具体分析（50字内）",
   "SN": "该维度的具体分析（50字内）",
   "TF": "该维度的具体分析（50字内）",
   "JP": "该维度的具体分析（50字内）
 },
 "caveats": "需要注意的事项（如低一致性维度、用户表达中的矛盾点等，50字内）",
 "recommendations": "给用户的建议（80字内）
}
`

    try {
      const response = await fetch(`${this.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`
        },
        body: JSON.stringify({
          model: this.model,
          messages: [
            { role: 'system', content: '你是一位经验丰富的MBTI分析师，擅长从评估数据中提炼洞察。' },
            { role: 'user', content: prompt }
          ],
          temperature: 0.5
        })
      })

      if (!response.ok) {
        throw new Error(`API调用失败: ${response.status}`)
      }

      const data = await response.json()
      const result = JSON.parse(data.choices[0].message.content)
      return result
    } catch (error) {
      console.error('生成报告失败:', error)
      return {
        personality_summary: `报告生成失败: ${error.message.slice(0, 50)}`,
        dimension_analysis: {
          EI: '生成失败',
          SN: '生成失败',
          TF: '生成失败',
          JP: '生成失败'
        },
        caveats: error.message.slice(0, 50),
        recommendations: '请稍后重试'
      }
    }
  }

  /**
   * 构建第一层评估提示词
   */
  buildFirstLayerPrompt(question, answer) {
    const dimensionDesc = {
      EI: '外向(E) vs 内向(I) - 能量来源、社交偏好、思考方式',
      SN: '实感(S) vs 直觉(N) - 信息收集、关注点、思维导向',
      TF: '思考(T) vs 情感(F) - 决策依据、价值判断、人际处理',
      JP: '判断(J) vs 感知(P) - 生活方式、计划性、开放性'
    }

    const anchors = {
      EI: { left: '外向(E)', right: '内向(I)' },
      SN: { left: '实感(S)', right: '直觉(N)' },
      TF: { left: '思考(T)', right: '情感(F)' },
      JP: { left: '判断(J)', right: '感知(P)' }
    }

    const dim = question.dimension
    const anchor = anchors[dim]

    return `你是一位MBTI专业评估分析师。请根据用户的论述，评估其在${question.dimension}维度上的倾向。

## 题目信息
题目ID：${question.id}
考察维度：${dimensionDesc[dim]}
细分面向：${question.sub_aspect || '未指定'}
题目：${question.open_ended}

## 用户论述
${answer}

## 评分标准
请评估用户在该维度上的倾向强度（0-10分）：
- 0-3分：强烈倾向${anchor.left}
- 4-6分：中间状态或混合倾向
- 7-10分：强烈倾向${anchor.right}

考虑因素：
- 用户描述的行为模式
- 表达的感受和偏好
- 具体例子中的表现
- 语言中的倾向性词汇

## 输出格式（严格JSON）
{
  "score": 0-10的整数,
  "confidence": 0-1之间的小数（评估的可信度）,
  "reasoning": "判断依据（20字内，简洁说明）",
  "key_quotes": ["用户论述中的关键句1", "关键句2"]
}

请评估：`
  }

  /**
   * 构建汇总报告的数据摘要
   */
  buildSummary(dimensionScores, assessments) {
    // 按维度分组
    const dimensionData = { EI: [], SN: [], TF: [], JP: [] }
    assessments.forEach(a => {
      if (dimensionData[a.dimension]) {
        dimensionData[a.dimension].push([a.score, a.confidence])
      }
    })

    let summary = '各维度加权平均得分：\n'
    ;['EI', 'SN', 'TF', 'JP'].forEach(dim => {
      const scores = dimensionData[dim]
      if (scores.length > 0) {
        const weightedSum = scores.reduce((sum, [s, c]) => sum + s * c, 0)
        const totalWeight = scores.reduce((sum, [, c]) => sum + c, 0)
        const avg = totalWeight > 0 ? weightedSum / totalWeight : 5
        dimensionScores[dim] = avg
        const left = dim === 'EI' ? 'E' : dim === 'SN' ? 'S' : dim === 'TF' ? 'T' : 'J'
        const right = dim === 'EI' ? 'I' : dim === 'SN' ? 'N' : dim === 'TF' ? 'F' : 'P'
        summary += `- ${dim}（${left}/${right}）：${avg.toFixed(1)}分（0=${left}，10=${right}）\n`
      }
    })

    summary += '\n各维度有效题目数及一致性：\n'
    ;['EI', 'SN', 'TF', 'JP'].forEach(dim => {
      const scores = dimensionData[dim]
      const count = scores.length
      if (count >= 3) {
        const values = scores.map(([s]) => s)
        const avg = values.reduce((a, b) => a + b, 0) / values.length
        const stdDev = Math.sqrt(values.reduce((sum, x) => sum + (x - avg) ** 2, 0) / values.length)
        let consistency
        if (stdDev < 1.5) consistency = '高度一致'
        else if (stdDev < 3) consistency = '中度一致'
        else consistency = '存在矛盾'
        summary += `- ${dim}：${count}题，一致性${consistency}\n`
      } else {
        summary += `- ${dim}：${count}题，信息不足\n`
      }
    })

    return summary
  }

  /**
   * 将得分转换为MBTI四字母
   */
  scoresToType(scores) {
    const ei = scores['EI'] < 5 ? 'E' : 'I'
    const sn = scores['SN'] < 5 ? 'S' : 'N'
    const tf = scores['TF'] < 5 ? 'T' : 'F'
    const jp = scores['JP'] < 5 ? 'J' : 'P'
    return `${ei}${sn}${tf}${jp}`
  }
}

export default MBTIEvaluator