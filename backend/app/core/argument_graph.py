import re
import uuid

from app.agents.base_agent import AgentResult


def _key(text: str) -> str:
    return re.sub(r"[^a-z]", "", (text or "").lower())


def resolve_agent(name: str, candidates) -> object | None:
    """Match a name the model wrote against an actual agent.

    Agents get named in whichever form the model reaches for: "Wittgenstein",
    "wittgensteinian", "the Kantian". The original matcher asked whether the
    written name appeared inside the node label, which fails for every
    adjectival form — "wittgensteinian" is not a substring of "wittgenstein",
    it is longer — so nearly every challenge edge was silently dropped and the
    graph showed a debate in which nobody answered anybody.
    """
    want = _key(name)
    if not want:
        return None
    fallback = None
    for c in candidates:
        label = _key(getattr(c, "agent_name", None) or c.get("label", "").split(" (")[0])
        arche = _key(getattr(c, "archetype", None) or c.get("archetype", ""))
        if want in (label, arche):
            return c
        # Containment both ways, so "wittgensteinian" finds Wittgenstein and
        # "the marxist" finds the marxist. Four characters minimum: shorter
        # fragments start matching things they should not.
        for form in (label, arche):
            if len(form) >= 4 and (form in want or want in form):
                fallback = fallback or c
    return fallback


def build_argument_graph(all_rounds: list[list[AgentResult]]) -> dict:
    """
    Build a D3-compatible force-directed graph from all debate rounds.
    Returns {nodes: [...], edges: [...]}
    """
    nodes = []
    edges = []
    seen_nodes = set()

    # Root node: the claim itself
    claim_node_id = "claim_root"
    nodes.append({
        "id": claim_node_id,
        "label": "Claim",
        "type": "claim",
        "group": 0,
    })

    for round_positions in all_rounds:
        for pos in round_positions:
            node_id = f"{pos.agent_id}_r{pos.round_number}"
            if node_id not in seen_nodes:
                seen_nodes.add(node_id)
                nodes.append({
                    "id": node_id,
                    "label": f"{pos.agent_name} (R{pos.round_number})",
                    "archetype": pos.archetype,
                    "belief_score": pos.belief_score,
                    "argument_content": pos.argument_content,
                    "round": pos.round_number,
                    "type": "position",
                    "group": pos.round_number,
                })

            # Edge from this position to the claim root (round 1) or to previous round position
            if pos.round_number == 1:
                edges.append({
                    "id": str(uuid.uuid4()),
                    "source": node_id,
                    "target": claim_node_id,
                    "type": pos.argument_type,
                    "strength": pos.argument_strength,
                    "label": pos.argument_type,
                })
            else:
                # Connect to same agent's previous round
                prev_node_id = f"{pos.agent_id}_r{pos.round_number - 1}"
                if prev_node_id in seen_nodes:
                    edges.append({
                        "id": str(uuid.uuid4()),
                        "source": node_id,
                        "target": prev_node_id,
                        "type": "updates",
                        "strength": 0.5,
                        "label": "updates",
                    })

            # Cross-agent challenge edges (round 2)
            if pos.round_number == 2 and pos.challenges:
                for challenge in pos.challenges:
                    target_agent_name = challenge.get("target_agent", "")
                    round1_nodes = [n for n in nodes if n.get("round") == 1]
                    target_node = resolve_agent(target_agent_name, round1_nodes)
                    if target_node:
                        edges.append({
                            "id": str(uuid.uuid4()),
                            "source": node_id,
                            "target": target_node["id"],
                            "type": challenge.get("type", "contradicts"),
                            "strength": 0.8,
                            "label": challenge.get("type", "contradicts"),
                            "challenge_text": challenge.get("challenge", ""),
                        })

    return {"nodes": nodes, "edges": edges}


def extract_unknown_unknowns(all_rounds: list[list[AgentResult]]) -> list[str]:
    """Collect questions that no agent could answer."""
    all_questions = []
    for round_positions in all_rounds:
        for pos in round_positions:
            all_questions.extend(pos.unanswered_questions)

    # Deduplicate roughly (a full version would cluster semantically)
    seen = set()
    unique = []
    for q in all_questions:
        q_normalized = q.lower().strip()
        if q_normalized not in seen and q_normalized:
            seen.add(q_normalized)
            unique.append(q)

    return unique[:10]  # Top 10 unknown unknowns
