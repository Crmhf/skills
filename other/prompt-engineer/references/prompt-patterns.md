# Prompt 设计模式

高效 Prompt 设计的常用模式与技巧。

## 目录

- [角色模式](#角色模式)
- [Few-Shot 模式](#few-shot-模式)
- [Chain-of-Thought](#chain-of-thought)
- [结构化输出](#结构化输出)

---

## 角色模式

为 AI 定义明确的角色和背景。

### 基本模板

```markdown
# Role
You are an expert [ROLE] with [X] years of experience in [DOMAIN].
Your expertise includes [SKILL1], [SKILL2], and [SKILL3].

## Communication Style
- Professional yet approachable
- Use clear, concise language
- Provide specific examples when helpful

## Approach
1. Analyze the problem thoroughly
2. Consider multiple solutions
3. Recommend the best option with reasoning
```

### 示例

```markdown
# Role
You are a senior software architect specializing in distributed systems.
With 15 years of experience at companies like Google and Amazon,
you excel at designing scalable, resilient architectures.

## Communication Style
- Technical but accessible
- Use analogies to explain complex concepts
- Always consider trade-offs
```

---

## Few-Shot 模式

通过示例教 AI 理解任务模式。

### 基本模板

```markdown
## Task
[Task description]

## Examples

Input: [Example input 1]
Output: [Example output 1]

Input: [Example input 2]
Output: [Example output 2]

## Your Turn
Input: {user_input}
Output:
```

### 分类任务示例

```markdown
Classify the sentiment as POSITIVE, NEGATIVE, or NEUTRAL.

Examples:
Text: "I love this product!"
Sentiment: POSITIVE

Text: "This is terrible quality."
Sentiment: NEGATIVE

Text: "The package arrived on time."
Sentiment: NEUTRAL

Text: {user_text}
Sentiment:
```

---

## Chain-of-Thought

引导 AI 逐步推理，提高复杂任务准确性。

### 基础模式

```markdown
Solve this step by step:
1. Identify the key information
2. Analyze the relationships
3. Apply the appropriate formula/method
4. Calculate the result
5. Verify the answer

Problem: {problem}
```

### 进阶模式 (Zero-Shot CoT)

```markdown
Q: [Question]
A: Let's think step by step.
```

### Self-Consistency

```markdown
Solve this problem 3 different ways and compare the results.
If there's disagreement, analyze why and provide your best answer.

Problem: {problem}
```

---

## 结构化输出

要求 AI 以特定格式输出。

### JSON 输出

```markdown
Analyze the following text and output JSON with this structure:
{
  "sentiment": "positive|negative|neutral",
  "confidence": 0.0-1.0,
  "key_phrases": ["phrase1", "phrase2"],
  "summary": "brief summary"
}

Text: {text}

Output only the JSON, no other text.
```

### Markdown 表格

```markdown
Compare the following products and output as a markdown table
columns: Feature, Product A, Product B, Winner

Products:
- Product A: {details}
- Product B: {details}
```

### 检查清单格式

```markdown
Review this code and output findings as a checklist:
- [ ] Issue 1: description
- [ ] Issue 2: description

Code:
```
{code}
```
```

---

## 高级技巧

### 思维树 (Tree of Thoughts)

```markdown
Problem: {problem}

Explore 3 different approaches:

Approach 1: [Description]
Pros: ...
Cons: ...

Approach 2: [Description]
Pros: ...
Cons: ...

Approach 3: [Description]
Pros: ...
Cons: ...

Now evaluate which approach is best and explain why.
```

### 反思模式

```markdown
Initial answer: {initial_answer}

Critique your answer:
- What could be wrong?
- What assumptions did you make?
- What edge cases weren't considered?

Now provide an improved answer.
```

---

## 检查清单

- [ ] 角色定义是否清晰？
- [ ] 任务描述是否具体？
- [ ] 是否提供了示例（Few-Shot）？
- [ ] 复杂任务是否有推理步骤？
- [ ] 输出格式是否明确？
- [ ] 是否设置了约束条件？
