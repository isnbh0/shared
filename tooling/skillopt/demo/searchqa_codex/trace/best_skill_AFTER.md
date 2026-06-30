# Question Answering Skill

When answering a factoid question, return only the shortest exact answer span that directly answers the question and is supported by the context. Do not add explanation, restate the question, or include surrounding context unless the question explicitly asks for it.

Formatting rule: put only the final answer span INSIDE the `<answer>` and `</answer>` tags. A bare word, number, name, or short phrase is correct when that is the minimal answer.
