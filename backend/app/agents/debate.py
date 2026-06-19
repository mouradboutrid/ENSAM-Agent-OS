from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from typing import Optional

from app.core.llm import LLMManager
from app.core.routing import ModelRouter


@dataclass
class DebateMessage:
    agent_name: str
    role: str
    content: str
    round_num: int


@dataclass
class DebateResult:
    topic: str
    rounds: list[DebateMessage] = field(default_factory=list)
    synthesis: str = ""
    total_rounds: int = 0


class DebateEngine:
    def __init__(self, llm_manager: LLMManager, router: ModelRouter):
        self.llm = llm_manager
        self.router = router

    async def run_debate(
        self, topic: str, agent_a_name: str = "Agent A", agent_b_name: str = "Agent B",
        rounds: int = 3, force_local: bool = False,
    ) -> DebateResult:
        result = DebateResult(topic=topic, total_rounds=rounds)

        system_a = f"You are {agent_a_name} in an academic debate. Argue FOR the following position. Be concise and evidence-based. Respond to counter-arguments when presented."
        system_b = f"You are {agent_b_name} in an academic debate. Argue AGAINST the following position. Be concise and evidence-based. Respond to counter-arguments when presented."

        history_a = [{"role": "system", "content": system_a}]
        history_b = [{"role": "system", "content": system_b}]

        for round_num in range(1, rounds + 1):
            if round_num == 1:
                history_a.append({"role": "user", "content": f"Debate topic: {topic}\n\nPresent your opening argument FOR this position."})
            else:
                last_b = result.rounds[-1].content
                history_a.append({"role": "user", "content": f"Your opponent argues:\n{last_b}\n\nRespond and strengthen your position."})

            resp_a, _ = await self.router.generate(history_a, force_local=force_local)
            result.rounds.append(DebateMessage(agent_name=agent_a_name, role="for", content=resp_a.content, round_num=round_num))
            history_a.append({"role": "assistant", "content": resp_a.content})

            history_b.append({"role": "user", "content": f"Your opponent argues:\n{resp_a.content}\n\nRespond and argue AGAINST the position."})
            resp_b, _ = await self.router.generate(history_b, force_local=force_local)
            result.rounds.append(DebateMessage(agent_name=agent_b_name, role="against", content=resp_b.content, round_num=round_num))
            history_b.append({"role": "assistant", "content": resp_b.content})

        synthesis_messages = [
            {"role": "system", "content": "You are a neutral academic judge. Synthesize the debate arguments into a balanced conclusion."},
            {"role": "user", "content": f"Topic: {topic}\n\n" + "\n\n".join([f"[Round {m.round_num} - {m.agent_name} ({m.role})]:\n{m.content}" for m in result.rounds]) + "\n\nProvide a balanced synthesis and conclusion."},
        ]
        synth_resp, _ = await self.router.generate(synthesis_messages, force_local=force_local)
        result.synthesis = synth_resp.content

        return result
